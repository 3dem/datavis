#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
from PyQt5.QtWidgets import QApplication

from emviz.models import TableViewConfig
from emviz.views import ColumnsView, TableDataModel
from emviz.core import ImageManager

import em


app = QApplication(sys.argv)
testDataPath = os.environ.get("EM_TEST_DATA", None)

if testDataPath is not None:
    path = os.path.join(testDataPath, "relion_tutorial", "import", "classify2d",
                            "extra", "relion_it015_classes.mrcs")

    table = em.Table([em.Table.Column(0, "index", em.typeInt32, "Image index"),
                      em.Table.Column(1, "path", em.typeString, "Image path")])

    tableViewConfig = TableViewConfig()
    tableViewConfig.addColumnConfig(name='index',
                                    dataType=TableViewConfig.TYPE_INT,
                                    label='Index', editable=False, visible=True)

    tableViewConfig.addColumnConfig(name='path',
                                    dataType=TableViewConfig.TYPE_STRING,
                                    label='Path', renderable=True,
                                    editable=False, visible=True)

    row = table.createRow()
    n = ImageManager.getDim(path).n
    for i in range(1, n+1):
        row['index'] = i
        row['path'] = '%d@%s' % (i, path)
        table.addRow(row)
    columnView = ColumnsView()
    columnView.setRowHeight(100)
    columnView.setModel(TableDataModel(table, parent=columnView,
                                       title="Stack",
                                       tableViewConfig=tableViewConfig))
    columnView.show()

sys.exit(app.exec_())
