#!/usr/bin/python
# -*- coding: utf-8 -*-

import scipy.ndimage as ndimage

from PyQt5.QtGui import QPixmap, QFont, QBrush
from PyQt5.QtCore import (Qt, pyqtSignal, pyqtSlot, QVariant, QSize,
                          QAbstractItemModel, QModelIndex)

from emqt5.views.config import TableViewConfig
from emqt5.utils import EmPath, EmImage, EmTable


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
            - titles: the titles that will be display
            FIXME: should this be here in the model?
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
        self._pageData = []
        self._page = 0
        self._pageSize = kwargs.get('pageSize', 1)
        self._pageCount = 0
        self._titles = kwargs.get('titles', [''])
        self._dataSource = kwargs.get('dataSource', None)
        self._defaultFont = QFont()
        self._indexWidth = 50
        self.__setupModel()

    def __getPageData(self, row, col):
        """ Return the data for specified column and row in the current page """
        if self._pageData and row < len(self._pageData):
            emRow = self._pageData[row]
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

    def clone(self):
        """ Clone this Model """
        clo = TableDataModel(self._emTable,
                             tableViewConfig=self._tableViewConfig,
                             pageSize=self._pageSize,
                             titles=self._titles[:],
                             dataSource=self._dataSource)
        return clo

    def data(self, qModelIndex, role=Qt.DisplayRole):
        """
        This is an reimplemented function from QAbstractItemModel.
        Reimplemented to hide the 'True' text in columns with boolean value.
        We use Qt.UserRole for store table data.
        TODO: Widgets with DataModel needs Qt.DisplayRole value to show
              So, we need to define what to do with Renderable data
              (may be return a QIcon or QPixmap)
        """
        if not qModelIndex.isValid() or not self._pageData:
            return None
        row = qModelIndex.row()
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
            return QVariant(self.__getPageData(row, col))
        if role == Qt.CheckStateRole:
            if t == TableViewConfig.TYPE_BOOL:
                return Qt.Checked \
                    if self.__getPageData(row, col) else Qt.Unchecked
            return QVariant()

        if role == Qt.EditRole or role == Qt.UserRole:
            return QVariant(self.__getPageData(row, col))

        if role == Qt.SizeHintRole:
            if self._tableViewConfig[col]["renderable"]:
                return self._iconSize
            return QVariant()

        if role == Qt.TextAlignmentRole:
            return Qt.AlignVCenter

        if role == Qt.FontRole:
            return self._defaultFont

        # Is good practice to provide data for Qt.ToolTipRole,
        # Qt.AccessibleTextRole and Qt.AccessibleDescriptionRole
        if role == Qt.ToolTipRole or \
           role == Qt.AccessibleTextRole or \
           role == Qt.AccessibleDescriptionRole:
            return QVariant(self.__getPageData(row, col))

        return QVariant()

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

        if role == Qt.EditRole and self.flags(qModelIndex) & Qt.ItemIsEditable:
            col = qModelIndex.column()
            row = self._page * self._pageSize + qModelIndex.row()
            print("Page: ", self._page)
            if self.setTableData(row, col, value):
                self.dataChanged.emit(qModelIndex, qModelIndex, [role])
                return True

        return False

    def setTableData(self, row, column, value):
        """
        Set table data.
        NOTE: Using this function, no view will be notified
        """
        if self.flags(self.createIndex(0, column)) & Qt.ItemIsEditable:
            tableColumn = self._emTable.getColumnByIndex(column)
            tableRow = self._emTable[row]
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

    def getEmTable(self):
        """ Returns the em.Table that contains the data """
        return self._emTable

    def getDataSource(self):
        """
        Returns the data source for this model.
        For now we use the path of the table file.
        """
        return self._dataSource

    @pyqtSlot(int)
    def loadPage(self, pageIndex=-1, force=False):
        """
        Load the page specified by pageIndex. If pageIndex is not within
        the page range then load the current page.
        """
        if force or (not self._page == pageIndex and pageIndex
                     in range(0, self._pageCount)):
            self.beginResetModel()
            if not pageIndex == -1:
                self._page = pageIndex
            self._pageData = []
            first = self._page * self._pageSize
            last = first + self._pageSize
            size = self._emTable.getSize()
            if last > size:
                last = size
            for i in range(first, last):
                self._pageData.append(self._emTable[i])
            self.headerDataChanged.emit(Qt.Vertical, 0, 0)
            self.endResetModel()
            self.sigPageChanged.emit(self._page)

    def prevPage(self):
        self._page = self._page - 1 \
            if self._page > 0 else 0
        self.loadPage()

    def nextPage(self):
        self._page = self._page + 1 \
            if (self._page + 1) * self._pageSize <= len(self._emTable) else \
            self._page
        self.loadPage()

    def headerData(self, column, orientation, role=Qt.DisplayRole):

        if self._tableViewConfig:
            if role == Qt.DisplayRole or role == Qt.ToolTipRole:
                if orientation == Qt.Horizontal \
                        and column in range(0, len(self._tableViewConfig)):
                    return self._tableViewConfig[column].getLabel()
                elif orientation == Qt.Vertical \
                        and self._tableViewConfig.isShowRowIndex():
                    return column + self._page * self._pageSize + 1
            elif role == Qt.SizeHintRole and orientation == Qt.Vertical:
                if self._iconSize:
                    size = QSize(self._indexWidth,
                                 self._iconSize.height())
                else:
                    size = QSize(50, 20)
                return size

        return QVariant()

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
        self.loadPage(currentPage, force=True)
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

    def getTitles(self):
        """ Return the title for this model """
        return self._titles

    def hasRenderableColumn(self):
        """ Return True if the model has renderable columns """
        if self._tableViewConfig is None:
            return False
        else:
            return self._tableViewConfig.hasRenderableColumn()

    def setTableViewConfig(self, config):
        """
        Sets the config how we want to display the data
        """
        self._tableViewConfig = config

    def sort(self, column, order=Qt.AscendingOrder):
        self.beginResetModel()
        od = " DESC" if order == Qt.DescendingOrder else ""
        self._emTable.sort([self._tableViewConfig[column].getName() + od])
        self.endResetModel()

    def insertRows(self, row, count, parent=QModelIndex()):
        """ Reimplemented from QAbstractItemModel """

        if row < self._emTable.getSize():
            self.beginInsertRows(parent, row, row + count)
            for index in range(row, row + count):
                r = self._emTable.createRow()
                self._emTable.addRow(r)
            self.endInsertRows()
            self.__setupModel()
            self.sigPageConfigChanged.emit(self._page, self._pageCount,
                                           self._pageSize)
            self.loadPage(self._page, force=True)
            return True
        return False

    def appendRow(self, row):
        """ Append a new row to the end of the model """
        self.beginResetModel()
        tr = self._emTable.getSize() - 1
        self.insertRow(self._emTable.getSize() - 1)
        tc = 0
        tr = tr + 1
        for value in row:
            self.setTableData(tr, tc, value)
            tc = tc + 1
        self.endResetModel()


