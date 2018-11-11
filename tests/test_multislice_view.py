#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow

from emqt5.views import MultiSliceView


app = QApplication(sys.argv)
testDataPath = os.environ.get("EM_TEST_DATA", None)

if testDataPath is not None:
    path = os.path.join(testDataPath, "relion_tutorial", "import", "classify2d",
                        "extra", "relion_it025_classes.mrcs")
path = '/media/pedro/Data/Work/Project/Repo/test-data/t20s_relion_class001.vol'
slicesView = MultiSliceView(None, tool_bar='off', axis='off')
slicesView.loadPath(path)

# Create window with ImageView widget
win = QMainWindow()
win.resize(800, 800)
win.setCentralWidget(slicesView)
win.show()
win.setWindowTitle('Slices Example')

sys.exit(app.exec_())
