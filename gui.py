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
        self.painter = QPainter(self.pixmap)
        self.image_label = QLabel()
        main_layout.addWidget(self.image_label)
        self.trunks = []

        self.pen = QPen(QtCore.Qt.red)
        self.pen.setWidth(3)
        self.painter.setPen(self.pen)

        self.image_label.setPixmap(self.pixmap)
        self.image_label.setObjectName("image")
        self.image_label.mousePressEvent = self.handle_mouse_click
        self.image_label.show()
        self.original_size_x = 0



        # UI-related stuff here
        options_ui = QHBoxLayout()
        button_1 = QPushButton('Test')
        button_1.clicked.connect(self.update_image)
        self.text_input = QLineEdit()
        options_ui.addWidget(button_1)
        options_ui.addWidget(self.text_input)

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
        self.painter = QPainter(self.pixmap)

        self.pen = QPen(QtCore.Qt.red)
        self.pen.setWidth(3)
        self.painter.setPen(self.pen)

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
            self.pen.setColor(QtCore.Qt.blue)
            self.painter.drawEllipse(click_x, click_y, 3, 3)
            self.image_label.setPixmap(self.pixmap)
            self.image_label.show()
            print('Drew circle')

        elif len(self.selections) == 2:

            self.pen.setColor(QtCore.Qt.red)
            x1, y1 = self.selections[0]
            x2, y2 = self.selections[1]
            x = min(x1, x2) / scale
            y = min(y1, y2) / scale
            w = abs(x2-x1) / scale
            h = abs(y2-y1) / scale

            self.painter.drawRect(x, y, w, h)
            self.selections = []
            self.image_label.setPixmap(self.pixmap)
            self.image_label.show()
            print('Drew rectangle')


if __name__ == '__main__':
    app = QApplication([])

    gui = DataLabeler()

    gui.show()

    app.exec_()