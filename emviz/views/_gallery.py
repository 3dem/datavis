#!/usr/bin/python
# -*- coding: utf-8 -*-

from random import sample as random_sample

from PyQt5.QtCore import (Qt, pyqtSlot, QSize, QModelIndex, QItemSelection,
                          QItemSelectionModel, QItemSelectionRange)
from PyQt5.QtWidgets import QAbstractItemView, QListView
from PyQt5 import QtCore

from emviz.widgets import EMImageItemDelegate, PagingInfo
from emviz.models import RENDERABLE
from ._paging_view import PagingView
from .model import TablePageItemModel


class GalleryView(PagingView):
    """
    The GalleryView class provides some functionality for show large numbers of
    items with simple paginate elements in gallery view.
    """
    sigCurrentRowChanged = QtCore.pyqtSignal(int)  # For current row changed
    sigPageSizeChanged = QtCore.pyqtSignal()  # Signal for page size changed
    sigGallerySizeChanged = QtCore.pyqtSignal(object, object)

    def __init__(self, parent=None, **kwargs):
        """
        Constructs an GalleryView.
        kwargs:
         model:             The data model
            displayConfig:  Input TableModel that will control how the data
                            fetched from the TableModel will be displayed.
                            displayConfig can be None, in which case the model
                            will be taken as displayConfig.
            selectionMode:  (int) SINGLE_SELECTION(default), EXTENDED_SELECTION,
                            MULTI_SELECTION or NO_SELECTION
            cellSpacing:    (int) The cell spacing
            iconSize:       (tuple) The icon size (width, height).
                            Default value: (100, 100)
        """
        PagingView.__init__(self, parent=parent, pagingInfo=PagingInfo(1, 1),
                            **kwargs)
        self._selection = set()
        self._delegate = EMImageItemDelegate(self)
        self._pageItemModel = None
        self._cellSpacing = kwargs.get('cellSpacing', 5)
        self._listView.setSpacing(self._cellSpacing)
        self.setSelectionMode(kwargs.get('selectionMode',
                                         PagingView.SINGLE_SELECTION))
        self.setModel(model=kwargs['model'],
                      displayConfig=kwargs.get('displayConfig'))
        w, h = kwargs.get('iconSize', (100, 100))
        self.setIconSize(QSize(w, h))

    def _createContentWidget(self):
        lv = QListView(self)
        lv.setViewMode(QListView.IconMode)
        lv.setSelectionBehavior(QAbstractItemView.SelectRows)
        lv.setSelectionMode(QAbstractItemView.SingleSelection)
        lv.setResizeMode(QListView.Adjust)
        lv.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        lv.setVerticalScrollMode(QAbstractItemView.ScrollPerItem)
        lv.setHorizontalScrollMode(QAbstractItemView.ScrollPerItem)
        lv.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        lv.setLayoutMode(QListView.Batched)
        lv.setBatchSize(500)
        lv.setMovement(QListView.Static)
        lv.setIconSize(QSize(32, 32))
        lv.setModel(None)
        lv.resizeEvent = self.__listViewResizeEvent
        self.sigGallerySizeChanged.connect(self.__onSizeChanged)
        self._listView = lv
        return lv

    def __connectSignals(self):
        """ Connects all signals related to the TablePageItemModel
        """
        if self._pageItemModel:
            self._pageBar.sigPageChanged.connect(
                self._pageItemModel.pageConfigChanged)
            self._pageBar.sigPageChanged.connect(self.__onCurrentPageChanged)

    def __disconnectSignals(self):
        """ Disconnects all signals related to the TablePageItemModel
        """
        if self._pageItemModel:
            self._pageBar.sigPageChanged.disconnect(
                self._pageItemModel.pageConfigChanged)
            self._pageBar.sigPageChanged.disconnect(self.__onCurrentPageChanged)

    def __listViewResizeEvent(self, evt):
        """
        Reimplemented to receive QListView resize events which are passed
        in the event parameter. Emits sigListViewSizeChanged
        :param evt:
        """
        QListView.resizeEvent(self._listView, evt)
        self.sigGallerySizeChanged.emit(evt.oldSize(), evt.size())

    def __calcPageSize(self):
        """
        Calculate the number of items per page according to the size of the
        view area. Returns a tuple (rows, columns)
        """
        size = self._listView.viewport().size()
        s = self._listView.iconSize()
        spacing = self._listView.spacing()

        if size.width() > 0 and size.height() > 0 \
                and s.width() > 0 and s.height() > 0:
            cols = int((size.width() - spacing - 1) / (s.width() + spacing))
            rows = int((size.height() - 1) / (s.height() + spacing))
            # if size.width() < iconSize.width() pRows may be 0
            if rows == 0:
                rows = 1
            if cols == 0:
                cols = 1

            return rows, cols
        else:
            return 1, 1

    def __getPage(self, row):
        """
        Return the page where row are located or -1 if it can not be calculated
        :param row: (int) The row index. 0 is the first
        :return:    (int) The page index. 0 is the first
        """
        return int(row / self._pagingInfo.pageSize) \
            if self._pagingInfo.pageSize > 0 and row >= 0 else -1

    def __updatePageBar(self):
        """Updates the PageBar paging settings """
        rows, cols = self.__calcPageSize()
        rows *= cols
        if not rows == self._pagingInfo.pageSize:
            self._pagingInfo.setPageSize(rows)
            self._pagingInfo.setCurrentPage(
                self.__getPage(self._currentRow) + 1)
            self._pageBar.setPagingInfo(self._pagingInfo)

    def __updateSelectionInView(self, page):
        """ Makes the current selection in the view """
        if self._model is not None:
            selModel = self._listView.selectionModel()
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

    @pyqtSlot(object, object)
    def __onSizeChanged(self, oldSize, newSize):
        """ Invoked when the gallery widget is resized """
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

    def setModel(self, model, displayConfig=None):
        """ Sets the model """
        if model is None:
            raise Exception('Invalid model: None')
        self._selection.clear()
        self._currentRow = 0
        self.__disconnectSignals()
        self._model = model
        self._pagingInfo.numberOfItems = model.getRowsCount()
        rows, cols = self.__calcPageSize()
        self._pagingInfo.setPageSize(rows * cols)
        self._pagingInfo.setCurrentPage(1)
        self._pageItemModel = TablePageItemModel(model, self._pagingInfo,
                                                 tableConfig=displayConfig,
                                                 parent=self)
        self.__connectSignals()

        self._listView.setModel(self._pageItemModel)
        sModel = self._listView.selectionModel()
        sModel.currentRowChanged.connect(self.__onCurrentRowChanged)
        sModel.selectionChanged.connect(self.__onInternalSelectionChanged)
        self._pageBar.setPagingInfo(self._pagingInfo)
        self.setIconSize(self._listView.iconSize())
        #  FIXME[phv] Review. Initialize the indexes of the columns that will be
        #             displayed as text below the images.
        #config = displayConfig or model
        #self.setLabelIndexes(
        #    [i for i, c in config.iterColumns(**{VISIBLE: True})])
        self.updateViewConfiguration()

    def getModel(self):
        """ Returns the current model """
        return self._model

    def resetView(self):
        """
        Reset the internal state of the view.
        """
        self._listView.reset()
        if self._selection:
            self.__updateSelectionInView(self._pagingInfo.currentPage - 1)

    def setModelColumn(self, column):
        """
        Holds the column in the model that is visible.
        :param column: (int) Column index. 0 is the first index.
        """
        self._listView.setModelColumn(column)
        self._listView.setItemDelegateForColumn(column, self._delegate)

    def setIconSize(self, size):
        """
        Sets the icon size.
        size: (width, height) or QSize
        """
        if not isinstance(size, QSize):
            s = QSize(size[0], size[1])
        else:
            s = size
            size = size.width(), size.height()
        dispConfig = self._pageItemModel.getDisplayConfig()
        if dispConfig is not None:
            vIndexes = self._delegate.getLabelIndexes()
            # FIXME[phv] Review. Initialize the indexes of the columns that will
            # be displayed as text below the images.
            #vIndexes = [(i, c) for i, c in dispConfig.iterColumns(
            #    **{VISIBLE: True})]
            lSize = len(vIndexes)
            s = QSize(size[0], size[1])
            if lSize > 0:
                maxWidth = 0
                r = self._model.getRowsCount()
                fontMetrics = self._listView.fontMetrics()
                for i in random_sample(range(r), min(10, r)):
                    for j, c in vIndexes:
                        text = ' %s = %s ' % (
                            c.getLabel(),
                            str(self._model.getValue(i, j)))
                        w = fontMetrics.boundingRect(text).width()
                        maxWidth = max(maxWidth, w)
                s.setWidth(max(s.width(), maxWidth))
                s.setHeight(s.height() + lSize * 16)
        self._listView.setIconSize(s)
        self._pageItemModel.setIconSize(s)
        self.__updatePageBar()
        self.sigPageSizeChanged.emit()

    def selectRow(self, row):
        """ Selects the given row """
        if 0 <= row < self._pagingInfo.numberOfItems:
            page = self.__getPage(row) + 1
            if not page == self._pagingInfo.currentPage:
                self._pageBar.setCurrentPage(page)

            if self._selectionMode == PagingView.SINGLE_SELECTION:
                self._selection.clear()
                self._selection.add(row)

            self._currentRow = row
            self.__updateSelectionInView(page - 1)
            self.sigCurrentRowChanged.emit(row)

    def getCurrentRow(self):
        """ Returns the current selected row """
        return self._currentRow

    def getViewDims(self):
        """ Returns a tuple (rows, columns) with the data size """
        size = self._model.getRowsCount()
        rows, cols = self.__calcPageSize()
        if size <= cols:
            return 1, size

        r = size % cols

        return int(size / cols) + (1 if r > 0 else 0), cols

    def getPreferedSize(self):
        """
        Returns a tuple (width, height), which represents
        the preferred dimensions to contain all the data
        """
        n = self._model.getRowsCount()
        s = self._listView.iconSize()
        spacing = self._listView.spacing()
        size = QSize(int(n**0.5) * (spacing + s.width()) + spacing,
                     int(n**0.5) * (spacing + s.height()) + spacing)

        w = int(size.width() / (spacing + s.width()))
        c = int(n / w)
        rest = n % w

        if c == 0:
            w = n * (spacing + s.width())
            h = 2 * spacing + s.height()
        else:
            w = w * (spacing + s.width()) + spacing
            h = (c + (1 if rest > 0 else 0)) * (spacing + s.height()) + spacing

        return w, h + (self._pageBar.height()
                       if self._pageBar.isVisible() else 0)

    def setSelectionMode(self, selectionMode):
        """
        Indicates how the view responds to user selections:
        SINGLE_SELECTION, EXTENDED_SELECTION, MULTI_SELECTION
        """
        PagingView.setSelectionMode(self, selectionMode)
        if selectionMode == self.SINGLE_SELECTION:
            self._listView.setSelectionMode(QAbstractItemView.SingleSelection)
        elif selectionMode == self.EXTENDED_SELECTION:
            self._listView.setSelectionMode(
                QAbstractItemView.ExtendedSelection)
        elif selectionMode == self.MULTI_SELECTION:
            self._listView.setSelectionMode(QAbstractItemView.MultiSelection)
        else:
            PagingView.setSelectionMode(self, PagingView.NO_SELECTION)
            self._listView.setSelectionMode(QAbstractItemView.NoSelection)

    def setSelectionBehavior(self, selectionBehavior):
        """
        This property holds which selection behavior the view uses.
        This property holds whether selections are done in terms of
        single items, rows or columns.

        Possible values:
                        SELECT_ITEMS, SELECT_ROWS, SELECT_COLUMNS
        """
        if selectionBehavior == self.SELECT_ITEMS:
            self._listView.setSelectionBehavior(QAbstractItemView.SelectItems)
        elif selectionBehavior == self.SELECT_COLUMNS:
            self._listView.setSelectionBehavior(
                QAbstractItemView.SelectColumns)
        elif selectionBehavior == self.SELECT_ROWS:
            self._listView.setSelectionBehavior(QAbstractItemView.SelectRows)

    def setLabelIndexes(self, labels):
        """
        Initialize the indexes of the columns that will be displayed as text
        below the images.
        :param labels: (list) The column indexes
        """
        self._delegate.setLabelIndexes(labels)

    def updateViewConfiguration(self):
        """ Update the columns configuration """
        d = self._pageItemModel.getDisplayConfig()
        indexes = [i for i, c in d.iterColumns(**{RENDERABLE: True})]
        if indexes:
            self._listView.setModelColumn(indexes[0])
            self._listView.setItemDelegateForColumn(indexes[0],
                                                    self._delegate)
