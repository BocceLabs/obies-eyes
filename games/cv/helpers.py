import cv2
from .pyimagesearch.descriptors.histogram import Histogram
from sklearn.cluster import KMeans
from scipy.spatial import distance as dist
import numpy as np
import imutils

def find_ball_contours(frame, minhsv, maxhsv):
    # convert image to HSV
    imageHSV = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # load min court mask
    minHSV = minhsv.split(",")
    minHSV = (int(minHSV[0]), int(minHSV[1]), int(minHSV[2]))

    # load max court mask
    maxHSV = maxhsv.split(",")
    maxHSV = (int(maxHSV[0]), int(maxHSV[1]), int(maxHSV[2]))

    # print status
    # print("[INFO] court mask minHSV={} maxHSV={}".format(minHSV, maxHSV))

    # calculate the court mask and display it until keypress
    courtMask = cv2.inRange(imageHSV, minHSV, maxHSV)

    # calculate the ball mask (inverse of the courtMask) and display it
    # until keypress
    ballMask = cv2.bitwise_not(courtMask)
    # cv2.imshow("ball mask", ballMask)

    # apply "opening" (series of erosions followed by dilation) to
    # eliminate salt and pepper noise and display it until keypress
    kernelSize = (5, 5)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, kernelSize)
    # morphed = cv2.morphologyEx(ballMask, cv2.MORPH_OPEN, kernel, iterations=3)
    morphed = cv2.erode(ballMask, (3, 3), iterations=8)
    morphed = cv2.dilate(morphed, (3, 3), iterations=4)
    morphed = cv2.erode(morphed, (3, 3), iterations=3)

    # find contours in the image, keeping only the EXTERNAL contours in
    # the image
    cnts = cv2.findContours(morphed.copy(), cv2.RETR_EXTERNAL,
                            cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    # print("Found {} EXTERNAL contours".format(len(cnts)))

    # sort the 1:1 aspect ratio contours according to size
    topCnts = 9
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:topCnts]

    # loop over the contours to eliminate non 1:1 aspect ratio balls
    cntsAROneToOne = []
    i = 0
    for c in cnts:
        # compute the area of the contour along with the bounding box
        # to compute the aspect ratio
        area = cv2.contourArea(c)
        (x, y, w, h) = cv2.boundingRect(c)
        if area > 2000:
            # print("[INFO] cnt[DISCARDED] area={}".format(area))
            continue

        # compute the aspect ratio of the contour, which is simply the width
        # divided by the height of the bounding box
        aspectRatio = w / float(h)

        # if the aspect ratio is approximately one, then the shape is a
        # circle or square
        if aspectRatio >= 0.79 and aspectRatio <= 1.35:
            # print("[INFO] cnts[{}] aspectRatio={}".format(i, aspectRatio))
            cntsAROneToOne.append(c)
            i += 1

        # otherwise, discard
        else:
            pass
            # print("[INFO] cnt[DISCARDED] aspectRatio={}".format(aspectRatio))
    return cntsAROneToOne, ballMask

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

def extract_balls(frame, ballMask, cnts, numBalls):
	# loop to extract ball ROIs
	balls = []
	for i, c in enumerate(cnts[:numBalls]):
		# compute the bounding box
		(x, y, w, h) = cv2.boundingRect(c)

		# compute the center of the contour
		M = cv2.moments(c)
		cX = int(M["m10"] / M["m00"])
		cY = int(M["m01"] / M["m00"])

		# grab roi from the ball mask image and add to the ball ROIs list
		ballMaskROI = ballMask[y-10:y+h+10, x-10:x+w+10]
		imageROI =       frame[y-10:y+h+10, x-10:x+w+10]

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
		ballMaskROI = cv2.dilate(ballMaskROI, (5, 5), iterations=3)

		# floodfill via
		# https://www.learnopencv.com/filling-holes-in-an-image-using-opencv-python-c/
		ballMaskROIinv = cv2.bitwise_not(ballMaskROI)
		height, width = ballMaskROIinv.shape[:2]
		mask = np.zeros((height+2, width+2), np.uint8)
		cv2.floodFill(ballMaskROIinv, mask, (0,0), 255)
		# cv2.imshow("flooded #{}".format(i+1), ballMaskROIinv)
		ballMaskROIfloodfillinv = cv2.bitwise_not(ballMaskROIinv)
		im_out = ballMaskROI | ballMaskROIfloodfillinv

		# ensure images are the same size for bitwise and
		im_out = cv2.resize(im_out.copy(), (108, 100))
		imageROI = cv2.resize(imageROI.copy(), (108, 100))

		# bitwise and the roi with the corresponding image roi
		ball = cv2.bitwise_and(imageROI, imageROI, mask=im_out)

		# add the ball to the balls list
		balls.append((ball, (cX, cY)))
	return balls

