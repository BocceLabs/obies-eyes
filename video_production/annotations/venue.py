# imports
from .annotation import Annotation
import cv2

class Venue(Annotation):
    def _annotate(self, frame, venue=None, *args, **kwargs):
        return frame