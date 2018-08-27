#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow

from emqt5.views import SlicesView


app = QApplication(sys.argv)
testDataPath = os.environ.get("EM_TEST_DATA", None)

if testDataPath is not None:
    path = os.path.join(testDataPath, "relion_tutorial", "import", "classify2d",
                        "extra", "relion_it025_classes.mrcs")
path = '/media/pedro/Data/Work/Project/Repo/test-data/relion_it025_classes.mrcs'
slicesView = SlicesView(None, tool_bar='off', axis='off', view_name='Top View',
                        volume_axis='h', index=0, back_color='#BBAAFF',
                        path=path)

# Create window with ImageView widget
win = QMainWindow()
win.resize(800, 800)
win.setCentralWidget(slicesView)
win.show()
win.setWindowTitle('Slices Example')

sys.exit(app.exec_())
