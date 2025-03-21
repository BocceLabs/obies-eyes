# import the necessary packages
import cv2
import imutils

class Histogram:
	def __init__(self, bins, colorspace):
		# store the number of bins for the histogram
		self.bins = bins
		self.colorspace = colorspace

	def describe(self, image, mask=None):
		# convert the image to the L*a*b* color space, compute a histogram,
		# and normalize it
		image = cv2.cvtColor(image, self.colorspace)
		hist = cv2.calcHist([image], [0, 1, 2], mask, self.bins,
			[0, 256, 0, 256, 0, 256])

		# handle if we are calculating the histogram for OpenCV 2.4
		if imutils.is_cv2():
			hist = cv2.normalize(hist).flatten()

		# otherwise, we are creating the histogram for OpenCV 3+
		else:
			hist = cv2.normalize(hist,hist).flatten()

		# return the histogram
		return hist
