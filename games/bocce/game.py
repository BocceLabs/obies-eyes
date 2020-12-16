# imports
from .frame import Frame
import time


class Timer():
    # todo implement timer
    def __init__(self, minutes):
        self.minutes = minutes
        self.outOfTime = None

    def start(self):
        self.outOfTime = False

    def get_remaining(self):
        # todo don't use RANDOM remaining time ;)
        import random
        return random.uniform(3.0, 15.0)

    def stop(self):
        self.outOfTime = True

class Game:
    def __init__(self, teamHome, teamAway, umpire, playTo=12, gameMinutes=25):
        self.playTo = playTo

        self.teamHome = teamHome
        self.teamAway = teamAway

        self.teamHomeScore = 0
        self.teamAwayScore = 0
        self.gameWinner = None

        self.orientation = None

        self.umpire = umpire

        self.teamHome_points = 0
        self.teamAway_points = 0
        self.framepoints = 0

        # game timer
        self.timeRemaining = None

        self.down_and_back = False

        self.currentFrame = None
        self.frameCount = 0
        self.frames = []
        


    def set_umpire(self, umpire):
        self.umpire = umpire

    def get_throwing_end(self):
        if self.orientation == None:
            raise ValueError("You forgot to assign the game to a court")

        # zero
        if self.frameCount == 0:
            return "not started!"
        # odd
        elif self.frameCount % 2 == 1:
            return self.orientation.split("-")[0]
        # even
        elif self.frameCount % 2 == 0:
            return self.orientation.split("-")[1]



    def play_next_frame(self):
        pallinoThrowingTeam = self.get_pallino_throwing_team()
        self.currentFrame = Frame(frameNumber=self.frameCount,
                                  throwingEnd=self.get_throwing_end(),
                                  pallinoThrowingTeam=pallinoThrowingTeam,
                                  teamHome=self.teamHome,
                                  teamAway=self.teamAway)
        self.frames.append(self.currentFrame)
        self.currentFrame.initialize_balls(len(self.teamHome.players))
        self.frameCount += 1
        self.currentFrame.frame_runner()

    def get_pallino_throwing_team(self):
        if self.frameCount == 0:
            return self.teamHome
        else:
            return self.currentFrame.frameWinner

    def play_a_frame(self):
        self.play_next_frame()
        self.end_frame_and_set_score()
        self.print_score()
        if self.teamHomeScore >= self.playTo:
            self.gameWinner = self.teamHome
            self.end()
        elif self.teamAwayScore >= self.playTo:
            self.gameWinner = self.teamAway
            self.end()
        if not self.timeRemaining:
            self.end()

    def end_frame_and_set_score(self):
        self.frameWinner, self.framePoints = self.currentFrame.end()
        if self.frameWinner == self.teamHome:
            self.teamHomeScore += self.framePoints
        elif self.frameWinner == self.teamAway:
            self.teamAwayScore += self.framePoints

    def get_frame_count(self):
        return self.frameCount

    def print_score(self):
        home = self.teamHomeScore
        away = self.teamAwayScore

        if home > away:
            print("[SCORE] {}={} leads {}={}\n".format(
                self.teamHome, home, self.teamAway, away))
        elif away > home:
            print("[SCORE] {}={} leads {}={}\n".format(
                self.teamAway, away, self.teamHome, home))
        elif away == home:
            print("[SCORE] {}={} tied with {}={}\n".format(
                self.teamAway, away, self.teamHome, home))

    def start(self):
        self.timeRemaining = True

    def time_is_up(self):
        print("[INFO] out of time!")
        self.end()

    def end(self):
        print("[INFO] Game over.")
        self.print_score()


    def __str__(self):
        return "{}: {}, home={} vs. away={}".format(self.__class__.__name__,
            self.umpire, self.teamHome, self.teamAway)