class VolumeDataModel(QAbstractItemModel):
    """
    Model for EM Volume
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
    """ 
    Signal emitted when change the current axis
    emit (axis) 
    X: 0
    Y: 1
    Z: 2
    """
    sigAxisChanged = pyqtSignal(int)
    """ 
    Signal emitted when change the current volume index
    emit (modelIndex)
    """
    sigVolumeIndexChanged = pyqtSignal(int)

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
                                 or TableViewConfig.createVolumeConfig())
        self._pageSize = kwargs.get('pageSize', 10)
        self._page = 0
        self._pageCount = 0
        t = kwargs.get('title', 'Axis-') + "(%s)"
        self._titles = [t % 'X', t % 'Y', t % 'Z']
        self._dim = EmImage.getDim(path)
        self._axis = kwargs.get('axis', X_AXIS)
        self._rows = 0
        self._volumeIndex = kwargs.get('volumeIndex', 0)
        self.setAxis(kwargs.get('axis', X_AXIS))
        self._defaultFont = QFont()
        
    def clone(self):
        """ Clone this model """
        clo = VolumeDataModel(self._path, tableViewConfig=self._tableViewConfig,
                              pageSize=self._pageSize, axis=self._axis,
                              volumeIndex=self._volumeIndex)
        clo._titles = self._titles[:]
        return clo

    def getVolumeIndex(self):
        """ Return the volume index """
        return self._volumeIndex

    def setVolumeIndex(self, index):
        """
        Sets the volume index.
        For volume stacks: 0 <= index < em-image.dim.n
        """
        if self._dim is None:
            self._volumeIndex = 0
        elif index in range(0, self._dim.n):
            self._volumeIndex = index
        else:
            self._volumeIndex = 0

        self.sigVolumeIndexChanged.emit(self._volumeIndex)
        self.setupPage(self._pageSize, 0)

    def getVolumeCount(self):
        """
        Return the volumes count for this model
        """
        if self._dim is None:
            return 0
        return self._dim.n

    def setAxis(self, axis):
        """ Sets the current axis """
        if axis == X_AXIS:
            self._rows = self._dim.x
        elif axis == Y_AXIS:
            self._rows = self._dim.y
        elif axis == Z_AXIS:
            self._rows = self._dim.z
        else:
            self._rows = 0

        self._axis = axis
        self.setupPage(self._pageSize, 0)
        self.sigAxisChanged.emit(self._axis)

    def data(self, qModelIndex, role=Qt.DisplayRole):
        """ Reimplemented function from QAbstractItemModel. """
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

        if role == Qt.EditRole or role == Qt.UserRole:
            return QVariant(self.getTableData(row, col))

        if role == Qt.SizeHintRole:
            if self._tableViewConfig[col]["renderable"]:
                return self._iconSize
            return QVariant()

        if role == Qt.TextAlignmentRole:
            return Qt.AlignVCenter

        if role == Qt.FontRole:
            return self._defaultFont

        # Is good practice to provide data for Qt.ToolTipRole,
        # Qt.AccessibleTextRole and Qt.AccessibleDescriptionRole
        if role == Qt.ToolTipRole or \
                role == Qt.AccessibleTextRole or \
                role == Qt.AccessibleDescriptionRole:
            return QVariant(self.getTableData(row, col))

        return QVariant()

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

        if self._axis == X_AXIS:
            ts = self._dim.x
        elif self._axis == Y_AXIS:
            ts = self._dim.y
        else:
            ts = self._dim.z

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
        if self._axis == X_AXIS:
            return self._dim.x
        elif self._axis == Y_AXIS:
            return self._dim.y

        return self._dim.z

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
        Set table data.
        TODO: how to store "enable" column
        """
        return False

    def getTableData(self, row, col):
        """
        Return the data for specified column and row
        """
        if row in range(0, self._rows) \
                and col in range(0, len(self._tableViewConfig)):
            if col == 0:
                return row + 1
            if col == 1:
                return True
            if col == 2:
                return '%d@%d@%d@%s' % (row, self._axis, self._volumeIndex,
                                        self._path)
        return None

    @pyqtSlot(int)
    def loadPage(self, pageIndex=-1, force=False):
        """
        Load the page specified by pageIndex. If pageIndex is not within
        the page range then load the current page.
        """
        if force or (not self._page == pageIndex and pageIndex
                     in range(0, self._pageCount)):
            self.beginResetModel()
            self._page = pageIndex
            self.endResetModel()
            self.sigPageChanged.emit(self._page)

    def prevPage(self):
        self._page = self._page - 1 \
            if self._page > 0 else 0
        self.loadPage()

    def nextPage(self):
        self._page = self._page + 1 \
            if (self._page + 1) * self._pageSize <= len(self._emTable) else \
            self._page
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
        self.loadPage(self._page, force=True)
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

    def getTitles(self):
        """ Return the titles for this model """
        return self._titles

    def hasRenderableColumn(self):
        """ Return True if the model has renderable columns """
        if self._tableViewConfig is None:
            return False
        else:
            return self._tableViewConfig.hasRenderableColumn()

    def getPath(self):
        """ Return the path of this volume model """
        return self._path

    def __setupModel(self):
        """
        Configure the model according to the pageSize and current page
        values
        """
        s = self._rows
        offset = self._page * self._pageSize

        if s < self._pageSize:
            self._pageCount = 1
        else:
            self._pageCount = int(s / self._pageSize) + \
                              (1 if s % self._pageSize else 0)

        self._page = int(offset / self._pageSize)


