#!/usr/bin/python
# -*- coding: utf-8 -*-

from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import (Qt, pyqtSignal, pyqtSlot, QVariant, QSize,
                          QAbstractItemModel, QModelIndex)

from emqt5.views.config import TableViewConfig
from emqt5.utils import EmPath, EmImage

import numpy as np

X_AXIS = 0
Y_AXIS = 1
Z_AXIS = 2
N_DIM = -1


class TableDataModel(QAbstractItemModel):
    """
    Model for EM Data
    """

    DataTypeRole = Qt.UserRole + 2

    """ 
    Signal emitted when change page configuration 
    emit (page, pageCount, pageSize)
    """
    sigPageConfigChanged = pyqtSignal(int, int, int)

    """ 
        Signal emitted when change the current page 
        emit (page)
        """
    sigPageChanged = pyqtSignal(int)

    def __init__(self, table, **kwargs):
        """
        Constructs an DataModel to be used from TableView
        :param table: input em.Table from where the data will be read
        :param **kwargs: Optional arguments:
            - parent: a parent QObject of the model (NOTE: see Qt framework)
            - title: a title that will be display (FIXME: should this be here in the model?)
            - tableViewConfig: specify a config how we want to display the
                data in the em.Table. If it is None, a default one will be
                created from the table.
            - pageSize: number of elements displayed per page (default 10)
        """
        QAbstractItemModel.__init__(self, kwargs.get('parent', None))
        self._iconSize = QSize(32, 32)
        self._emTable = table
        self._tableViewConfig = (kwargs.get('tableViewConfig', None)
                                 or TableViewConfig.fromTable(table))
        self._page = 0
        self._pageSize = kwargs.get('pageSize', 10)
        self._pageCount = 0
        self._title = kwargs.get('title', '')
        self.__setupModel()

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
        row = qModelIndex.row() + self._page * self._pageSize
        col = qModelIndex.column()

        t = self._tableViewConfig[col].getType() \
            if self._tableViewConfig else None

        if role == TableDataModel.DataTypeRole:
            return t
        if role == Qt.DecorationRole:
            return QVariant()
        if role == Qt.DisplayRole:
            if t == TableViewConfig.TYPE_BOOL:
                return QVariant()  # hide 'True' or 'False'
            # we use Qt.UserRole for store data
            return QVariant(self.getTableData(row, col))
        if role == Qt.CheckStateRole:
            if t == TableViewConfig.TYPE_BOOL:
                return Qt.Checked \
                    if self.getTableData(row, col) else Qt.Unchecked
            return QVariant()

        if role == Qt.EditRole:
            return QVariant(self.getTableData(row, col))

        if role == Qt.SizeHintRole:
            if self._tableViewConfig[col]["renderable"]:
                return self._iconSize

        if role == Qt.TextAlignmentRole:
            return Qt.AlignVCenter

        return QVariant(self.getTableData(row, col))

    def columnCount(self, index=QModelIndex()):
        """
        Reimplemented from QAbstractItemModel.
        Return the column count
        """
        return len(self._tableViewConfig) if self._tableViewConfig else 0

    def rowCount(self, index=QModelIndex()):
        """
        Reimplemented from QAbstractItemModel.
        Return the items per page.
        """
        vc = (self._page + 1) * self._pageSize
        ts = self._emTable.getSize()
        if vc > ts:  # last page
            return self._pageSize - (vc - ts)

        return self._pageSize

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
            t = self._tableViewConfig[col].getType()

            if t == TableViewConfig.TYPE_STRING:
                return emRow[emCol.getName()].toString()
            elif t == TableViewConfig.TYPE_BOOL:
                return bool(int(emRow[emCol.getName()]))
            elif t == TableViewConfig.TYPE_INT:
                return int(emRow[emCol.getName()])
            elif t == TableViewConfig.TYPE_FLOAT:
                return float(emRow[emCol.getName()])

            return emRow[emCol.getId()]

        return None

    @pyqtSlot(int)
    def loadPage(self, pageIndex=-1):
        """
        Load the page specified by pageIndex. If pageIndex is not within
        the page range then load the current page.
        """
        self.beginResetModel()
        if pageIndex in range(0, self._pageCount):
            self._page = pageIndex
        self.endResetModel()

    def prevPage(self):
        self._page = self._page - 1 \
            if self._page > 0 else 0
        self.loadPage()

    def nextPage(self):
        self._page = self._page + 1 \
            if (self._page + 1) * self._pageSize <= len(self._emTable)\
             else self._page
        self.loadPage()

    def headerData(self, column, orientation, role=Qt.DisplayRole):
        if self._tableViewConfig and \
                column in range(0, len(self._tableViewConfig)) \
                and orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._tableViewConfig[column].getLabel()

    def setItemsPerPage(self, pageSize):
        """
        Set the items per page value and calculates the current configuration
        """
        if pageSize <= 0:
            pageSize = 1

        self._pageSize = pageSize
        self.__setupModel()

    def setupPage(self, pageSize, currentPage):
        """
        Configure paging properties. Load the model data for the specified page
        :param pageSize:
        :param currentPage:
        :return:
        """
        if pageSize <= 0:
            pageSize = 1

        self._pageSize = pageSize
        self._page = currentPage if currentPage >= 0 else 0
        self.__setupModel()
        self.loadPage()
        self.sigPageConfigChanged.emit(self._page, self._pageCount,
                                       self._pageSize)

    def flags(self, qModelIndex):
        """
        Reimplemented from QStandardItemModel
        :param qModelIndex: index in the model
        :return: The flags for the item. See :  Qt.ItemDataRole
        """
        fl = Qt.NoItemFlags
        col = qModelIndex.column()
        if qModelIndex.isValid():
            if self._tableViewConfig:
                if self._tableViewConfig[col]["editable"]:
                    fl |= Qt.ItemIsEditable
                if self._tableViewConfig[col].getType() == \
                        TableViewConfig.TYPE_BOOL:
                    fl |= Qt.ItemIsUserCheckable

        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | fl

    def setColumnConfig(self, colConfig):
        """
        Set the column properties for the model
        """
        self._tableViewConfig = colConfig

    def getColumnConfig(self, column=-1):
        """
        Return column configuration for the given column index
        :param column: column index, first column is 0.
                       column <0 return entire list
        :return: ColumnConfig.
        """
        if column < 0 or not self._tableViewConfig:
            return self._tableViewConfig

        if column < len(self._tableViewConfig):
            return self._tableViewConfig[column]

        return None

    def setIconSize(self, size):
        """
        Sets the size for renderable items
        :param size: QSize
        """
        self._iconSize = size

    def getPageCount(self):
        """ Return the page count for this model """
        return self._pageCount

    def getPage(self):
        """ Return the current page for this model """
        return self._page

    def getPageSize(self):
        """ Return the items per page for this model """
        return self._pageSize

    def getTitle(self):
        """ Return the title for this model """
        return self._title

    def __setupModel(self):
        """
        Configure the model according to the pageSize and current page
        values
        """
        s = self._emTable.getSize()
        offset = self._page * self._pageSize

        if s < self._pageSize:
            self._pageCount = 1
        else:
            self._pageCount = int(s / self._pageSize) + \
                              (1 if s % self._pageSize else 0)

        self._page = int(offset / self._pageSize)


