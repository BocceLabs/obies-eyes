# import packages
import os
import cv2
import imutils
import argparse
import numpy as np

# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-i", "--image", required=True,
    help="path to the image")
ap.add_argument("-m", "--minhsv", default="29,86,6",
    help="hsv comma delimited")
ap.add_argument("-x", "--maxhsv", default="67,255,236",
    help="hsv comma delimited")
args = vars(ap.parse_args())

# load image and display it until keypress
image = imutils.resize(cv2.imread(args["image"]), width=600)
cv2.imshow("input image", image)
#cv2.waitKey(0)

# convert image to HSV
imageHSV = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

# load min court mask
minHSV = args["minhsv"].split(",")
minHSV = (int(minHSV[0]), int(minHSV[1]), int(minHSV[2]))

# load max court mask
maxHSV = args["maxhsv"].split(",")
maxHSV = (int(maxHSV[0]), int(maxHSV[1]), int(maxHSV[2]))

# print status
print("[INFO] court mask minHSV={} maxHSV={}".format(minHSV, maxHSV))

# calculate the court mask and display it until keypress
courtMask = cv2.inRange(imageHSV, minHSV, maxHSV)
cv2.imshow("court mask", courtMask)
#cv2.waitKey(0)

# calculate the ball mask (inverse of the courtMask) and display it
#until keypress
ballMask = cv2.bitwise_not(courtMask)
cv2.imshow("ball mask", ballMask)
#cv2.waitKey(0)

# apply "opening" (series of erosions followed by dilation) to
# eliminate salt and pepper noise and display it until keypress
kernelSize = (5, 5)
kernel = cv2.getStructuringElement(cv2.MORPH_RECT, kernelSize)
#morphed = cv2.morphologyEx(ballMask, cv2.MORPH_OPEN, kernel, iterations=3)
morphed = cv2.erode(ballMask, (3, 3), iterations=8)
morphed = cv2.dilate(morphed, (3, 3), iterations=4)
morphed = cv2.erode(morphed, (3, 3), iterations=1)
cv2.imshow("morphed", morphed)
#cv2.waitKey(0)

# find contours in the image, keeping only the EXTERNAL contours in
# the image
cnts = cv2.findContours(morphed.copy(), cv2.RETR_EXTERNAL,
    cv2.CHAIN_APPROX_SIMPLE)
cnts = imutils.grab_contours(cnts)
print("Found {} EXTERNAL contours".format(len(cnts)))

# sort the 1:1 aspect ratio contours according to size
topCnts = 12
cnts = sorted(cnts, key=cv2.contourArea,reverse=True)[:topCnts]

# loop over the contours to eliminate non 1:1 aspect ratio balls
cntsAROneToOne = []
i=0
for c in cnts:
    # compute the area of the contour along with the bounding box
    # to compute the aspect ratio
    area = cv2.contourArea(c)
    (x, y, w, h) = cv2.boundingRect(c)
    if area > 300:
        print("[INFO] cnt[DISCARDED] area={}".format(area))
        continue

    # compute the aspect ratio of the contour, which is simply the width
    # divided by the height of the bounding box
    aspectRatio = w / float(h)

    # if the aspect ratio is approximately one, then the shape is a
    # circle or square
    if aspectRatio >= 0.79 and aspectRatio <= 1.35:
        print("[INFO] cnts[{}] aspectRatio={}".format(i, aspectRatio))
        cntsAROneToOne.append(c)
        i+=1

    # otherwise, discard
    else:
        print("[INFO] cnt[DISCARDED] aspectRatio={}".format(aspectRatio))

def draw_contour(image, c, i):
    # compute the center of the contour area and draw a circle
    # representing the center
    M = cv2.moments(c)
    try:
        cX = int(M["m10"] / M["m00"])
        cY = int(M["m01"] / M["m00"])
    except:
        return
    # draw the countour number on the image
    cv2.putText(image, "#{}".format(i + 1), (cX - 20, cY),
        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 4)
    # return the image with the contour number drawn on it
    return image

# loop over the (now sorted) contours and draw them
numBalls = 8
numberedImage = image.copy()
for (i, c) in enumerate(cntsAROneToOne[:numBalls]):
    draw_contour(numberedImage, c, i)
cv2.imshow("labeled contours", numberedImage)
cv2.waitKey(0)

# loop to extract ball ROIs
balls = []
for i, c in enumerate(cntsAROneToOne[:numBalls]):
    # compute the bounding box
    (x, y, w, h) = cv2.boundingRect(c)

    # grab roi from the ball mask image and add to the ball ROIs list
    ballMaskROI = ballMask[y-10:y+h+10, x-10:x+w+10]
    imageROI =       image[y-10:y+h+10, x-10:x+w+10]

    # make a border before eroding and floodfilling
    # https://docs.opencv.org/3.4/dc/da3/tutorial_copyMakeBorder.html
    top = int(0.05 * ballMaskROI.shape[0])  # shape[0] = rows
    bottom = top
    left = int(0.05 * ballMaskROI.shape[1])  # shape[1] = cols
    right = left
    borderType = cv2.BORDER_CONSTANT
    value = 0
    ballMaskROI = cv2.copyMakeBorder(ballMaskROI.copy(), 3, 3, 3, 3, borderType, 0)

    # apply erosions
    ballMaskROI = cv2.erode(ballMaskROI, (5, 5), iterations=5)
    # cv2.imshow("ball mask #{}".format(i+1), ballMaskROI)
    # cv2.waitKey(0)
    ballMaskROI = cv2.dilate(ballMaskROI, (5, 5), iterations=3)

    # floodfill via
    # https://www.learnopencv.com/filling-holes-in-an-image-using-opencv-python-c/
    ballMaskROIinv = cv2.bitwise_not(ballMaskROI)
    height, width = ballMaskROIinv.shape[:2]
    mask = np.zeros((height+2, width+2), np.uint8)
    cv2.floodFill(ballMaskROIinv, mask, (0,0), 255)
    cv2.imshow("flooded #{}".format(i+1), ballMaskROIinv)
    ballMaskROIfloodfillinv = cv2.bitwise_not(ballMaskROIinv)
    im_out = ballMaskROI | ballMaskROIfloodfillinv

    # ensure images are the same size for bitwise and
    im_out = cv2.resize(im_out.copy(), (108, 100))
    imageROI = cv2.resize(imageROI.copy(), (108, 100))

    # bitwise and the roi with the corresponding image roi
    ball = cv2.bitwise_and(imageROI, imageROI, mask=im_out)

    # add the ball to the balls list
    balls.append(ball)

    # display the ball roi
    cv2.imshow("ball #{}".format(i+1), ball)

    # save to the balls folder
    try:
        os.mkdir(args["image"][:-4] + "/")
        os.mkdir(args["image"][:-4] + "/balls/")
    except OSError as error:
        pass
    cv2.imwrite(args["image"][:-4] + "/balls/" + str(i) + ".png", ball)

# wait for keypress
cv2.waitKey(0)

# destroy windows and exit
cv2.destroyAllWindows()




