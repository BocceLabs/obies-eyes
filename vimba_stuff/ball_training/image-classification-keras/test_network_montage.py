# USAGE
# python test_network_montage.py --model bocce.model --images bocce

# import the necessary packages
from tensorflow.keras.preprocessing.image import img_to_array
from tensorflow.keras.models import load_model
from imutils import paths
from imutils import build_montages
import numpy as np
import argparse
import imutils
import random
import cv2

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-m", "--model", required=True,
	help="path to trained model model")
ap.add_argument("-i", "--images", required=True,
	help="path to test images")
args = vars(ap.parse_args())

# load the trained convolutional neural network
print("[INFO] loading network...")
model = load_model(args["model"])

# grab the image paths and randomly shuffle them
imagePaths = sorted(list(paths.list_images(args["images"])))
random.seed(42)
random.shuffle(imagePaths)

# randomly select a few testing images and then initialize the output
# set of images
idxs = np.arange(0, len(imagePaths))
idxs = np.random.choice(idxs, size=(150,), replace=False)
images = []

# loop over the testing indexes
for i in idxs:
	# pre-process the image for classification
	image_orig = cv2.imread(imagePaths[i])
	image = cv2.resize(image_orig.copy(), (28, 28))
	image = image.astype("float") / 255.0
	image = img_to_array(image)
	image = np.expand_dims(image, axis=0)

	# grab the current testing image and classify it
	# classify the input image
	(notBocce, bocce) = model.predict(image)[0]
	label = "Bocce" if bocce > notBocce else "Not Bocce"
	proba = "{:.2f}%".format(bocce*100) if bocce > notBocce else "{:.2f}%".format(notBocce*100)

	# draw the colored class label on the output image and add it to
	# the set of output images
	image_orig = cv2.resize(image_orig, (128, 128))
	color = (0, 0, 255) if "Not" in label else (0, 255, 0)
	cv2.putText(image_orig, label, (3, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
		color, 2)
	cv2.putText(image_orig, proba, (3, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
				color, 1)
	images.append(image_orig)

# create a montage using 128x128 "tiles" with 5 rows and 5 columns
montages = build_montages(images, (128, 128), (5, 5))

# display montages
for m in montages:
	# show the output montage
	cv2.imshow("Output", m)
	key = cv2.waitKey(0) & 0xFF
	if key == ord("q"):
		break