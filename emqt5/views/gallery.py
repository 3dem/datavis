#!/usr/bin/python
# -*- coding: utf-8 -*-


from PyQt5.QtCore import Qt, pyqtSlot, QSize, QModelIndex
from PyQt5.QtWidgets import QAbstractItemView, QListView

from PyQt5 import QtCore

from .model import ImageCache
from .base import AbstractView, EMImageItemDelegate


class _QListViewResizable(QListView):
    """
    Just overwrite the resizeEvent to fire a signal
    """
    sigSizeChanged = QtCore.pyqtSignal()  # when the widget has been resized

    def __init__(self, parent=None):
        QListView.__init__(self, parent)

    def resizeEvent(self, evt):
        """
        Reimplemented from TableWidget
        """
        QListView.resizeEvent(self, evt)
        self.sigSizeChanged.emit()


class GalleryView(AbstractView):
    """
    The GalleryView class provides some functionality for show large numbers of
    items with simple paginate elements in gallery view.
    """

    sigCurrentRowChanged = QtCore.pyqtSignal(int)  # For current row changed

    def __init__(self, parent=None):
        AbstractView.__init__(self, parent)
        self._pageSize = 0
        self._imgCache = ImageCache(50)
        self.__setupUI()

    def __setupUI(self):
        self._listView = _QListViewResizable(self)
        self._listView.sigSizeChanged.connect(self.__onSizeChanged)
        self._listView.setViewMode(QListView.IconMode)
        self._listView.setResizeMode(QListView.Adjust)
        self._listView.setSpacing(5)
        self._listView.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._listView.setVerticalScrollMode(QAbstractItemView.ScrollPerItem)
        self._listView.setHorizontalScrollMode(QAbstractItemView.ScrollPerItem)
        self._listView.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._listView.setLayoutMode(QListView.Batched)
        self._listView.setBatchSize(500)
        self._listView.setMovement(QListView.Static)
        self._listView.setIconSize(QSize(32, 32))
        self._listView.setModel(None)
        self._delegate = EMImageItemDelegate(self)
        self._delegate.setImageCache(self._imgCache)
        self._mainLayout.insertWidget(0, self._listView)

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
            pCols = int((size.width() - spacing - 1) / (s.width() + spacing))
            pRows = int((size.height() - 1) / (s.height() + spacing))
            # if size.width() < iconSize.width() pRows may be 0
            if pRows == 0:
                pRows = 1
            if pCols == 0:
                pCols = 1

            self._pageSize = pRows * pCols

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

    def setImageCache(self, imgCache):
        """ Sets the image cache """
        self._imgCache = imgCache
        self._delegate.setImageCache(imgCache)

    def selectRow(self, row):
        """ Selects the given row """
        if self._model and row in range(0, self._model.totalRowCount()):
            page = self.__getPage(row)
            self._model.loadPage(page)
            index = self._model.createIndex(
                0 if row == 0 else row % self._pageSize,
                self._listView.modelColumn())

            self._listView.setCurrentIndex(index)
