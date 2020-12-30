# imports
import time
import cv2
import imutils
import numpy as np
from scipy.spatial import distance as dist
from sklearn.cluster import KMeans

# typically we'll import modularly
try:
    from games.bocce.ball import Ball, Pallino, Bocce
    from .pyimagesearch.descriptors.histogram import Histogram
    unit_test = False

# otherwise, we're running main test code at the bottom of this script
except:
    import sys
    import os
    sys.path.append(os.path.abspath(os.getcwd()))
    print(sys.path)
    from games.bocce.cv.pyimagesearch.descriptors.histogram import Histogram
    from games.bocce.ball import Ball, Pallino, Bocce
    unit_test = True


# Ball Algorithm pipeline:
# (1) Mask court via HSV
# (2) Grabcut via ball mask (opposite of court mask)
# (3) Find contours
# (4) Filter contours based on (A) Aspect Ratio and (B) Area
# (5) Clustering - Cluster Ball ROIs based on L*A*B* Color Histogram
# (6) Sort clusters
#       Pallino has len=1
#       Home and Away Bocce balls remain in the other clusters
# (7) Assign balls to objects
#        Pallino()
#        Bocce()
# (8) Assign team balls
#        homeBalls = [] # list of Bocce
#        awayBalls = [] # list of Bocce



