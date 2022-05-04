# imports
import numpy as np
import cv2
import PIL
import random
import re
from pyimagesearch.centroidtracker import CentroidTracker

# dimension multiplier
DIM_MULTIPLIER = 50

# dimension constants
COURT_WIDTH = 8
COURT_LENGTH = 30
WALL_WIDTH = 0.33
BOCCE_RADIUS = 4.21/12/2
PALLINO_RADIUS = 1.57/12/2

# deterimine image dimensions
WALL_THICKNESS = int(WALL_WIDTH * DIM_MULTIPLIER)
W = int((COURT_WIDTH + WALL_WIDTH) * DIM_MULTIPLIER + WALL_THICKNESS)
H = int((COURT_LENGTH + WALL_WIDTH) * DIM_MULTIPLIER + WALL_THICKNESS)
BOCCE_RADIUS = int(BOCCE_RADIUS * DIM_MULTIPLIER)
PALLINO_RADIUS = int(PALLINO_RADIUS * DIM_MULTIPLIER)

# dashed line pixels
DASHED_LINE_GAP = 7

# color BGR
COURT_COLOR = (100, 200, 0)
WALL_COLOR = (255, 255, 255)
MIDCOURT_LINE_COLOR = (255, 255, 255)
TARGET_ZONE_LINE_COLOR = (180, 255, 0)
BOCCE_A_COLOR = (255, 0, 0)
BOCCE_B_COLOR = (0, 0, 255)
PALLINO_COLOR = (0, 255, 255)

# image to real world coordinate conversion
# (0,0) is the middle of the court
def convert_coord(pt1_real):
    # a real coordinate is in ft centered on the court
    # extract (x,y)-coordinates
    x = pt1_real[0]
    y = pt1_real[1]

    # translate right
    X = int((x + WALL_WIDTH + COURT_WIDTH/2) * DIM_MULTIPLIER)

    # translate down and flip
    Y = int(((COURT_LENGTH/2 - y) + WALL_WIDTH) * DIM_MULTIPLIER)

    pt1_court_drawing = (X, Y)

    return pt1_court_drawing



