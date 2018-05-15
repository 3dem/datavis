#!/usr/bin/python
# -*- coding: utf-8 -*-

from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QVariant, QSize, QAbstractItemModel, QModelIndex


class TableDataModel(QAbstractItemModel):
    """
    Model for EM Data
    """
    def __init__(self, parent=None, emTable=None, columnProperties=None,
                 itemsXPage=10):
        """
        Constructs an DataModel with the given parent.
        :param parent: The parent
        :param data: table data. Example: [[2,3,4], [6,5,7], [4,5,6]].
        :param columnProperties: The properties for each column
        """
        QAbstractItemModel.__init__(self, parent)
        self._colProperties = columnProperties
        self._iconSize = QSize(32, 32)
        self._emTable = emTable
        self._itemsXPage = itemsXPage
        self._currentPage = 0
        self._pageCount = 0
        self._items = []
        self.__setupModel__()

    def data(self, qModelIndex, role=Qt.DisplayRole):
        """
        This is an reimplemented function from QAbstractItemModel.
        Reimplemented to hide the 'True' text in columns with boolean value.
        We use Qt.UserRole for store table data.
        TODO: Widgets with DataModel needs Qt.DisplayRole value to show
              So, we need to define what to do with Renderable data
              (may be return a QIcon or QPixmap)
        """
        if not qModelIndex.isValid():
            return None
        row = qModelIndex.row() + self._currentPage * self._itemsXPage
        col = qModelIndex.column()

        if role == Qt.DecorationRole:
            return QVariant()
        if role == Qt.DisplayRole:
            t = self._colProperties[col].getType() \
                if self._colProperties else ""
            if t == 'Bool' or t == 'Image':
                return QVariant()  # hide 'True' or 'False', path in Image type
            # we use Qt.UserRole for store data
            return QVariant(self.getTableData(row, col))
        if role == Qt.CheckStateRole:
            if self._colProperties and \
                    self._colProperties[col].getType() == 'Bool':
                return Qt.Checked \
                    if self.getTableData(row, col) else Qt.Unchecked
            return QVariant()

        if role == Qt.EditRole:
            return QVariant(self.getTableData(row, col))

        if role == Qt.SizeHintRole:
            if self._colProperties and \
                    self._colProperties[col].isRenderable():
                return self._iconSize

        if role == Qt.TextAlignmentRole:
            return Qt.AlignVCenter

        return QVariant(self.getTableData(row, col))

    def columnCount(self, index=QModelIndex()):
        """
        Reimplemented from QAbstractItemModel.
        Return the column count
        """
        return len(self._colProperties) if self._colProperties else 0

    def rowCount(self, index=QModelIndex()):
        """
        Reimplemented from QAbstractItemModel.
        Return the items per page.
        """
        return self._itemsXPage if self._itemsXPage <= self._emTable.getSize() \
            else self._emTable.getSize()

    def index(self, row, column, parent=QModelIndex()):
        """
        Reimplemented from QAbstractItemModel.
        Returns the index of the item in the model specified by the given row,
        column and parent index.
        """
        return self.createIndex(row, column)

    def parent(self, index):
        """
        Reimplemented from QAbstractItemModel.
        Returns the parent of the model item with the given index.
        If the item has no parent, an invalid QModelIndex is returned.
        """
        return QModelIndex()

    def totalRowCount(self):
        """
        Return the row count for the entire model
        """
        if self._emTable:
            return self._emTable.getSize()

        return 0

    def setData(self, qModelIndex, value, role=Qt.EditRole):
        """
        Reimplemented from QAbstractItemModel
        """
        if not qModelIndex.isValid():
            return False

        if self.flags(qModelIndex) & Qt.ItemIsEditable:
            return self.setTableData(qModelIndex.row(),
                                     qModelIndex.column(),
                                     value)

        return False

    def setTableData(self, row, column, value):
        """
        Set table data
        """
        if self.flags(self.createIndex(row, column)) & Qt.ItemIsEditable:
            tableRow = self._emTable[row]
            tableColumn = self._emTable.getColumnByIndex(column)
            tableRow[tableColumn.getName()] = value
            return True

        return False

    def getTableData(self, row, col):
        """
        Return the data for specified column and row
        """
        if self._emTable and row in range(0, self._emTable.getSize())\
            and col in range(0, self._emTable.getColumnsSize()):
            emRow = self._emTable[row]
            emCol = self._emTable.getColumnByIndex(col)
            t = self._colProperties[col].getType()

            if t == 'Str' or t == 'Image':
                return emRow[emCol.getId()].toString()
            elif t == 'Bool':
                return bool(int(emRow[emCol.getId()]))
            elif t == 'Int':
                return int(emRow[emCol.getId()])

            return emRow[emCol.getId()]

        return None

    def loadPage(self, pageIndex=-1):
        """
        Load the page specified by pageIndex. If pageIndex is not within
        the page range then load the current page.
        """
        self.beginResetModel()
        if pageIndex in range(0, self._pageCount):
            self._currentPage = pageIndex
        self.endResetModel()

    def prevPage(self):
        self._currentPage = self._currentPage - 1 \
            if self._currentPage > 0 else 0
        self.loadPage()

    def nextPage(self):
        self._currentPage = self._currentPage + 1 \
            if (self._currentPage + 1) * self._itemsXPage <= len(self._emTable) \
            else self._currentPage
        self.loadPage()

    def headerData(self, column, orientation, role=Qt.DisplayRole):
        if self._colProperties and column in range(0, len(self._colProperties))\
                and orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._colProperties[column].getLabel()

    def setItemsXPage(self, itemsXPage):
        """
        Set the items per page value and calculates the current configuration
        """
        if itemsXPage <= 0:
            itemsXPage = 1

        self._itemsXPage = itemsXPage
        self.__setupModel__()

    def setupPage(self, itemsXPage, currentPage):
        """
        Configure paging properties. Load the model data for the specified page
        :param itemsXPage:
        :param currentPage:
        :return:
        """
        if itemsXPage <= 0:
            itemsXPage = 1

        self._itemsXPage = itemsXPage
        self._currentPage = currentPage

        self.__setupModel__()
        self.loadPage()

    def flags(self, qModelIndex):
        """
        Reimplemented from QStandardItemModel
        :param qModelIndex: index in the model
        :return: The flags for the item. See :  Qt.ItemDataRole
        """
        fl = Qt.NoItemFlags
        col = qModelIndex.column()
        if qModelIndex.isValid():
            if self._colProperties:
                if self._colProperties[col].isEditable():
                    fl |= Qt.ItemIsEditable
                if self._colProperties[col].getType() == 'Bool':
                    fl |= Qt.ItemIsUserCheckable

        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | fl

    def setColumnProperties(self, properties):
        """
        Set the column properties for the model
        """
        self._colProperties = properties

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

    def __setupModel__(self):
        """
        Configure the model according to the itemsXPage and current page values
        """
        s = self._emTable.getSize()
        offset = self._currentPage * self._itemsXPage

        if s < self._itemsXPage:
            self._pageCount = 1
        else:
            self._pageCount = int(s / self._itemsXPage) + s % self._itemsXPage

        self._currentPage = int(offset / self._itemsXPage)


class ImageCache:
    """
    The ImageCache provide a data cache for images
    """
    def __init__(self, cacheSize, imgSize):
        """
        Constructor
        :param cacheSize: max length for internal image list
        :param imgSize: image size in percent
        """
        self._cacheSize = cacheSize
        self._imgSize = imgSize
        self._imgData = dict()

    def addImage(self, imgId, imgData):
        """
        Adds an image data to the chache
        :param imgData: image path
        TODO: Use an ID in the future, now we use the image path
        """
        ret = self._imgData.get(imgId)
        if not ret:
            ret = self.__createThumb__(imgData)
            self._imgData[imgId] = ret
        return ret

    def getImage(self, imgId):

        ret = self._imgData.get(imgId)
        return ret

    def __createThumb__(self, imgData):
        """
        Return the thumbail created for the specified image path.
        Rescale the original image according to  self._imageSize
        """
        pixmap = QPixmap(imgData)
        pixmap = pixmap.scaledToHeight(
            int(pixmap.height() * self._imgSize / 100), Qt.SmoothTransformation)

        return pixmap
