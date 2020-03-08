import pickle
import numpy as np
from xml.etree.ElementTree import Element, SubElement, ElementTree, tostring, parse
from copy import deepcopy
import os

with open('labelled_data.pickle', 'rb') as fh:
    data = pickle.load(fh)

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


for file_name in data:
    labels = data[file_name]

    current_template = deepcopy(template)
    name = SubElement(current_template, 'filename')
    name.text = file_name

    for label in labels:
        x, y, width, angle = label
        angle -= np.pi/2

        corner = np.array([x, y])
        up_vec = np.array([np.cos(angle), np.sin(angle)]) * width
        perp_vec = np.array([-up_vec[1], up_vec[0]])

        center = corner + (up_vec + perp_vec) / 2

        min_x = int(center[0] - width)
        max_x = int(center[0] + width)
        min_y = int(center[1] - width * 2.5)
        max_y = int(center[1] + width * 0.5)

        if min_x < 0 or min_y < 0 or max_x >= IMG_WIDTH or max_y >= IMG_HEIGHT:
            continue

        obj = make_obj(min_x, min_y, max_x, max_y)
        current_template.append(obj)

    with open(os.path.join('annotations', file_name.split('.')[0] + '.xml'), 'w') as fh:
        fh.write(tostring(current_template).decode('utf8'))


