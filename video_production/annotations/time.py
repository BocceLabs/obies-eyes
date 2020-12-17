# imports
from .annotation import Annotation
import cv2

class Time(Annotation):
    def _annotate(self, frame, time=None, *args, **kwargs):
        return frame