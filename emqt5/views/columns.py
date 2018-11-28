#!/usr/bin/python
# -*- coding: utf-8 -*-

from math import log10

from PyQt5.QtCore import Qt, pyqtSlot, QSize, QModelIndex
from PyQt5.QtWidgets import QTableView, QHeaderView, QAction, QMenu
from PyQt5 import QtCore
from .model import ImageCache
from .base import AbstractView, EMImageItemDelegate

import qtawesome as qta


class ColumnsView(AbstractView):
    """
    The ColumnsView class provides some functionality for show large numbers of
    items with simple paginate elements in columns view. """

    sigCurrentRowChanged = QtCore.pyqtSignal(int)  # For current row changed
    sigTableSizeChanged = QtCore.pyqtSignal()  # when the Table has been resized

    def __init__(self, parent, **kwargs):
        AbstractView.__init__(self, parent=parent)
        self._pageSize = 0
        self._imgCache = ImageCache(50)
        self._thumbCache = ImageCache(500, (100, 100))
        self.__setupUI(**kwargs)

    def __setupUI(self, **kwargs):
        self._tableView = QTableView(self)
        self._tableView.setHorizontalHeader(HeaderView(self._tableView))
        self._tableView.verticalHeader().setTextElideMode(QtCore.Qt.ElideRight)
        self._defaultDelegate = self._tableView.itemDelegate()
        self.sigTableSizeChanged.connect(self.__onSizeChanged)
        self._tableView.setSelectionBehavior(QTableView.SelectRows)
        self._tableView.setSelectionMode(QTableView.SingleSelection)
        self._tableView.setSortingEnabled(False)
        self._tableView.setModel(None)
        self._tableView.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._tableView.resizeEvent = self.__tableViewResizeEvent
        self._delegate = EMImageItemDelegate(self)
        self._delegate.setImageCache(self._thumbCache)
        self._mainLayout.insertWidget(0, self._tableView)
        self._pageBar.sigPageChanged.connect(self.__onCurrentPageChanged)

    def __tableViewResizeEvent(self, evt):
        """
        Reimplemented to receive tableview resize events which are passed
        in the event parameter. Emits sigTableSizeChanged
        :param evt:
        """
        QTableView.resizeEvent(self._tableView, evt)
        self.sigTableSizeChanged.emit()

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

        if tableSize.width() > 0 and tableSize.height() > 0 and rowSize > 0:
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

    @pyqtSlot(int)
    def __onCurrentPageChanged(self, page):
        """ Invoked when change current page """
        if self._model is not None:
            size = self._model.getPageSize()
            self.selectRow(page * size)

    @pyqtSlot(QModelIndex, QModelIndex)
    def __onCurrentRowChanged(self, current, previous):
        """ Invoked when current row change """
        if current.isValid():
            row = current.row()
            self.sigCurrentRowChanged.emit(
                row + self._pageSize * self._model.getPage())

    @pyqtSlot(Qt.Orientation, int, int)
    def __onHeaderDataChanged(self, orientation, first, last):
        if self._model is not None and orientation == Qt.Vertical:
            row = self._model.headerData(0, orientation, Qt.DisplayRole)
            if row < 10:
                row = 10
            vHeader = self._tableView.verticalHeader()
            w = int(log10(row) + 1) * 12
            vHeader.setFixedWidth(w)
            vHeader.geometriesChanged.emit()

    def setModel(self, model):

        if self._model is not None:
            self._model.headerDataChanged.disconnect(self.__onHeaderDataChanged)

        self._tableView.setModel(model)
        self._tableView.resizeColumnsToContents()
        AbstractView.setModel(self, model)
        if model:
            self.__setupDelegatesForColumns()
            self.__setupVisibleColumns()
            s = self._tableView.verticalHeader().defaultSectionSize()
            model.setIconSize(QSize(s, s))
            model.setupPage(self._pageSize, 0)
            self._tableView.selectionModel().currentRowChanged.connect(
                self.__onCurrentRowChanged)
            model.headerDataChanged.connect(self.__onHeaderDataChanged)

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

            if row in range(0, self._model.totalRowCount()):
                page = self.__getPage(row)
                if not page == self._model.getPage():
                    self._model.loadPage(page)
                self._tableView.selectRow(0 if row == 0 else
                                          row % self._pageSize)

    def currentRow(self):
        """ Returns the current selected row """
        if self._model is None:
            return -1
        r = self._tableView.currentIndex().row()
        return r if r <= 0 else r + self._pageSize * self._model.getPage()

    def setImageCache(self, imgCache):
        self._imgCache = imgCache

    def setThumbCache(self, thumbCache):
        self._thumbCache = thumbCache
        self._delegate.setImageCache(thumbCache)

    def getViewDims(self):
        """ Returns a tuple (rows, columns) with the data size """
        if self._model is None:
            return 0, 0
        else:
            return self._model.rowCount(), self._model.columnCount(None)

    def getHeaderSize(self, columnIndex=None):
        """
        Returns the header size in pixels for the given column.
        If columnIndex is None, then returns the entire header size
        """
        header = self._tableView.horizontalHeader()

        if columnIndex is None:
            return header.length()
        else:
            return header.sectionSize(columnIndex)

    def getPreferedSize(self):
        """
        Returns a tuple (width, height), which represents
        the preferred dimensions to contain all the data
        """
        if self._model is None or self._model.rowCount() == 0:
            return 0, 0

        rowHeight = self._tableView.verticalHeader().sectionSize(0)
        h = rowHeight * self._model.totalRowCount() + \
            (self._pageBar.height() if self._pageBar.isVisible() else 0) + 90
        return self.getHeaderSize(), h


class HeaderView(QHeaderView):
    def __init__(self, table):
        QHeaderView.__init__(self, Qt.Horizontal, table)
        self.setSectionsClickable(True)
        self.setHighlightSections(True)
        self.setResizeMode(QHeaderView.Interactive)
        self._vheader = table.verticalHeader()
        self._resizing = False
        self._start_position = -1
        self._start_width = -1

    def mouseMoveEvent(self, event):
        if self._resizing:
            width = event.globalX() - self._start_position + self._start_width
            if width > 0:
                self._vheader.setFixedWidth(width)
                self._vheader.geometriesChanged.emit()
        else:
            QHeaderView.mouseMoveEvent(self, event)
            if 0 <= event.x() <= 3:
                if not self.testAttribute(Qt.WA_SetCursor):
                    self.setCursor(Qt.SplitHCursor)

    def mousePressEvent(self, event):
        if not self._resizing and event.button() == Qt.LeftButton:
            if 0 <= event.x() <= 3:
                self._start_position = event.globalX()
                self._start_width = self._vheader.width()
                self._resizing = True
                return
        QHeaderView.mousePressEvent(self, event)

    def mouseReleaseEvent(self, event):
        self._resizing = False
        QHeaderView.mouseReleaseEvent(self, event)
