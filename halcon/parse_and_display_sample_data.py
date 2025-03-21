# imports
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


# load sample data
with open("sample_data_3.txt", "r") as file:
    lines = file.read()

# split via new line character
lines = lines.split("\n")

# draw a blank canvas
# dims 2464, 2056
dims = (2056, 2464)
divisor = 3
dims = (int(dims[0]/divisor), int(dims[1]/divisor))
canvas = np.zeros((dims[0], dims[1], 3), np.uint8)
canvas.fill(255)

# loop over each row of sample data
for sample in lines:
    # make a new canvas
    canvas = np.zeros((dims[0], dims[1], 3), np.uint8)
    canvas.fill(255)

    # parse sample data
    balls = parse_sample(sample)
    print(balls)

    # draw a colored circle for each ball
    for i, ball_coords in enumerate(balls):
        if ball_coords is None:
            continue
        if i == 0:
            radius = 3
        else:
            radius = 8
        ball_coords = (int(ball_coords[0]/divisor), int(ball_coords[1]/divisor))
        cv2.circle(canvas, ball_coords, radius, colors[i], -1)

    # wait for keypress
    cv2.imshow("Bocce", canvas)
    cv2.waitKey(1)
    time.sleep(.15)

