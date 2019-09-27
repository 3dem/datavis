#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys

from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QAction,
                             QLineEdit, QTreeView, QVBoxLayout, QHBoxLayout,
                             QToolButton, QMenu, QSpacerItem, QSizePolicy,
                             QTableWidget, QLabel)
from datavis.widgets import SpinSlider


# Connect to the valueChanged signal and print value
@pyqtSlot(int)
def onValueChanged(value):
    print("value: %s" % value)


app = QApplication(sys.argv)

win = QMainWindow()
win.resize(200, 200)

# Create a SpinSlider
spinSlider = SpinSlider(win,
                        text='Testing SpinSlider',
                        minValue=1, maxValue=100)

spinSlider.sigValueChanged.connect(onValueChanged)

win.setCentralWidget(spinSlider)
win.show()
win.setWindowTitle('SpinSlider Example')

sys.exit(app.exec_())
