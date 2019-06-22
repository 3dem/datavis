#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys

from PyQt5.QtWidgets import QApplication, QMainWindow

from emviz.core import ModelsFactory
from emviz.views import ItemsView

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


app = QApplication(sys.argv)
model = ModelsFactory.createStackModel(imagePath)

itemsView = ItemsView(parent=None, model=model, selectionMode=ItemsView.MULTI_SELECTION)
# Create window with ItemsView widget
win = QMainWindow()
win.setCentralWidget(itemsView)
win.show()
win.setWindowTitle('ItemsView Example')

sys.exit(app.exec_())
