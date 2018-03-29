#!/usr/bin/python
# -*- coding: utf-8 -*-

from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt, QVariant, QSize


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
        self._iconSize = QSize(32, 32)
        if data:
            for row in data:
                colums = []
                for d in row:
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
              So, we need to define what to do with Renderable data
              (may be return a QIcon or QPixmap)
        :param qModelIndex:
        :param role:
        :return: QVariant
        """
        if not qModelIndex.isValid():
            return None
        if role == Qt.DecorationRole:
            return QVariant
        if role == Qt.DisplayRole:
            t = self._colProperties[qModelIndex.column()].getType()
            if t == 'Bool' or t == 'Image':
                return QVariant  # hide 'True' or 'False', path in Image type
            # we use Qt.UserRole for store data
            return QStandardItemModel.data(self, qModelIndex, Qt.UserRole)
        if role == Qt.CheckStateRole:
            if self._colProperties[qModelIndex.column()].getType() == 'Bool':
                return Qt.Checked \
                    if QStandardItemModel.data(self, qModelIndex,
                                               Qt.UserRole) else Qt.Unchecked
        if role == Qt.EditRole:
            return QStandardItemModel.data(self, qModelIndex, Qt.UserRole)

        if role == Qt.SizeHintRole:
            if self._colProperties[qModelIndex.column()].isRenderable():
                return self._iconSize

        return QStandardItemModel.data(self, qModelIndex, role)

    def setData(self, qModelIndex, value, role=None):
        """
        Set data in the model. We use Qt.UserRole for store data
        :param qModelIndex:
        :param value:
        :param role:
        :return:
        """
        #we use ICON_ROLE for store renderable data like icons (QPixmap)
        #not check Qt.ItemIsEditable flag
        if role == Qt.UserRole + 1:
            return QStandardItemModel.setData(self, qModelIndex, value, role)

        if not self.flags(qModelIndex) & Qt.ItemIsEditable:
            return False

        if role == Qt.CheckStateRole:  # use CheckStateRole for boolean data
            return QStandardItemModel.setData(self, qModelIndex,
                                              value == Qt.Checked,
                                              Qt.UserRole)
        if role == Qt.EditRole:
            return QStandardItemModel.setData(self, qModelIndex, value,
                                              Qt.UserRole)
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

    def getColumnProperties(self, column=-1):
        """
        Return column properties for the given column index
        :param column: column index, first column is 0.
                       column <0 return entire list
        :return: ColumnProperties.
        """
        if column < 0 or not self._colProperties:
            return self._colProperties

        if column < len(self._colProperties):
            return self._colProperties[column]

        return None

    def setIconSize(self, size):
        """
        Sets the size for renderable items
        :param size: QSize
        """
        self._iconSize = size