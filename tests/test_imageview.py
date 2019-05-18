#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow

from emqt5.views import ImageView
from emqt5.utils import ImageManager

import numpy as np


app = QApplication(sys.argv)

# Test script that loads an image in a ImageView
# The image path can be passed or it will be loaded from the test data

if len(sys.argv) > 1:
    imgPath = sys.argv[1]
else:
    testDataPath = os.environ.get("EM_TEST_DATA", None)

    if testDataPath is None:
        raise Exception("Path not available to display ImageView. \n"
                        "Either provide an input path or set the "
                        "variable environment EM_TEST_DATA")

    imgPath = os.path.join(testDataPath, "relion_tutorial", "import", "classify2d",
                        "extra", "relion_it025_classes.mrcs")

imageView = ImageView(None, border_color='#FFAA33')
img = ImageManager.readImage(imgPath, 1)
data = np.array(img, copy=False)
imageView.setImage(data)
desc = "<html><head/><body><p><span style=\" color:#0055ff;\">Dimension: " \
       "</span><span style=\" color:#000000;\">(x,y,z)</span></p></body>" \
       "</html>"
imageView.setImageInfo(text=desc)

# Create window with ImageView widget
win = QMainWindow()
win.resize(800, 800)
win.setCentralWidget(imageView)
win.show()
win.setWindowTitle('Image Operation Example')

sys.exit(app.exec_())
