#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
from PIL import Image
from PyQt5.QtWidgets import QApplication, QMainWindow

from emqt5.views import ImageView
from emqt5.utils import EmImage

import numpy as np


app = QApplication(sys.argv)
testDataPath = os.environ.get("EM_TEST_DATA", None)

if testDataPath is not None:
    path = os.path.join(testDataPath, "relion_tutorial", "import", "classify2d",
                        "extra", "relion_it025_classes.mrcs")

    imageView = ImageView(None, border_color='#FFAA33')
    # standard image
    #image = Image.open('/media/pedro/Data/1.jpg')
    #data = np.array(image)
    # EM-Image
    img = EmImage.load(path, 1)
    data = np.array(img, copy=False)
    imageView.setImage(data)
    desc = "<html><head/><body><p><span style=\" color:#0055ff;\">Dimension: " \
           "</span><span style=\" color:#000000;\">(x,y,z)</span></p></body>" \
           "</html>"
    imageView.setImageDescription(desc)

    # Create window with ImageView widget
    win = QMainWindow()
    win.resize(800, 800)
    win.setCentralWidget(imageView)
    win.show()
    win.setWindowTitle('Image Operation Example')

sys.exit(app.exec_())
