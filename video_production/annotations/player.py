# imports
from .annotation import Annotation
import cv2

class Player(Annotation):
    def _annotate(self, frame, player=None, *args, **kwargs):
        return frame