class BallFinder():
    def __init__(self):
        self.pallino = None
        self.homeBalls = []
        self.awayBalls = []

        self.minHSV = (72, 0, 134)
        self.maxHSV = (175, 66, 223)

    def adjust_HSV_ranges(self, newMinHSV, newMaxHSV):
        self.minHSV = newMinHSV
        self.maxHSV = newMaxHSV

    def pipeline(self, court, throwsHome, throwsAway):
        # add the pallino, home throws, and away throws
        # todo doesn't take into account balls removed from play!!!!!
        expectedBalls = 1 + throwsHome + throwsAway
        clusters = 1 + (1 if throwsHome >= 1 else 0) + (1 if throwsAway >= 1 else 0)

        # (0) slice out the court
        (h, w) = court.shape[:2]
        court = court[int(h*.20):int(h*.80), int(0):int(w*.75)]
        cv2.imshow("court", court)
        cv2.waitKey(0)

        # (0.1) Stich birds eye feeds
        # todo

        # (0.2) Detect court
        # todo

        # (1) Mask court via HSV
        ballMask = self.mask_out_court(court, self.minHSV, self.maxHSV)
        cv2.imshow("ballMask", ballMask)
        cv2.waitKey(0)

        # (2) Grabcut via ball mask (opposite of court mask)
        # ballMask = self.grab_cut_mask(court, ballMask)
        # cv2.imshow("ballMask", ballMask)
        # cv2.waitKey(0)

        # (3) Find contours
        cnts = self.find_and_sort_ball_contours(ballMask, expectedBalls)

        # (4) Filter contours based on (A) Aspect Ratio and (B) Area
        cnts = self.filter_contours(cnts)

        # (5) Create Balls
        balls = self.extract_balls(court, ballMask, cnts, expectedBalls)

        # (6) Clustering - Cluster Ball ROIs based on L*A*B* Color Histogram
        ballClusterIdxs = self.cluster_balls(balls, clusters, debug=True)

        # (6) Sort clusters and Assign team balls
        self.assign_balls(balls, ballClusterIdxs)

    def mask_out_court(self, frame, minHSV, maxHSV):
        # convert image to HSV
        imageHSV = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # calculate the court mask and display it until keypress
        courtMask = cv2.inRange(imageHSV, minHSV, maxHSV)

        ballMask = cv2.bitwise_not(courtMask)
        # cv2.imshow("ball mask", ballMask)

        # apply "opening" (series of erosions followed by dilation) to
        # eliminate salt and pepper noise and display it until keypress
        # morphed = cv2.morphologyEx(ballMask, cv2.MORPH_OPEN, kernel, iterations=3)
        morphed = cv2.erode(ballMask, (3, 3), iterations=6)
        morphed = cv2.dilate(morphed, (3, 3), iterations=6)
        morphed = cv2.erode(morphed, (3, 3), iterations=1)

        return morphed

    def grab_cut_mask(self, court, mask):
        ####### BEGIN GRABCUT MASK ALGO
        # method: https://www.pyimagesearch.com/2020/07/27/opencv-grabcut-foreground-segmentation-and-extraction/

        # apply a bitwise mask to show what the rough, approximate mask would
        # give us
        roughOutput = cv2.bitwise_and(court, court, mask=mask)

        # show the rough, approximated output
        # cv2.imshow("Rough Output", roughOutput)
        # cv2.waitKey(0)

        # any mask values greater than zero should be set to probable
        # foreground
        mask[mask > 0] = cv2.GC_PR_FGD
        mask[mask == 0] = cv2.GC_BGD

        # allocate memory for two arrays that the GrabCut algorithm internally
        # uses when segmenting the foreground from the background
        fgModel = np.zeros((1, 65), dtype="float")
        bgModel = np.zeros((1, 65), dtype="float")

        # apply GrabCut using the the mask segmentation method
        start = time.time()
        (mask, bgModel, fgModel) = cv2.grabCut(court, mask, None, bgModel,
                                               fgModel, iterCount=5,
                                               mode=cv2.GC_INIT_WITH_MASK)
        end = time.time()
        # print("[INFO] applying GrabCut took {:.2f} seconds".format(end - start))

        # the output mask has for possible output values, marking each pixel
        # in the mask as (1) definite background, (2) definite foreground,
        # (3) probable background, and (4) probable foreground
        values = (
            ("Definite Background", cv2.GC_BGD),
            ("Probable Background", cv2.GC_PR_BGD),
            ("Definite Foreground", cv2.GC_FGD),
            ("Probable Foreground", cv2.GC_PR_FGD),
        )

        # # loop over the possible GrabCut mask values
        # for (name, value) in values:
        #     # construct a mask that for the current value
        #     print("[INFO] showing mask for '{}'".format(name))
        #     valueMask = (mask == value).astype("uint8") * 255
        #
        #     # display the mask so we can visualize it
        #     cv2.imshow(name, valueMask)
        #     cv2.waitKey(0)

        # set all definite background and probable background pixels to 0
        # while definite foreground and probable foreground pixels are set
        # to 1, then scale teh mask from the range [0, 1] to [0, 255]
        outputMask = np.where((mask == cv2.GC_BGD) | (mask == cv2.GC_PR_BGD), 0, 1)
        outputMask = (outputMask * 255).astype("uint8")

        # apply a bitwise AND to the image using our mask generated by
        # GrabCut to generate our final output image
        output = cv2.bitwise_and(court, court, mask=outputMask)

        # show the input image followed by the mask and output generated by
        # GrabCut and bitwise masking
        # cv2.imshow("Input", frame)
        # cv2.imshow("GrabCut Mask", outputMask)
        # cv2.imshow("GrabCut Output", output)
        # cv2.waitKey(0)

        ####### END GRABCUT MASK ALGO
        # we will use "outputMask" from the above algo

        return outputMask

    def find_and_sort_ball_contours(self, ballMask, expectedBalls):
        # find contours in the image, keeping only the EXTERNAL contours in
        # the image
        cnts = cv2.findContours(ballMask.copy(), cv2.RETR_EXTERNAL,
                                cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        # print("Found {} EXTERNAL contours".format(len(cnts)))

        # sort the 1:1 aspect ratio contours according to size
        cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:expectedBalls + 1]

        return cnts

    def filter_contours(self, cnts):
        # loop over the contours to eliminate non 1:1 aspect ratio balls
        filteredCnts = []
        i = 0
        for c in cnts:
            # compute the area of the contour along with the bounding box
            # to compute the aspect ratio
            area = cv2.contourArea(c)
            (x, y, w, h) = cv2.boundingRect(c)
            if area > 1000:
                print("[INFO] cnt[DISCARDED] area={}".format(area))
                continue

            # compute the aspect ratio of the contour, which is simply the width
            # divided by the height of the bounding box
            aspectRatio = w / float(h)

            # if the aspect ratio is approximately one, then the shape is a
            # circle or square
            if aspectRatio >= 0.35 and aspectRatio <= 1.71:
                print("[INFO] cnts[{}] aspectRatio={} area={}".format(i, aspectRatio, area))
                filteredCnts.append(c)
                i += 1

            # otherwise, discard
            else:
                print("[INFO] cnt[DISCARDED] aspectRatio={} area={}".format(aspectRatio, area))

        return filteredCnts

    def draw_contour(self, image, c, i):
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

    def extract_balls(self, frame, ballMask, cnts, expectedBalls):
        (h, w) = frame.shape[:2]
        blankImage = np.zeros((h, w, 1), dtype=np.uint8)


        # loop to extract ball ROIs
        balls = []
        for i, c in enumerate(cnts[:expectedBalls+1]):
            # compute the bounding box
            # (x, y, w, h) = cv2.boundingRect(c)

            center, radius = cv2.minEnclosingCircle(c)
            radius = int(radius)
            center = ( int(center[0]), int(center[1]) )
            cv2.circle(blankImage, center, radius, 255, -1)

            # compute the center of the contour
            M = cv2.moments(c)
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])

            # grab roi from the ball mask image and add to the ball ROIs list
            # ballMaskROI = ballMask[y-10:y+h+10, x-10:x+w+10]
            (x, y) = center
            ballMaskROI = blankImage[y - radius - 5:y + radius + 5, x - radius - 5:x + radius + 5]
            imageROI =         frame[y - radius - 5:y + radius + 5, x - radius - 5:x + radius + 5]

            # # # make a border before eroding and floodfilling
            # # # https://docs.opencv.org/3.4/dc/da3/tutorial_copyMakeBorder.html
            # # #
            # # top = int(0.05 * ballMaskROI.shape[1])  # shape[0] = rows
            # # bottom = top
            # # left = int(0.05 * ballMaskROI.shape[0])  # shape[1] = cols
            # # right = left
            # # borderType = cv2.BORDER_CONSTANT
            # # value = 0
            # # ballMaskROI = cv2.copyMakeBorder(ballMaskROI.copy(), 3, 3, 3, 3, borderType, 0)
            # #
            # # # apply erosions
            # # ballMaskROI = cv2.erode(ballMaskROI, (5, 5), iterations=5)
            # # ballMaskROI = cv2.dilate(ballMaskROI, (5, 5), iterations=3)
            #
            # # floodfill via
            # # https://www.learnopencv.com/filling-holes-in-an-image-using-opencv-python-c/
            # # Copy the thresholded image.
            # im_floodfill = ballMaskROI.copy()
            #
            # # Mask used to flood filling.
            # # Notice the size needs to be 2 pixels larger than the image.
            # bmH, bmW = ballMaskROI.shape[:2]
            # mask = np.zeros((bmH + 2, bmW + 2), np.uint8)
            #
            # # Floodfill from point (0, 0)
            # cv2.floodFill(im_floodfill, mask, (0, 0), 255);
            #
            # # Invert floodfilled image
            # im_floodfill_inv = cv2.bitwise_not(im_floodfill)
            #
            # # Combine the two images to get the foreground.
            # im_out = ballMaskROI | im_floodfill_inv
            #
            # # ensure images are the same size for bitwise and
            # im_out = cv2.resize(im_out.copy(), (100, 100))
            # imageROI = cv2.resize(imageROI.copy(), (100, 100))

            # bitwise and the roi with the corresponding image roi
            imageROI = cv2.bitwise_and(imageROI, imageROI, mask=ballMaskROI)

            # determine the average color
            avgColor = cv2.mean(imageROI, mask=ballMaskROI)

            # create a ball object
            b = Ball(color=avgColor)
            b.coordinates = (cX, cY)
            b.roi = imageROI

            # add the ball to balls
            balls.append(b)

        return balls

    def cluster_balls(self, balls, clusters=3, debug=False):
        print("expected clusters = {}".format(str(clusters)))

        # initialize the image descriptor along with the image matrix
        desc = Histogram([8, 8, 8], cv2.COLOR_BGR2LAB)
        data = []

        # loop over the input dataset of images
        for ball in balls:
            roi = ball.roi
            # load the image, describe the image, then update the list of data
            hist = desc.describe(roi)
            data.append(hist)

        # cluster the color histograms
        clt = KMeans(n_clusters=clusters, random_state=42)
        labels = clt.fit_predict(data)

        # list of stacks
        stacks = []
        ballClusterIdxs = []

        # loop over the unique labels
        for label in np.unique(labels):
            # grab all image paths that are assigned to the current label
            indices = np.where(np.array(labels, copy=False) == label)[0].tolist()
            ballClusterIdxs.append(indices)

            # placeholder for horizontal stack
            stack = []

            # loop over the image paths that belong to the current label
            for (i, idx) in enumerate(indices):
                # load the image, force size, and display it
                image = cv2.resize(balls[idx].roi, (200, 200))
                stack.append(image)

            # add the stack to the stacks
            stacks.append(np.hstack(stack))

        # display the cluster
        if debug:
            for (i, stack) in enumerate(stacks):
                cv2.imshow("Cluster #{}".format(i + 1), stack)
                cv2.waitKey(0)

        return ballClusterIdxs

    def assign_balls(self, balls, ballClusterIdxs):
        # sort the clusters by length
        sortedBallClusterIdxs = sorted(ballClusterIdxs, key=len)

        # assign balls
        for (i, cluster) in enumerate(sortedBallClusterIdxs):
            # pallino
            for ballIdx in cluster:
                # create a Ball and assign coordinates
                b = balls[ballIdx]

                # the pallino should be the smallest cluster and only have one index in it
                if i == 0 and len(cluster) == 1:
                    # cast the Ball to a Pallino and set the class attribute
                    b.__class__ = Pallino
                    self.pallino = b

                # home balls
                elif i == 1:
                    # cast the Ball to a Bocce ball and add it to the home balls
                    b.__class__ = Bocce
                    self.homeBalls.append(b)

                # away balls
                elif i == 2:
                    # cast the Ball to a Bocce ball and add it to the away balls
                    b.__class__ = Bocce
                    self.awayBalls.append(b)


# test code
def test_static_image():
    # append to the path so we can find the modules and test image
    sys.path.append(os.path.abspath(os.path.join(__file__, "../../..")))

    # load an image
    court = cv2.imread(os.path.join("exploratory_code/assets/court.png"))

    # test the BallFinder pipeline
    bf = BallFinder()
    bf.pipeline(court, 2, 2)
    pallino = bf.pallino
    teamHomeBalls = bf.homeBalls
    teamAwayBalls = bf.awayBalls

    print(pallino)
    print(teamHomeBalls)
    print(teamAwayBalls)


# run the test code
if __name__ == "__main__":
    test_static_image()