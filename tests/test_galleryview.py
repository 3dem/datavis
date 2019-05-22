#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
from PyQt5.QtWidgets import QApplication

from emqt5.models import TableViewConfig
from emqt5.views import TableDataModel, GalleryView
from emqt5.utils import ImageManager

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
    galleryView = GalleryView()
    galleryView.setIconSize((100, 100))
    galleryView.setModel(TableDataModel(table, parent=galleryView,
                                        title="Stack",
                                        tableViewConfig=tableViewConfig))
    galleryView.setModelColumn(1)
    galleryView.show()

sys.exit(app.exec_())
