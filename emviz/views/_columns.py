#!/usr/bin/python
# -*- coding: utf-8 -*-

from math import log10

from PyQt5.QtCore import (Qt, pyqtSlot, QSize, QModelIndex, QItemSelection,
                          QItemSelectionModel, QItemSelectionRange)
from PyQt5.QtWidgets import (QTableView, QHeaderView, QAbstractItemView)
from PyQt5 import QtCore

from emviz.widgets import EMImageItemDelegate, PagingInfo
from emviz.models import VISIBLE, RENDERABLE
from ._paging_view import PagingView
from .model import TablePageItemModel


class ColumnsView(PagingView):
    """
    The ColumnsView class provides some functionality for show large numbers of
    items with simple paginate elements in columns view. """

    # For current row changed
    sigCurrentRowChanged = QtCore.pyqtSignal(int)
    # when the Table has been resized (oldSize, newSize)
    sigTableSizeChanged = QtCore.pyqtSignal(object, object)

    def __init__(self, parent=None, **kwargs):
        """
        :param parent:  (QWidget) Parent widget
        :param kwargs:
            model:          The data model
            displayConfig:  Input TableModel that will control how the data
                            fetched from the TableModel will be displayed.
                            displayConfig can be None, in which case the model
                            will be taken as displayConfig.
            selectionMode:  (int) SINGLE_SELECTION(default), EXTENDED_SELECTION,
                            MULTI_SELECTION or NO_SELECTION
        """
        PagingView.__init__(self, parent=parent,
                            pagingInfo=PagingInfo(1, 1),
                            **kwargs)
        self._selection = set()
        self._delegate = EMImageItemDelegate(self)
        self._pageItemModel = None
        self.setSelectionMode(kwargs.get("selectionMode",
                                         PagingView.SINGLE_SELECTION))
        self.setModel(model=kwargs['model'],
                      displayConfig=kwargs.get('displayConfig'))

    def _createContentWidget(self):
        tv = QTableView(self)
        hHeader = HeaderView(tv)
        hHeader.setHighlightSections(False)
        hHeader.sectionClicked.connect(self.__onHeaderClicked)
        hHeader.setSectionsMovable(True)
        tv.setHorizontalHeader(hHeader)
        tv.verticalHeader().setTextElideMode(Qt.ElideRight)
        tv.setObjectName("ColumnsViewTable")
        self._defaultDelegate = tv.itemDelegate()
        self.sigTableSizeChanged.connect(self.__onSizeChanged)
        tv.setSelectionBehavior(QTableView.SelectRows)
        tv.setSelectionMode(QTableView.SingleSelection)
        tv.setSortingEnabled(True)
        tv.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        #tv.setStyleSheet(
        #    "QTableView#ColumnsViewTable::item:selected:!active{"
        #    "selection-background-color: red;}")  # palette(light);}")

        tv.resizeEvent = self.__tableViewResizeEvent
        tv.setModel(None)
        self._tableView = tv
        return tv

    def __connectSignals(self):
        """ Connects all signals related to the TablePageItemModel
        """
        if self._pageItemModel:
            self._pageBar.sigPageChanged.connect(
                self._pageItemModel.pageConfigChanged)
            self._pageBar.sigPageChanged.connect(self.__onCurrentPageChanged)
            self._pageItemModel.headerDataChanged.connect(
                self.__onHeaderDataChanged)

    def __disconnectSignals(self):
        """ Disconnects all signals related to the TablePageItemModel
        """
        if self._pageItemModel:
            self._pageBar.sigPageChanged.disconnect(
                self._pageItemModel.pageConfigChanged)
            self._pageBar.sigPageChanged.disconnect(self.__onCurrentPageChanged)
            self._pageItemModel.headerDataChanged.disconnect(
                self.__onHeaderDataChanged)

    def __tableViewResizeEvent(self, evt):
        """
        Reimplemented to receive QTableView resize events which are passed
        in the event parameter. Emits sigTableSizeChanged
        :param evt: The event
        """
        QTableView.resizeEvent(self._tableView, evt)
        self.sigTableSizeChanged.emit(evt.oldSize(), evt.size())

    def __getPage(self, row):
        """
        Return the page where row are located or -1 if it can not be calculated
        :param row: (int) The row index. 0 is the first
        :return:    (int) The page index. 0 is the first
        """
        return int(row / self._pagingInfo.pageSize) \
            if self._pagingInfo.pageSize > 0 and row >= 0 else -1

    def __calcPageSize(self):
        """
        Calculate the number of items per page according to the size of the
        view area.
        """
        tableSize = self._tableView.viewport().size()
        rowSize = self._tableView.verticalHeader().defaultSectionSize()

        if tableSize.width() > 0 and tableSize.height() > 0 and rowSize > 0:
            rows = int(tableSize.height() / rowSize)
            # if tableSize.width() < rowSize.width() pRows may be 0
            return 1 if rows == 0 else rows
        return 1

    def __updatePageBar(self):
        """Updates the PageBar paging settings """
        rows = self.__calcPageSize()
        if not rows == self._pagingInfo.pageSize:
            self._pagingInfo.setPageSize(rows)
            self._pagingInfo.setCurrentPage(
                self.__getPage(self._currentRow) + 1)
            self._pageBar.setPagingInfo(self._pagingInfo)

    def __setupDelegatesForColumns(self):
        """
        Sets the corresponding Delegate for all columns
        """
        # we have defined one delegate for the moment: ImageItemDelegate
        if self._model:
            for i, colConfig in self._model.iterColumns():
                delegate = self._defaultDelegate
                if colConfig[RENDERABLE]:
                    delegate = self._delegate
                self._tableView.setItemDelegateForColumn(i, delegate)

    def setupVisibleColumns(self):
        """
        Hide the columns with visible property=True
        """
        for i, colConfig in self._model.iterColumns():
            if not colConfig[VISIBLE]:
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
                pageSize = self._pagingInfo.pageSize
                m = self._pageItemModel
                sel = QItemSelection()
                for row in range(page * pageSize, (page + 1) * pageSize):
                    if row in self._selection:
                        sel.append(
                            QItemSelectionRange(m.index(row % pageSize, 0),
                                                m.index(row % pageSize,
                                                        m.columnCount() - 1)))
                allSel = QItemSelection(m.index(0, 0),
                                        m.index(pageSize - 1,
                                                m.columnCount() - 1))
                selModel.select(allSel, QItemSelectionModel.Deselect)
                if not sel.isEmpty():
                    selModel.select(sel, QItemSelectionModel.Select)

    @pyqtSlot(int)
    def __onHeaderClicked(self, logicalIndex):
        """
        Invoked when a section is clicked.
        The section's logical index is specified by logicalIndex.
        """
        if self._selectionMode == PagingView.SINGLE_SELECTION or \
                self._selectionMode == PagingView.NO_SELECTION:
            self.__updateSelectionInView(self._pagingInfo.currentPage - 1)
        else:
            self._selection.clear()
            self.sigSelectionChanged.emit()

    @pyqtSlot(object, object)
    def __onSizeChanged(self, oldSize, newSize):
        """ Invoked when the table widget is resized """
        if not oldSize.height() == newSize.height():
            self.__updatePageBar()
            self.selectRow(self._currentRow)

    @pyqtSlot(int)
    def __onCurrentPageChanged(self, page):
        """
        Invoked when change current page. Emits sigCurrentRowChanged signal.
        1 is the index of the first page.
        """
        if self._model is not None:
            self._currentRow = (page - 1) * self._pagingInfo.pageSize
            if self._selectionMode == PagingView.SINGLE_SELECTION:
                self._selection.clear()
                self._selection.add(self._currentRow)

            self.__updateSelectionInView(page - 1)
            self.sigCurrentRowChanged.emit(self._currentRow)

    @pyqtSlot(QModelIndex, QModelIndex)
    def __onCurrentRowChanged(self, current, previous):
        """ Invoked when current row change """
        if current.isValid():
            row = current.row()
            p = self._pagingInfo
            self._currentRow = row + p.pageSize * (p.currentPage - 1)
            if self._selectionMode == PagingView.SINGLE_SELECTION:
                self._selection.clear()
                self._selection.add(self._currentRow)
            self.__updateSelectionInView(p.currentPage - 1)
            self.sigCurrentRowChanged.emit(self._currentRow)

    @pyqtSlot(Qt.Orientation, int, int)
    def __onHeaderDataChanged(self, orientation, first, last):
        """
        This slot is invoked whenever a header is changed.
        :param orientation:  (Qt.Orientation) The orientation indicates whether
                             the horizontal or vertical header has changed.
        :param first:        (int) First section index
        :param last:         (int) Last section index
        """
        if self._pageItemModel is not None and orientation == Qt.Vertical:
            row = self._pageItemModel.headerData(0, orientation, Qt.DisplayRole)
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
        self.__updateSelectionInView(self._pagingInfo.currentPage - 1)

    @pyqtSlot(QItemSelection, QItemSelection)
    def __onInternalSelectionChanged(self, selected, deselected):
        """ Invoked when the internal selection is changed """
        page = self._pagingInfo.currentPage - 1
        pageSize = self._pagingInfo.pageSize

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

    def updateViewConfiguration(self):
        """ Reimplementing from PagingView.
        Updates the columns configuration.
        """
        self.setupVisibleColumns()
        self.__setupDelegatesForColumns()

    def setModel(self, model, displayConfig=None):
        """
        Sets the model for this view.
        Raise Exception when the model is None
        :param model:         (emviz.model.TableModel) The data model
        :param displayConfig: (emviz.model.TableModel) Input TableModel that
                              will control how the data fetched from the
                              TableModel will be displayed.
        """
        if model is None:
            raise Exception('Invalid model: None')

        self._selection.clear()
        self._currentRow = 0
        self.__disconnectSignals()
        self._model = model
        self._pagingInfo.numberOfItems = model.getRowsCount()
        self._pagingInfo.pageSize = self.__calcPageSize()
        self._pagingInfo.currentPage = 1
        self._pageItemModel = TablePageItemModel(model, self._pagingInfo,
                                                 tableConfig=displayConfig,
                                                 parent=self)
        self.__connectSignals()
        self._tableView.setModel(self._pageItemModel)
        sModel = self._tableView.selectionModel()
        sModel.currentRowChanged.connect(self.__onCurrentRowChanged)
        sModel.selectionChanged.connect(self.__onInternalSelectionChanged)
        self._pageBar.setPagingInfo(self._pagingInfo)

        #  remove sort indicator from all columns
        self._tableView.horizontalHeader().setSortIndicator(-1,
                                                            Qt.AscendingOrder)
        self.updateViewConfiguration()
        s = self._tableView.verticalHeader().defaultSectionSize()
        self._pageItemModel.setIconSize(QSize(s, s))
        self.setupColumnsWidth()

    def resetView(self):
        """ Reset the internal state of the view. """
        self._tableView.reset()
        if self._selection:
            self.__updateSelectionInView(self._pagingInfo.currentPage - 1)

    def setRowHeight(self, height):
        """
        Sets the height for all rows
        :param height: (int) The row height in pixels
        """
        self._tableView.verticalHeader().setDefaultSectionSize(height)
        self.__updatePageBar()

    def setColumnWidth(self, column, width):
        """
        Sets the width for the given column
        :param column: (int) The column index. First index is 0.
        :param width:  (int) The column width
        """
        self._tableView.setColumnWidth(column, width)

    def getColumnWidth(self, column):
        """
        Returns the width for the given column.
        :param column: (int) The column index. First index is 0.
        """
        return self._tableView.columnWidth(column)

    def selectRow(self, row):
        """ Selects the given row """
        if 0 <= row < self._pagingInfo.numberOfItems:
            page = self.__getPage(row) + 1
            self._currentRow = row
            if not page == self._pagingInfo.currentPage:
                self._pageBar.setCurrentPage(page)

            if self._selectionMode == PagingView.SINGLE_SELECTION:
                self._selection.clear()
                self._selection.add(row)

            self.sigCurrentRowChanged.emit(row)
            self.__updateSelectionInView(page - 1)

    def getCurrentRow(self):
        """ Returns the current selected row """
        return self._currentRow

    def getViewDims(self):
        """ Returns a tuple (rows, columns) with the data size """
        return self._pageItemModel.rowCount(), self._pageItemModel.columnCount()

    def getHeaderSize(self, columnIndex=None):
        """
        Returns the header size in pixels for the given column.
        If columnIndex is None, then returns the entire header size.
        0 is the first index.
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
        rowHeight = self._pageItemModel.headerData(0, Qt.Vertical,
                                                   Qt.SizeHintRole)
        rowHeight = 30 if rowHeight is None else rowHeight.height()
        h = rowHeight * self._model.getRowsCount() + \
            (self._pageBar.height() if self._pageBar.isVisible() else 0) + 90
        return self.getHeaderSize(), h

    def setSelectionMode(self, selectionMode):
        """
        Indicates how the view responds to user selections:
        SINGLE_SELECTION, EXTENDED_SELECTION, MULTI_SELECTION
        """
        PagingView.setSelectionMode(self, selectionMode)
        if selectionMode == self.SINGLE_SELECTION:
            self._tableView.setSelectionMode(QAbstractItemView.SingleSelection)
        elif selectionMode == self.EXTENDED_SELECTION:
            self._tableView.setSelectionMode(
                QAbstractItemView.ExtendedSelection)
        elif selectionMode == self.MULTI_SELECTION:
            self._tableView.setSelectionMode(QAbstractItemView.MultiSelection)
        else:
            PagingView.setSelectionMode(self, PagingView.NO_SELECTION)
            self._tableView.setSelectionMode(QAbstractItemView.NoSelection)

    def setSelectionBehavior(self, selectionBehavior):
        """
        This property holds which selection behavior the view uses.
        Holds whether selections are done in terms of single items,
        rows or columns.

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

    def resizeColumnToContents(self, col=-1):
        """
        From QTableView:
        Resizes the given column based on the size hints of the delegate used
        to render each item in the row.
        """
        if col < 0:
            self._tableView.resizeColumnsToContents()
        else:
            self._tableView.resizeColumnToContents(col)

    def getHorizontalHeader(self):
        """
        From QTableView:
        Returns the table view's horizontal header.
        """
        return self._tableView.horizontalHeader()

    def setLabelIndexes(self, labels):
        """
        Initialize the indexes of the columns that will be displayed as text
        below the images
        labels (list)
        """
        self._delegate.setLabelIndexes(labels)


class HeaderView(QHeaderView):
    """ HeaderView that allows to display the row indexes """
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
        """ Reimplemented from QHeaderView """
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
        """ Reimplemented from QHeaderView """
        if not self._resizing and event.button() == Qt.LeftButton:
            if 0 <= event.x() <= 3:
                self._start_position = event.globalX()
                self._start_width = self._vheader.width()
                self._resizing = True
                return
        QHeaderView.mousePressEvent(self, event)

    def mouseReleaseEvent(self, event):
        """ Reimplemented from QHeaderView """
        self._resizing = False
        QHeaderView.mouseReleaseEvent(self, event)
