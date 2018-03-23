#!/usr/bin/python
# -*- coding: utf-8 -*-

from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt, QVariant


class TableDataModel(QStandardItemModel):
    """
    Model for test
    """
    def __init__(self, parent=None, data=[], columnProperties=None):
        """
        Constructs an TableDataModel with the given parent.
        :param parent: The parent
        :param data: table data. Example: [[2,3,4], [6,5,7], [4,5,6]].
        :param columnProperties: The properties for each column
        """
        QStandardItemModel.__init__(self, parent)
        self._colProperties = columnProperties

        for row in data:
            colums = []
            for i, d in enumerate(row):
                item = QStandardItem()
                item.setData(d, Qt.UserRole)  # Store the data

                colums.append(item)

            self.appendRow(colums)

        for i, prop in enumerate(columnProperties):
            self.setHorizontalHeaderItem(i, QStandardItem(prop.getLabel()))

    def data(self, qModelIndex, role=Qt.UserRole):
        """
        This is an reimplemented function from QStandardItemModel.
        Reimplemented to hide the 'True' text in columns with boolean value.
        We use Qt.UserRole for store table data.
        TODO: Widgets with TableDataModel needs Qt.DisplayRole value to show
              So, we need to define what todo with Renderable data
              (may be return a QIcon or QPixmap)
        :param qModelIndex:
        :param role:
        :return: QVariant
        """
        if not qModelIndex.isValid():
            return None
        item = self.itemFromIndex(qModelIndex)

        if role == Qt.DisplayRole:
            if self._colProperties[qModelIndex.column()].getType() == 'Bool':
                return QVariant  # hide 'True' or 'False' text

            return item.data(Qt.UserRole)  # we use Qt.UserRole for store data
        if role == Qt.CheckStateRole:
            if self._colProperties[qModelIndex.column()].getType() == 'Bool':
                return Qt.Checked if item.data(Qt.UserRole) else Qt.Unchecked

        return QStandardItemModel.data(self, qModelIndex, role)

    def setData(self, qModelIndex, value, role=None):
        """
        Set data in the model. We use Qt.UserRole for store data
        :param qModelIndex:
        :param value:
        :param role:
        :return:
        """
        if not self.flags(qModelIndex) & Qt.ItemIsEditable:
            return False

        if role == Qt.CheckStateRole:
            return QStandardItemModel.setData(self, qModelIndex,
                                                  value, Qt.UserRole)

        if role == Qt.EditRole:
            QStandardItemModel.setData(self, qModelIndex,
                                       value, Qt.UserRole)

        return QStandardItemModel.setData(self, qModelIndex, value, role)

    def flags(self, qModelIndex):
        """
        Reimplemented from QStandardItemModel
        :param qModelIndex: index in the model
        :return: The flags for the item. See :  Qt.ItemDataRole
        """
        fl = Qt.NoItemFlags
        col = qModelIndex.column()
        if qModelIndex.isValid():
            if self._colProperties[col].isEditable():
                fl |= Qt.ItemIsEditable
            if self._colProperties[col].getType() == 'Bool':
                fl |= Qt.ItemIsUserCheckable

        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | fl
