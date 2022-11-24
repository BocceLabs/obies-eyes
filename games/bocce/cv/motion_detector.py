import cv2
import imutils


class MotionDetector:
    def __init__(self, drawMotionZones=False):
        self.firstFrame = None
        self.frameCount = 0
        self.drawMotionZones = drawMotionZones

    def update(self, frame):
        # set motion indicator
        motion = False

        # grayscale and blur
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (25, 25), 0)

        # if the first frame is None, initialize it
        if self.firstFrame is None or self.frameCount >= 20:
            self.firstFrame = gray
            self.frameCount = 0
            return frame, motion
        self.frameCount += 1

        # compute the absolute difference between the current frame and first frame
        frameDelta = cv2.absdiff(self.firstFrame, gray)
        thresh = cv2.threshold(frameDelta, 25, 255, cv2.THRESH_BINARY)[1]

        # dilate the thresholded image to fill in holes, then find contours
        # on thresholded image
        thresh = cv2.dilate(thresh, None, iterations=2)
        cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)

        # loop over the contours
        for c in cnts:
            # grab the area
            area = cv2.contourArea(c)

            # if the contour is too small, ignore it
            if cv2.contourArea(c) < 500:
                continue

            # indicate motion
            if area >= 500:
                motion = True

            # compute the bounding box for the contour, draw it on the frame,
            # and update the text
            if self.drawMotionZones:
                (x, y, w, h) = cv2.boundingRect(c)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        return frame, motion
