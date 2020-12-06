# imports
import cv2
import argparse
import tensorflow as tf
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import numpy as np
import pathlib
import math
from PIL import Image
from google.protobuf import text_format
import platform
import imutils


# https://colab.research.google.com/github/trekhleb/machine-learning-experiments/blob/master/experiments/objects_detection_ssdlite_mobilenet_v2/objects_detection_ssdlite_mobilenet_v2.ipynb



def download_model(model_name):
    model_url = 'http://download.tensorflow.org/models/object_detection/' + model_name + '.tar.gz'

    model_dir = tf.keras.utils.get_file(
        fname=model_name,
        origin=model_url,
        untar=True,
        cache_dir=pathlib.Path('assets').absolute()
    )
    model_path = tf.saved_model.load(model_dir + '/saved_model')

    return model_path

def download_labels(labels_name):
    labels_url = 'https://raw.githubusercontent.com/tensorflow/models/master/research/object_detection/data/' + labels_name

    labels_path = tf.keras.utils.get_file(
        fname=labels_name,
        origin=labels_url,
        cache_dir=pathlib.Path('assets').absolute()
    )

    labels_file = open(labels_path, 'r')
    labels_string = labels_file.read()

    labels_map = string_int_label_map_pb2.StringIntLabelMap()
    try:
        text_format.Merge(labels_string, labels_map)
    except text_format.ParseError:
        labels_map.ParseFromString(labels_string)

    labels_dict = {}
    for item in labels_map.item:
        labels_dict[item.id] = item.display_name

    return labels_dict

def getClassLabel(class_id, classes):
    for key,value in classes.items():
        if class_id == key:
            return value

def detect_objects_on_image(image, model):
    image = np.asarray(image)
    input_tensor = tf.convert_to_tensor(image)
    # Adding one more dimension since model expect a batch of images.
    input_tensor = input_tensor[tf.newaxis, ...]

    output_dict = model(input_tensor)

    num_detections = int(output_dict['num_detections'])
    output_dict = {
        key:value[0, :num_detections].numpy()
        for key,value in output_dict.items()
        if key != 'num_detections'
    }
    output_dict['num_detections'] = num_detections
    output_dict['detection_classes'] = output_dict['detection_classes'].astype(np.int64)

    return output_dict

def draw_detections_on_image(image, detections, labels):
    image_with_detections = image
    width, height, channels = image_with_detections.shape

    font = cv2.FONT_HERSHEY_SIMPLEX
    color = (0, 255, 0)
    label_padding = 5

    num_detections = detections['num_detections']
    print("num_detections={}".format(num_detections))
    if num_detections > 0:
        for detection_index in range(num_detections):
            detection_score = detections['detection_scores'][detection_index]
            detection_box = detections['detection_boxes'][detection_index]
            detection_class = detections['detection_classes'][detection_index]
            detection_label = labels[detection_class]
            detection_label_full = detection_label + ' ' + str(math.floor(100 * detection_score)) + '%'

            y1 = int(width * detection_box[0])
            x1 = int(height * detection_box[1])
            y2 = int(width * detection_box[2])
            x2 = int(height * detection_box[3])

            # Detection rectangle.
            image_with_detections = cv2.rectangle(
                image_with_detections,
                (x1, y1),
                (x2, y2),
                color,
                3
            )

            # Label background.
            label_size = cv2.getTextSize(
                detection_label_full,
                cv2.FONT_HERSHEY_COMPLEX,
                0.7,
                2
            )
            image_with_detections = cv2.rectangle(
                image_with_detections,
                (x1, y1 - label_size[0][1] - 2 * label_padding),
                (x1 + label_size[0][0] + 2 * label_padding, y1),
                color,
                -1
            )

            # Label text.
            cv2.putText(
                image_with_detections,
                detection_label_full,
                (x1 + label_padding, y1 - label_padding),
                font,
                0.7,
                (0, 0, 0),
                1,
                cv2.LINE_AA
            )

    return image_with_detections

# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-i", "--image", required=True,
    help="path to the image")
ap.add_argument("-m", "--model", default="ssdlite_mobilenet_v2_coco_2018_05_09",
    help="tensorflow model name")
ap.add_argument("-p", "--pbtxt", default="mscoco_label_map.pbtxt",
    help="desired labels file")
args = vars(ap.parse_args())

# load the image
image = cv2.imread(args["image"])
image = imutils.resize(image, width=1000)
#image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

# download the model and labels
saved_model= download_model(args["model"])
labels = download_labels(args["pbtxt"])

model = saved_model.signatures['serving_default']



detections = detect_objects_on_image(image, model)
print(detections)

output_image = draw_detections_on_image(image, detections, labels)

cv2.imshow("output", output_image)
cv2.waitKey(0)