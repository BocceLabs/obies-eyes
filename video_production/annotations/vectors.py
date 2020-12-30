# imports
import cv2
import numpy as np
from PIL import ImageFont, ImageDraw, Image
from scipy.spatial import distance as dist

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

# for now, these are "pixels" (not "inches" or "cm")
TOO_CLOSE_MARGIN = 5

class Vectors(Annotation):
    def __init__(self):
        super(Vectors, self).__init__()

        # load Luckiest Guy font
        if unit_test:
            self.font = ImageFont.truetype(
                "../../fonts/Luckiest_Guy/LuckiestGuy-Regular.ttf",
                size=30)

        else:
            self.font = ImageFont.truetype(
                "fonts/Luckiest_Guy/LuckiestGuy-Regular.ttf",
                size=30)

    # todo sometimes the second balls are "tooCloseToCall"
    # todo need to account for that in the future
    def _annotate(self, frame, pallino=None, homeBalls=None, awayBalls=None, *args, **kwargs):
        # ball format is list of Ball objects

        if pallino is None:
            print("not annotating; couldn't find pallino")

        # grab frame dimensions
        (h, w) = frame.shape[:2]

        # calculate Euclidean distance for each ball to the pallino
        homeBallsDistances = []
        awayBallsDistances = []
        for ball in homeBalls:
            D = dist.euclidean(pallino.coordinates, ball.coordinates)
            homeBallsDistances.append(D)
        for ball in awayBalls:
            D = dist.euclidean(pallino.coordinates, ball.coordinates)
            awayBallsDistances.append(D)

        # sort balls and distances
        homeBallsDistances, homeBalls = zip(*sorted(zip(homeBallsDistances, homeBalls)))
        awayBallsDistances, awayBalls = zip(*sorted(zip(awayBallsDistances, awayBalls)))

        # grab each min distance (the 0th element in the sorted list)
        homeBallsMinDistance = homeBallsDistances[0]
        awayBallsMinDistance = awayBallsDistances[0]

        # who is closer?
        homeIsCloser = homeBallsMinDistance < awayBallsMinDistance
        awayIsCloser = awayBallsMinDistance < homeBallsMinDistance
        equidistant = homeBallsMinDistance == awayBallsMinDistance

        # check if it is "too close to call"
        tooCloseToCall = abs(homeBallsMinDistance - awayBallsMinDistance) <= TOO_CLOSE_MARGIN


        # draw the "closer team's" closest ball vectors
        if homeIsCloser:
            frame, framePoints = self.draw_lines_and_get_frame_points(frame, pallino,
                homeBalls, homeBallsDistances, awayBalls, awayBallsDistances)
        elif awayIsCloser:
            frame, framePoints = self.draw_lines_and_get_frame_points(frame, pallino,
                awayBalls, awayBallsDistances, homeBalls, homeBallsDistances)

        # inform the umpire that they need to measure
        if tooCloseToCall or equidistant:
            # load the image for annotation with PIL
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = Image.fromarray(frame)
            draw = ImageDraw.Draw(frame)
            draw.text(xy=(int(w * .5), int(h * .25)),
                      text="Too close:",
                      align="center",
                      font=self.font)
            draw.text(xy=(int(w * .5), int(h * .75)),
                      text="Umpire please measure!",
                      align="center",
                      font=self.font)

            frame = cv2.cvtColor(np.array(frame), cv2.COLOR_RGBA2BGR)

        return frame

    def draw_lines_and_get_frame_points(self, frame, pallino, teamA_balls_sorted,
        teamA_distances_sorted, teamB_balls_sorted, teamB_distances_sorted):

        # draw the closest vectors and at the same time calculate the points for this frame
        framePoints = 0
        for (i, dB) in enumerate(teamB_distances_sorted):
            for (j, dA) in enumerate(teamA_distances_sorted):
                if dA < dB:
                    framePoints += 1
                    frame = cv2.line(frame, pallino.coordinates,
                        teamA_balls_sorted[j].coordinates, teamA_balls_sorted[j].color, 3)
                else:
                    break
            break
        return frame, framePoints


# test code
def test_static_image():
    # append to the path so we can find the modules and test image
    sys.path.append(os.path.abspath(os.path.join(__file__ ,"../../..")))

    # load an image
    frame = cv2.imread(os.path.join(sys.path[-1], "exploratory_code/assets/towel_background.png"))

    # imports
    from games.bocce.ball import Pallino
    from games.bocce.ball import Bocce

    # ball colors
    yellow = (156, 210, 236)
    orange = (94, 102, 193)
    white = (255, 255, 255)

    # manually create balls (coordinates determined from PaintS / Photoshop)
    pallino = Pallino(color=yellow)
    pallino.coordinates = (261, 164)

    orange1 = Bocce(color=orange)
    orange1.coordinates = (289, 119)

    orange2 = Bocce(color=orange)
    orange2.coordinates = (317, 192)

    white1 = Bocce(color=white)
    white1.coordinates = (497, 329)

    white2 = Bocce(color=white)
    white2.coordinates = (191, 238)

    # add balls to teams
    homeBalls = [orange1, orange2]
    awayBalls = [white1, white2]

    # initialize the Vectors Annotation object
    v = Vectors()
    v.activate()
    frame = v.annotate(frame, pallino, homeBalls, awayBalls)

    # display until keypress
    cv2.imshow("vectors", frame)
    cv2.waitKey(0)

# test code
def test_live_image():
    # append to the path so we can find the modules and test image
    sys.path.append(os.path.abspath(os.path.join(__file__ ,"../../..")))

    # imports
    from games.camera.camera import ImageZMQCamera
    from games.bocce.cv import ballfinder as cv

    # create a camera
    westCam = ImageZMQCamera(name="west", source="rpi4b4gb,5556")
    input("did you start the client?")
    westCam.initialize()

    # loop continuously
    while True:
        # grab a frame
        frame = westCam._get_frame()
        (h, w) = frame.shape[:2]

        # grab only the ROI of the court
        courtROI = frame[65:h-80, 110:w]
        # cv2.imshow("courtROI", courtROI)
        # cv2.waitKey(0)

        # set constants for 1 pallino, 2 bocce home, 2 bocce away, on gray towel
        numBalls = 5
        clusters = 3
        minHSV = (26, 0, 117)
        maxHSV = (198, 43, 230)

        # find the balls
        cnts, ballMask = cv.find_ball_contours(courtROI, numBalls, minHSV, maxHSV)
        balls = cv.extract_balls(courtROI, ballMask, cnts, numBalls=numBalls)
        cluster_idxs = cv.cluster_balls(balls, clusters, debug=True)

        # sort clusters according to length and assume pallino, teamA, teamB
        cluster_idxs.sort(key=len)
        pallino = balls[cluster_idxs[0][0]]
        if len(cluster_idxs) >= 1:
            homeBalls = [balls[i] for i in cluster_idxs[1]]
        else:
            homeBalls = None
        if len(cluster_idxs) >= 2:
            awayBalls = [balls[i] for i in cluster_idxs[2]]
        else:
            awayBalls = None

        # initialize the Vectors Annotation object
        v = Vectors()
        v.activate()
        courtROI = v.annotate(courtROI, pallino, homeBalls, awayBalls)

        # display until keypress
        cv2.imshow("vectors", courtROI)
        if cv2.waitKey(0) & 0xFF is ord('q'):
            break


# run the test code
if __name__ == "__main__":
    test_static_image()
    test_live_image()