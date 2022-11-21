from ball_finding import draw_circles, extract_circle_contours, find_circles, balls_to_disk
from lib.centroidtracker import CentroidTracker
from vimba import *
from imutils.video import FPS
import cv2
import time
import config

bocce_ct = CentroidTracker()
pallino_ct = CentroidTracker()

bocce_queues = {}


def centroid_of_centroids(points):
    x = [p[0] for p in points]
    y = [p[1] for p in points]
    return int(sum(x) / len(points)), int(sum(y) / len(points))


with Vimba.get_instance() as vimba:
    # select the camera
    cam = vimba.get_camera_by_id(config.CAMERA_LEFT)

    # open the camera
    with cam:
        # settings
        cam.ExposureAuto.set('Once')
        cam.BalanceWhiteAuto.set('Once')
        cam.GainAuto.set('Once')
        time.sleep(10)
        # settings
        cam.ExposureAuto.set('Off')
        cam.BalanceWhiteAuto.set('Off')
        cam.GainAuto.set('Off')

        start = time.time()
        frames = 0

        # loop over frames
        while True:
            # grab the frame and convert it
            frame = cam.get_frame()
            frame.convert_pixel_format(PixelFormat.Bgra8)
            frame = frame.as_opencv_image()
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            disp_frame = frame.copy()

            # extract the court ROI
            y1, y2, x1, x2 = config.LEFT_ROI_SLICE
            frame = frame[y1:y2, x1:x2]

            # find the bocce balls
            circles_bocce = find_circles(frame.copy(), config.RADIUS_BOCCE, config.RADIUS_BOCCE_TOLERANCE)
            balls_dict_bocce = extract_circle_contours(circles_bocce, frame, config.RADIUS_BOCCE)

            # find the pallino ball
            circles_pallino = find_circles(frame.copy(), config.RADIUS_PALLINO, config.RADIUS_PALLINO_TOLERANCE)
            balls_dict_pallino = extract_circle_contours(circles_pallino, frame, config.RADIUS_PALLINO)

            # update the centroid tracker
            bocce_ball_coords = []
            pallino_ball_coords = []
            for b, v in balls_dict_bocce.items():
                bocce_ball_coords.append(v['coord'])
            for b, v in balls_dict_pallino.items():
                pallino_ball_coords.append(v['coord'])
            bocces = bocce_ct.update(bocce_ball_coords)
            pallinos = pallino_ct.update(pallino_ball_coords)

            # stabilization
            for (objectID, centroid) in bocces.items():
                # populate the centroid queues
                if objectID not in bocce_queues.keys():
                    bocce_queues[objectID] = {}
                    bocce_queues[objectID]["center"] = None
                    bocce_queues[objectID]["history"] = []

                # add the item to the queue
                if len(bocce_queues[objectID]["history"]) >= config.SMA_QUEUE_SIZE:
                    del bocce_queues[objectID]["history"][0]
                bocce_queues[objectID]["history"].append(centroid)

                # calculate the centroid average of each queue
                bocce_queues[objectID]["center"] = centroid_of_centroids(bocce_queues[objectID]["history"])

            # display
            for (objectID, centroid_info) in bocce_queues.items():
                if objectID not in bocces.keys():
                    continue

                # extract the center
                center = centroid_info["center"]
                if center is None:
                    continue

                # draw a line to the pallino
                for (objectID, pallino_centroid) in pallinos.items():
                    cv2.line(disp_frame, (int(pallino_centroid[0]), int(pallino_centroid[1])),
                             (center[0], center[1]),
                             config.COLOR_WHITE, 1)

                # draw both the ID of the object and the centroid of the
                # object on the output frame
                text = "{}".format(objectID)
                cv2.putText(disp_frame, text, (center[0]-5, center[1]+5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, config.COLOR_BOCCE_BALL_TEXT, 3)

            for (objectID, centroid) in pallinos.items():
                # draw both the ID of the object and the centroid of the
                # object on the output frame
                text = "{}".format(objectID)
                cv2.putText(disp_frame, text, (int(centroid[0]-5), int(centroid[1]+5)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, config.COLOR_BOCCE_BALL_TEXT, 3)

            frames += 1
            elapsed = time.time() - start
            fps = frames / elapsed
            disp_frame[0:25, 0:140] = (0, 0, 0)
            cv2.putText(disp_frame, "FPS: {:.2f}".format(fps), (20, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, config.COLOR_GREEN, 2)

            # display and wait for keypress
            cv2.imshow('frame', disp_frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            #time.sleep(.02)


