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
QUEUE_LENGTH = 20

class Ball:
    def __init__(self, objectID, color):
        # object id
        self.objectID = objectID

        # coordinates
        self.coord_sensor_q = deque(maxlen=QUEUE_LENGTH)
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
        if len(self.coord_sensor_q) >= QUEUE_LENGTH:
            # average
            q_sum = ( sum(i[0] for i in self.coord_sensor_q), sum(i[1] for i in self.coord_sensor_q) )
            q_sma = ( q_sum[0] / QUEUE_LENGTH, q_sum[1] / QUEUE_LENGTH )
            return q_sma

        else:
            return self.coord_sensor_q[-1]

    def sensor_to_smoothed_court_coord(self):
        # determine the imperial court coordinates
        sma_coord_sensor = self._get_sma_coord_sensor()
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

    def is_moving(self):
        # todo: determine if the ball is still in motion
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


if __name__ == "__main__":
    b = Ball("red")
    b.add_coord_sensor((0, 10))
    b.add_coord_sensor((1, 11))
    b.add_coord_sensor((2, 12))
    b.add_coord_sensor((3, 13))
    b.add_coord_sensor((4, 14))
    b.add_coord_sensor((5, 15))
    b.add_coord_sensor((6, 15))
    b.add_coord_sensor((7, 15))
    b.add_coord_sensor((8, 15))
    b.add_coord_sensor((9, 15))
    b.add_coord_sensor((10, 15))
    b.add_coord_sensor((11, 15))
    b.add_coord_sensor((12, 15))
    b.add_coord_sensor((13, 15))
    b.add_coord_sensor((14, 15))
    b.add_coord_sensor((15, 15))
    b.add_coord_sensor((16, 15))
    b.add_coord_sensor((17, 15))
    b.add_coord_sensor((18, 15))
    b.add_coord_sensor((19, 15))
    b.add_coord_sensor((20, 15))
    b.add_coord_sensor((21, 15))
    b.add_coord_sensor((22, 15))
    b.add_coord_sensor((23, 15))
    b.add_coord_sensor((24, 15))
    b.add_coord_sensor((25, 15))
    b.add_coord_sensor((26, 15))


    print(b._get_sma_coord_sensor())