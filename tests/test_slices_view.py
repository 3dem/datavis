#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import numpy as np

from PyQt5.QtWidgets import QApplication, QMainWindow

import em
from emviz.core import ImageManager
from emviz.models import SlicesModel
from emviz.views import SlicesView


if len(sys.argv) > 1:
    imgPath = sys.argv[1]
else:
    testDataPath = os.environ.get("EM_TEST_DATA", None)

    if testDataPath is None:
        raise Exception("Path not available to display ImageView. \n"
                        "Either provide an input path or set the "
                        "variable environment EM_TEST_DATA")

    imgPath = os.path.join(testDataPath, "relion_tutorial", "import",
                           "classify2d", "extra", "relion_it015_classes.mrcs")

app = QApplication(sys.argv)


class EmSlicesModel(SlicesModel):
    """ Example class about how to implement an SlicesModel
    that can be used by the SlicesView
    """
    def __init__(self, imgPath):
        SlicesModel.__init__(self)
        imgio = em.ImageIO()
        imgio.open(imgPath, em.File.READ_ONLY)
        print("dim: ", imgio.getDim())
        dim = imgio.getDim()
        image = em.Image()

        if dim.z > 1:
            imgio.read(1, image)
            self._data = np.array(image, copy=False)
            self._dim = dim.x, dim.y, dim.z
            self.initialSlice = dim.z / 2
            self.text = 'Volume, Z slice: '
        elif dim.n > 1:
            print("Loading stack in memory, only first 100 images")
            n = min(100, dim.n)
            self._data = []
            self._dim = dim.x, dim.y, n
            self.initialSlice = 1
            self.text = 'Stack, image number:'
            for i in range(1, n+1):
                imgio.read(i, image)
                self._data.append(np.array(image, copy=True))
        imgio.close()


slicesModel = EmSlicesModel(imgPath)


slicesView = SlicesView(None, slicesModel, text=slicesModel.text,
                        currentValue=slicesModel.initialSlice)

# Create window with ImageView widget
win = QMainWindow()
win.setCentralWidget(slicesView)
win.show()
win.setWindowTitle('Slices Example')

sys.exit(app.exec_())
