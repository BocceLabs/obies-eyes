# imports
from pyimagesearch.centroidtracker import CentroidTracker
import socket
import re
import numpy as np
import cv2
import time

# colors
# red
red_coral = (128, 128, 240)
red_salmon = (122, 160, 255)
red_crimson = (60, 20, 220)
red_dark = (0, 0, 139)
red_colors = [red_coral, red_salmon, red_crimson, red_dark]
# blue
blue_azure = (255, 128, 0)
blue_sapphire = (186, 82, 15)
blue_steel = (180, 130, 70)
blue_electric = (255, 249, 126)
blue_colors = [blue_azure, blue_sapphire, blue_steel, blue_electric]
yellow = (0, 191, 255)
colors = [yellow] + red_colors + blue_colors

# define the host and port
HOST = 'localhost'
PORT = 60000

"""
Expects socket data in this format:
P=[None],A=[None;None;None;None],B=[None;None;None;None]
    -or-
P=[(517.4,28.7)],A=[(1236.8, 483.6);None;None;None],B=[(843.2,568.9);(246.4,523.9);None;None]
"""

def parse_sample(data):
    match = "^P=\[(\S*?)\],A=\[(\S*?);(\S*?);(\S*?);(\S*?)\],B=\[(\S*?);(\S*?);(\S*?);(\S*?)\]\Z"
    r = re.search(match, data)

    # extract the ball coordinates
    try:
        balls_str = [r.group(1),  # p
                     r.group(2),  # a1
                     r.group(3),  # a2
                     r.group(4),  # a3
                     r.group(5),  # a4
                     r.group(6),  # b1
                     r.group(7),  # b2
                     r.group(8),  # b3
                     r.group(9)]  # b4
    except AttributeError:
        return []

    # extract the coordinates
    balls = []
    for b in balls_str:
        if b == "None":
            balls.append(None)
        else:
            match = "\((\S*?),(\S*?)\)"
            r = re.search(match, b)
            try:
                x = float(r.group(1))
                y = float(r.group(2))
                balls.append((x, y))
            except:
                balls.append(None)

    return balls

# draw a blank canvas
# dims 2464, 2056
dims = (2056, 2464)
divisor = 2.5
dims = (int(dims[0]/divisor), int(dims[1]/divisor))
canvas = np.zeros((dims[0], dims[1], 3), np.uint8)
canvas.fill(255)

# centroid trackers
p_ct = CentroidTracker()
r_ct = CentroidTracker()
b_ct = CentroidTracker()

# receive data
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))

    while True:
        # make a new canvas
        canvas = np.zeros((dims[0], dims[1], 3), np.uint8)
        canvas.fill(255)

        # receive data from the socket
        data = s.recv(1024)
        data = data.decode('ascii').strip()

        # parse sample data
        balls = parse_sample(data)
        print(balls)
        # debug
        s.send(b"bocce")

        # update our centroid trackers
        pallinos = p_ct.update([balls[0]])
        reds = r_ct.update(balls[1:5])
        blues = b_ct.update(balls[5:9])

        # loop over the tracked objects
        for (objectID, centroid) in pallinos.items():
            # draw both the ID of the object and the centroid of the
            # object on the output frame
            text = "P {}".format(objectID)
            cv2.putText(canvas, text, (int(centroid[0]/divisor) - 10, int(centroid[1]/divisor) - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 255, 0), 1)
            cv2.circle(canvas, (int(centroid[0]/divisor), int(centroid[1]/divisor)), 3, yellow, -1)

        # loop over the tracked objects
        for (objectID, centroid) in reds.items():
            # draw both the ID of the object and the centroid of the
            # object on the output frame
            text = "R {}".format(objectID)
            cv2.putText(canvas, text, (int(centroid[0]/divisor) - 10, int(centroid[1]/divisor) - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.3, red_salmon, 1)
            cv2.circle(canvas, (int(centroid[0]/divisor), int(centroid[1]/divisor)), 8, red_crimson, -1)

        # loop over the tracked objects
        for (objectID, centroid) in blues.items():
            # draw both the ID of the object and the centroid of the
            # object on the output frame
            text = "B {}".format(objectID)
            cv2.putText(canvas, text, (int(centroid[0]/divisor) - 10, int(centroid[1]/divisor) - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.3, blue_steel, 1)
            cv2.circle(canvas, (int(centroid[0]/divisor), int(centroid[1]/divisor)), 8, blue_azure, -1)

        # # draw a colored circle for each ball
        # for i, ball_coords in enumerate(balls):
        #     if ball_coords is None:
        #         continue
        #     if i == 0:
        #         radius = 3
        #     else:
        #         radius = 8
        #     ball_coords = (int(ball_coords[0]/divisor), int(ball_coords[1]/divisor))
        #     cv2.circle(canvas, ball_coords, radius, colors[i], -1)

        # display
        cv2.imshow("Bocce", canvas)
        cv2.waitKey(1)
        time.sleep(.15)



