# imports
from .annotation import Annotation
import cv2

class Venue(Annotation):
    def __init__(self):
        super(Venue, self).__init__()

    def _annotate(self, frame, venue=None, *args, **kwargs):
        return frame