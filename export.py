import pickle
import numpy as np
from xml.etree.ElementTree import Element, SubElement, ElementTree, tostring, parse
from copy import deepcopy
import os
import imageio
import scipy as sp
import sys
try:
    sys.path.remove('/opt/ros/kinetic/lib/python2.7/dist-packages')
except:
    pass
import cv2

# ----------------- PARAMS ----------------------
MAX_CUT = 0.1               # Can be cut 20% on each side
AUGMENTATION_NUM = 1        # How many augmented images to produced?

RAW_DATA_FOLDER = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'raw_data')
DATA_LOCATION = os.path.join(os.path.expanduser('~'), 'data', 'OurData')
ANNOTATION_FOLDER = os.path.join(DATA_LOCATION, 'annotations')
IMAGE_FOLDER = os.path.join(DATA_LOCATION, 'images')
IMAGE_SET_CUTOFFS = {
    '001': '001700',
    '003': '001900',
    '005': '001500',
}

data = {}
files = ['labelled_data.pickle', 'labelled_data_2.pickle']
for file_name in files:
    with open(file_name, 'rb') as fh:
        data.update(pickle.load(fh))

IMG_WIDTH = 640
IMG_HEIGHT = 360

template = parse('template.xml').getroot()

def make_obj(xmin_v, ymin_v, xmax_v, ymax_v):
    obj = Element('object')
    name = SubElement(obj, 'name')
    name.text = 'trunk'
    box = SubElement(obj, 'bndbox')
    xmin = SubElement(box, 'xmin')
    xmin.text = str(xmin_v)

    xmax = SubElement(box, 'xmax')
    xmax.text = str(xmax_v)

    ymin = SubElement(box, 'ymin')
    ymin.text = str(ymin_v)

    ymax = SubElement(box, 'ymax')
    ymax.text = str(ymax_v)

    return obj

def get_boxes(file_name):
    labels = data[file_name]
    truths = []
    for label in labels:
        x, y, angle, width = label
        angle -= np.pi / 2

        corner = np.array([x, y])
        up_vec = np.array([np.cos(angle), np.sin(angle)]) * width
        perp_vec = np.array([-up_vec[1], up_vec[0]])

        center = corner + (up_vec + perp_vec) / 2

        min_x = int(center[0] - width)
        max_x = int(center[0] + width)
        min_y = int(center[1] - width * 2.5)
        max_y = int(center[1] + width * 0.5)

        truths.append([min_x, max_x, min_y, max_y])

    return np.array(truths).reshape((-1, 4))

for file_name in data:

    metadata = file_name.replace('.jpg', '').split('_')
    dataset = metadata[0]
    item = metadata[1]
    is_test = item > IMAGE_SET_CUTOFFS[dataset]

    boxes = get_boxes(file_name)
    cuts = np.random.uniform(0, MAX_CUT, size=(1 if is_test else AUGMENTATION_NUM+1, 4))
    cuts[0] = 0

    img = imageio.imread(os.path.join(RAW_DATA_FOLDER, file_name))

    for i, cut in enumerate(cuts):

        output_file = file_name.replace('.jpg', '_{}.jpg'.format(i)) if i > 0 else file_name
        if is_test:
            output_file = 'test_' + output_file

        current_template = deepcopy(template)
        name = SubElement(current_template, 'filename')
        name.text = output_file

        if np.any(cut):
            start_x = int(np.floor(IMG_WIDTH * cut[0]))
            end_x = IMG_WIDTH - int(np.floor(IMG_WIDTH * cut[1]))
            start_y = int(np.floor(IMG_HEIGHT * cut[2]))
            scale = IMG_WIDTH / (end_x - start_x)
            end_y = IMG_HEIGHT - int(np.floor((1-1/scale) * IMG_HEIGHT - start_y))

            origin_shift = np.array([start_x, start_x, start_y, start_y])

            boxes_to_export = ((boxes - origin_shift) * scale).astype(int)
            image_to_export = cv2.resize(img[start_y:end_y, start_x:end_x], dsize=(IMG_WIDTH, IMG_HEIGHT), interpolation=cv2.INTER_CUBIC)

        else:
            boxes_to_export = boxes
            image_to_export = img

        for min_x, max_x, min_y, max_y in boxes_to_export:
            if min_x < 0 or max_x >= IMG_WIDTH or min_y < 0 or max_y >= IMG_HEIGHT:
                continue
            obj = make_obj(min_x, min_y, max_x, max_y)
            current_template.append(obj)

        with open(os.path.join(ANNOTATION_FOLDER, output_file.replace('.jpg', '.xml')), 'w') as fh:
            fh.write(tostring(current_template).decode('utf8'))

        imageio.imwrite(os.path.join(IMAGE_FOLDER, output_file), image_to_export)



