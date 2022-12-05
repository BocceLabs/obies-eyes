from games.bocce.cv.pyimagesearch.centroidtracker import CentroidTracker
from games.bocce.cv.pyimagesearch.descriptors.histogram import Histogram
from tensorflow.keras.preprocessing.image import img_to_array
from tensorflow.keras.models import load_model
from collections import OrderedDict
from sklearn.cluster import KMeans
import numpy as np
import config
import math
import uuid
import cv2
import os

from pprint import pprint

# load the trained convolutional neural network
BOCCE_CLASSIFIER_MODEL = load_model(config.BOCCE_MODEL_PATH)
P = config.RADIUS_BALL_ROI_PADDING


class BallFinder:
    def __init__(self):
        self.bocce_ct = CentroidTracker(maxDisappeared=15)
        self.pallino_ct = CentroidTracker(maxDisappeared=15)
        self.bocce_queues = {}
        self.bocces = OrderedDict()
        self.pallinos = OrderedDict()

    def update(self, frame):
        # initialize ball info dict
        ballinfo = {
            "home": {
                "balls_on_court": 0,
                "balls_in": 0,
                "closest_ball_dist_inches": 0,
                "closest_ball_dist_pixels": 0
            },
            "away": {
                "balls_on_court": 0,
                "balls_in": 0,
                "closest_ball_dist_inches": 0,
                "closest_ball_dist_pixels": 0
            }
        }

        # find the bocce balls
        circles_bocce = find_circles(frame.copy(), config.RADIUS_BOCCE, config.RADIUS_BOCCE_TOLERANCE)
        #frame = draw_circles((circles_bocce, config.RADIUS_BOCCE, config.COLOR_WHITE), frame)
        balls_dict_bocce = circles_to_ball_info(circles_bocce, frame, config.RADIUS_BOCCE)

        # find the pallino ball
        circles_pallino = find_circles(frame.copy(), config.RADIUS_PALLINO, config.RADIUS_PALLINO_TOLERANCE)
        #frame = draw_circles((circles_pallino, config.RADIUS_PALLINO, config.COLOR_RED), frame)
        balls_dict_pallino = circles_to_ball_info(circles_pallino, frame, config.RADIUS_PALLINO)

        # update the centroid tracker
        bocce_ball_coords = []
        pallino_ball_coords = []
        for b, v in balls_dict_bocce.items():
            bocce_ball_coords.append(v['coord'])
        for b, v in balls_dict_pallino.items():
            pallino_ball_coords.append(v['coord'])
        self.bocces = self.bocce_ct.update(bocce_ball_coords)
        self.pallinos = self.pallino_ct.update(pallino_ball_coords)

        # stabilization
        for (objectID, centroid) in self.bocces.items():
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

        # delete queues we no-longer need
        to_del = []
        for objectID in self.bocce_queues.keys():
            if objectID not in self.bocces.keys():
                to_del.append(objectID)
        for objectID in to_del:
            del self.bocce_queues[objectID]

        # correlate bocce balls object with bocce_queues center
        for id, ball in balls_dict_bocce.items():
            for bqid, bocce_queue in self.bocce_queues.items():
                if math.dist(ball["coord"], bocce_queue["center"]) < 6:
                    self.bocce_queues[bqid]["cluster"] = ball["cluster"]

        # separate dicts
        home_balls = {}
        away_balls = {}
        for objectID, ball_info in self.bocce_queues.items():
            if ball_info["cluster"] == 0:
                home_balls[objectID] = ball_info
            elif ball_info["cluster"] == 1:
                away_balls[objectID] = ball_info

        # grab the shortest distance
        home_distances = calc_distances(home_balls, self.bocces, self.pallinos)
        try:
            ballinfo["home"]["closest_ball_dist_pixels"] = home_distances[0][0]
            ballinfo["home"]["closest_ball_dist_inches"] = home_distances[0][1]
        except IndexError:
            ballinfo["home"]["closest_ball_dist_pixels"] = 0
            ballinfo["home"]["closest_ball_dist_inches"] = 0
        away_distances = calc_distances(away_balls, self.bocces, self.pallinos)
        try:
            ballinfo["away"]["closest_ball_dist_pixels"] = away_distances[0][0]
            ballinfo["away"]["closest_ball_dist_inches"] = away_distances[0][1]
        except IndexError:
            ballinfo["away"]["closest_ball_dist_pixels"] = 0
            ballinfo["away"]["closest_ball_dist_inches"] = 0

        # determine num in
        away_num_in = 0
        home_num_in = 0
        for away_dist in away_distances:
            try:
                if away_dist[0] < home_distances[0][0]:
                    away_num_in += 1
            except IndexError:
                break
        for home_dist in home_distances:
            try:
                if home_dist[0] < away_distances[0][0]:
                    home_num_in += 1
            except:
                break
        ballinfo["home"]["balls_in"] = home_num_in
        ballinfo["away"]["balls_in"] = away_num_in

        # count balls
        ballinfo["home"]["balls_on_court"] = len(home_balls.keys())
        ballinfo["away"]["balls_on_court"] = len(away_balls.keys())


        for (objectID, centroid_info) in self.bocce_queues.items():
            # extract the cluster
            cluster = centroid_info["cluster"]

            # extract the center
            center = centroid_info["center"]
            if center is None:
                continue

            # draw a line to the pallino
            for _, pallino_centroid in self.pallinos.items():
                cv2.line(frame, (int(pallino_centroid[0]), int(pallino_centroid[1])),
                         (center[0], center[1]),
                         config.COLOR_WHITE, 1)

            # draw  the ID of the object on the output frame
            # if cluster == 0:
            #     cv2.circle(frame, (center[0], center[1]), int(config.RADIUS_BOCCE/1.5), config.COLOR_GREEN, -1)
            # elif cluster == 1:
            #     cv2.circle(frame, (center[0], center[1]), int(config.RADIUS_BOCCE/1.5), config.COLOR_RED, -1)
            # else:
            #     cv2.circle(frame, (center[0], center[1]), int(config.RADIUS_BOCCE / 1.5), config.COLOR_WHITE, -1)
            # cv2.putText(frame, str(objectID), (center[0] - 6, center[1] + 6),
            #             cv2.FONT_HERSHEY_SIMPLEX, 0.8, config.COLOR_BLUE_STEEL, 2)


        # for (objectID, centroid) in self.pallinos.items():
        #     # draw the ID of the object on the ball
        #     cv2.putText(frame, str(objectID), (int(centroid[0] - 5), int(centroid[1] + 5)),
        #                 cv2.FONT_HERSHEY_SIMPLEX, 0.4, config.COLOR_BOCCE_BALL_TEXT, 1)

        return frame, ballinfo


