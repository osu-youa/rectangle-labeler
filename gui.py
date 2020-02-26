#!/usr/bin/env python3

import os
import PyQt5.QtCore as QtCore
from PyQt5.QtWidgets import QMainWindow, QCheckBox, QGroupBox, QGridLayout, QVBoxLayout, QHBoxLayout, QPushButton

from PyQt5.QtWidgets import QApplication, QHBoxLayout, QWidget, QLabel, QLineEdit
from PyQt5.QtGui import QPainter, QPixmap, QPen
import numpy as np

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
        button_1 = QPushButton('Load')
        button_1.clicked.connect(self.update_image)

        button_2 = QPushButton('Clear')
        button_2.clicked.connect(self.clear_overlay)

        self.text_input = QLineEdit()
        options_ui.addWidget(button_1)
        options_ui.addWidget(self.text_input)
        options_ui.addWidget(button_2)

        main_layout.addLayout(options_ui)

        # Temp
        self.text_input.setText('test/farm-environment.jpg')
        self.update_image()


    def update_image(self):
        path = self.text_input.text()
        if not os.path.exists(path):
            print('Path does not exist!')
            return
        self.pixmap = QPixmap(path)
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
        print('New image {} loaded!'.format(path))

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


    def clear_overlay(self):
        self.image_label.setMouseTracking(False)
        self.overlay.fill(QtCore.Qt.transparent)
        self.selections = []
        self.image_label.setPixmap(self.orig_pixmap)


if __name__ == '__main__':
    app = QApplication([])

    gui = DataLabeler()

    gui.show()

    app.exec_()