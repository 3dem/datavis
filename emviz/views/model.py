#!/usr/bin/python
# -*- coding: utf-8 -*-

from PyQt5.QtGui import QFont
from PyQt5.QtCore import (Qt, pyqtSlot, QVariant, QSize,
                          QAbstractItemModel, QModelIndex)

from emviz.models import (TYPE_BOOL, TYPE_STRING, TYPE_INT, TYPE_FLOAT,
                          RENDERABLE, EDITABLE, VISIBLE)
from ._constants import DATA_ROLE, LABEL_ROLE


class TablePageItemModel(QAbstractItemModel):
    """
    Model to display tabular data coming from a TableModel and using
    a TableModel, but only showing a page of the whole data.
    """

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
        """
        QAbstractItemModel.__init__(self, kwargs.get('parent', None))
        self._model = tableModel
        self._displayConfig = tableConfig or tableModel.createDefaultConfig()
        self._defaultFont = QFont()
        self._indexWidth = 50
        self._iconSize = None

        # Internal variable related to the pages
        self._pagingInfo = pagingInfo

    def _getPageValue(self, row, col, role=Qt.DisplayRole):
        """ Return the value for specified column and row in the current page
        """
        if self._pagingInfo.pageSize > 1:
            row += (self._pagingInfo.currentPage - 1)*self._pagingInfo.pageSize
        if role == DATA_ROLE:
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

        if role == DATA_ROLE:
            return self._getPageValue(row, col, role)

        if role == LABEL_ROLE:
            return []

        if role == Qt.DisplayRole and t != TYPE_BOOL:
            return QVariant(self._getPageValue(row, col))

        if role == Qt.CheckStateRole and t == TYPE_BOOL:
            return Qt.Checked if self._getPageValue(row, col) else Qt.Unchecked

        if (role == Qt.EditRole or role == Qt.UserRole
                or role == Qt.AccessibleTextRole
                or role == Qt.AccessibleDescriptionRole):
            return QVariant(self._getPageValue(row, col))

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


class GalleryItemModel(TablePageItemModel):
    """
    The GalleryItemModel class provides  data coming from a TableModel and using
    a TableModel, but only showing a page of the whole data. It is suitable for
    use with GalleryView
    """
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
        """
        TablePageItemModel.__init__(self, tableModel, pagingInfo, tableConfig,
                                    **kwargs)

    def columnCount(self, index=QModelIndex()):
        """ Reimplemented from TablePageItemModel.
            Return the number of columns that are visible in the model.
        """
        return self._displayConfig.getColumnsCount()

    def data(self, qModelIndex, role=Qt.DisplayRole):
        """ Reimplemented from TablePageItemModel """
        if role == LABEL_ROLE:
            if not qModelIndex.isValid():
                return []

            row = qModelIndex.row()
            d = self._displayConfig
            it = d.iterColumns(visible=True)
            labels = ['%s=%s' % (cc.getLabel(), self._getPageValue(row, col))
                      for (col, cc) in it]
            return labels

        return TablePageItemModel.data(self, qModelIndex, role)
