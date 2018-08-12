#!/usr/bin/python
# -*- coding: utf-8 -*-


from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal, QSize, QRectF, QModelIndex
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QToolBar, QAction,
                             QTableView, QSpinBox, QLabel, QStyledItemDelegate,
                             QStyle, QAbstractItemView, QStatusBar,
                             QApplication, QHeaderView, QComboBox, QHBoxLayout,
                             QStackedLayout, QLineEdit, QActionGroup, QListView,
                             QSizePolicy, QSpacerItem, QPushButton, QSplitter,
                             QGraphicsPixmapItem)
from PyQt5.QtGui import (QPixmap, QPen, QIcon, QPalette, QStandardItemModel,
                         QStandardItem)
from PyQt5 import QtCore
import qtawesome as qta
import pyqtgraph as pg

import em
from emqt5.utils import EmPath, EmTable, parseImagePath
from .config import TableViewConfig
from .model import ImageCache, TableDataModel, X_AXIS, Y_AXIS, Z_AXIS
from .base import AbstractView, EMImageItemDelegate


# FIXME: Is it really necessary to subclass to do this?
class _QTableViewResizable(QTableView):
    """
    Just overwrite the resizeEvent to fire a signal
    """
    sigSizeChanged = QtCore.pyqtSignal()  # when the widget has been resized

    def __init__(self, parent=None):
        QTableView.__init__(self, parent)

    def resizeEvent(self, evt):
        """
        Reimplemented from TableWidget
        """
        QTableView.resizeEvent(self, evt)
        self.sigSizeChanged.emit()


class ColumnsView(AbstractView):
    """
    The ColumnsView class provides some functionality for show large numbers of
    items with simple paginate elements in columns view. """

    sigCurrentRowChanged = QtCore.pyqtSignal(int)  # For current row changed

    def __init__(self, parent, **kwargs):
        AbstractView.__init__(self, parent=parent)
        self._pageSize = 0
        self._imgCache = ImageCache(50)
        self.__setupUI(**kwargs)

    def __setupUI(self, **kwargs):
        self._tableView = _QTableViewResizable(self)
        self._defaultDelegate = self._tableView.itemDelegate()
        self._tableView.sigSizeChanged.connect(self.__onSizeChanged)
        self._tableView.setSelectionBehavior(QTableView.SelectRows)
        self._tableView.setSelectionMode(QTableView.SingleSelection)
        self._tableView.verticalHeader().hide()
        self._tableView.setSortingEnabled(False)
        self._tableView.setModel(None)
        self._tableView.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._delegate = EMImageItemDelegate(self)
        self._delegate.setImageCache(self._imgCache)
        self._mainLayout.insertWidget(0, self._tableView)

    def __getPage(self, row):
        """
        Return the page where row are located or -1 if it can not be calculated
        """
        return int(row / self._pageSize) \
            if self._pageSize > 0 and row >= 0 else -1

    def __calcPageSize(self):
        """
        Calculate the number of items per page according to the size of the
        view area.
        """
        self._pageSize = 0

        tableSize = self._tableView.viewport().size()
        rowSize = self._tableView.verticalHeader().defaultSectionSize()

        if tableSize.width() > 0 and tableSize.height() > 0 and rowSize:
            pRows = int(tableSize.height() / rowSize)
            # if tableSize.width() < rowSize.width() pRows may be 0
            if pRows == 0:
                pRows = 1

            self._pageSize = pRows

    def __setupDelegatesForColumns(self):
        """
        Sets the corresponding Delegate for all columns
        """
        # we have defined one delegate for the moment: ImageItemDelegate
        if self._model:
            for i, colConfig in enumerate(self._model.getColumnConfig()):
                delegate = self._defaultDelegate
                if colConfig["renderable"] and \
                        colConfig["visible"]:
                    delegate = self._delegate

                self._tableView.setItemDelegateForColumn(i, delegate)

    def __setupVisibleColumns(self):
        """
        Hide the columns with visible property=True or allowSetVisible=False
        """
        for i, colConfig in enumerate(self._model.getColumnConfig()):
            if not colConfig["visible"]:
                self._tableView.hideColumn(i)
            else:
                self._tableView.showColumn(i)

    @pyqtSlot()
    def __onSizeChanged(self):
        """ Invoked when the table widget is resized """
        self.__calcPageSize()
        if self._model:
            index = self._tableView.currentIndex()
            row = index.row() if index and index.isValid() else 0
            self._model.setupPage(self._pageSize, self.__getPage(row))

    @pyqtSlot(QModelIndex, QModelIndex)
    def __onCurrentRowChanged(self, current, previous):
        """ Invoked when current row change """
        if current.isValid():
            row = current.row()
            self.sigCurrentRowChanged.emit(
                row + self._pageSize * self._model.getPage())

    def setModel(self, model):
        self._tableView.setModel(model)
        AbstractView.setModel(self, model)
        if model:
            self.__setupDelegatesForColumns()
            self.__setupVisibleColumns()
            s = self._tableView.verticalHeader().defaultSectionSize()
            model.setIconSize(QSize(s, s))
            model.setupPage(self._pageSize, 0)
            self._tableView.selectionModel().currentRowChanged.connect(
                self.__onCurrentRowChanged)

    def setRowHeight(self, height):
        """ Sets the heigth for all rows """
        self._tableView.verticalHeader().setDefaultSectionSize(height)
        self.__calcPageSize()
        if self._model:
            index = self._tableView.currentIndex()
            row = index.row() if index and index.isValid() else 0
            self._model.setupPage(self._pageSize, self.__getPage(row))
            self._model.setIconSize(QSize(height, height))

    def setColumnWidth(self, column, width):
        """ Sets the width for the given column """
        self._tableView.setColumnWidth(column, width)

    def getColumnWidth(self, column):
        """ Returns the width for the given column """
        return self._tableView.columnWidth(column)

    def selectRow(self, row):
        """ Selects the given row """
        if self._model:
            r = self._tableView.currentIndex().row()
            r = r if r <= 0 else r + self._pageSize * self._model.getPage()

            if not r == row and row in range(0, self._model.totalRowCount()):
                page = self.__getPage(row)
                self._model.loadPage(page)
                self._tableView.selectRow(
                    0 if row == 0 else row % self._pageSize)

    def setImageCache(self, imgCache):
        self._imgCache = imgCache
        self._delegate.setImageCache(imgCache)