class BocceCourtDrawing(object):
    def __init__(self):
        self.court = None

        # List to store mouse start/end points
        self.image_coordinates = []
        self.drawing = False

    def get_court_image(self):
        return self.court

    def create_court(self, walls=True):
        # create the empty array
        self.court = np.zeros((H, W, 3), dtype="uint8")

        # colorize the canvas
        self.court[0:H, 0:W] = COURT_COLOR

    def dashed_line(self, img, pt1, pt2, color, radius=1, gap=DASHED_LINE_GAP):
        # determine the distance
        dist =((pt1[0]-pt2[0])**2+(pt1[1]-pt2[1])**2)**.5

        # populate the points list
        pts= []
        for i in  np.arange(0,dist,gap):
            r=i/dist
            x=int((pt1[0]*(1-r)+pt2[0]*r)+.5)
            y=int((pt1[1]*(1-r)+pt2[1]*r)+.5)
            p = (x,y)
            pts.append(p)

        # draw the dots
        for p in pts:
            cv2.circle(img, p, radius, color, -1)

    def overlay_midcourt_line(self):
        cv2.line(self.court, (0, H//2), (W, H//2), MIDCOURT_LINE_COLOR, 2)

    def draw_walls(self):
        # draw the walls
        cv2.rectangle(self.court, (0, 0), (W, H), WALL_COLOR, WALL_THICKNESS)

    def overlay_target_zones(self):
        # long court bottom
        pt1 = (int((1            )*DIM_MULTIPLIER + WALL_THICKNESS), int((COURT_LENGTH-3)*DIM_MULTIPLIER + WALL_THICKNESS))
        pt2 = (int((COURT_WIDTH-1)*DIM_MULTIPLIER + WALL_THICKNESS), int((COURT_LENGTH-3)*DIM_MULTIPLIER + WALL_THICKNESS))
        self.dashed_line(self.court, pt1, pt2, TARGET_ZONE_LINE_COLOR)

        # long court top
        pt1 = (int((1            )*DIM_MULTIPLIER + WALL_THICKNESS), int((3)*DIM_MULTIPLIER + WALL_THICKNESS))
        pt2 = (int((COURT_WIDTH-1)*DIM_MULTIPLIER + WALL_THICKNESS), int((3)*DIM_MULTIPLIER + WALL_THICKNESS))
        self.dashed_line(self.court, pt1, pt2, TARGET_ZONE_LINE_COLOR)

        # short court bottom
        pt1 = (int((1            )*DIM_MULTIPLIER + WALL_THICKNESS), int((COURT_LENGTH/2+3)*DIM_MULTIPLIER + WALL_THICKNESS))
        pt2 = (int((COURT_WIDTH-1)*DIM_MULTIPLIER + WALL_THICKNESS), int((COURT_LENGTH/2+3)*DIM_MULTIPLIER + WALL_THICKNESS))
        self.dashed_line(self.court, pt1, pt2, TARGET_ZONE_LINE_COLOR)

        # short court top
        pt1 = (int((1            )*DIM_MULTIPLIER + WALL_THICKNESS), int((COURT_LENGTH/2-3)*DIM_MULTIPLIER + WALL_THICKNESS))
        pt2 = (int((COURT_WIDTH-1)*DIM_MULTIPLIER + WALL_THICKNESS), int((COURT_LENGTH/2-3)*DIM_MULTIPLIER + WALL_THICKNESS))
        self.dashed_line(self.court, pt1, pt2, TARGET_ZONE_LINE_COLOR)

        # wall left
        pt1 = (int((1)*DIM_MULTIPLIER + WALL_THICKNESS), 0 + WALL_THICKNESS)
        pt2 = (int((1)*DIM_MULTIPLIER + WALL_THICKNESS), int(COURT_LENGTH*DIM_MULTIPLIER + WALL_THICKNESS))
        self.dashed_line(self.court, pt1, pt2, TARGET_ZONE_LINE_COLOR)

        # wall right
        pt1 = (int((COURT_WIDTH-1)*DIM_MULTIPLIER + WALL_THICKNESS), 0 + WALL_THICKNESS)
        pt2 = (int((COURT_WIDTH-1)*DIM_MULTIPLIER + WALL_THICKNESS), int(COURT_LENGTH*DIM_MULTIPLIER + WALL_THICKNESS))
        self.dashed_line(self.court, pt1, pt2, TARGET_ZONE_LINE_COLOR)

    def draw_bocce(self, pt, color):
        if pt == (None, None) or pt == None:
            return
        cv2.circle(self.court, convert_coord(pt), BOCCE_RADIUS, color, -1)

    def draw_pallino(self, pt, color):
        if pt == (None, None) or pt == None:
            return
        cv2.circle(self.court, convert_coord(pt), PALLINO_RADIUS, color, -1)

    def indicate_moving(self, pt):
        if pt == (None, None) or pt == None:
            return
        pt = convert_coord(pt)
        pt = (pt[0]-6, pt[1]+4)
        cv2.putText(self.court, "M", pt, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)


if __name__ == "__main__":
    # import
    from ball import Bocce, Pallino
    import socket

    # define the host and port
    HOST = 'localhost'
    PORT = 60000

    # intstantiate court drawing
    court = BocceCourtDrawing()

    # # Halcon Sample Data
    # def parse_sample(data):
    #     match = "^P=\[(\S*?)\],A=\[(\S*?);(\S*?);(\S*?);(\S*?)\],B=\[(\S*?);(\S*?);(\S*?);(\S*?)\]\Z"
    #     r = re.search(match, data)
    #
    #     # extract the ball coordinates
    #     try:
    #         balls_str = [r.group(1),  # p
    #                      r.group(2),  # a1
    #                      r.group(3),  # a2
    #                      r.group(4),  # a3
    #                      r.group(5),  # a4
    #                      r.group(6),  # b1
    #                      r.group(7),  # b2
    #                      r.group(8),  # b3
    #                      r.group(9)]  # b4
    #     except AttributeError:
    #         return []
    #
    #     # extract the coordinates
    #     balls = []
    #     for b in balls_str:
    #         if b == "None":
    #             balls.append(None)
    #         else:
    #             match = "\((\S*?),(\S*?)\)"
    #             r = re.search(match, b)
    #             try:
    #                 x = float(r.group(1))
    #                 y = float(r.group(2))
    #                 balls.append((x, y))
    #             except:
    #                 balls.append(None)
    #
    #     return balls
    #
    #
    # # load sample data
    # with open("sample_data.txt", "r") as file:
    #     lines = file.read()
    #
    # # split via new line character
    # lines = lines.split("\n")

    # centroid trackers
    p_ct = CentroidTracker()
    r_ct = CentroidTracker()
    b_ct = CentroidTracker()

    blue_objectIDs = {}
    red_objectIDs = {}
    pallino_objectIDs = {}

    # receive data
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))

        while True:
            data = s.recv(1024)
            data = data.decode('ascii').strip()
            print(data)
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
                s.send(b"parse error")
                print("parse error")
                continue

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

            # debug
            s.send(b"bocce")

            # create the court, walls, and lines
            court.create_court()
            court.draw_walls()
            court.overlay_midcourt_line()
            court.overlay_target_zones()

            if len(balls) == 0:
                continue

            # update our centroid trackers
            pallinos = p_ct.update([balls[0]])
            reds = r_ct.update(balls[1:5])
            blues = b_ct.update(balls[5:9])

            # loop over the tracked objects
            for (objectID, centroid) in pallinos.items():
                if objectID not in pallino_objectIDs:
                    # add the object to the set
                    pallino_objectIDs[objectID] = Pallino(objectID, PALLINO_COLOR)

                pallino_objectIDs[objectID].add_coord_sensor(centroid)
                pallino_objectIDs[objectID].sensor_to_smoothed_court_coord()
                court.draw_pallino(pallino_objectIDs[objectID].coord_court_imperial, pallino_objectIDs[objectID].color)

            # loop over the tracked objects
            for (objectID, centroid) in blues.items():
                if objectID not in blue_objectIDs:
                    # add the object to the set
                    blue_objectIDs[objectID] = Bocce(objectID, BOCCE_A_COLOR)

                blue_objectIDs[objectID].add_coord_sensor(centroid)
                blue_objectIDs[objectID].sensor_to_smoothed_court_coord()
                court.draw_bocce(blue_objectIDs[objectID].coord_court_imperial, blue_objectIDs[objectID].color)
                if blue_objectIDs[objectID].isMoving:
                    court.indicate_moving(blue_objectIDs[objectID].coord_court_imperial)

            # loop over the tracked objects
            for (objectID, centroid) in reds.items():
                if objectID not in red_objectIDs:
                    # add the object to the set
                    red_objectIDs[objectID] = Bocce(objectID, BOCCE_B_COLOR)

                red_objectIDs[objectID].add_coord_sensor(centroid)
                red_objectIDs[objectID].sensor_to_smoothed_court_coord()
                court.draw_bocce(red_objectIDs[objectID].coord_court_imperial, red_objectIDs[objectID].color)
                if red_objectIDs[objectID].isMoving:
                    court.indicate_moving(red_objectIDs[objectID].coord_court_imperial)

            # display and capture keypress
            cv2.imshow("bocce court", court.court)
            key = cv2.waitKey(1)

            # display court until "q" button pressed
            if key == ord("q"):
                cv2.destroyAllWindows()
                exit(1)

        s.close()

