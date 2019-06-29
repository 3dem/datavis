#!/usr/bin/python
# -*- coding: utf-8 -*-

from PyQt5.QtGui import QFont
from PyQt5.QtCore import (Qt, pyqtSignal, pyqtSlot, QVariant, QSize,
                          QAbstractItemModel, QModelIndex)

from emviz.models import (AXIS_X, AXIS_Y, AXIS_Z, TableModel,
                          TYPE_BOOL, TYPE_STRING, TYPE_INT, TYPE_FLOAT,
                          RENDERABLE, EDITABLE, VISIBLE)


class TablePageItemModel(QAbstractItemModel):
    """
    Model to display tabular data coming from a TableModel and using
    a TableModel, but only showing a page of the whole data.
    """

    DataRole = Qt.UserRole + 2

    def __init__(self, tableModel, pagingInfo, tableConfig, **kwargs):
        """
        Constructs an DataModel to be used from TableView
        :param tableModel: (TableModel) Input TableModel from where the data
                           will be read and present in pages.
        :param tableConfig: input TableConfig that will control how the data
                            fetched from the TableModel will be displayed
        :param pagingInfo: (PagingInfo) Page configuration
        :param **kwargs: Optional arguments:
            - parent: a parent QObject of the model (NOTE: see Qt framework)
            - titles: the titles that will be display
        """
        QAbstractItemModel.__init__(self, kwargs.get('parent', None))
        self._model = tableModel
        self._displayConfig = tableConfig or tableModel.createDefaultConfig()
        self._defaultFont = QFont()
        self._indexWidth = 50
        self._iconSize = None

        # Internal variable related to the pages
        self._pagingInfo = pagingInfo

    def __getPageValue(self, row, col, role=Qt.DisplayRole):
        """ Return the value for specified column and row in the current page
        """
        if self._pagingInfo.pageSize > 1:
            row += (self._pagingInfo.currentPage - 1)*self._pagingInfo.pageSize
        if role == self.DataRole:
            return self._model.getData(row, col)

        data = self._model.getValue(row, col)
        if data is None:
            return None

        t = self._displayConfig[col].getType()

        if t == TYPE_STRING:
            return str(data)
        elif t == TYPE_BOOL:
            return bool(int(data))
        elif t == TYPE_INT:
            return int(data)
        elif t == TYPE_FLOAT:
            return float(data)

        return data

    @pyqtSlot()
    def pageConfigChanged(self):
        """
        This function should be called, or the slot connect whenever the
        page configuration changes, either the current page, number of elements
        or the page size (number of elements per page).
        """
        self.beginResetModel()
        self.headerDataChanged.emit(Qt.Vertical, 0, 0)
        self.endResetModel()

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

        row = qModelIndex.row()
        col = qModelIndex.column()

        cc = self._displayConfig.getColumnConfig(col)
        t = cc.getType()

        if role == TablePageItemModel.DataRole:
            return self.__getPageValue(row, col, role)

        if role == Qt.DisplayRole and t != TYPE_BOOL:
            return QVariant(self.__getPageValue(row, col))

        if role == Qt.CheckStateRole and t == TYPE_BOOL:
            return Qt.Checked if self.__getPageValue(row, col) else Qt.Unchecked

        if (role == Qt.EditRole or role == Qt.UserRole
                or role == Qt.AccessibleTextRole
                or role == Qt.AccessibleDescriptionRole):
            return QVariant(self.__getPageValue(row, col))

        if role == Qt.SizeHintRole and cc[RENDERABLE]:
            return self._iconSize or QSize(50, 50)

        if role == Qt.TextAlignmentRole:
            return Qt.AlignVCenter

        if role == Qt.FontRole:
            return self._defaultFont

        return QVariant()

    def columnCount(self, index=QModelIndex()):
        """ Reimplemented from QAbstractItemModel.
        Return the number of columns that are visible in the model.
        """
        return self._displayConfig.getColumnsCount(visible=True)

    def rowCount(self, index=QModelIndex()):
        """
        Reimplemented from QAbstractItemModel.
        Return the items per page.
        """
        p = self._pagingInfo  # short notation
        return p.itemsInLastPage if p.isLastPage() else p.pageSize

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
        This function is abstract in QAbstractItemModel
        Returns the parent of the model item with the given index.
        If the item has no parent, an invalid QModelIndex is returned.
        """
        return QModelIndex()

    def setData(self, qModelIndex, value, role=Qt.EditRole):
        """
        Reimplemented from QAbstractItemModel
        """
        if not qModelIndex.isValid():
            return False

        if role == Qt.EditRole and self.flags(qModelIndex) & Qt.ItemIsEditable:
            col = qModelIndex.column()
            row = qModelIndex.row()
            pi = self._pagingInfo
            row += (pi.currentPage - 1) * pi.pageSize
            # FIXME [phv] waiting for setData or setValue in the Model
            #if self._model.setTableData(row, col, value):
            #    self.dataChanged.emit(qModelIndex, qModelIndex, [role])
            #    return True

        return False

    def headerData(self, column, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole or role == Qt.ToolTipRole:
            cc = self._displayConfig.getColumnConfig(column)
            if cc is not None and orientation == Qt.Horizontal and cc[VISIBLE]:
                return cc.getLabel()
            elif orientation == Qt.Vertical:
                p = self._pagingInfo
                return column + (p.currentPage - 1) * p.pageSize + 1
        elif role == Qt.SizeHintRole and orientation == Qt.Vertical:
            if self._iconSize:
                size = QSize(self._indexWidth,
                             self._iconSize.height())
            else:
                size = QSize(self._indexWidth, 20)
            return size

        return QVariant()

    def flags(self, qModelIndex):
        """
        Reimplemented from QStandardItemModel
        :param qModelIndex: index in the model
        :return: The flags for the item. See :  Qt.ItemDataRole
        """
        fl = Qt.NoItemFlags
        if qModelIndex.isValid():
            col = qModelIndex.column()
            cc = self._displayConfig.getColumnConfig(col)
            if cc[EDITABLE]:
                fl |= Qt.ItemIsEditable
            if cc.getType() == TYPE_BOOL:
                fl |= Qt.ItemIsUserCheckable

        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | fl

    def setIconSize(self, size):
        """
        Sets the size for renderable items
        :param size: QSize
        """
        self._iconSize = size

    def getTitles(self):
        """ Return the titles for this model """
        return self._titles

    def hasRenderableColumn(self):
        """ Return True if the model has renderable columns """
        return self._displayConfig.hasColumnConfig(renderable=True)

    def getModel(self):
        """ Returns the current data model """
        return self._model

    def getDisplayConfig(self, column=-1):
        """
        Returns column configuration for the given column index
        :param column: column index, first column is 0.
                       column <0 return entire list
        :return: ColumnConfig.
        """
        if column < 0 or not self._displayConfig:
            return self._displayConfig

        if column < self._displayConfig.getColumnsCount():
            return self._displayConfig[column]

        return None

    def setDisplayConfig(self, config):
        """
        Sets the config how we want to display the data
        """
        self._displayConfig = config

    # TODO: We need to check about the sorting in the TableModel
    # def sort(self, column, order=Qt.AscendingOrder):
    #     self.beginResetModel()
    #     od = " DESC" if order == Qt.DescendingOrder else ""
    #     self._emTable.sort([self._tableViewConfig[column].getName() + od])
    #     self.endResetModel()

    # TODO: I'm commenting out these functions for simplicity now
    # TODO: although we migth need them, so better not to delete for now.
    # def insertRows(self, row, count, parent=QModelIndex()):
    #     """ Reimplemented from QAbstractItemModel """
    #
    #     if row < self._emTable.getSize():
    #         self.beginInsertRows(parent, row, row + count)
    #         for index in range(row, row + count):
    #             r = self._emTable.createRow()
    #             self._emTable.addRow(r)
    #         self.endInsertRows()
    #         self.__setupModel()
    #         self.sigPageConfigChanged.emit(self._page, self._pageCount,
    #                                        self._pageSize)
    #         self.loadPage(self._page, force=True)
    #         return True
    #     return False
    #
    # def appendRow(self, row):
    #     """ Append a new row to the end of the model """
    #     self.beginResetModel()
    #     tr = self._emTable.getSize() - 1
    #     self.insertRow(self._emTable.getSize() - 1)
    #     tc = 0
    #     tr = tr + 1
    #     for value in row:
    #         self.setTableData(tr, tc, value)
    #         tc = tc + 1
    #     self.endResetModel()


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

    def __init__(self, **kwargs):
        """
        Constructs an DataModel to be used from a View for display volume data.
        VolumeDataModel has three columns: index, enabled, slice.
        :param kwargs: Optional arguments.
            - parent: a parent QObject of the model
            - title: a title for the model
            - axisModels:      (tuple) The models (AXIS_X, AXIS_Y, AXIS_Z)
            - tableModel: (TableViewConfig) Specify a config how we want
                               to display the three data colums. If it is None,
                               a default one will be created.
            - pageSize:        (int) Number of elements displayed per page.
            - axis:            Default axis: AXIS_X or AXIS_Y or AXIS_Z
            - volumeIndex      (int) Default volume index. First index is 0.
        """
        QAbstractItemModel.__init__(self, kwargs.get('parent', None))
        self._iconSize = QSize(32, 32)
        self._xModel, self._yModel, self._zModel = kwargs['axisModels']
        self._tableViewConfig = (kwargs.get('tableModel', None)
                                 or TableModel.createVolumeConfig())
        self._pageSize = kwargs.get('pageSize', 10)
        self._page = 0
        self._pageCount = 0
        t = kwargs.get('title', 'Axis-') + "(%s)"
        self._titles = [t % 'X', t % 'Y', t % 'Z']
        self._dim = self._zModel.getDim()
        self._axis = kwargs.get('axis', AXIS_X)
        self._volumeIndex = kwargs.get('volumeIndex', 0)
        self.setAxis(self._axis)
        self._defaultFont = QFont()
        
    def __setupModel(self):
        """
        Configure the model according to the pageSize and current page
        values
        """
        s = self._dim[2]
        offset = self._page * self._pageSize

        if s < self._pageSize:
            self._pageCount = 1
        else:
            self._pageCount = int(s / self._pageSize) + \
                              (1 if s % self._pageSize else 0)

        self._page = int(offset / self._pageSize)

    def clone(self):
        """ Clone this model """
        clo = VolumeDataModel(axisModels=(self._xModel,
                                          self._yModel,
                                          self._zModel),
                              tableViewConfig=self._tableViewConfig,
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
        self._volumeIndex = index
        self.sigVolumeIndexChanged.emit(self._volumeIndex)
        self.setupPage(self._pageSize, 0)

    def getVolumeCount(self):
        """
        Return the volumes count for this model
        TODO[phv] Review when multiples volumes
        """
        return 1

    def setAxis(self, axis):
        """ Sets the current axis. Raise Exception for invalid axis values """
        if axis == AXIS_X:
            self._dim = self._xModel.getDim()
        elif axis == AXIS_Y:
            self._dim = self._yModel.getDim()
        elif axis == AXIS_Z:
            self._dim = self._zModel.getDim()
        else:
            raise Exception("Invalid axis value: %d" % axis)

        self._axis = axis
        self.setupPage(self._pageSize, 0)
        self.sigAxisChanged.emit(self._axis)

    def data(self, qModelIndex, role=Qt.DisplayRole):
        """ Reimplemented function from QAbstractItemModel. """
        if not qModelIndex.isValid():
            return None

        row = qModelIndex.row() + self._page * self._pageSize
        col = qModelIndex.column()

        cc = self._model.getColumnConfig(col)
        t = cc.getType()

        if role == TablePageItemModel.DataTypeRole:
            return t

        if role == Qt.DecorationRole:
            return QVariant()

        if role == Qt.DisplayRole:
            if t ==TYPE_BOOL:
                return QVariant()  # hide 'True' or 'False'
            # we use Qt.UserRole for store data
            return QVariant(self.getTableData(row, col))

        if role == Qt.CheckStateRole:
            if t ==TYPE_BOOL:
                return Qt.Checked \
                    if self.getTableData(row, col) else Qt.Unchecked
            return QVariant()

        if role == Qt.EditRole or role == Qt.UserRole:
            return QVariant(self.getTableData(row, col))

        if role == Qt.SizeHintRole:
            if cc[RENDERABLE]:
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

        ts = self._dim[2]
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
        return self._dim[2]

    def setData(self, qModelIndex, value, role=Qt.EditRole):
        """
        Reimplemented from QAbstractItemModel. VolumeDataModel is not editable.
        """
        return False

    def getTableData(self, row, col):
        """
        Return the data for specified column and row
        """
        if row in range(0, self._dim[2]) \
                and col in range(0, len(self._tableViewConfig)):
            if col == 0:
                return row + 1
            if col == 1:
                return True
            if col == 2:
                return '%d@%d@%d@%s' % (row, self._axis, self._volumeIndex,
                                        self._dataSource)
        return None

    @pyqtSlot(int)
    def loadPage(self, pageIndex=0):
        """ Load the page specified by pageIndex(First index is 1).
        If pageIndex is not within the page range then load the current page.
        """
        if (pageIndex in range(1, self._p)):
            self.beginResetModel()
            self._page = pageIndex
            self.endResetModel()
            self.sigPageChanged.emit(self._page)

    def prevPage(self):
        """ Change to the previous page """
        self._page = self._page - 1 if self._page > 0 else 0
        self.loadPage()

    def nextPage(self):
        """ Change to the next page """
        self._page = self._page + 1 \
            if (self._page + 1) * self._pageSize <= len(self._dim[2]) else \
            self._page
        self.loadPage()

    def headerData(self, column, orientation, role=Qt.DisplayRole):
        """ Reimplemented from QAbstractItemModel """
        if self._tableViewConfig and \
                column in range(0, len(self._tableViewConfig)) \
                and orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._tableViewConfig[column].getLabel()

    def setItemsPerPage(self, pageSize):
        """
        Set the items per page value and calculates the current configuration.
        :param pageSize: (int) The page size
        """
        if pageSize <= 0:
            pageSize = 1

        self._pageSize = pageSize
        self.__setupModel()

    def setupPage(self, pageSize, currentPage):
        """
        Configure paging properties. Load the model data for the specified page
        :param pageSize:     (int) The page size
        :param currentPage:  (int) The current page
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
                       TYPE_BOOL:
                    fl |= Qt.ItemIsUserCheckable

        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | fl

    def setColumnConfig(self, colConfig):
        """
        Set the column properties for the model
        :param colConfig: (TableViewConfig) The columns configuration
        """
        self._tableViewConfig = colConfig

    def getColumnConfig(self, column=-1):
        """
        Return column configuration for the given column index
        :param column: (int) Column index, first column is 0.
                       If column<0 then return the entire list
        :return: ColumnConfig object.
        """
        if column < 0 or not self._tableViewConfig:
            return self._tableViewConfig

        if column < len(self._tableViewConfig):
            return self._tableViewConfig[column]

        return None

    def setIconSize(self, size):
        """
        Sets the size for renderable items
        :param size: (QSize) The icon size
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

    def getDataSource(self):
        """ Return the path of this volume model """
        return self._xModel.getLocation()

    def getTableViewConfig(self):
        return self._tableViewConfig


def createTableModel(path):
    """ Return the TablePageItemModel for the given EM table file """
    # FIXME: The following import is here because it cause a cyclic dependency
    # FIXME: we should remove the use of EmTable
    from emviz.core import EmTable
    t = EmTable.load(path)  # [names], table
    return TablePageItemModel(t[1], parent=None, titles=t[0],
                              tableViewConfig=TableModel.fromTable(t[1]),
                              dataSource=path)


def createStackModel(imagePath, title='Stack'):
    """ Return a stack model for the given image """
    # FIXME: The following import is here because it cause a cyclic dependency
    # FIXME: we should remove the use of EmTable
    from emviz.core import EmTable
    table = EmTable.fromStack(imagePath)

    return TablePageItemModel(table, titles=[title],
                              tableViewConfig=TableModel.createStackConfig(),
                              dataSource=imagePath)


def createVolumeModel(imagePath, axis=AXIS_X, titles=["Volume"]):

    return VolumeDataModel(imagePath, parent=None, axis=axis, titles=titles)
