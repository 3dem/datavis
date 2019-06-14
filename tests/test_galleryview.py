#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys

from PyQt5.QtWidgets import QApplication, QMainWindow

from emviz.core import ModelsFactory
from emviz.views import GalleryView

if len(sys.argv) > 1:
    imagePath = sys.argv[1]
else:
    testDataPath = os.environ.get("EM_TEST_DATA", None)

    if testDataPath is None:
        raise Exception("Path not available to display ImageView. \n"
                        "Either provide an input path or set the "
                        "variable environment EM_TEST_DATA")

    imagePath = os.path.join(testDataPath,
                             "relion_tutorial", "import",
                             "classify2d", "extra",
                             "relion_it015_classes.mrcs")


def getPreferedBounds(width=None, height=None):
    size = QApplication.desktop().size()
    p = 0.8
    (w, h) = (int(p * size.width()), int(p * size.height()))
    width = width or w
    height = height or h
    w = min(width, w)
    h = min(height, h)
    return (size.width() - w) / 2, (size.height() - h) / 2, w, h


app = QApplication(sys.argv)

model = ModelsFactory.createStackModel(imagePath)

galleryView = GalleryView(parent=None, model=model)
width, height = galleryView.getPreferedSize()
# Create window with ImageView widget
win = QMainWindow()
win.setCentralWidget(galleryView)
win.show()
win.setWindowTitle('GalleryView Example')
x, y, width, height = getPreferedBounds(width, height)
win.setGeometry(x, y, width, height)

sys.exit(app.exec_())

