#!/usr/bin/python
# -*- coding: utf-8 -*-

from math import log10

from PyQt5.QtCore import (Qt, pyqtSlot, QSize, QModelIndex, QItemSelection,
                          QItemSelectionModel, QItemSelectionRange)
from PyQt5.QtWidgets import (QTableView, QHeaderView, QAbstractItemView)
from PyQt5 import QtCore

from .. import models
from .. import widgets
from ._paging_view import PagingView
from ._constants import COLUMNS
from .model import TablePageItemModel
from ._image_view import EMImageItemDelegate


class ColumnsView(PagingView):
    """
    The ColumnsView class provides some functionality for show large numbers of
    items with simple paginate elements in columns view. """

    # For current row changed
    sigCurrentRowChanged = QtCore.pyqtSignal(int)
    # when the Table has been resized (oldSize, newSize)
    sigSizeChanged = QtCore.pyqtSignal(object, object)

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
        self._model = kwargs['model']
        PagingView.__init__(self, parent=parent,
                            pagingInfo=widgets.PagingInfo(1, 1),
                            **kwargs)
        self._selection = set()
        self._delegate = EMImageItemDelegate(self)
        self._pageItemModel = None
        self.setSelectionMode(kwargs.get('selectionMode',
                                         PagingView.SINGLE_SELECTION))
        self.setModel(model=self._model,
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
        self.sigSizeChanged.connect(self.__onSizeChanged)
        tv.setSelectionBehavior(QTableView.SelectRows)
        tv.setSelectionMode(QTableView.SingleSelection)
        tv.setSortingEnabled(True)
        tv.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        #tv.setStyleSheet(
        #    "QTableView#ColumnsViewTable::item:selected:!active{"
        #    "selection-background-color: red;}")  # palette(light);}")

        tv.resizeEvent = self.__tableViewResizeEvent
        tv.setModel(None)
        tv.setFocusPolicy(Qt.NoFocus)
        self._tableView = tv
        return tv

    def __connectSignals(self):
        """ Connects all signals related to the TablePageItemModel
        """
        if self._pageItemModel:
            self._pageBar.sigPageChanged.connect(
                self._pageItemModel.modelConfigChanged)
            self._pageBar.sigPageChanged.connect(self.__onCurrentPageChanged)
            self._pageItemModel.headerDataChanged.connect(
                self.__onHeaderDataChanged)

    def __disconnectSignals(self):
        """ Disconnects all signals related to the TablePageItemModel
        """
        if self._pageItemModel:
            self._pageBar.sigPageChanged.disconnect(
                self._pageItemModel.modelConfigChanged)
            self._pageBar.sigPageChanged.disconnect(self.__onCurrentPageChanged)
            self._pageItemModel.headerDataChanged.disconnect(
                self.__onHeaderDataChanged)

    def __tableViewResizeEvent(self, evt):
        """
        Reimplemented to receive QTableView resize events which are passed
        in the event parameter. Emits sigSizeChanged
        :param evt: The event
        """
        QTableView.resizeEvent(self._tableView, evt)
        self.sigSizeChanged.emit(evt.oldSize(), evt.size())

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
                self._pagingInfo.getPage(self._currentRow) + 1)
            self._pageBar.setPagingInfo(self._pagingInfo)

    def __setupDelegatesForColumns(self):
        """
        Sets the corresponding Delegate for all columns
        """
        # we have defined one delegate for the moment: ImageItemDelegate
        for i, colConfig in self._displayConfig.iterColumns():
            delegate = self._defaultDelegate
            if colConfig[models.RENDERABLE]:
                delegate = self._delegate
            self._tableView.setItemDelegateForColumn(i, delegate)

    def __updatePagingInfo(self):
        self._pagingInfo.numberOfItems = self._model.getRowsCount()
        self._pagingInfo.setPageSize(self.__calcPageSize())
        self._pagingInfo.currentPage = 1

    def __updateSelectionInView(self, page):
        """ Makes the current selection in the view """
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
        if self.isSingleSelection() or self.isNoSelection():
            self.__updateSelectionInView(self._pagingInfo.currentPage - 1)
        else:
            self._selection.clear()
            self.sigSelectionChanged.emit()

    @pyqtSlot(object, object)
    def __onSizeChanged(self, oldSize, newSize):
        """ Invoked when the table widget is resized """
        if not oldSize.height() == newSize.height():
            self._resizing = True
            self.__updatePageBar()
            self._resizing = False
            self.selectRow(self._currentRow)

    @pyqtSlot(int)
    def __onCurrentPageChanged(self, page):
        """
        Invoked when change current page. Emits sigCurrentRowChanged signal.
        1 is the index of the first page.
        """
        if not self._resizing:
            self._currentRow = (page - 1) * self._pagingInfo.pageSize
            if self.isSingleSelection():
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
            if self.isSingleSelection():
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

    @pyqtSlot(set)
    def changeSelection(self, selection):
        """ Invoked when the selection is changed """
        self._selection = selection
        self.__updateSelectionInView(self._pagingInfo.currentPage - 1)

    @pyqtSlot()
    def updatePage(self):
        """ Updates the visualization of the current page """
        self._pageItemModel.modelConfigChanged()
        self.__updateSelectionInView(self._pagingInfo.currentPage - 1)

    @pyqtSlot()
    def modelChanged(self):
        """Slot for model data changed notification """
        self.__updatePagingInfo()
        self._pageBar.setPagingInfo(self._pagingInfo)

        #  remove sort indicator from all columns
        self._tableView.horizontalHeader().setSortIndicator(-1,
                                                            Qt.AscendingOrder)
        self.updateViewConfiguration()
        s = self._tableView.verticalHeader().defaultSectionSize()
        self._pageItemModel.setIconSize(QSize(s, s))
        self.setupColumnsWidth()

    def setupVisibleColumns(self):
        """
        Hide the columns with visible property=True
        """
        for i, colConfig in self._displayConfig.iterColumns():
            if not colConfig[models.VISIBLE]:
                self._tableView.hideColumn(i)
            else:
                self._tableView.showColumn(i)

    def setupColumnsWidth(self):
        """ Setups the width for all columns """
        self._tableView.horizontalHeader().setStretchLastSection(True)
        self._tableView.resizeColumnsToContents()

    def updateViewConfiguration(self):
        """ Reimplementing from PagingView.
        Updates the columns configuration.
        """
        if self._pageItemModel is not None:
            self.setupVisibleColumns()
            self.__setupDelegatesForColumns()

    def setModel(self, model, displayConfig=None):
        """
        Sets the model for this view.
        Raise Exception when the model is None
        :param model:         (datavis.model.TableModel) The data model
        :param displayConfig: (datavis.model.TableModel) Input TableModel that
                              will control how the data fetched from the
                              TableModel will be displayed.
        """
        if model is None:
            raise Exception('Invalid model: None')

        self._selection.clear()
        self._currentRow = 0
        self._model = model
        self._displayConfig = displayConfig or model.createDefaultConfig()
        self._resizing = False
        if self._pageItemModel is None:
            self._pageItemModel = TablePageItemModel(
                model, self._pagingInfo, tableConfig=self._displayConfig,
                parent=self)
            self.__connectSignals()

            self._tableView.setModel(self._pageItemModel)
            sModel = self._tableView.selectionModel()
            sModel.currentRowChanged.connect(self.__onCurrentRowChanged)
            sModel.selectionChanged.connect(self.__onInternalSelectionChanged)
        else:
            self._pageItemModel.setModelConfig(tableModel=model,
                                               tableConfig=self._displayConfig,
                                               pagingInfo=self._pagingInfo)
        self.modelChanged()

    def clear(self):
        """ Clear the view """
        self.setModel(models.EmptyTableModel())

    def resetView(self):
        """ Reset the internal state of the view. """
        self._tableView.reset()
        if self._selection:
            self.__updateSelectionInView(self._pagingInfo.currentPage - 1)

    def getDisplayConfig(self):
        """ Returns the display configuration """
        return self._displayConfig

    def getViewType(self):
        """ Returns the view type """
        return COLUMNS

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

    def setIconSize(self, size):
        """
        Sets the icon size for renderable columns.
        size: (width, height) or QSize
        """
        if isinstance(size, QSize):
            w, h = size.width(), size.height()
            self._pageItemModel.setIconSize(size)
        else:
            w, h = size
            self._pageItemModel.setIconSize(QSize(w, h))

        config = self.getDisplayConfig()
        if config is not None:
            render = False
            for i, colConfig in config.iterColumns(renderable=True,
                                                   visible=True):
                if self.getColumnWidth(i) < w:
                    self.setColumnWidth(i, w)
                if not render:
                    render = True
            if render:
                self.setRowHeight(h)
            else:
                self.setRowHeight(25)
            self.__updatePageBar()
            self.__updateSelectionInView(self._pageBar.getCurrentPage() - 1)

    def getColumnWidth(self, column):
        """
        Returns the width for the given column.
        :param column: (int) The column index. First index is 0.
        """
        return self._tableView.columnWidth(column)

    def selectRow(self, row):
        """ Selects the given row """
        if 0 <= row < self._pagingInfo.numberOfItems:
            page = self._pagingInfo.getPage(row) + 1
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

    def getPreferredSize(self):
        """
        Returns a tuple (width, height), which represents
        the preferred dimensions to contain all the data
        """
        rowHeight = self._pageItemModel.headerData(0, Qt.Vertical,
                                                   Qt.SizeHintRole)
        rowHeight = 30 if rowHeight is None else rowHeight.height()
        a = (self._pageBar.height() if self._pageBar.isVisible() else 0) + 90
        h = rowHeight * self._model.getRowsCount() + a

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

    def getPageSize(self):
        """ Return the number of elements for page """
        return self._pagingInfo.pageSize


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
