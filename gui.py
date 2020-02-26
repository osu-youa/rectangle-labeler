#!/usr/bin/env python3

import os
import PyQt5.QtCore as QtCore
from PyQt5.QtWidgets import QMainWindow, QCheckBox, QGroupBox, QGridLayout, QVBoxLayout, QHBoxLayout, QPushButton

from PyQt5.QtWidgets import QApplication, QHBoxLayout, QWidget, QLabel, QLineEdit
from PyQt5.QtGui import QPainter, QPixmap, QPen
import numpy as np
import pickle
from _collections import defaultdict
import random

class Trunk(object):
    def __init__(self, o_x, o_y, width, angle):
        self.o_x = o_x
        self.o_y = o_y
        self.width = width
        self.angle = angle


# https://stackoverflow.com/questions/53420826/overlay-two-pixmaps-with-alpha-value-using-qpainter
def overlay_pixmap(base, overlay):
    # Assumes both have same size
    rez = QPixmap(base.size())
    rez.fill(QtCore.Qt.transparent)
    painter = QPainter(rez)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.drawPixmap(QtCore.QPoint(), base)
    painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
    painter.drawPixmap(rez.rect(), overlay, overlay.rect())
    painter.end()

    return rez


class DataLabeler(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.setWindowTitle('Mega cool interface')

        # State variables
        self.selections = []

        # The layout of the interface
        widget = QWidget()
        self.setCentralWidget(widget)

        main_layout = QVBoxLayout()
        widget.setLayout(main_layout)

        # Drawing-related stuff here
        self.pixmap = QPixmap()
        self.orig_pixmap = QPixMap()
        self.image_label = QLabel()
        main_layout.addWidget(self.image_label)
        self.trunks = []

        self.overlay = None
        self.overlay_painter = None

        self.image_label.setPixmap(self.pixmap)
        self.image_label.setObjectName("image")
        self.image_label.mousePressEvent = self.handle_mouse_click
        self.image_label.mouseMoveEvent = self.handle_mouse_move
        self.image_label.show()
        self.original_size_x = 0



        # UI-related stuff here
        options_ui = QHBoxLayout()
        # button_1 = QPushButton('Load')
        # button_1.clicked.connect(self.update_image)

        button_2 = QPushButton('Clear')
        button_2.clicked.connect(self.clear_overlay)

        # self.text_input = QLineEdit()
        # options_ui.addWidget(button_1)
        options_ui.addWidget(button_2)

        main_layout.addLayout(options_ui)

        # Data initialization
        self.clicks = 0
        try:
            with open('labelled_data.pickle', 'rb') as fh:
                self.current_data = pickle.load(fh)
            self.previous = sorted(self.current_data.keys())
            self.current = len(self.previous)


        except FileNotFoundError:
            self.current_data = defaultdict(list)
            self.current = 0
            self.previous = []

        all_files = os.listdir('images')
        if not all_files:
            raise ValueError('Please put some images into the images folder first!')
        self.remaining = list(set(all_files) - set(self.previous))
        random.shuffle(self.remaining)
        if not self.remaining:
            self.current = len(self.current_data) - 1

        self.update_image()

    def keyPressEvent(self,event):
        pressed = event.key()
        if pressed == QtCore.Qt.Key_D and len(self.selections) == 0:

            if self.current > 0:
                self.current -= 1
                self.update_image()
            else:
                print('This is the first image!')

        elif pressed == QtCore.Qt.Key_F and len(self.selections) == 0:
            self.current += 1
            if self.remaining:
                self.update_image()
            else:
                if self.current >= len(self.previous):
                    print('All out of images to load!')
                    self.save()
                    self.current -= 1
                else:
                    self.update_image()
        elif pressed == QtCore.Qt.Key_E:
            self.clear_overlay()

        elif pressed == QtCore.Qt.Key_S:
            self.save()

    def update_image(self):

        if self.current >= len(self.previous):

            self.clicks = (self.clicks + 1) % 5
            if not self.clicks:
                self.save()

            # Pick a random image to load
            image_name = self.remaining.pop()
            self.previous.append(image_name)
            self.current_data[image_name] = []
        else:
            image_name = self.previous[self.current]

        if self.overlay_painter is not None:
            self.overlay_painter.end()

        self.pixmap = QPixmap(os.path.join('images', image_name))
        self.original_size_x = self.pixmap.width()
        self.pixmap = self.pixmap.scaled(1280, 800, QtCore.Qt.KeepAspectRatio)
        self.orig_pixmap = self.pixmap.copy()

        self.overlay = QPixmap(self.pixmap.size())
        self.overlay.fill(QtCore.Qt.transparent)

        self.overlay_painter = QPainter(self.overlay)
        pen = QPen(QtCore.Qt.blue)
        pen.setWidth(3)
        self.overlay_painter.setPen(pen)

        self.image_label.setPixmap(self.pixmap)
        self.image_label.show()
        print('New image {} loaded!'.format(image_name))

        self.selections = []


    def handle_mouse_click(self, event):

        pos = event.pos()
        click_x, click_y = pos.x(), pos.y()
        scale = self.original_size_x / self.pixmap.width()
        img_x, img_y = click_x * scale, click_y * scale

        self.selections.append((img_x, img_y))

        if len(self.selections) == 1:
            self.image_label.setMouseTracking(True)
        if len(self.selections) == 3:
            self.image_label.setMouseTracking(False)
            # Process the clicks, add them to the master data list
            self.current_data[self.previous[self.current]] = 3
            print(self.current_data)

            self.selections = []

    def handle_mouse_move(self, event):
        pos = event.pos()
        click_x, click_y = pos.x(), pos.y()
        scale = self.original_size_x / self.pixmap.width()
        # img_x, img_y = click_x * scale, click_y * scale

        if len(self.selections) == 1:
            # Draw line
            last_x, last_y = self.selections[0]
            last_x /= scale
            last_y /= scale

            last = np.array([last_x, last_y])

            self.overlay.fill(QtCore.Qt.transparent)
            self.overlay_painter.drawLine(last_x, last_y, click_x, click_y)

        if len(self.selections) == 2:
            last_x, last_y = self.selections[0]
            last_x /= scale
            last_y /= scale

            last = np.array([last_x, last_y])

            second_x, second_y = self.selections[1]
            second_x /= scale
            second_y /= scale

            second = np.array([second_x, second_y])
            diff = second - last
            diff_perp = np.array([-diff[1], diff[0]])

            # Solve for how long vec should be
            vec_scale = (click_x - second_x) / diff_perp[0]
            corner_top = second + vec_scale * diff_perp
            corner_bottom = last + vec_scale * diff_perp
            self.overlay.fill(QtCore.Qt.transparent)
            self.overlay_painter.drawLine(second[0], second[1], last[0], last[1])
            self.overlay_painter.drawLine(second[0], second[1], corner_top[0], corner_top[1])
            self.overlay_painter.drawLine(last[0], last[1], corner_bottom[0], corner_bottom[1])
            self.overlay_painter.drawLine(corner_top[0], corner_top[1], corner_bottom[0], corner_bottom[1])

        merged = overlay_pixmap(self.pixmap, self.overlay)
        self.image_label.setPixmap(merged)

    def update_pixmap_with_markers(self):
        data = self.current_data[self.current]
        # Take orig pixmap, create overlay with all shapes
        # Set as the displayed pixmap


    def clear_overlay(self):
        self.image_label.setMouseTracking(False)
        self.overlay.fill(QtCore.Qt.transparent)
        self.selections = []
        self.image_label.setPixmap(self.orig_pixmap)
        self.current_data[self.current] = []

    def save(self):
        with open('labelled_data.pickle', 'wb') as fh:
            pickle.dump(self.current_data, fh)
        print('Saved data!')


if __name__ == '__main__':
    app = QApplication([])

    gui = DataLabeler()

    gui.show()

    app.exec_()