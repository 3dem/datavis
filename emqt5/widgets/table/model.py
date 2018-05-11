#!/usr/bin/python
# -*- coding: utf-8 -*-

from PyQt5.QtGui import QStandardItemModel, QStandardItem, QPixmap
from PyQt5.QtCore import Qt, QVariant, QSize, QAbstractItemModel, QModelIndex


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
        if columnProperties:
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
            t = self._colProperties[qModelIndex.column()].getType() \
                if self._colProperties else ""
            if t == 'Bool' or t == 'Image':
                return QVariant  # hide 'True' or 'False', path in Image type
            # we use Qt.UserRole for store data
            return QStandardItemModel.data(self, qModelIndex, Qt.UserRole)
        if role == Qt.CheckStateRole:
            if self._colProperties and \
                    self._colProperties[qModelIndex.column()].getType() \
                    == 'Bool':
                return Qt.Checked \
                    if QStandardItemModel.data(self, qModelIndex,
                                               Qt.UserRole) else Qt.Unchecked
        if role == Qt.EditRole:
            return QStandardItemModel.data(self, qModelIndex, Qt.UserRole)

        if role == Qt.SizeHintRole:
            if self._colProperties and \
                    self._colProperties[qModelIndex.column()].isRenderable():
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


class DataModel(QAbstractItemModel):
    """
    Model for EM Data
    """
    def __init__(self, parent=None, data=[], columnProperties=None,
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
        self._data = data
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

        if role == Qt.DecorationRole:
            return QVariant()
        if role == Qt.DisplayRole:
            t = self._colProperties[qModelIndex.column()].getType() \
                if self._colProperties else ""
            if t == 'Bool' or t == 'Image':
                return QVariant()  # hide 'True' or 'False', path in Image type
            # we use Qt.UserRole for store data
            return QVariant(self._items[qModelIndex.row()][qModelIndex.column()])
        if role == Qt.CheckStateRole:
            if self._colProperties and \
                    self._colProperties[qModelIndex.column()].getType() \
                    == 'Bool':
                return Qt.Checked \
                    if self._items[qModelIndex.row()][qModelIndex.column()] \
                    else Qt.Unchecked
            return QVariant()

        if role == Qt.EditRole:
            return QVariant(
                self._items[qModelIndex.row()][qModelIndex.column()])

        if role == Qt.SizeHintRole:
            if self._colProperties and \
                    self._colProperties[qModelIndex.column()].isRenderable():
                return self._iconSize

        if role == Qt.TextAlignmentRole:
            return Qt.AlignVCenter

        return QVariant(self._items[qModelIndex.row()][qModelIndex.column()])

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
        return len(self._items)

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
        if self._data:
            return len(self._data)

        return 0

    def getData(self, row, col):
        """
        Return the data for specificied column and row
        """
        return self._data[row][col]

    def loadPage(self, pageIndex=-1):
        """
        Load the page specified by pageIndex. If pageIndex is not within
        the page range then load the current page.
        """
        self.beginResetModel()
        self._items = []
        self.endResetModel()

        if pageIndex in range(0, self._pageCount):
            self._currentPage = pageIndex

        self.beginInsertRows(QModelIndex(), 0, self._itemsXPage)
        self._items = self.__getItems__(self._currentPage * self._itemsXPage,
                                        self._itemsXPage)
        self.endInsertRows()

    def prevPage(self):
        self._currentPage = self._currentPage - 1 \
            if self._currentPage > 0 else 0
        self.loadPage()

    def nextPage(self):
        self._currentPage = self._currentPage + 1 \
            if (self._currentPage + 1) * self._itemsXPage <= len(self._data) \
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
        s = len(self._data)
        offset = self._currentPage * self._itemsXPage

        if s < self._itemsXPage:
            self._pageCount = 1
        else:
            self._pageCount = int(s / self._itemsXPage) + s % self._itemsXPage

        self._currentPage = int(offset / self._itemsXPage)

    def __getItems__(self, offset, itemsXPage):
        """
        Retrieve the items from the initial position with the specified length
        """
        return self._data[offset:offset + itemsXPage]


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
