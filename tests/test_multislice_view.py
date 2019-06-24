#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import numpy as np

from PyQt5.QtWidgets import QApplication, QMainWindow

import em
from emviz.models import AXIS_X, AXIS_Y, AXIS_Z, SlicesModel, VolumeModel
from emviz.views import MultiSliceView
from emviz.core import ModelsFactory


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

volModel = ModelsFactory.createVolumeModel(imgPath)
msv = MultiSliceView(None,
                     {axis: {'model': volModel.getSlicesModel(axis)}
                      for axis in [AXIS_X, AXIS_Y, AXIS_Z]})
# Create window with ImageView widget
win = QMainWindow()
win.setCentralWidget(msv)
win.show()
win.setWindowTitle('Multi-Slices Example')

sys.exit(app.exec_())
