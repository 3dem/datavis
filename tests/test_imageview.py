#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow

from emqt5.views.data_view import GalleryView, TableViewConfig
from emqt5.views.model import TableDataModel
from emqt5.utils import EmImage

import pyqtgraph as pg
import numpy as np


app = QApplication(sys.argv)
testDataPath = os.environ.get("EM_TEST_DATA", None)

if testDataPath is not None:
    path = os.path.join(testDataPath, "relion_tutorial", "import", "classify2d",
                        "extra", "relion_it025_classes.mrcs")
    image = EmImage.load(path)
    data = np.array(image, copy=False)
    imageView = pg.ImageView()

    ## Create window with ImageView widget
    win = QMainWindow()
    win.resize(800, 800)
    win.setCentralWidget(imageView)
    win.show()
    win.setWindowTitle('Image Operation Example')
    imageView.setImage(data)

sys.exit(app.exec_())
