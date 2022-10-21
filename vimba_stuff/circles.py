import cv2
import numpy as np
import uuid
import os
import config

P = config.RADIUS_BALL_ROI_PADDING


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


def draw_circles(ball_circles, frame):
    for ball_circle in ball_circles:
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

        # todo this can be used for training a classifier, so it would be good to log these to disk and
        # todo potentially perform the classification right here
        cropped = frame[y-radius-P:y+radius+P, x-radius-P:x+radius+P]

        # create a dictionary consisting of the center coord and the roi mask
        balls[i] = {
            "coord": (x, y),
            "roi": cropped,
            "roi_mask": masked_cropped
        }

    return balls


def balls_to_disk(balls_dict):
    for k, v in balls_dict.items():
        filename = str(uuid.uuid4()) + ".png"
        try:
            cv2.imwrite(os.path.join("ball_training", filename), v["roi"])
        except:
            pass
