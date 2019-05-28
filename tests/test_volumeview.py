#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import numpy as np

from PyQt5.QtWidgets import QApplication, QMainWindow

import em
from emviz.models import AXIS_X, AXIS_Y, AXIS_Z, SlicesModel
from emviz.views import VolumeView


if len(sys.argv) > 1:
    imgPath = sys.argv[1]
else:
    testDataPath = os.environ.get("EM_TEST_DATA", None)

    if testDataPath is None:
        raise Exception("Path not available to display ImageView. \n"
                        "Either provide an input path or set the "
                        "variable environment EM_TEST_DATA")

    imgPath = os.path.join(testDataPath, "xmipp_tutorial", "volumes",
                           "BPV_scale_filtered_windowed_110.vol")

app = QApplication(sys.argv)


imgio = em.ImageIO()
imgio.open(imgPath, em.File.READ_ONLY)
print("dim: ", imgio.getDim())
dim = imgio.getDim()
image = em.Image()

if dim.z > 1:
    imgio.read(1, image)
    data = np.array(image, copy=True)
else:
    raise Exception('Input image should be a volume, current dim: %s' % dim)

imgio.close()


class AxisSlicesModel(SlicesModel):
    """ Example class about how to implement an SlicesModel for different axis.
    """
    def __init__(self, axis, data):
        SlicesModel.__init__(self, data)
        self._axis = axis

    def getData(self, i):
        i -= 1
        if self._axis == AXIS_Z:
            return self._data[i]
        elif self._axis == AXIS_Y:
            return self._data[:, i, :]
        elif self._axis == AXIS_X:
            return self._data[:, :, i]

    def getDim(self):
        if self._axis == AXIS_Z:
            return self._dim
        elif self._axis == AXIS_Y:
            return self._dim[0], self._dim[2], self._dim[1]
        elif self._axis == AXIS_X:
            return self._dim[1], self._dim[2], self._dim[0]


v = VolumeView(None,
               slicesKwargs={
                   AXIS_X: {'model': AxisSlicesModel(AXIS_X, data)},
                   AXIS_Y: {'model': AxisSlicesModel(AXIS_Y, data)},
                   AXIS_Z: {'model': AxisSlicesModel(AXIS_Z, data)}
               })


# Create window with ImageView widget
win = QMainWindow()
win.resize(800, 800)
win.setCentralWidget(v)
win.show()
win.setWindowTitle('Volume View Example')

sys.exit(app.exec_())
