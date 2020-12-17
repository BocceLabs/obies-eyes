# imports
from .annotation import Annotation
import cv2

class Team(Annotation):
    def _annotate(self, frame, team=None, *args, **kwargs):
        return frame