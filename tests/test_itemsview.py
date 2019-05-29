#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
from PyQt5.QtWidgets import QApplication

from emviz.views import TableModel, ItemsView, TablePageItemModel
from emviz.core import ImageManager

import em


app = QApplication(sys.argv)
testDataPath = os.environ.get("EM_TEST_DATA", None)

if testDataPath is not None:
    path = os.path.join(testDataPath, "relion_tutorial", "import", "classify2d",
                            "extra", "relion_it015_classes.mrcs")

    table = em.Table([em.Table.Column(0, "index", em.typeInt32, "Image index"),
                      em.Table.Column(1, "path", em.typeString, "Image path")])

    tableViewConfig = TableModel.createStackConfig()
    row = table.createRow()
    n = ImageManager.getDim(path).n
    for i in range(1, n+1):
        row['index'] = i
        row['path'] = '%d@%s' % (i, path)
        table.addRow(row)
    itemsView = ItemsView()
    itemsView.setModelColumn(1)
    itemsView.setModel(TablePageItemModel(table, parent=itemsView,
                                          title="Stack",
                                          tableViewConfig=tableViewConfig))
    itemsView.show()

sys.exit(app.exec_())
