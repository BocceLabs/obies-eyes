# USAGE
# This script is typically run via the UNIX systemd service
#    sudo systemctl start imagenode.service
#
# Or if you're running it standalone:
#    python client.py --server-ip Davids-MBP --server-port 5558

# import the necessary packages
from imutils.video import VideoStream
import argparse
import imagezmq
import socket
import time
import signal
import cv2

# constant for the patience timeout
TIMEOUT = 5

class Patience:
    """
    This class is borrowed from Jeff Bass' GitHub ImageNode

    Timing class using operating system SIGALRM signal.
    When instantiated, starts a timer using the system SIGALRM signal.
    If the timer expires before __exit__ is called, raises Timeout exception.
    Caveats:
    1. There can be only 1 active SIGALRM timer running per program. If a
       second SIGALRM timer is started, it replaces and nullifies the first one.
    2. This class can only be used in the main thread. Python only allows the
       use of SIGALRM in the main thread (or also in the main thread of a separate
       process? Don't know. Need to run the experiment.)
    Parameters:
        seconds (int): number of seconds to wait before raising exception
    """
    class Timeout(Exception):
        pass

    def __init__(self, seconds):
        self.seconds = seconds

    def __enter__(self):
        signal.signal(signal.SIGALRM, self.raise_timeout)
        signal.alarm(self.seconds)

    def __exit__(self, *args):
        signal.alarm(0)    # disable alarm

    def raise_timeout(self, *args):
        raise Patience.Timeout()

# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-s", "--server-ip", required=True,
    help="ip address of the server to which the client will connect")
ap.add_argument("-p", "--server-port", required=True,
    help="ip address of the server to which the client will connect")
args = vars(ap.parse_args())

# initialize the ImageSender object with the socket address of the
# server
sender = imagezmq.ImageSender(connect_to="tcp://{}:{}".format(
    args["server_ip"], args["server_port"]))

# get the host name, initialize the video stream, and allow the
# camera sensor to warmup
rpiName = socket.gethostname()

# USB camera is commented out
#vs = VideoStream(src=0).start()

# use the PiCamera instead
vs = VideoStream(usePiCamera=True).start()

# wait for the camera to warm up
time.sleep(2.0)

# loop over frames from the camera
while True:
    # read a frame from the camera stream
    frame = vs.read()

    # flip horizontally and vertically
    frame = cv2.flip(frame, -1)

    # begins a try/catch block
    try:
        # be patient for 5 seconds
        with Patience(TIMEOUT):
            # send an image to the ImageHub
            hub_reply = sender.send_image(rpiName, frame)

    # if 5 seconds passed with no response from ImageHub, then catch
    # the timeout
    except Patience.Timeout:
        print('TIMOUT: No imagehub reply for ' + str(int(TIMEOUT)) + ' seconds')
        print('RESTART: The systemd service handles restarting this script if it is running')
