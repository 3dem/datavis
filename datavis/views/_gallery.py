#!/usr/bin/python
# -*- coding: utf-8 -*-

from random import sample as random_sample

import PyQt5.QtCore as qtc
import PyQt5.QtWidgets as qtw

from .. import models
from .. import widgets
from ._paging_view import PagingView
from ._constants import GALLERY
from .model import TablePageItemModel
from ._image_view import EMImageItemDelegate


class GalleryView(PagingView):
    """
    The GalleryView class provides some functionality for show large numbers of
    items with simple paginate elements in gallery view.
    """
    sigCurrentRowChanged = qtc.pyqtSignal(int)  # For current row changed
    sigPageSizeChanged = qtc.pyqtSignal()  # Signal for page size changed
    sigSizeChanged = qtc.pyqtSignal(object, object)

    def __init__(self, parent=None, **kwargs):
        """
        Constructs an GalleryView.
        kwargs:
            model:          The data model
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
        PagingView.__init__(self, parent=parent,
                            pagingInfo=widgets.PagingInfo(1, 1),
                            **kwargs)
        self._selection = set()
        self._delegate = EMImageItemDelegate(self)
        self._pageItemModel = None
        self._cellSpacing = kwargs.get('cellSpacing', 5)
        self._listView.setSpacing(self._cellSpacing)
        self.setSelectionMode(kwargs.get('selectionMode',
                                         PagingView.SINGLE_SELECTION))
        # When the icon size is in percent units,
        # we need to setIconSize in each setModel
        self._percentIconSize = None
        self.setModel(model=kwargs['model'],
                      displayConfig=kwargs.get('displayConfig'))
        w, h = kwargs.get('iconSize', (100, 100))
        self.setIconSize(qtc.QSize(w, h))

    def _createContentWidget(self):
        lv = qtw.QListView(self)
        lv.setViewMode(qtw.QListView.IconMode)
        lv.setSelectionBehavior(qtw.QAbstractItemView.SelectRows)
        lv.setSelectionMode(qtw.QAbstractItemView.SingleSelection)
        lv.setResizeMode(qtw.QListView.Adjust)
        lv.setVerticalScrollBarPolicy(qtc.Qt.ScrollBarAlwaysOff)
        lv.setVerticalScrollMode(qtw.QAbstractItemView.ScrollPerItem)
        lv.setHorizontalScrollMode(qtw.QAbstractItemView.ScrollPerItem)
        lv.setHorizontalScrollBarPolicy(qtc.Qt.ScrollBarAlwaysOff)
        lv.setLayoutMode(qtw.QListView.Batched)
        lv.setBatchSize(500)
        lv.setMovement(qtw.QListView.Static)
        lv.setIconSize(qtc.QSize(32, 32))
        lv.setModel(None)
        lv.resizeEvent = self.__listViewResizeEvent
        self.sigSizeChanged.connect(self.__onSizeChanged)
        self._listView = lv
        return lv

    def __connectSignals(self):
        """ Connects all signals related to the TablePageItemModel
        """
        if self._pageItemModel:
            self._pageBar.sigPageChanged.connect(
                self._pageItemModel.modelConfigChanged)
            self._pageBar.sigPageChanged.connect(self.__onCurrentPageChanged)

    def __disconnectSignals(self):
        """ Disconnects all signals related to the TablePageItemModel
        """
        if self._pageItemModel:
            self._pageBar.sigPageChanged.disconnect(
                self._pageItemModel.modelConfigChanged)
            self._pageBar.sigPageChanged.disconnect(self.__onCurrentPageChanged)

    def __listViewResizeEvent(self, evt):
        """
        Reimplemented to receive qtw.QListView resize events which are passed
        in the event parameter. Emits sigListViewSizeChanged
        :param evt:
        """
        qtw.QListView.resizeEvent(self._listView, evt)
        self.sigSizeChanged.emit(evt.oldSize(), evt.size())

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
                sel = qtc.QItemSelection()
                for row in range(page * pageSize, (page + 1) * pageSize):
                    if row in self._selection:
                        sel.append(
                            qtc.QItemSelectionRange(m.index(row % pageSize, 0),
                                                m.index(row % pageSize,
                                                        m.columnCount() - 1)))
                allSel = qtc.QItemSelection(m.index(0, 0),
                                        m.index(pageSize - 1,
                                                m.columnCount() - 1))
                selModel.select(allSel, qtc.QItemSelectionModel.Deselect)
                if not sel.isEmpty():
                    selModel.select(sel, qtc.QItemSelectionModel.Select)

    def __updatePagingInfo(self):
        """"""
        self._pagingInfo.numberOfItems = self._model.getRowsCount()
        rows, cols = self.__calcPageSize()
        self._pagingInfo.setPageSize(rows * cols)
        self._pagingInfo.setCurrentPage(1)

    @qtc.pyqtSlot(object, object)
    def __onSizeChanged(self, oldSize, newSize):
        """ Invoked when the gallery widget is resized """
        self.__updatePageBar()
        self.selectRow(self._currentRow)

    @qtc.pyqtSlot(int)
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

    @qtc.pyqtSlot(qtc.QModelIndex, qtc.QModelIndex)
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

    @qtc.pyqtSlot(qtc.QItemSelection, qtc.QItemSelection)
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

    @qtc.pyqtSlot(set)
    def changeSelection(self, selection):
        """ Invoked when the selection is changed """
        self._selection = selection
        self.__updateSelectionInView(self._pagingInfo.currentPage - 1)

    @qtc.pyqtSlot()
    def modelChanged(self):
        """Slot for model data changed notification """
        self.__updatePagingInfo()
        self._pageBar.setPagingInfo(self._pagingInfo)
        tableConfig = self._pageItemModel.getDisplayConfig()
        indexes = [i for i, c in tableConfig.iterColumns(renderable=True)]
        self.setModelColumn(indexes[0] if indexes else 0)
        if self._percentIconSize is None:
            self.setIconSize(self._listView.iconSize())
        else:
            self.setIconSize(self._percentIconSize)

        self.updateViewConfiguration()

    def setModel(self, model, displayConfig=None, minMax=None):
        """ Sets the model """
        if model is None:
            raise Exception('Invalid model: None')
        self._selection.clear()
        self._currentRow = 0
        self._model = model

        if displayConfig is None:
            displayConfig = model.createDefaultConfig()

        labels = None
        for i, cc in displayConfig.iterColumns():
            if labels is None:  # same labels for all columns
                labels = cc.getLabels()
            else:
                cc.setLabels(labels)

        if self._pageItemModel is None:
            self._pageItemModel = TablePageItemModel(model, self._pagingInfo,
                                                     tableConfig=displayConfig,
                                                     parent=self)
            self.__connectSignals()

            self._listView.setModel(self._pageItemModel)
            sModel = self._listView.selectionModel()
            sModel.currentRowChanged.connect(self.__onCurrentRowChanged)
            sModel.selectionChanged.connect(self.__onInternalSelectionChanged)
        else:
            self._pageItemModel.setModelConfig(tableModel=model,
                                               tableConfig=displayConfig,
                                               pagingInfo=self._pagingInfo)
        self._delegate.setLevels(minMax)

        self.modelChanged()

    def getModel(self):
        """ Returns the current model """
        return self._model

    def getViewType(self):
        """ Returns the view type """
        return GALLERY

    def getDisplayConfig(self):
        """ Returns the display configuration """
        if self._pageItemModel is not None:
            return self._pageItemModel.getDisplayConfig()
        return None

    def clear(self):
        """ Clear the view """
        self.setModel(models.EmptyTableModel())

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

    def getModelColumn(self):
        """ Returns the column in the model that is visible """
        return self._listView.modelColumn()

    def setIconSize(self, size):
        """
        Sets the icon size.
        size: (width, height), qtc.QSize or int in % units
        """
        if isinstance(size, tuple):
            s = qtc.QSize(size[0], size[1])
            self._percentIconSize = None
        elif isinstance(size, int) or isinstance(size, float):  # in % units
            self._percentIconSize = size
            x, y = self._model.getDim()
            x = int(x * (size / 100.0))
            y = int(y * (size / 100.0))
            s = qtc.QSize(x, y)
            size = x, y
        elif isinstance(size, qtc.QSize):
            s = size
            size = size.width(), size.height()
            self._percentIconSize = None
        else:
            raise Exception("Invalid icon size.")

        self._pageItemModel.setIconSize(qtc.QSize(s))
        dispConfig = self._pageItemModel.getDisplayConfig()
        if dispConfig is not None:
            m = self._pageItemModel
            cc = dispConfig.getColumnConfig(0)
            lSize = len(cc.getLabels()) if cc is not None else 0
            s = qtc.QSize(size[0], size[1])
            margin = 10
            if lSize > 0:
                maxWidth = 0
                r = m.rowCount()
                fontMetrics = self._listView.fontMetrics()

                for i in random_sample(range(r), min(10, r)):
                    index = m.createIndex(i, 0)
                    labels = m.data(index, widgets.LABEL_ROLE)
                    for text in labels:
                        w = fontMetrics.boundingRect(text).width() + margin
                        maxWidth = max(maxWidth, w)
                s.setWidth(max(s.width(), maxWidth))
                s.setHeight(s.height() + lSize * 16)
        self._listView.setIconSize(s)
        self._pageItemModel.setIconSize(s)
        self.__updatePageBar()
        self.__updateSelectionInView(self._pageBar.getCurrentPage() - 1)
        self.sigPageSizeChanged.emit()

    def setImageItemDelegate(self, delegate):
        """ Set the ImageItemDelegate, responsible for rendering each cell """
        self._delegate = delegate

    def getImageItemDelegate(self):
        """ Return the ImageItemDelegate """
        return self._delegate

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

    def getPreferredSize(self):
        """
        Returns a tuple (width, height), which represents
        the preferred dimensions to contain all the data
        """
        n = self._model.getRowsCount()
        s = self._listView.iconSize()
        spacing = self._listView.spacing()
        size = qtc.QSize(int(n**0.5) * (spacing + s.width()) + spacing,
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
            self._listView.setSelectionMode(qtw.QAbstractItemView.SingleSelection)
        elif selectionMode == self.EXTENDED_SELECTION:
            self._listView.setSelectionMode(
                qtw.QAbstractItemView.ExtendedSelection)
        elif selectionMode == self.MULTI_SELECTION:
            self._listView.setSelectionMode(qtw.QAbstractItemView.MultiSelection)
        else:
            PagingView.setSelectionMode(self, PagingView.NO_SELECTION)
            self._listView.setSelectionMode(qtw.QAbstractItemView.NoSelection)

    def setSelectionBehavior(self, selectionBehavior):
        """
        This property holds which selection behavior the view uses.
        This property holds whether selections are done in terms of
        single items, rows or columns.

        Possible values:
                        SELECT_ITEMS, SELECT_ROWS, SELECT_COLUMNS
        """
        if selectionBehavior == self.SELECT_ITEMS:
            self._listView.setSelectionBehavior(qtw.QAbstractItemView.SelectItems)
        elif selectionBehavior == self.SELECT_COLUMNS:
            self._listView.setSelectionBehavior(
                qtw.QAbstractItemView.SelectColumns)
        elif selectionBehavior == self.SELECT_ROWS:
            self._listView.setSelectionBehavior(qtw.QAbstractItemView.SelectRows)
