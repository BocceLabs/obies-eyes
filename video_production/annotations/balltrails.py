# imports
from .annotation import Annotation
import cv2

class BallTrails(Annotation):
    def _annotate(self, frame, balltrails=None, *args, **kwargs):
        return frame