#!/usr/bin/python
# -*- coding: utf-8 -*-


from PyQt5.QtCore import (Qt, pyqtSlot, QSize, QModelIndex, QItemSelection,
                          QItemSelectionModel, QItemSelectionRange)
from PyQt5.QtWidgets import QAbstractItemView, QListView

from PyQt5 import QtCore

from emqt5.widgets._delegates import AbstractView, EMImageItemDelegate
from ..utils import ImageManager

from random import sample as random_sample


class GalleryView(AbstractView):
    """
    The GalleryView class provides some functionality for show large numbers of
    items with simple paginate elements in gallery view.
    """

    sigCurrentRowChanged = QtCore.pyqtSignal(int)  # For current row changed
    sigPageSizeChanged = QtCore.pyqtSignal()
    sigListViewSizeChanged = QtCore.pyqtSignal()

    def __init__(self, parent, **kwargs):
        """
        kwargs:
         - imageManager: the ImageManager for internal read/manage
                          image operations.
        """
        AbstractView.__init__(self, parent=parent)
        self._pageSize = 0
        self._pRows = 0
        self._pCols = 0
        self._cellSpacing = 0
        self._imageManager = kwargs.get('imageManager') or ImageManager(50)
        self._selection = set()
        self._currentRow = 0
        self.__setupUI(**kwargs)
        self.setSelectionMode(kwargs.get('selection_mode',
                                         AbstractView.SINGLE_SELECTION))

    def __setupUI(self, **kwargs):
        self._listView = QListView(self)
        self._listView.setViewMode(QListView.IconMode)
        self._listView.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._listView.setSelectionMode(QAbstractItemView.SingleSelection)
        self._listView.setResizeMode(QListView.Adjust)
        self._listView.setSpacing(self._cellSpacing)
        self._listView.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._listView.setVerticalScrollMode(QAbstractItemView.ScrollPerItem)
        self._listView.setHorizontalScrollMode(QAbstractItemView.ScrollPerItem)
        self._listView.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._listView.setLayoutMode(QListView.Batched)
        self._listView.setBatchSize(500)
        self._listView.setMovement(QListView.Static)
        self._listView.setIconSize(QSize(32, 32))
        self._listView.setModel(None)
        self._listView.resizeEvent = self.__listViewResizeEvent
        self.sigListViewSizeChanged.connect(self.__onSizeChanged)
        self._delegate = EMImageItemDelegate(self)
        self._delegate.setImageManager(self._imageManager)
        self._mainLayout.insertWidget(0, self._listView)
        self._pageBar.sigPageChanged.connect(self.__onCurrentPageChanged)

    def __listViewResizeEvent(self, evt):
        """
        Reimplemented to receive QListView resize events which are passed
        in the event parameter. Emits sigListViewSizeChanged
        :param evt:
        """
        QListView.resizeEvent(self._listView, evt)
        self.sigListViewSizeChanged.emit()

    def __calcPageSize(self):
        """
        Calculate the number of items per page according to the size of the
        view area.
        """
        self._pageSize = 0

        size = self._listView.viewport().size()
        s = self._listView.iconSize()
        spacing = self._listView.spacing()

        if size.width() > 0 and size.height() > 0 \
                and s.width() > 0 and s.height() > 0:
            self._pCols = int((size.width() - spacing - 1) /
                              (s.width() + spacing))
            self._pRows = int((size.height() - 1) / (s.height() + spacing))
            # if size.width() < iconSize.width() pRows may be 0
            pRows = 1 if self._pRows == 0 else self._pRows
            pCols = 1 if self._pCols == 0 else self._pCols

            self._pageSize = pRows * pCols
        else:
            self._pRows = self._pCols = 0

    def __getPage(self, row):
        """
        Return the page where row are located or -1 if it can not be calculated
        """
        return int(row / self._pageSize) \
            if self._pageSize > 0 and row >= 0 else -1

    def __updateSelectionInView(self, page):
        """ Makes the current selection in the view """
        if self._model is not None:
            selModel = self._listView.selectionModel()
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

    @pyqtSlot()
    def __onSizeChanged(self):
        """ Invoked when the gallery widget is resized """
        self.__calcPageSize()
        if self._model:
            self._model.setupPage(self._pageSize,
                                  self.__getPage(self._currentRow))

    @pyqtSlot(int)
    def __onCurrentPageChanged(self, page):
        """ Invoked when change current page """
        if self._model is not None:
            size = self._model.getPageSize()
            self._currentRow = page * size
            self.sigCurrentRowChanged.emit(self._currentRow)

    @pyqtSlot(QModelIndex, QModelIndex)
    def __onCurrentRowChanged(self, current, previous):
        """ Invoked when current row change """
        if current.isValid():
            row = current.row()
            self._currentRow = row + self._pageSize * self._model.getPage()
            self.sigCurrentRowChanged.emit(self._currentRow)

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

    def setImageManager(self, imageManager):
        """ Setter for ImageManager"""
        self._imageManager = imageManager

    def setModel(self, model):
        """ Sets the model """
        self._listView.setModel(model)
        self._selection.clear()
        self._currentRow = 0
        AbstractView.setModel(self, model)
        if model:
            model.setupPage(self._pageSize, 0)
            self.setIconSize(self._listView.iconSize())
            sModel = self._listView.selectionModel()
            sModel.currentRowChanged.connect(self.__onCurrentRowChanged)
            sModel.selectionChanged.connect(self.__onInternalSelectionChanged)
            config = model.getTableViewConfig()
            self.setLabelIndexes(
                config.getIndexes('visible', True) if config else [])
            self.updateViewConfiguration()
        else:
            self.setLabelIndexes([])

    def resetGallery(self):
        self._listView.reset()
        if self._selection and self._model is not None:
            self.__updateSelectionInView(self._model.getPage())

    def setModelColumn(self, column):
        """ Holds the column in the model that is visible. """
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
        if self._model is not None:
            colConfig = self._model.getColumnConfig()
            if colConfig is not None:
                vIndexes = colConfig.getIndexes('visible', True)
                lSize = len(vIndexes)
                s = QSize(size[0], size[1])
                if lSize > 0:
                    maxWidth = 0
                    r = self._model.totalRowCount()
                    fontMetrics = self._listView.fontMetrics()
                    for i in random_sample(range(r), min(10, r)):
                        for j in vIndexes:
                            text = ' %s = %s ' % (
                                self._model.getColumnConfig(j).getName(),
                                str(self._model.getTableData(i, j)))
                            # TODO [HV]:  fontMetrics.width(text) cause error
                            w = fontMetrics.boundingRect(text).width() # len(text) * 7.3
                            maxWidth = max(maxWidth, w)
                    s.setWidth(max(s.width(), maxWidth))
                    s.setHeight(s.height() + lSize * 16)
        self._listView.setIconSize(s)
        self.__calcPageSize()
        if self._model is not None:
            self._model.setIconSize(s)
            self._model.setupPage(self._pageSize, self._model.getPage())

        self.sigPageSizeChanged.emit()

    def setImageManager(self, imageManager):
        """ Sets the image manager """
        self._imageManager = imageManager
        self._delegate.setImageManager(imageManager)

    def selectRow(self, row):
        """ Selects the given row """
        if self._model is not None:
            page = self.__getPage(row)
            if row in range(0, self._model.totalRowCount()):
                self._currentRow = row
                if self._selectionMode == AbstractView.SINGLE_SELECTION:
                    self._selection.clear()
                    self._selection.add(self._currentRow)
                self._model.loadPage(page)
            self.__updateSelectionInView(page)

    def currentRow(self):
        """ Returns the current selected row """
        if self._model is None:
            return -1
        r = self._listView.currentIndex().row()
        return r if r <= 0 else r + self._pageSize * self._model.getPage()

    def getViewDims(self):
        """ Returns a tuple (rows, columns) with the data size """
        if self._model is None or self._pCols == 0:
            return 0, 0
        size = self._model.rowCount()

        if size <= self._pCols:
            return 1, size

        r = size % self._pCols

        return int(size / self._pCols) + (1 if r > 0 else 0), self._pCols

    def getPreferedSize(self):
        """
        Returns a tuple (width, height), which represents
        the preferred dimensions to contain all the data
        """
        if self._model is None or self._model.rowCount() == 0:
            return 0, 0

        n = self._model.totalRowCount()
        s = self._listView.iconSize()
        spacing = self._listView.spacing()
        size = QSize(int(n**0.5) * (spacing + s.width()) + spacing,
                     int(n**0.5) * (spacing + s.height()) + spacing)

        w = int(size.width() / (spacing + s.width()))
        n = self._model.totalRowCount()
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
        AbstractView.setSelectionMode(self, selectionMode)
        if selectionMode == self.SINGLE_SELECTION:
            self._listView.setSelectionMode(QAbstractItemView.SingleSelection)
        elif selectionMode == self.EXTENDED_SELECTION:
            self._listView.setSelectionMode(
                QAbstractItemView.ExtendedSelection)
        elif selectionMode == self.MULTI_SELECTION:
            self._listView.setSelectionMode(QAbstractItemView.MultiSelection)
        else:
            AbstractView.setSelectionMode(self, AbstractView.NO_SELECTION)
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

    def getListView(self):
        """ Return the QListView widget used to display the items """
        return self._listView

    def setLabelIndexes(self, labels):
        """
        Initialize the indexes of the columns that will be displayed as text
        below the images
        labels (list)
        """
        self._delegate.setLabelIndexes(labels)

    def updateViewConfiguration(self):
        """ Update the columns configuration """
        if self._model is not None:
            indexes = self._model.getColumnConfig().getIndexes('renderable',
                                                               True)
            if indexes:
                self._listView.setModelColumn(indexes[0])
                self._listView.setItemDelegateForColumn(indexes[0],
                                                        self._delegate)
