# imports
from .frame import Frame
import time

class Game:
    def __init__(self, teamHome, teamAway):
        self.teamHome = teamHome
        self.teamAway = teamAway

        self.teamHomeScore = 0
        self.teamAwayScore = 0
        self.gameWinner = None

        self.teamHome_points = 0
        self.teamAway_points = 0
        self.framepoints = 0

        # game timer
        self.timeRemaining = None

        self.frames = []

    def end_frame_and_set_score(self):
        self.frameWinner, self.framePoints = self.currentFrame.end()
        if self.frameWinner == self.teamHome:
            self.teamHomeScore += self.framePoints
        elif self.frameWinner == self.teamAway:
            self.teamAwayScore += self.framePoints




