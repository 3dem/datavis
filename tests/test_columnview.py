#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
from PyQt5.QtWidgets import QApplication

from emviz.models import TableModel, TYPE_INT, TYPE_STRING
from emviz.views import ColumnsView, TablePageItemModel
from emviz.core import ImageManager, EmTableModel

import em


app = QApplication(sys.argv)
testDataPath = os.environ.get("EM_TEST_DATA", None)

if testDataPath is not None:
    path = os.path.join(testDataPath, "relion_tutorial", "gold",
                        "relion_it020_data.star")

    tio = em.TableIO()
    tio.open(path)
    table = em.Table()
    tio.read(tio.getTableNames()[0], table)
    tableModel = EmTableModel(table)

    columnView = ColumnsView(model=tableModel)
    columnView.setRowHeight(100)
    columnView.show()

sys.exit(app.exec_())