class ImageCache:
    """
    The ImageCache provide a data cache for images
    """
    def __init__(self, cacheSize, imgSize=None):
        """
        Constructor
        :param cacheSize : (int) max length for internal image list
        :param imgSize: (tuple) image size. Calculates an appropriate thumbnail
                        size to preserve the aspect of the image
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
            try:
                ret = self.__createThumb(imgData, index)
                self._imgData[imgId] = ret
                if len(self._imgData) > self._cacheSize:
                    self._imgData.popitem()
            except Exception as ex:
                raise ex
            except RuntimeError as ex:
                raise ex
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
            array = EmImage.getNumPyArray(img)
            if self._imgSize is None:
                return array

            # preserve aspect ratio
            x, y = array.shape[0], array.shape[1]
            if x > self._imgSize[0]:
                y = int(max(y * self._imgSize[0] / x, 1))
                x = int(self._imgSize[0])
            if y > self._imgSize[1]:
                x = int(max(x * self._imgSize[1] / y, 1))
                y = int(self._imgSize[1])

            if x >= array.shape[0] and y >= array.shape[1]:
                return array

            return ndimage.zoom(array, x / float(array.shape[0]), order=1)

        return None


def createTableModel(path):
    """ Return the TableDataModel for the given EM table file """
    t = EmTable.load(path)  # [names], table
    return TableDataModel(t[1], parent=None, titles=t[0],
                          tableViewConfig=TableViewConfig.fromTable(t[1]),
                          dataSource=path)


def createStackModel(imagePath, title='Stack'):
    """ Return a stack model for the given image """
    table = EmTable.fromStack(imagePath)

    return TableDataModel(table, titles=[title],
                          tableViewConfig=TableViewConfig.createStackConfig(),
                          dataSource=imagePath)


def createVolumeModel(imagePath, axis=X_AXIS, titles=["Volume"]):

    return VolumeDataModel(imagePath, parent=None, axis=axis, titles=titles)
