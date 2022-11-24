import sys

import os
import time

# add the parent directory (absolute, not relative) to the sys.path
# (this makes the games package imports work)
sys.path.append(os.path.abspath(os.pardir))

import cv2
import imutils
from PyQt5 import QtCore, QtWidgets
from PyQt5 import uic
from PyQt5.QtCore import QThread, QTimer
from PyQt5.QtGui import QImage, QPixmap, QColor
from PyQt5 import QtTest
from PyQt5.QtWidgets import QTableWidgetItem
from games.bocce.cv.motion_detector import MotionDetector
from games.bocce.cv.ball_finder import BallFinder

from vimba import *

# bocce imports
from games.bocce.game import Game
from games.camera.camera import USBCamera, RTSPCamera, PubSubImageZMQCamera, ImageZMQCamera, VimbaCamera

# config
import config

class MovieThread(QThread):
    def __init__(self, camera):
        super().__init__()
        self.camera = camera

    def run(self):
        print("attempting to acquire movie")
        self.camera.acquire_movie()

    def quit(self):
        self.camera.stop_recording()

class MainWindow(QtWidgets.QMainWindow):
    """
    constructor
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # load the ui file which was made with Qt Creator
        uic.loadUi("views/ui/oddball.ui", self)

        # motion detection
        self.motion = False
        self.motionDetector = MotionDetector(drawMotionZones=False)
        self.checkBox_motion_draw.stateChanged.connect(self.motion_box_state_change)

        # ball finding
        self.ballFinder = BallFinder()

        ### court tab ###
        # each of the cameras are set up in the
        # set_camera_source_data() method
        self.radioButton_cam1.setEnabled(True)
        self.radioButton_cam2.setEnabled(True)
        self.cam1, self.movie_thread_cam1 = None, None
        self.cam2, self.movie_thread_cam2 = None, None

        VIMBA = Vimba.get_instance()
        VIMBA._startup()

        self.cam1 = VimbaCamera(name="DEV_000F315DAB70", source="DEV_000F315DAB70", flip=False)
        self.cam1._initialize(VIMBA)

        # self.cam2 = VimbaCamera(name="DEV_000F315DAB39", source="DEV_000F315DAB39", flip=False)
        # self.cam2._initialize(VIMBA)

        # movie timer
        self.movie_thread = None
        self.movie_thread_timer = QTimer()
        self.movie_thread_timer.timeout.connect(self.update_movie)
        self.movie_ticker = 0

        # game timer and down/back setting
        self.GAME_MINUTES = None
        self.DOWN_BACK_ENABLED = None
        self.gameTimer = QTimer()
        self.time_min_left = 0
        self.time_sec_left = 0
        self.game_time_ui_update()

        self.pushButton_adjust_picture.clicked.connect(self.adjust_picture)

        # minimal game info
        self.teamHome_name = ""
        self.teamAway_name = ""

        # camera source radio buttons
        #self.radioButton_cam1.clicked.connect(self.get_camera_source)
        #self.radioButton_cam2.clicked.connect(self.get_camera_source)

        # set the no camera image
        # self.label_camera.setScaledContents(True)
        self.set_default_img()

        # scoring
        self.g = None
        self.th = None
        self.toggleFrame = 1

        # recording
        ### config tab ###
        self.start_movie()

    def closeEvent(self, event):
        """
        Runs when the QMainWindow is closed
        :param event:
        :return:
        """
        self.movie_thread_cam1.quit()
        #self.movie_thread_cam2.quit()

    def motion_box_state_change(self, state):
        if state == QtCore.Qt.Checked:
            self.motionDetector.drawMotionZones = True
        else:
            self.motionDetector.drawMotionZones = False

    def set_default_img(self):
        frame = cv2.imread('views/ui/oddball.png')
        frame = imutils.resize(frame, width = 600)
        height, width, channel = frame.shape
        bytesPerLine = 3 * width
        qImg = QImage(frame.data, width, height, bytesPerLine, QImage.Format_RGB888)

        self.label_camera.setPixmap(QPixmap(qImg))
        self.label_camera.repaint()

    def get_camera_source(self):
        """
        sets the camera view source from the radio buttons on the court tab
        :return:
        """
        # switch case to change the camera source
        if self.radioButton_cam1.isChecked():
            return self.cam1, self.movie_thread_cam1

        elif self.radioButton_cam2.isChecked():
            return self.cam2, self.movie_thread_cam2

        else:
            return self.cam1, self.movie_thread_cam1

    def get_image_from_cam(self):
        """
        grabs an image from a camera and displays it
        :return:
        """
        cam = self.get_camera_source()[0]
        frame = cam.get_frame()

        #frame = cv2.resize(frame, (800, 600))
        #print(frame.shape)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width, channel = frame.shape
        bytesPerLine = 3 * width
        qImg = QImage(frame.data, width, height, bytesPerLine, QImage.Format_RGB888)
        self.label_camera.setPixmap(QPixmap(qImg))
        self.label_camera.repaint()
        return frame

    def adjust_picture(self):
        # settings
        self.cam1.cam.ExposureAuto.set('Once')
        QtTest.QTest.qWait(4000)
        self.cam1.cam.ExposureAuto.set('Off')

        self.cam1.cam.GainAuto.set('Once')
        QtTest.QTest.qWait(4000)
        self.cam1.cam.GainAuto.set('Off')

        self.cam1.cam.BalanceWhiteAuto.set('Once')
        QtTest.QTest.qWait(4000)
        self.cam1.cam.BalanceWhiteAuto.set('Off')

    def update_ball_info(self, ballinfo):
        self.lcdNumber_home_ballsoncourt.display(ballinfo["home"]["balls_on_court"])
        self.lcdNumber_away_ballsoncourt.display(ballinfo["away"]["balls_on_court"])
        self.lcdNumber_home_num_in.display(ballinfo["home"]["balls_in"])
        self.lcdNumber_away_num_in.display(ballinfo["away"]["balls_in"])
        self.label_closest_ball_dist_home.setText("{:.2f}".format(ballinfo["home"]["closest_ball_dist"]))
        self.label_closest_ball_dist_away.setText("{:.2f}".format(ballinfo["away"]["closest_ball_dist"]))

    def update_movie(self):
        """
        grabs frames from a camera and displays it continuously
        :return:
        """
        # grab the last frame from the selected camera source
        frame = self.get_camera_source()[0].last_frame

        # swap color channels for Qt GUI default
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # resize
        frame = imutils.resize(frame, width = 600)

        # motion detection
        frame, self.motion = self.motionDetector.update(frame)
        if self.motion:
            self.label_motion.setText("Motion...")
        else:
            self.label_motion.setText("")

        # ball finder
        if not self.motion:
            frame, ballinfo = self.ballFinder.update(frame)
            self.update_ball_info(ballinfo)

        # paint the label_camera frame area
        height, width, channel = frame.shape
        bytesPerLine = 3 * width
        qImg = QImage(frame.data, width, height,
            bytesPerLine, QImage.Format_RGB888)
        self.label_camera.setPixmap(QPixmap(qImg))
        self.label_camera.repaint()

    def start_movie(self):
        """
        starts movie threads for each active camera and sets the camera source to record
        :return:
        """
        self.movie_thread_cam1 = MovieThread(self.cam1)
        self.movie_thread_cam1.start()

        # self.movie_thread_cam2 = MovieThread(self.cam1)
        # self.movie_thread_cam2.start()

        self.movie_thread_timer.start(30)

    def stop_movie(self):
        """
        stops movie threads for each active camera and sets the camera source to record
        :return:
        """
        # otherwise, record all camera feeds
        table_data = self.get_tableWidget_cameras_data(self.tableWidget_cameras)
        for t in table_data:
            # if the checkbox in column 1 is checked, set it to record
            if t[1]:
                getattr(self, "movie_thread_{}".format(t[0])).quit()
                print("stopped: movie_thread_{}".format(t[0]))
        self.tableWidget_cameras.setEnabled(True)

    def time_tick(self):
        """
        this method is called each time a second passes
        :return:
        """
        # subtract a second
        self.time_sec_left -= 1

        # if the seconds < 0, we need to account for minutes
        if self.time_sec_left < 0:
            # subtract a minute
            self.time_min_left -= 1

            # if there are no more minutes
            if self.time_min_left < 0:
                self.time_is_out = True
                self.time_min_left = 0
                self.time_sec_left = 0

            # otherwise, the seconds are set to 59
            else:
                self.time_sec_left = 59

        # update the timer on the UI
        self.game_time_ui_update()


    def game_time_ui_update(self):
        """
        this method updates the time indicator on the GUI
        :return:
        """
        pass
        #self.lcdNumber_game_time_remaining_min.display(str(self.time_min_left).zfill(2))
        #self.lcdNumber_game_time_remaining_sec.display(str(self.time_sec_left).zfill(2))



if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec_()