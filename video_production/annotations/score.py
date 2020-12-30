# imports
from PIL import ImageFont, ImageDraw, Image
import cv2
import numpy as np
import imutils

# typically we'll import modularly
try:
    from .annotation import Annotation
    unit_test = False

# otherwise, we're running main test code at the bottom of this script
except:
    import sys
    import os
    sys.path.append(os.path.abspath(os.pardir))
    from annotation import Annotation

    unit_test = True




class Score(Annotation):
    def __init__(self):
        super(Score, self).__init__()

        # load Luckiest Guy font
        if unit_test:
            self.font = ImageFont.truetype(
                "../../fonts/Luckiest_Guy/LuckiestGuy-Regular.ttf",
                size=220)

        else:
            self.font = ImageFont.truetype(
                "fonts/Luckiest_Guy/LuckiestGuy-Regular.ttf",
                size=220)



    def _annotate(self, frame, score=None, relFrameSize=0.20, *args, **kwargs):
        # force score to 0-0 if no score is passed or if it is unknown
        if score is None:
            score = (0, 0)

        # convert to string and fill with another digit
        teamHomeScore = str(score[0]).zfill(2)
        teamAwayScore = str(score[1]).zfill(2)

        if unit_test:
            scoreboard = Image.open(
                "../graphics/scoreboard.png")
        else:
            scoreboard = Image.open("video_production/graphics/scoreboard.png")

        # prepare the image for drawing
        draw = ImageDraw.Draw(scoreboard)

        # determine the placement of characters
        x = scoreboard.size[0] / 16
        y = scoreboard.size[1] / 4

        # first digit
        xMult = 0.32 if teamHomeScore[0] == "0" else 1
        draw.text(xy=(x*xMult, y),
                  text=teamHomeScore[0],
                  align="center",
                  font=self.font)

        # second digit
        draw.text(xy=(x*4.2, y),
                  text=teamHomeScore[1],
                  align="center",
                  font=self.font)

        # third digit
        xMult = 8.25 if teamAwayScore[0] == "0" else 8.6
        draw.text(xy=(x*xMult, y),
                  text=teamAwayScore[0],
                  align="center",
                  font=self.font)

        # fourth digit
        draw.text(xy=(x*12.3, y),
                  text=teamAwayScore[1],
                  align="center",
                  font=self.font)

        # load the scoreboard into OpenCV format
        scoreboard = cv2.cvtColor(np.array(scoreboard), cv2.COLOR_RGBA2BGR)

        # resize the scoreboard relative to the frame
        h, w = frame.shape[:2]
        scoreboard = imutils.resize(scoreboard, width=int(w * relFrameSize))
        sH, sW = scoreboard.shape[:2]

        # slice the scoreboard into the frame
        frame[20:20+sH, 20:20+sW] = scoreboard

        # return the frame
        return frame



# test code
if __name__ == "__main__":
    homeScore = 10
    awayScore = 10
    score = (homeScore, awayScore)
    frame = cv2.imread("../../views/ui/oddball.png")
    s = Score()
    s.activate()
    scoreboard = s.annotate(frame, score)
    cv2.imwrite("tmp_home-{}_away-{}.png".format(
        str(homeScore).zfill(2),
        str(awayScore).zfill(2)),
        scoreboard)