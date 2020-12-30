class Ball:
    def __init__(self, color, roi=None):
        self.color = color
        self.roi = roi

        self.coordinates = (None, None)
        self.coordinates_history = []
        self.isThrown = False
        self.isMoving = False
        self.contactedAnotherBall = False
        self.thrownBy = None
        self.inPlay = None

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
