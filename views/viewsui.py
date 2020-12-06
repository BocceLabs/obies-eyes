import sys

import cv2
import imutils
from PyQt5 import QtCore, QtWidgets
from PyQt5 import uic
from PyQt5.QtCore import QThread, QTimer
from PyQt5.QtGui import QImage, QPixmap

from games import USBCamera, PubSubImageZMQCamera, \
	RTSPCamera


class MovieThread(QThread):
    def __init__(self, camera):
        super().__init__()
        self.camera = camera

    def run(self):
        self.camera.acquire_movie()

class MainWindow(QtWidgets.QMainWindow):
    """
    constructor
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # load the ui file which was made with Qt Creator
        uic.loadUi("views/ui/oddball.ui", self)

        ### config tab ###
        self.tableWidget_cameras.clicked.connect(self.set_camera_source_data)
        self.initialize_tableWidget_cameras_checkedstate()

        ### court tab ###
        # each of the cameras are set up in the
        # set_camera_source_data() method
        self.cam1, self.movie_thread_cam1 = None, None
        self.cam2, self.movie_thread_cam2 = None, None
        self.cam3, self.movie_thread_cam3 = None, None
        self.cam4, self.movie_thread_cam4 = None, None
        self.cam5, self.movie_thread_cam5 = None, None
        self.cam6, self.movie_thread_cam6 = None, None
        self.cam8, self.movie_thread_cam7 = None, None
        self.cam8, self.movie_thread_cam8 = None, None

        # movie timer
        #self.movie_thread = None
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_movie)
        self.recording = False
        self.pushButton_record.clicked.connect(self.start_movie)

        # camera source radio buttons
        self.radioButton_cam1.clicked.connect(self.get_camera_source)
        self.radioButton_cam2.clicked.connect(self.get_camera_source)
        self.radioButton_cam3.clicked.connect(self.get_camera_source)
        self.radioButton_cam4.clicked.connect(self.get_camera_source)
        self.radioButton_cam5.clicked.connect(self.get_camera_source)
        self.radioButton_cam6.clicked.connect(self.get_camera_source)
        self.radioButton_cam7.clicked.connect(self.get_camera_source)

        # set the no camera image
        self.set_default_img()

    """
    sets the camera view to an oddball image residing on disk
    """
    def set_default_img(self):
        frame = cv2.imread('views/ui/oddball.png')
        frame = imutils.resize(frame, width = 600)
        height, width, channel = frame.shape
        bytesPerLine = 3 * width
        qImg = QImage(frame.data, width, height, bytesPerLine, QImage.Format_RGB888)

        self.label_camera.setPixmap(QPixmap(qImg))
        self.label_camera.repaint()

    """
    sets the camera view source from the radio buttons on the court tab
    @return (camera object, movie thread object)
    """
    def get_camera_source(self):
        # switch case to change the camera source
        if self.radioButton_cam1.isChecked():
            return self.cam1, self.movie_thread_cam1

        elif self.radioButton_cam2.isChecked():
            return self.cam2, self.movie_thread_cam2

        elif self.radioButton_cam3.isChecked():
            return self.cam3, self.movie_thread_cam3

        elif self.radioButton_cam4.isChecked():
            return self.cam4, self.movie_thread_cam4

        elif self.radioButton_cam5.isChecked():
            return self.cam5, self.movie_thread_cam5

        elif self.radioButton_cam6.isChecked():
            return self.cam6, self.movie_thread_cam6

        elif self.radioButton_cam7.isChecked():
            return self.cam7, self.movie_thread_cam7

        elif self.radioButton_cam8.isChecked():
            return self.cam8, self.movie_thread_cam8

        else:
            return None

    """
    this method reads the config tab camera table data
    @return table_data
    """
    def get_tableWidget_cameras_data(self, item):
        rows = self.tableWidget_cameras.rowCount()
        r=0

        table_data = []

        while r < rows:
            table_data.append(
                (
                "cam{}".format(r+1),
                self.tableWidget_cameras.item(r, 0).checkState() == QtCore.Qt.Checked,
                self.tableWidget_cameras.item(r, 1).text(),
                self.tableWidget_cameras.item(r, 2).text(),
                self.tableWidget_cameras.item(r, 3).text()
                )
            )
            r+=1
        #print(table_data)
        return table_data

    """
    this method unchecks all camera sources in the config tab table
    """
    def initialize_tableWidget_cameras_checkedstate(self):
        rows = self.tableWidget_cameras.rowCount()
        r=0
        while r < rows:
            self.tableWidget_cameras.item(r, 0).setCheckState(False)
            r+=1

    """
    this method reads the config tab table and sets up camera sources
    """
    def set_camera_source_data(self):
        table_data = self.get_tableWidget_cameras_data(self.tableWidget_cameras)

        # set Court1 radio button labels
        for t in table_data:
            # if the checkbox in column 1 is checked
            if t[1]:
                #self.radioButton_cam1.setText(t[4])
                getattr(self, "radioButton_{}".format(t[0])).setEnabled(True)
                getattr(self, "radioButton_{}".format(t[0])).setChecked(True)
                getattr(self, "radioButton_{}".format(t[0])).setText(t[4])

                # strip spaces from camera name for video filename purposes
                cam_name = t[4].replace(" ", "")

                # initialize the cameras based on type
                if t[2] == "USBCamera":
                    setattr(self, t[0], USBCamera(name=cam_name,
                        source=int(t[3])))
                elif t[2] == "RTSPCamera":
                    setattr(self, t[0], RTSPCamera(name=cam_name,
                        source=str(t[3])))
                elif t[2] == "PubSubImageZMQCamera":
                    setattr(self, t[0], PubSubImageZMQCamera(name=cam_name,
                        source=str(t[3])))

                # initialize the camera
                getattr(self, t[0]).initialize()

            else:
                getattr(self, "radioButton_{}".format(t[0])).setEnabled(False)

    """
    grabs an image from a camera and displays it
    """
    def get_image_from_cam(self):
        cam = self.get_camera_source()[0]
        frame = cam.get_frame()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width, channel = frame.shape
        bytesPerLine = 3 * width
        qImg = QImage(frame.data, width, height, bytesPerLine, QImage.Format_RGB888)
        self.label_camera.setPixmap(QPixmap(qImg))
        self.label_camera.repaint()

    """
    grabs frames from a camera and displays it continuously
    """
    def update_movie(self):
        frame = cv2.cvtColor(self.get_camera_source()[0].last_frame, cv2.COLOR_BGR2RGB)
        height, width, channel = frame.shape
        bytesPerLine = 3 * width
        qImg = QImage(frame.data, width, height,
            bytesPerLine, QImage.Format_RGB888)
        self.label_camera.setPixmap(QPixmap(qImg))
        self.label_camera.repaint()

    """
    starts movie threads for each active camera and sets the camera source to record
    """
    def start_movie(self):
        if self.recording:
            self.stop_movie()
            return

        table_data = self.get_tableWidget_cameras_data(self.tableWidget_cameras)

        for t in table_data:
            # if the checkbox in column 1 is checked, set it to record
            if t[1]:
                setattr(self, "movie_thread_{}".format(t[0]), MovieThread(getattr(self, t[0])))
                getattr(self, "movie_thread_{}".format(t[0])).start()
                getattr(self, t[0]).start_recording()
                print("started: movie_thread_{}".format(t[0]))

        self.recording = True
        self.update_timer.start(30)

        # cam, movie_thread = self.get_camera_source()
        # movie_thread = MovieThread(cam)
        # movie_thread.start()
        # self.update_timer.start(30)

    """
    stops all movie threads and sets recording to false
    """
    def stop_movie(self):
        table_data = self.get_tableWidget_cameras_data(self.tableWidget_cameras)

        for t in table_data:
            # if the checkbox in column 1 is checked, set it to record
            if t[1]:
                getattr(self, "movie_thread_{}".format(t[0])).quit()
                setattr(self, "movie_thread_{}".format(t[0]), None)
                getattr(self, t[0]).stop_recording()
                print("stopped: movie_thread_{}".format(t[0]))

        self.recording = False

        # movie_thread.quit()
        # time.sleep(.2)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec_()