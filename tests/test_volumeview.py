#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow

from emviz.views import VolumeView


app = QApplication(sys.argv)
testDataPath = os.environ.get("EM_TEST_DATA", None)

if testDataPath is not None:
    path = os.path.join(testDataPath, "relion_tutorial", "import", "classify2d",
                        "extra", "relion_it025_classes.mrcs")
path = '/media/pedro/Data/Work/Project/Repo/test-data/t20s_relion_class001.vol'
volumeView = VolumeView(None, tool_bar='off', axis='off', path=path)

# Create window with ImageView widget
win = QMainWindow()
win.resize(800, 800)
win.setCentralWidget(volumeView)
win.show()
win.setWindowTitle('Volume View Example')

sys.exit(app.exec_())
