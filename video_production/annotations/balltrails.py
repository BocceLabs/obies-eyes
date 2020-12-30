# imports
from .annotation import Annotation
import cv2

class BallTrails(Annotation):
    def __init__(self):
        super(BallTrails, self).__init__()

    def _annotate(self, frame, balltrails=None, *args, **kwargs):
        return frame