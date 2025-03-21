import os

RADIUS_BOCCE = 26
RADIUS_PALLINO = 9

RADIUS_BOCCE_TOLERANCE = 4
RADIUS_PALLINO_TOLERANCE = 2

RADIUS_BALL_ROI_PADDING = 4

COLOR_BLUE_STEEL = (180, 130, 70)
COLOR_WHITE = (255, 255, 255)
COLOR_GREEN = (0, 255, 0)
COLOR_RED = (0, 0, 255)

COLOR_BOCCE_BALL_TEXT = COLOR_RED
COLOR_PALLINO_BALL_TEXT = COLOR_RED

CAMERA_LEFT = 'DEV_000F315DAB70'
CAMERA_RIGHT = 'DEV_000F315DAB39'

# y1:y2, x1:x2
LEFT_ROI_SLICE = (520, 1220, 260, 1700)
RIGHT_ROI_SLICE = None

SMA_QUEUE_SIZE = 6

BOCCE_MODEL_PATH = os.path.join("ball_training", "image-classification-keras", "bocce.model")

PIXELS_PER_FOOT = 132
METERS_PER_FOOT = 0.3048
CAMERA_RESOLUTION_PIXELS = (2464, 2056) # Allied Vision Mako G-507C
CAMERA_CENTER_PIXELS = (CAMERA_RESOLUTION_PIXELS[0] / 2, CAMERA_RESOLUTION_PIXELS[1] / 2)