def cluster_balls(balls_rois, clusters=3, debug=False):
	# initialize the image descriptor along with the image matrix
	desc = Histogram([8, 8, 8], cv2.COLOR_BGR2LAB)
	data = []

	# loop over the input dataset of images
	for ball in balls_rois:
		# load the image, describe the image, then update the list of data
		hist = desc.describe(ball[0])
		data.append(hist)

	# cluster the color histograms
	clt = KMeans(n_clusters=clusters, random_state=42)
	labels = clt.fit_predict(data)

	# list of stacks
	stacks = []
	cluster_idxs = []

	# loop over the unique labels
	for label in np.unique(labels):
		# grab all image paths that are assigned to the current label
		indices = np.where(np.array(labels, copy=False) == label)[0].tolist()
		cluster_idxs.append(indices)

		# placeholder for horizontal stack
		stack = []

		# loop over the image paths that belong to the current label
		for (i, idx) in enumerate(indices):
			# load the image, force size, and display it
			image = cv2.resize(balls_rois[idx][0], (200, 200))
			stack.append(image)

		# add the stack to the stacks
		stacks.append(np.hstack(stack))

	# display the cluster
	if debug:
		for (i, stack) in enumerate(stacks):
			cv2.imshow("Cluster #{}".format(i + 1), stack)

	return cluster_idxs

def calculate_frame_score(frame, balls_rois, pallino_idx, teamA_idxs, teamB_idxs, key):
	# copy the frame
	frame_annotated = frame.copy()

	# grab the pallino
	pallino = balls_rois[pallino_idx[0]][1]
	pallino = tuple(float(s) for s in str(pallino).strip("()").split(","))

	# determine all teamA distances to pallino
	teamA_distances = []
	for ball_idx in teamA_idxs:
		# convert the ball coordinates to a float tuple
		ball_coords = tuple(float(s) for s in str(balls_rois[ball_idx][1]).strip("()").split(","))

		# determine the euclidean distance and add it to the teamA distances list
		D = dist.euclidean(pallino, ball_coords)
		teamA_distances.append(D)

	# determine all teamB distances to pallino
	teamB_distances = []
	for ball_idx in teamB_idxs:
		# convert the ball coordinates to a float tuple
		ball_coords = tuple(float(s) for s in str(balls_rois[ball_idx][1]).strip("()").split(","))

		# determine the euclidean distance and add it to the teamA distances list
		D = dist.euclidean(pallino, ball_coords)
		teamB_distances.append(D)

	# sort teamA balls and distances
	teamA_distances, teamA_idxs = zip(*sorted(zip(teamA_distances, teamA_idxs)))

	# sort teamB balls and distances
	teamB_distances, teamB_idxs = zip(*sorted(zip(teamB_distances, teamB_idxs)))

	# grab each min distance
	teamA_min_distance = teamA_distances[0]
	teamB_min_distance = teamB_distances[0]

	# compare and handle
	# teamA is closer
	if teamA_min_distance < teamB_min_distance:
		# keep track of winner and points
		# keep track of winner and points
		if key == ord("r"):
			frameWinner = "Red"
			color = (0, 0, 255)

		elif key == ord("p"):
			frameWinner = "Purple"
			color = (226, 43, 138)


		framePoints = 0

		# determine how many are closer
		for (i, dB) in enumerate(teamB_distances):
			for (j, dA) in enumerate(teamA_distances):
				if dA < dB:
					framePoints +=1
					pallino_coords = (int(pallino[0]), int(pallino[1]))
					ball_coords = (int(balls_rois[teamA_idxs[j]][1][0]),
								   int(balls_rois[teamA_idxs[j]][1][1]))
					frame_annotated = cv2.line(frame_annotated, pallino_coords, ball_coords,
						color, 3)

				else:
					break
			break

	# teamB is closer
	elif teamB_min_distance < teamA_min_distance:
		# keep track of winner and points
		if key == ord("r"):
			frameWinner = "Red"
			color = (0, 0, 255)

		elif key == ord("p"):
			frameWinner = "Purple"
			color = (226, 43, 138)


		framePoints = 0

		# determine how many are closer
		for (i, dA) in enumerate(teamA_distances):
			for (j, dB) in enumerate(teamB_distances):
				if dB < dA:
					framePoints += 1
					pallino_coords = (
					int(pallino[0]), int(pallino[1]))
					ball_coords = (int(balls_rois[teamB_idxs[j]][1][0]),
								   int(balls_rois[teamB_idxs[j]][1][1]))
					frame_annotated = cv2.line(frame_annotated, pallino_coords, ball_coords,
							 color, 3)
				else:
					break
			break

		# annotate the winner
	# text = "{} won this frame with {} points".format(frameWinner, framePoints)
	# frame_annotated = cv2.putText(frame_annotated, text, (20, 20),
	# 				cv2.FONT_HERSHEY_SIMPLEX,
	# 				0.8, color, 2)

	# print the info about who won
	return frame_annotated, color, frameWinner, framePoints