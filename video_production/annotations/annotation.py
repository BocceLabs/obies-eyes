class Annotation():
    def __init__(self):
        self.active = False

    def activate(self):
        self.active = True

    def deactivate(self):
        self.active = False

    """frame is expected to be in BGR color space"""
    def annotate(self, frame, *args, **kwargs):
        # annotate if this annotation is active
        if self.active:
            return self._annotate(frame, *args, **kwargs)

        # otherwise, don't annotate
        else:
            return frame

    """annotation logic happens here"""
    def _annotate(self, frame, *args, **kwargs):
        pass
