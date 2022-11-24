from games.bocce.cv.pyimagesearch.centroidtracker import CentroidTracker
from tensorflow.keras.preprocessing.image import img_to_array
from tensorflow.keras.models import load_model
import numpy as np
import config
import time
import uuid
import cv2
import os

# load the trained convolutional neural network
BOCCE_CLASSIFIER_MODEL = load_model(config.BOCCE_MODEL_PATH)
P = config.RADIUS_BALL_ROI_PADDING


class BallFinder:
    def __init__(self):
        self.bocce_ct = CentroidTracker()
        self.pallino_ct = CentroidTracker()
        self.bocce_queues = {}

    def update(self, frame):
        # initialize ball info dict
        ballinfo = {
            "home": {
                "balls_on_court": 0,
                "balls_in": 0,
                "closest_ball_dist": 0
            },
            "away": {
                "balls_on_court": 0,
                "balls_in": 0,
                "closest_ball_dist": 0
            }
        }

        # find the bocce balls
        circles_bocce = find_circles(frame.copy(), config.RADIUS_BOCCE, config.RADIUS_BOCCE_TOLERANCE)
        balls_dict_bocce = extract_circle_contours(circles_bocce, frame, config.RADIUS_BOCCE)

        # find the pallino ball
        circles_pallino = find_circles(frame.copy(), config.RADIUS_PALLINO, config.RADIUS_PALLINO_TOLERANCE)
        #frame = draw_circles((circles_pallino, config.RADIUS_PALLINO, config.COLOR_RED), frame)
        balls_dict_pallino = extract_circle_contours(circles_pallino, frame, config.RADIUS_PALLINO)

        # update the centroid tracker
        bocce_ball_coords = []
        pallino_ball_coords = []
        for b, v in balls_dict_bocce.items():
            bocce_ball_coords.append(v['coord'])
        for b, v in balls_dict_pallino.items():
            pallino_ball_coords.append(v['coord'])
        bocces = self.bocce_ct.update(bocce_ball_coords)
        pallinos = self.pallino_ct.update(pallino_ball_coords)

        # stabilization
        for (objectID, centroid) in bocces.items():
            # populate the centroid queues
            if objectID not in self.bocce_queues.keys():
                self.bocce_queues[objectID] = {}
                self.bocce_queues[objectID]["center"] = None
                self.bocce_queues[objectID]["history"] = []

            # add the item to the queue
            if len(self.bocce_queues[objectID]["history"]) >= config.SMA_QUEUE_SIZE:
                del self.bocce_queues[objectID]["history"][0]
            self.bocce_queues[objectID]["history"].append(centroid)

            # calculate the centroid average of each queue
            self.bocce_queues[objectID]["center"] = centroid_of_centroids(self.bocce_queues[objectID]["history"])

        # display
        for (objectID, centroid_info) in self.bocce_queues.items():
            if objectID not in bocces.keys():
                continue

            # extract the center
            center = centroid_info["center"]
            if center is None:
                continue

            # draw a line to the pallino
            for (objectID, pallino_centroid) in pallinos.items():
                cv2.line(frame, (int(pallino_centroid[0]), int(pallino_centroid[1])),
                         (center[0], center[1]),
                         config.COLOR_WHITE, 1)

            # draw both the ID of the object and the centroid of the
            # object on the output frame
            text = "{}".format(objectID)
            cv2.putText(frame, text, (center[0] - 5, center[1] + 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, config.COLOR_BOCCE_BALL_TEXT, 1)

        for (objectID, centroid) in pallinos.items():
            # draw both the ID of the object and the centroid of the
            # object on the output frame
            text = "{}".format(objectID)
            cv2.putText(frame, text, (int(centroid[0] - 5), int(centroid[1] + 5)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, config.COLOR_BOCCE_BALL_TEXT, 1)

        return frame, ballinfo





def preprocess(circle_roi):
    # pre-process the image for classification
    image = cv2.resize(circle_roi, (28, 28))
    image = image.astype("float") / 255.0
    image = img_to_array(image)
    image = np.expand_dims(image, axis=0)
    return image


def bocce_roi_inference(circle_roi):
    preprocessed_roi = preprocess(circle_roi)
    (notBocce, bocce) = BOCCE_CLASSIFIER_MODEL.predict(preprocessed_roi)[0]
    return True if bocce > notBocce else False


def find_circles(frame, radius, radius_tolerance):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    circles = cv2.HoughCircles(gray,
                               method=cv2.HOUGH_GRADIENT,
                               dp=1.2,
                               minDist=40,
                               param1=60,
                               param2=25,
                               minRadius=radius - radius_tolerance,
                               maxRadius=radius + radius_tolerance)
    return circles


def draw_circles(ball_circle, frame):
    # extract the circles
    circles, radius, color = ball_circle

    # ensure at least some circles were found
    if circles is not None:
        # convert the (x, y) coordinates and radius of the circles to integers
        circles = np.round(circles[0, :]).astype("int")
        # loop over the (x, y) coordinates and radius of the circles
        for (x, y, r) in circles:
            # draw the circle in the output image, then draw a rectangle
            # corresponding to the center of the circle
            cv2.circle(frame, (x, y), radius, color, 2)

    return frame


def extract_circle_contours(circles, frame, radius):
    balls = {}

    if circles is None or len(circles) == 0:
        return balls

    for i, circle in enumerate(circles[0]):
        # extract the center and radius of the circle
        x, y, r = circle
        x = int(x)
        y = int(y)
        r = int(r)

        # create an empty mask the same size as the frame
        mask = np.zeros(frame.shape[:2], dtype="uint8")

        # draw a solid circle on the mask image where the probable ball is
        cv2.circle(mask, (x, y), radius - 2, 255, -1)

        # mask out the probable circular ball region
        masked = cv2.bitwise_and(frame, frame, mask=mask)

        # crop out the masked ball
        masked_cropped = masked[y-r:y+r, x-r:x+r]

        # cropped area
        cropped = frame[y-radius-P:y+radius+P, x-radius-P:x+radius+P]

        # perform classification
        try:
            is_bocce = bocce_roi_inference(cropped)
        except:
            is_bocce = False

        if is_bocce:
            # create a dictionary consisting of the center coord and the roi mask
            balls[i] = {
                "coord": (x, y),
                "roi": cropped,
                "roi_mask": masked_cropped
            }

        else:
            continue

    return balls


def centroid_of_centroids(points):
    x = [p[0] for p in points]
    y = [p[1] for p in points]
    return int(sum(x) / len(points)), int(sum(y) / len(points))


def balls_to_disk(balls_dict):
    for k, v in balls_dict.items():
        filename = str(uuid.uuid4()) + ".png"
        try:
            cv2.imwrite(os.path.join("ball_training", filename), v["roi"])
        except:
            pass

