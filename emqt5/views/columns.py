#!/usr/bin/python
# -*- coding: utf-8 -*-

from math import log10

from PyQt5.QtCore import (Qt, pyqtSlot, QSize, QModelIndex, QItemSelection,
                          QItemSelectionModel, QItemSelectionRange)
from PyQt5.QtWidgets import (QTableView, QHeaderView, QAbstractItemView,
                             QStyleOptionViewItem)
from PyQt5 import QtCore
from .model import ImageCache
from .base import AbstractView, EMImageItemDelegate


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
        self._selection = set()
        self._currentRow = 0
        self.__setupUI(**kwargs)

    def __setupUI(self, **kwargs):
        self._tableView = QTableView(self)
        hHeader = HeaderView(self._tableView)
        hHeader.setHighlightSections(False)
        hHeader.sectionClicked.connect(self.__onHeaderClicked)
        self._tableView.setHorizontalHeader(hHeader)
        self._tableView.verticalHeader().setTextElideMode(Qt.ElideRight)
        self._tableView.setObjectName("ColumnsViewTable")
        self._defaultDelegate = self._tableView.itemDelegate()
        self.sigTableSizeChanged.connect(self.__onSizeChanged)
        self._tableView.setSelectionBehavior(QTableView.SelectRows)
        self._tableView.setSelectionMode(QTableView.SingleSelection)
        self._tableView.setSortingEnabled(True)
        self._tableView.setModel(None)
        self._tableView.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        #self._tableView.setStyleSheet(
        #    "QTableView#ColumnsViewTable::item:selected:!active{"
        #    "selection-background-color: red;}")  # palette(light);}")

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

    def setupColumnsWidth(self):
        """  """
        self._tableView.horizontalHeader().setStretchLastSection(True)
        self._tableView.resizeColumnsToContents()
        #print("calc: ", self._tableView.horizontalScrollBar().maximum())
        #if self._model is not None:
        #    if self._tableView.horizontalScrollBar().maximum() > 0:
        #        option = QStyleOptionViewItem()
        #       for col in range(0, self._model.columnCount()):
        #            delegate = self._tableView.itemDelegateForColumn(0)
        #            w = 0
        #            for row in range(0, self._model.rowCount()):
        #                s = delegate.sizeHint(option,
        #                                      self._model.createIndex(row, col))
        #                rw = s.width() + 3
        #                w = max(rw, w)
        #            self._tableView.setColumnWidth(
        #                col,
        #                min(w, self._tableView.columnWidth(col), 80))

    def __updateSelectionInView(self, page):
        """ Makes the current selection in the view """
        if self._model is not None:
            selModel = self._tableView.selectionModel()
            if selModel is not None:
                pageSize = self._model.getPageSize()
                sel = QItemSelection()
                for row in range(page * pageSize, (page + 1) * pageSize):
                    if row in self._selection:
                        sel.append(
                            QItemSelectionRange(
                                self._model.index(row % pageSize, 0),
                                self._model.index(
                                    row % pageSize,
                                    self._model.columnCount() - 1)))

                allSel = QItemSelection(self._model.index(0, 0),
                                        self._model.index(
                                            pageSize - 1,
                                            self._model.columnCount() - 1))
                selModel.select(allSel, QItemSelectionModel.Deselect)
                if not sel.isEmpty():
                    selModel.select(sel, QItemSelectionModel.Select)

    @pyqtSlot(int)
    def __onHeaderClicked(self, logicalIndex):
        """
        Invoked when a section is clicked.
        The section's logical index is specified by logicalIndex.
        """
        if self._selectionMode == AbstractView.SINGLE_SELECTION or \
                self._selectionMode == AbstractView.NO_SELECTION:
            self.__updateSelectionInView(self._model.getPage())
        else:
            self._selection.clear()
            self.sigSelectionChanged.emit()

    @pyqtSlot()
    def __onSizeChanged(self):
        """ Invoked when the table widget is resized """
        self.__calcPageSize()
        if self._model is not None:
            self._model.setupPage(self._pageSize,
                                  self.__getPage(self._currentRow))

    @pyqtSlot(int)
    def __onCurrentPageChanged(self, page):
        """ Invoked when change current page """
        if self._model is not None:
            size = self._model.getPageSize()
            self._currentRow = page * size
            self.sigCurrentRowChanged.emit(self._currentRow)
            self._model.dataChanged.emit(self._model.createIndex(0, 0),
                                         self._model.createIndex(
                                             self._pageSize - 1,
                                             self._model.columnCount()),
                                         [Qt.ForegroundRole])

    @pyqtSlot(QModelIndex, QModelIndex)
    def __onCurrentRowChanged(self, current, previous):
        """ Invoked when current row change """
        if current.isValid():
            row = current.row()
            self._currentRow = row + self._pageSize * self._model.getPage()
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

    @pyqtSlot(set)
    def changeSelection(self, selection):
        """ Invoked when the selection is changed """
        self._selection = selection
        self.__updateSelectionInView(self._model.getPage())

    @pyqtSlot(QItemSelection, QItemSelection)
    def __onInternalSelectionChanged(self, selected, deselected):
        """ Invoked when the internal selection is changed """
        page = self._model.getPage()
        pageSize = self._model.getPageSize()

        for sRange in selected:
            top = sRange.top() + page * pageSize
            bottom = sRange.bottom() + page * pageSize
            self._selection.update(range(top, bottom + 1))

        for sRange in deselected:
            top = sRange.top() + page * pageSize
            bottom = sRange.bottom() + page * pageSize
            for row in range(top, bottom + 1):
                self._selection.discard(row)

        self.sigSelectionChanged.emit()

    def setModel(self, model):
        """ Sets the model for this view """
        self._selection.clear()
        self._currentRow = 0
        if self._model is not None:
            self._model.headerDataChanged.disconnect(self.__onHeaderDataChanged)

        self._tableView.setModel(model)
        #  remove sort indicator from all columns
        self._tableView.horizontalHeader().setSortIndicator(-1,
                                                            Qt.AscendingOrder)
        AbstractView.setModel(self, model)
        if model:
            self.__setupDelegatesForColumns()
            self.__setupVisibleColumns()
            s = self._tableView.verticalHeader().defaultSectionSize()
            model.setIconSize(QSize(s, s))
            model.setupPage(self._pageSize, 0)
            selModel = self._tableView.selectionModel()
            selModel.currentRowChanged.connect(self.__onCurrentRowChanged)
            selModel.selectionChanged.connect(self.__onInternalSelectionChanged)
            model.headerDataChanged.connect(self.__onHeaderDataChanged)

            self.setupColumnsWidth()

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
        if self._model and row in range(0, self._model.totalRowCount()):
                page = self.__getPage(row)
                self._currentRow = row
                if not page == self._model.getPage():
                    self._model.loadPage(page)
                self.__updateSelectionInView(page)
                self._model.dataChanged.emit(self._model.createIndex(0, 0),
                                             self._model.createIndex(
                                                 self._pageSize - 1,
                                                 self._model.columnCount()),
                                             [Qt.ForegroundRole])

    def currentRow(self):
        """ Returns the current selected row """
        if self._model is None:
            return -1

        return self._currentRow

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

    def setSelectionMode(self, selectionMode):
        """
        Indicates how the view responds to user selections:
        SINGLE_SELECTION, EXTENDED_SELECTION, MULTI_SELECTION
        """
        self._selectionMode = selectionMode
        if selectionMode == self.SINGLE_SELECTION:
            self._tableView.setSelectionMode(QAbstractItemView.SingleSelection)
        elif selectionMode == self.EXTENDED_SELECTION:
            self._tableView.setSelectionMode(
                QAbstractItemView.ExtendedSelection)
        elif selectionMode == self.MULTI_SELECTION:
            self._tableView.setSelectionMode(QAbstractItemView.MultiSelection)
        else:
            self._selectionMode = AbstractView.NO_SELECTION
            self._tableView.setSelectionMode(QAbstractItemView.NoSelection)

    def setSelectionBehavior(self, selectionBehavior):
        """
        This property holds which selection behavior the view uses.
        This property holds whether selections are done in terms of
        single items, rows or columns.

        Possible values:
                        SELECT_ITEMS, SELECT_ROWS, SELECT_COLUMNS
        """
        if selectionBehavior == self.SELECT_ITEMS:
            self._tableView.setSelectionBehavior(QAbstractItemView.SelectItems)
        elif selectionBehavior == self.SELECT_COLUMNS:
            self._tableView.setSelectionBehavior(
                QAbstractItemView.SelectColumns)
        elif selectionBehavior == self.SELECT_ROWS:
            self._tableView.setSelectionBehavior(QAbstractItemView.SelectRows)

    def resizeColumnToContents(self, row):
        """
        From QTableView:
        Resizes the given row based on the size hints of the delegate used
        to render each item in the row.
        """
        self._tableView.resizeColumnToContents(row)

    def selectedIndexes(self):
        """
        From QTableView:
        This convenience function returns a list of all selected and non-hidden
        item indexes in the view. The list contains no duplicates,
        and is not sorted.
        """
        return self._tableView.selectedIndexes()

    def currentIndex(self):
        """
        From QTableView:
        Returns the model index of the current item.
        """
        return self._tableView.currentIndex()

    def getHorizontalHeader(self):
        """
        From QTableView:
        Returns the table view's horizontal header.
        """
        return self._tableView.horizontalHeader()

    def getTableView(self):
        """ Return the QTableView widget used to display the items """
        return self._tableView


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
