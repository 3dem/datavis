#!/usr/bin/python
# -*- coding: utf-8 -*-

import PyQt5.QtCore as qtc
import PyQt5.QtGui as qtg

from .. import models
from .. import widgets


class TablePageItemModel(qtc.QAbstractItemModel):
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
            - parent: a parent QObject of the model (NOTE: see qtc.Qt framework)
        """
        qtc.QAbstractItemModel.__init__(self, kwargs.get('parent', None))
        self.setModelConfig(tableModel, tableConfig, pagingInfo)
        self._defaultFont = qtg.QFont()
        self._indexWidth = 50
        self._iconSize = None

    def _getPageValue(self, row, col, role=qtc.Qt.DisplayRole):
        """ Return the value for specified column and row in the current page
        """
        pi = self._pagingInfo
        if pi.pageSize > 1:
            row += (pi.currentPage - 1) * pi.pageSize
        if role == widgets.DATA_ROLE:
            return self._model.getData(row, col)

        data = self._model.getValue(row, col)
        if data is None:
            return None

        t = self._displayConfig[col].getType()

        if t == models.TYPE_STRING:
            return str(data)
        elif t == models.TYPE_BOOL:
            return bool(int(data))
        elif t == models.TYPE_INT:
            return int(data)
        elif t == models.TYPE_FLOAT:
            return float(data)

        return data

    @qtc.pyqtSlot()
    def modelConfigChanged(self):
        """
        This function should be called, or the slot connect whenever the
        model configuration changes, either the PagingInfo, TableModel
        or TableConfig.
        """
        self.beginResetModel()
        self.headerDataChanged.emit(qtc.Qt.Vertical, 0, 0)
        self.endResetModel()

    def setModelConfig(self, tableModel, tableConfig, pagingInfo):
        """"""
        self._model = tableModel
        # Information related to the view configuration
        self._displayConfig = tableConfig or tableModel.createDefaultConfig()
        # Internal variable related to the pages
        self._pagingInfo = pagingInfo

    def data(self, qModelIndex, role=qtc.Qt.DisplayRole):
        """
        This is an reimplemented function from qtc.QAbstractItemModel.
        Reimplemented to hide the 'True' text in columns with boolean value.
        We use qtc.Qt.UserRole for store table data.
        TODO: Widgets with DataModel needs qtc.Qt.DisplayRole value to show
              So, we need to define what to do with Renderable data
              (may be return a QIcon or QPixmap)
        """
        if not qModelIndex.isValid():
            return None

        row = qModelIndex.row()
        col = qModelIndex.column()

        cc = self._displayConfig.getColumnConfig(col)
        t = cc.getType()

        if role == widgets.DATA_ROLE:
            try:
                data = self._getPageValue(row, col, role)
            except RuntimeError:
                data = None
            return data

        if role == widgets.LABEL_ROLE:
            d = self._displayConfig
            cc = d.getColumnConfig(col)
            labels = cc.getLabels()
            try:
                ret = ['%s=%s' % (d.getColumnConfig(i).getLabel(),
                                  self._getPageValue(row, i))
                       for i in labels]
            except RuntimeError:
                print('Error labels =', labels)
            return ret

        if role == qtc.Qt.DisplayRole and t != models.TYPE_BOOL:
            return qtc.QVariant(self._getPageValue(row, col))

        if role == qtc.Qt.CheckStateRole and t == models.TYPE_BOOL:
            CHECKED = qtc.Qt.Checked
            return CHECKED if self._getPageValue(row, col) else qtc.Qt.Unchecked

        if (role == qtc.Qt.EditRole or role == qtc.Qt.UserRole
                or role == qtc.Qt.AccessibleTextRole
                or role == qtc.Qt.AccessibleDescriptionRole):
            return qtc.QVariant(self._getPageValue(row, col))

        if role == qtc.Qt.SizeHintRole and cc[models.RENDERABLE]:
            return self._iconSize or qtc.QSize(50, 50)

        if role == qtc.Qt.TextAlignmentRole:
            return qtc.Qt.AlignVCenter

        if role == qtc.Qt.FontRole:
            return self._defaultFont

        return qtc.QVariant()

    def columnCount(self, index=qtc.QModelIndex()):
        """ Reimplemented from qtc.QAbstractItemModel.
        Return the number of columns that are visible in the model.
        """
        return self._displayConfig.getColumnsCount()

    def rowCount(self, index=qtc.QModelIndex()):
        """
        Reimplemented from qtc.QAbstractItemModel.
        Return the items per page.
        """
        p = self._pagingInfo  # short notation
        return p.itemsInLastPage if p.isLastPage() else p.pageSize

    def index(self, row, column, parent=qtc.QModelIndex()):
        """
        Reimplemented from qtc.QAbstractItemModel.
        Returns the index of the item in the model specified by the given row,
        column and parent index.
        """
        return self.createIndex(row, column)

    def parent(self, index):
        """
        Reimplemented from qtc.QAbstractItemModel.
        This function is abstract in qtc.QAbstractItemModel
        Returns the parent of the model item with the given index.
        If the item has no parent, an invalid qtc.QModelIndex is returned.
        """
        return qtc.QModelIndex()

    def setData(self, qModelIndex, value, role=qtc.Qt.EditRole):
        """
        Reimplemented from qtc.QAbstractItemModel
        """
        if not qModelIndex.isValid():
            return False

        if (role == qtc.Qt.EditRole
            and self.flags(qModelIndex) & qtc.Qt.ItemIsEditable):
            col = qModelIndex.column()
            row = qModelIndex.row()
            pi = self._pagingInfo
            row += (pi.currentPage - 1) * pi.pageSize
            # FIXME [phv] waiting for setData or setValue in the Model
            #if self._model.setTableData(row, col, value):
            #    self.dataChanged.emit(qModelIndex, qModelIndex, [role])
            #    return True

        return False

    def headerData(self, column, orientation, role=qtc.Qt.DisplayRole):
        if role == qtc.Qt.DisplayRole or role == qtc.Qt.ToolTipRole:
            cc = self._displayConfig.getColumnConfig(column)
            if cc is not None and orientation == qtc.Qt.Horizontal:
                return cc.getLabel()
            elif orientation == qtc.Qt.Vertical:
                p = self._pagingInfo
                return column + (p.currentPage - 1) * p.pageSize + 1
        elif role == qtc.Qt.SizeHintRole and orientation == qtc.Qt.Vertical:
            h = self._iconSize.height() if self._iconSize else 20
            return qtc.QSize(self._indexWidth, h)

        return qtc.QVariant()

    def flags(self, qModelIndex):
        """
        Reimplemented from QStandardItemModel
        :param qModelIndex: index in the model
        :return: The flags for the item. See :  qtc.Qt.ItemDataRole
        """
        fl = qtc.Qt.NoItemFlags
        if qModelIndex.isValid():
            col = qModelIndex.column()
            cc = self._displayConfig.getColumnConfig(col)
            if cc is None:
                return fl
            if cc[models.EDITABLE]:
                fl |= qtc.Qt.ItemIsEditable
            if cc.getType() == models.TYPE_BOOL:
                fl |= qtc.Qt.ItemIsUserCheckable

        return qtc.Qt.ItemIsEnabled | qtc.Qt.ItemIsSelectable | fl

    def setIconSize(self, size):
        """
        Sets the size for renderable items
        :param size: qtc.QSize
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
    # def sort(self, column, order=qtc.Qt.AscendingOrder):
    #     self.beginResetModel()
    #     od = " DESC" if order == qtc.Qt.DescendingOrder else ""
    #     self._emTable.sort([self._tableViewConfig[column].getName() + od])
    #     self.endResetModel()

    # TODO: I'm commenting out these functions for simplicity now
    # TODO: although we migth need them, so better not to delete for now.
    # def insertRows(self, row, count, parent=qtc.QModelIndex()):
    #     """ Reimplemented from qtc.QAbstractItemModel """
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
