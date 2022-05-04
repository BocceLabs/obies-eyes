# imports
from collections import deque
import numpy as np

#  constants
PIXELS_PER_FOOT = 132
METERS_PER_FOOT = 0.3048
CAMERA_RESOLUTION_PIXELS = (2464, 2056) # Allied Vision Mako G-507C
CAMERA_CENTER_PIXELS = (CAMERA_RESOLUTION_PIXELS[0] / 2, CAMERA_RESOLUTION_PIXELS[1] / 2)
CAMERA_CENTER_TRANSLATION_FEET = (0, 8.75)

# FIFO Queue
COORD_SENSOR_QUEUE_LENGTH = 50

# min max difference to determine if a ball is moving
# 11 sensor pixels is an inch, so going with approximately half of that
MIN_MAX_DIFF_IS_MOVING = 3

class Ball:
    def __init__(self, objectID, color):
        # object id
        self.objectID = objectID

        # coordinates
        self.coord_sensor_q = deque(maxlen=COORD_SENSOR_QUEUE_LENGTH)
        self.sma_q = deque(maxlen=COORD_SENSOR_QUEUE_LENGTH // 10)
        self.coord_court_imperial = (None, None)
        self.coord_court_metric = (None, None)

        # color
        self.color = color

        # throw logic
        self.isThrown = None
        self.isMoving = None
        self.in_bounds = None

    def add_coord_sensor(self, coord_sensor):
        # ensure the sensor coordinates are two elements
        assert len(coord_sensor) == 2

        # set the sensor coordinates
        self.coord_sensor_q.append(tuple(coord_sensor))

    def _get_sma_coord_sensor(self):
        q_len = len(self.coord_sensor_q)

        # average
        q_sum = ( sum(i[0] for i in self.coord_sensor_q), sum(i[1] for i in self.coord_sensor_q) )
        q_sma = ( q_sum[0] / q_len, q_sum[1] / q_len )

        # add to the sma queue
        self.sma_q.append(q_sma)

        return q_sma

    def sensor_to_smoothed_court_coord(self):
        # grab the sma coordinates
        sma_coord_sensor = self._get_sma_coord_sensor()

        # determine if the ball is moving
        self._is_moving()

        x_pixels = sma_coord_sensor[0]
        y_pixels = sma_coord_sensor[1]
        x_pixels_centered = x_pixels - CAMERA_CENTER_PIXELS[0]
        y_pixels_centered = y_pixels - CAMERA_CENTER_PIXELS[1]
        x_feet = y_pixels_centered / PIXELS_PER_FOOT + CAMERA_CENTER_TRANSLATION_FEET[0] # intentionally based on y
        y_feet = x_pixels_centered / PIXELS_PER_FOOT + CAMERA_CENTER_TRANSLATION_FEET[1] # intentionally based on x
        self.coord_court_imperial = (x_feet, y_feet)

        # set the metric court coordinates
        self.coord_court_metric = (x_feet * METERS_PER_FOOT, y_feet * METERS_PER_FOOT)

    def set_thrower(self, player):
        self.thrownBy = player

    def _is_moving(self):
        # check to see if the sma_q of averages is changing by looking at the min and max
        min_x = min(self.sma_q, key=lambda x: x[0])[0]
        max_x = max(self.sma_q, key=lambda x: x[0])[0]
        min_y = min(self.sma_q, key=lambda x: x[1])[1]
        max_y = max(self.sma_q, key=lambda x: x[1])[1]

        # determine the difference between min and max
        diff_x = max_x - min_x
        diff_y = max_y - min_y

        # if the difference is sufficiently large, then the ball is moving
        if diff_x > MIN_MAX_DIFF_IS_MOVING or diff_y > MIN_MAX_DIFF_IS_MOVING:
            self.isMoving = True
        else:
            self.isMoving = False

        return self.isMoving

    def tracking(self):
        # todo
        # keep history
        # keep head coordinate

        pass

    def stop_tracking(self):
        # when the ball hits the back wall without touching a ball first
        # when the ball exits the court
        # when the ball doesn't make it to the centerline
        pass


class Pallino(Ball):
    pass

class Bocce(Ball):
    pass
