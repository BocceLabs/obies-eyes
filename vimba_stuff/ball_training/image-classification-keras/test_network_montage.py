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

BATCH_SIZE = 8
MODEL = load_model("bocce.model")


def preprocess(circle_roi):
    # pre-process the image for classification
    image = cv2.resize(circle_roi, (28, 28))
    image = image.astype("float") / 255.0
    image = img_to_array(image)
    #image = np.expand_dims(image, axis=0)
    return image


def inference(circle_roi):
    preprocessed_roi = preprocess(circle_roi)
    (notBocce, bocce) = MODEL.predict(preprocessed_roi)[0]
    return True if bocce > notBocce else False


def chunker(seq, size):
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))

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
idxs = np.random.choice(idxs, size=(32*4,), replace=False)
images = []

# loop over the testing indexes
for chunk in chunker(idxs, BATCH_SIZE):
	# preprocess the chunk
	image_origs = []
	preprocessed_images = []
	for idx in chunk:
		image_orig = cv2.imread(imagePaths[idx])
		image_origs.append(image_orig)
		preprocessed_images.append(preprocess(image_orig))

	# put the preprocessed images in an array
	preprocessed_images = np.array(preprocessed_images, dtype="float")

	# classify the chunk of images
	predictions = model.predict(preprocessed_images, batch_size=BATCH_SIZE)

	# loop over the predictions
	for i, p in enumerate(predictions):
		notBocce, bocce = p
		label = "Bocce" if bocce > notBocce else "Not Bocce"
		proba = "{:.2f}%".format(bocce*100) if bocce > notBocce else "{:.2f}%".format(notBocce*100)

		# draw the colored class label on the output image and add it to
		# the set of output images
		image_orig = cv2.resize(image_origs[i], (128, 128))
		color = (0, 0, 255) if "Not" in label else (0, 255, 0)
		cv2.putText(image_orig, label, (3, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
			color, 2)
		cv2.putText(image_orig, proba, (3, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
					color, 1)
		images.append(image_orig)

# create a montage using 128x128 "tiles" with 4 rows and 8 columns
montages = build_montages(images, (128, 128), (8, 4))

# display montages
for m in montages:
	# show the output montage
	cv2.imshow("Output", m)
	key = cv2.waitKey(0) & 0xFF
	if key == ord("q"):
		break