# imports
import imutils
import time
import cv2
import imagezmq
import threading
import numpy as np
import multiprocessing as mp
from datetime import datetime

class Camera:
    def __init__(self, name, source):
        self.name = name
        self.source = source
        self.recording = False
        self.fourcc = cv2.VideoWriter_fourcc(*"MP4V")
        self.writer = None
        self.h = None
        self.w = None

    def initialize(self):
        pass

    def get_frame(self):
        pass

    def acquire_movie(self):
        while True:
            if self.recording:
                if self.writer is None:
                    (self.h, self.w) = self.get_frame().shape[:2]
                    filename = self.name + "_" + \
                        datetime.now().strftime("%Y-%m-%d_%H%M%S") + \
                        ".mp4"
                    self.writer = cv2.VideoWriter(filename, self.fourcc,
                        25, (self.w, self.h), True)
                self.writer.write(self.get_frame())
            else:
                self.get_frame()

    def start_recording(self):
        self.recording = True

    def stop_recording(self):
        self.recording = False
        self.writer.release()
        self.writer = None

    def __str__(self):
        return "{}: {}".format(self.__class__.__name__, self.name, self.source)

    def close_camera(self):
        pass


class USBCamera(Camera):
    def __init__(self, name, source):
        self.name = name
        self.recording = False
        self.fourcc = cv2.VideoWriter_fourcc(*"MP4V")
        self.writer = None
        self.h = None
        self.w = None

        self.source = int(source)
        self.width = 600
        self.last_frame = None

    def initialize(self):
        self.cap = cv2.VideoCapture(self.source)
        time.sleep(2)
        self.get_frame()

    def get_frame(self):
        ret, frame = self.cap.read()
        self.last_frame = imutils.resize(frame, width=self.width)
        return self.last_frame

    def close_camera(self):
        self.cap.release()

class RTSPCamera(Camera):
    def __init__(self, name, source):
        self.name = name
        self.recording = False
        self.fourcc = cv2.VideoWriter_fourcc(*"MP4V")
        self.writer = None
        self.h = None
        self.w = None

        self.source = str(source)
        self.receiver = None
        self.width = 600
        self.last_frame = None

    def initialize(self):
        # use multiprocessing
        self.parent_conn, child_conn = mp.Pipe()
        self.is_open = True
        self.p = mp.Process(target=self.rtsp_update, args=(child_conn, self.source, self.is_open))

        # start the process
        self.p.daemon = True
        self.p.start()
        self.get_frame()

    def get_frame(self):
        # request a frame and send ack
        self.parent_conn.send(1)
        frame = self.parent_conn.recv()
        self.parent_conn.send(0)

        # convert to RGB and resize
        #frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self.last_frame = imutils.resize(frame, width=self.width)
        return self.last_frame

    def rtsp_update(self, conn, rtsp, is_open):
        cap = cv2.VideoCapture(rtsp)  # ,cv2.CAP_FFMPEG)
        while is_open:
            # grab frames from the buffer
            cap.grab()

            # recieve input data
            rec_dat = conn.recv()
            if rec_dat == 1:
                # if frame requested
                ret, frame = cap.read()
                conn.send(frame)
            elif rec_dat == 2:
                # if close requested
                cap.release()
                break
        print("Camera Connection Closed")
        conn.close()

    def close_camera(self):
        self.is_open = False

class ImageZMQCamera(Camera):
    def __init__(self, name, source):
        self.name = name
        self.recording = False
        self.fourcc = cv2.VideoWriter_fourcc(*"MP4V")
        self.writer = None
        self.h = None
        self.w = None


        self.image_hub = imagezmq.ImageHub()
        self.last_frame = None
        self.source = str(source)

    def get_frame(self):
        rpi_name, frame = self.image_hub.recv_image()
        #image = cv2.imdecode(np.frombuffer(jpg_buffer, dtype='uint8'), -1)
        self.image_hub.send_reply(b'OK')
        self.last_frame = imutils.resize(frame, width=600)
        return self.last_frame

    def close_camera(self):
        self.image_hub = None

class PubSubImageZMQCamera(Camera):
    def __init__(self, name, source):
        self.name = name
        self.source = source
        self.recording = False
        self.fourcc = cv2.VideoWriter_fourcc(*"MP4V")
        self.writer = None
        self.h = None
        self.w = None

        self.hostname = str(source)
        self.port = 5555
        self.receiver = None
        self.last_frame = None

    def initialize(self):
        self.receiver = VideoStreamSubscriber(self.hostname, self.port)
        self.get_frame()

    def get_frame(self):
        msg, frame = self.receiver.receive()
        image = cv2.imdecode(np.frombuffer(frame, dtype='uint8'), -1)

        self.last_frame = imutils.resize(image, width=600)
        return self.last_frame

    def close_camera(self):
        self.receiver.close()

class VideoStreamSubscriber:
    def __init__(self, hostname, port):
        self.hostname = hostname
        self.port = port
        self._stop = False
        self._data_ready = threading.Event()
        self._thread = threading.Thread(target=self._run, args=())
        self._thread.daemon = True
        self._thread.start()

    def receive(self, timeout=15.0):
        flag = self._data_ready.wait(timeout=timeout)
        if not flag:
            raise TimeoutError(
                "Timeout while reading from subscriber tcp://{}:{}".format(self.hostname, self.port))
        self._data_ready.clear()
        return self._data

    def _run(self):
        receiver = imagezmq.ImageHub("tcp://{}:{}".format(self.hostname, self.port), REQ_REP=False)
        while not self._stop:
            self._data = receiver.recv_jpg()
            self._data_ready.set()
        receiver.close()

    def close(self):
        self._stop = True



def get_balls(self, color=None):
    blueLower = (57, 22, 21)
    blueUpper = (154, 255, 163)

    redLower = (129, 125, 88)
    redUpper = (255, 255, 255)

    yellowLower = (0, 17, 64)
    yellowUpper = (54, 151, 255)

    if color == "blue":
        lower = blueLower
        upper = blueUpper
        color_circle = (255, 0, 0)
    elif color == "red":
        lower = redLower
        upper = redUpper
        color_circle = (0, 0, 255)
    elif color == "yellow":
        lower = yellowLower
        upper = yellowUpper
        color_circle = (255, 255, 0)
    else:
        return self.get_frame()


    frame = self.get_frame()


    hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)



    mask = cv2.inRange(hsv, lower, upper)
    mask = cv2.erode(mask, None, iterations=2)
    mask = cv2.dilate(mask, None, iterations=1)

    # find contours in the mask and initialize the current
    # (x, y) center of the ball
    cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    center = None

    # only proceed if at least one contour was found
    for cnt in cnts:
        # find the largest contour in the mask, then use
        # it to compute the minimum enclosing circle and
        # centroid
        #c = cnt.contourArea()

        ((x, y), radius) = cv2.minEnclosingCircle(cnt)
        M = cv2.moments(cnt)
        center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
        # only proceed if the radius meets a minimum size
        if radius > 5 and radius < 20:
            # draw the circle and centroid on the frame,
            # then update the list of tracked points
            cv2.circle(frame, (int(x), int(y)), int(radius),
                       color_circle, 2)
            #cv2.circle(frame, center, 2, (0, 0, 255), -1)

    self.last_frame = frame
    return self.last_frame