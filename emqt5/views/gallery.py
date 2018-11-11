#!/usr/bin/python
# -*- coding: utf-8 -*-


from PyQt5.QtCore import Qt, pyqtSlot, QSize, QModelIndex
from PyQt5.QtWidgets import QAbstractItemView, QListView, QApplication

from PyQt5 import QtCore

from .model import ImageCache
from .base import AbstractView, EMImageItemDelegate


class GalleryView(AbstractView):
    """
    The GalleryView class provides some functionality for show large numbers of
    items with simple paginate elements in gallery view.
    """

    sigCurrentRowChanged = QtCore.pyqtSignal(int)  # For current row changed
    sigPageSizeChanged = QtCore.pyqtSignal()
    sigListViewSizeChanged = QtCore.pyqtSignal()

    def __init__(self, parent, **kwargs):
        AbstractView.__init__(self, parent=parent)
        self._pageSize = 0
        self._pRows = 0
        self._pCols = 0
        self._cellSpacing = 0
        self._imgCache = ImageCache(50)
        self._thumbCache = ImageCache(500, (100, 100))
        self.__setupUI(**kwargs)

    def __setupUI(self, **kwargs):
        self._listView = QListView(self)
        self._listView.setViewMode(QListView.IconMode)
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
        self._delegate.setImageCache(self._thumbCache)
        self._mainLayout.insertWidget(0, self._listView)

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

    @pyqtSlot()
    def __onSizeChanged(self):
        """ Invoked when the gallery widget is resized """
        self.__calcPageSize()
        if self._model:
            index = self._listView.currentIndex()
            row = index.row() if index and index.isValid() else 0
            self._model.setupPage(self._pageSize, self.__getPage(row))

        self.sigPageSizeChanged.emit()

    @pyqtSlot(QModelIndex, QModelIndex)
    def __onCurrentRowChanged(self, current, previous):
        """ Invoked when current row change """
        if current.isValid():
            row = current.row()
            self.sigCurrentRowChanged.emit(
                row + self._pageSize * self._model.getPage())

    def setModel(self, model):
        """ Sets the model """
        self._listView.setModel(model)
        AbstractView.setModel(self, model)
        if model:
            model.setIconSize(self._listView.iconSize())
            model.setupPage(self._pageSize, 0)
            self._listView.selectionModel().currentRowChanged.connect(
                self.__onCurrentRowChanged)

    def setModelColumn(self, column):
        """ Holds the column in the model that is visible. """
        self._listView.setModelColumn(column)
        self._listView.setItemDelegateForColumn(column, self._delegate)

    def setIconSize(self, size):
        """
        Sets the icon size.
        size: (width, height)
        """
        s = QSize(size[0], size[1])
        self._listView.setIconSize(s)
        self.__calcPageSize()
        if self._model:
            self._model.setupPage(self._pageSize, self._model.getPage())
            self._model.setIconSize(s)

        self.sigPageSizeChanged.emit()

    def setImageCache(self, imgCache):
        """ Sets the image cache """
        self._imgCache = imgCache

    def setThumbCache(self, thumbCache):
        self._thumbCache = thumbCache
        self._delegate.setImageCache(thumbCache)

    def selectRow(self, row):
        """ Selects the given row """
        if self._model:
            if not row == self.currentRow() \
                    and row in range(0, self._model.totalRowCount()):
                page = self.__getPage(row)
                self._model.loadPage(page)
            index = self._model.createIndex(
                0 if row == 0 else row % self._pageSize,
                self._listView.modelColumn())

            self._listView.setCurrentIndex(index)

    def currentRow(self):
        """ Returns the current selected row """
        if self._model is None:
            return -1
        r = self._listView.currentIndex().row()
        return r if r <= 0 else r + self._pageSize * self._model.getPage()

    def getViewDims(self):
        """ Returns a tuple (rows, columns) with the data size """
        return self._pRows, self._pCols

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
