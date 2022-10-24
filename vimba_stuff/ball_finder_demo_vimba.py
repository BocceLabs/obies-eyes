from circles import draw_circles, extract_circle_contours, find_circles, balls_to_disk
from lib.centroidtracker import CentroidTracker
from vimba import *
import cv2
import time
import config

bocce_ct = CentroidTracker()
pallino_ct = CentroidTracker()

with Vimba.get_instance() as vimba:
    # select the camera
    cam = vimba.get_camera_by_id(config.CAMERA_LEFT)

    # open the camera
    with cam:
        # settings
        # cam.ExposureAuto.set('Once')
        # cam.BalanceWhiteAuto.set('Once')
        # cam.GainAuto.set('Continuous')

        # loop over frames
        while True:
            # grab the frame and convert it
            frame = cam.get_frame()
            frame.convert_pixel_format(PixelFormat.Bgra8)
            frame = frame.as_opencv_image()
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

            # find the bocce balls
            circles_bocce = find_circles(frame.copy(), config.RADIUS_BOCCE, config.RADIUS_BOCCE_TOLERANCE)
            balls_dict_bocce = extract_circle_contours(circles_bocce, frame, config.RADIUS_BOCCE)

            # find the pallino ball
            circles_pallino = find_circles(frame.copy(), config.RADIUS_PALLINO, config.RADIUS_PALLINO_TOLERANCE)
            balls_dict_pallino = extract_circle_contours(circles_pallino, frame, config.RADIUS_PALLINO)

            # write the ball ROI to disk IF you need data for classification training
            # balls_to_disk(balls_dict_bocce)
            # balls_to_disk(balls_dict_pallino)

            # draw the unclassified circles
            # ball_circles = [(circles_bocce, config.RADIUS_BOCCE, config.COLOR_GREEN),
            #                 (circles_pallino, config.RADIUS_PALLINO, config.COLOR_RED)]
            # disp_frame = draw_circles(ball_circles, frame.copy())
            disp_frame = frame.copy()

            # update the centroid tracker
            bocce_ball_coords = []
            pallino_ball_coords = []
            for b, v in balls_dict_bocce.items():
                bocce_ball_coords.append(v['coord'])
            for b, v in balls_dict_pallino.items():
                pallino_ball_coords.append(v['coord'])
            bocces = bocce_ct.update(bocce_ball_coords)
            pallinos = pallino_ct.update(pallino_ball_coords)

            # draw the stabilized centroid
            # todo stabilize

            # loop over the tracked objects
            for (objectID, centroid) in bocces.items():
                # draw both the ID of the object and the centroid of the
                # object on the output frame
                text = "{}".format(objectID)
                cv2.putText(disp_frame, text, (int(centroid[0]-5), int(centroid[1]+5)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, config.COLOR_WHITE, 3)
            for (objectID, centroid) in pallinos.items():
                # draw both the ID of the object and the centroid of the
                # object on the output frame
                text = "{}".format(objectID)
                cv2.putText(disp_frame, text, (int(centroid[0]-5), int(centroid[1]+5)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, config.COLOR_RED, 3)

            # display and wait for keypress
            cv2.imshow('frame', disp_frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            time.sleep(.03)
