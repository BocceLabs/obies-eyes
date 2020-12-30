# imports
import cv2
import imutils

# typically we'll import modularly
try:
    from games.bocce.cv.pyimagesearch.panorama import Stitcher
    from camera.camera import ImageZMQCamera
    unit_test = False

# otherwise, we're running main test code at the bottom of this script
except:
    import sys
    import os
    sys.path.append(os.path.abspath(os.getcwd()))
    print(sys.path)
    from games.camera.camera import ImageZMQCamera
    from games.bocce.cv.pyimagesearch.panorama import Stitcher
    unit_test = True


# for "pairs" of any length
def chunkwise(t, size=2):
    it = iter(t)
    return zip(*[it]*size)

# class Stitch():
#     def __init__(self, frames):
#         # ordered and oriented in the same way
#         self.frames = frames
#
#     def stitch(self):
#         # stitch pairs progressively
#         stitcher = Stitcher()
#
#         # force same dimensions
#         for frame in self.frames:
#             frame = imutils.resize(frame, width=600)
#
#         # stitch the frames together to form the panorama
#         # IMPORTANT: you might have to change this line of code
#         # depending on how your cameras are oriented; frames
#         # should be supplied in left-to-right order
#         for pair in chunkwise(self.frames, size=2):
#             pass
#         pass


# run the test code
if __name__ == "__main__":
    # cams = ["east", "center0", "center1", "center2", "west"]
    # pairs = []
    # camsLen = len(cams) % 2
    # for pair in chunkwise(cams, size=2):
    #     pairs.append(pair)
    # # odd
    # if camsLen == 1:
    #     print("stich cams[:-1] with result")
    # append to the path so we can find the modules and test image
    sys.path.append(os.path.abspath(os.path.join(__file__, "../../..")))

    c0 = ImageZMQCamera(name="west", source="rpi4b8gb,5557")
    c1 = ImageZMQCamera(name="center", source="rpi4b2gb,5555")
    c2 = ImageZMQCamera(name="east", source="rpi4b4gb,5556")

    input("initialized?")

    c0.initialize()
    c1.initialize()
    c2.initialize()

    frame0 = c0._get_frame()
    frame1 = c1._get_frame()
    frame2 = c2._get_frame()

    frame0 = imutils.resize(frame0, width=600)
    frame1 = imutils.resize(frame1, width=600)
    frame2 = imutils.resize(frame2, width=600)

    cv2.imshow("frame0", frame0)
    cv2.imshow("frame1", frame1)
    cv2.imshow("frame2", frame2)
    cv2.waitKey(0)

    # s = cv2.Stitcher()
    #
    # errorCode, result = s.stitch((frame0, frame1, frame2))
    #
    # print(errorCode)

    s = Stitcher()
    result = s.stitch((frame0, frame1))

    cv2.imshow("stitched", result)
    cv2.waitKey(0)

    result2 = s.stitch((result, frame2))
    cv2.imshow("stitched2", result2)
    cv2.waitKey(0)