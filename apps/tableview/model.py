#!/usr/bin/python
# -*- coding: utf-8 -*-

from PyQt5.QtGui import QStandardItemModel, QStandardItem, QPixmap
from PyQt5.QtCore import Qt, QVariant


class TableDataModel(QStandardItemModel):
    """
    Model for test
    """
    def __init__(self, data=None, parent=None):
        QStandardItemModel.__init__(self, parent)
        for i, d in enumerate(data):
            col_1 = QStandardItem(d["name"])
            col_2 = QStandardItem(d["image"])
            col_3 = QStandardItem(d["ext"])
            self.setItem(i, 0, col_1)
            self.setItem(i, 1, col_2)
            self.setItem(i, 2, col_3)
        self.setHorizontalHeaderLabels(["Name", "Image", "Ext"])

    def data(self, qModelIndex, role=None):
        data = self.itemData(qModelIndex)
        if role == Qt.DisplayRole:
            if qModelIndex.column() == 1:  # Image column, don't return data
                return QVariant()
            return data[0]
        if role == Qt.DecorationRole:
            return QPixmap(data[0]).scaledToHeight(25)
        return QVariant()