class VolumeDataModel(QAbstractItemModel):
    """
    Model for EM Volume
    """

    DataTypeRole = Qt.UserRole + 2

    def __init__(self, path, **kwargs):
        """
        Constructs an DataModel to be used from a View for display volume data.
        VolumeDataModel has three columns: index, enabled, slice.
        :param path: input path from where the volume will be read
        :param **kwargs: Optional arguments:
            - parent: a parent QObject of the model
            - title: a title for the model
            - tableViewConfig: specify a config how we want to display the three
                colums data. If it is None, a default one will be
                created.
            - pageSize: number of elements displayed per page (default 10)
        """
        QAbstractItemModel.__init__(self, kwargs.get('parent', None))
        self._iconSize = QSize(32, 32)
        self._path = path
        self._tableViewConfig = (kwargs.get('tableViewConfig', None)
                                 or self.__createDefaultTableViewConfig())
        self._pageSize = kwargs.get('pageSize', 10)
        self._page = 0
        self._pageCount = 0
        self._title = kwargs.get('title', '')
        self.__setupModel()

    def __createDefaultTableViewConfig(self):
        """
        Return the default configuration for the three columns:
        index, enabled, slice
        """
        return None


class ImageCache:
    """
    The ImageCache provide a data cache for images
    """
    def __init__(self, cacheSize, imgSize=100):
        """
        Constructor
        :param cacheSize: max length for internal image list
        :param imgSize: image size in percent
        """
        self._cacheSize = cacheSize
        self._imgSize = imgSize
        self._imgData = dict()

    def addImage(self, imgId, imgData, index=0):
        """
        Adds an image data to the chache
        :param imgData: image path
        TODO: Use an ID in the future, now we use the image path
        """
        ret = self._imgData.get(imgId)
        if ret is None:
            ret = self.__createThumb(imgData, index)
            self._imgData[imgId] = ret
            if len(self._imgData) > self._cacheSize:
                self._imgData.popitem()
        return ret

    def getImage(self, imgId):
        """ Return the image data for the given image id """
        ret = self._imgData.get(imgId)
        return ret

    def __createThumb(self, path, index=1):
        """
        Return the thumbnail created for the specified image path.
        Rescale the original image according to  self._imageSize
        """
        if EmPath.isStandardImage(path):
            pixmap = QPixmap(path)
            height = int(pixmap.height() * self._imgSize / 100)
            return pixmap.scaledToHeight(height, Qt.SmoothTransformation)

        elif EmPath.isData(path):
            img = EmImage.load(path, index)
            return np.array(img, copy=False)

        return None