def calc_distances(bocce_queues, bocces, pallinos):
    distances = []
    for (objectID, bocce) in bocce_queues.items():
        if objectID not in bocces.keys():
            continue
        for (objectID, pallino_centroid) in pallinos.items():

            d_pixels = math.dist(pallino_centroid, bocce["center"])
            d_inches = d_pixels / config.PIXELS_PER_INCH
            distances.append( (d_pixels, d_inches) )

    return sorted(distances)


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
    gray = cv2.GaussianBlur(gray, (27, 27), 0)

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
            cv2.circle(frame, (x, y), radius, color, 4)

    return frame


def circles_to_ball_info(circles, frame, radius):
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
                "roi_mask": masked_cropped,
                "cluster": None
            }

        else:
            continue

    # determine the cluster (team) for all balls
    balls = cluster_balls(balls)

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


def cluster_balls(balls, clusters=2):
    # initialize the image descriptor along with the image matrix
    desc = Histogram([8, 8, 8], cv2.COLOR_BGR2HSV)
    hist_data = []
    ball_idxs = []

    # loop over the input dataset of images
    for ball_idx, ball in balls.items():
        # grab the circular roi mask
        roi_mask = ball["roi_mask"]

        # load the image, describe the image, then update the list of data
        hist = desc.describe(roi_mask)
        hist_data.append(hist)
        ball_idxs.append(ball_idx)

    # ensure we have enough data
    if len(hist_data) < 2:
        return balls

    # cluster the color histograms
    clt = KMeans(n_clusters=2, random_state=42)
    labels = clt.fit_predict(hist_data)

    print(labels)

    # loop over the unique labels
    for label in np.unique(labels):
        # grab all image paths that are assigned to the current label
        indices = np.where(np.array(labels, copy=False) == label)[0].tolist()
        for idx in indices:
            try:
                balls[ball_idxs[idx]]["cluster"] = label
            except IndexError:
                continue

    return balls