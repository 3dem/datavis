#!/usr/bin/python
# -*- coding: utf-8 -*-


from PyQt5.QtCore import Qt, pyqtSlot, QModelIndex
from PyQt5.QtWidgets import QTableView, QSplitter
from PyQt5.QtGui import QStandardItemModel, QStandardItem

from PyQt5 import QtCore

from .model import ImageCache, X_AXIS, Y_AXIS, Z_AXIS
from .base import AbstractView
from emqt5.utils import EmPath, parseImagePath, ImageRef
from .image_view import ImageView


class ItemsView(AbstractView):
    """
    The Items class provides functionality for show large numbers of
    items with simple paginate elements in items view """

    sigCurrentRowChanged = QtCore.pyqtSignal(int)  # For current row changed

    def __init__(self, parent, **kwargs):
        AbstractView.__init__(self, parent)
        self._column = 0
        self._row = 0
        self._selection = set()
        self._disableFitToSize = False
        self._imgCache = ImageCache(50)
        self._imageRef = ImageRef()
        self.__setupUI(**kwargs)

    def __setupUI(self, **kwargs):
        self._splitter = QSplitter(self)
        self._splitter.setOrientation(Qt.Horizontal)
        self._itemsViewTable = QTableView(self._splitter)
        self._itemsViewTable.setModel(QStandardItemModel(self._itemsViewTable))
        self._imageView = ImageView(self._splitter, **kwargs)
        self._mainLayout.insertWidget(0, self._splitter)

    def __loadItem(self, row, col):
        """ Show the item at (row,col)"""
        self._imageView.clear()
        model = self._itemsViewTable.model()
        model.clear()
        if self._model and row in range(0, self._model.totalRowCount()) and \
                col in range(0, self._model.columnCount()):
            vLabels = []
            for i in range(0, self._model.columnCount()):
                item = QStandardItem()
                item.setData(self._model.getTableData(row, i),
                             Qt.DisplayRole)
                if i == col and self._model.getColumnConfig(col)['renderable']:
                    imgPath = self._model.getTableData(row, i)
                    imgRef = parseImagePath(imgPath, self._imageRef)
                    if imgRef is not None:
                        if imgRef.imageType & \
                                ImageRef.SINGLE == ImageRef.SINGLE:
                            imgId = imgRef.path
                            index = 0
                        elif imgRef.imageType & \
                                ImageRef.STACK == ImageRef.STACK:
                            if imgRef.imageType & \
                                    ImageRef.VOLUME == ImageRef.VOLUME:
                                imgId = '%d-%s' % (imgRef.volumeIndex,
                                                   imgRef.path)
                                index = imgRef.volumeIndex
                            else:
                                imgId = '%d-%s' % (imgRef.index, imgRef.path)
                                index = imgRef.index

                        data = self._imgCache.addImage(imgId, imgRef.path,
                                                       index)
                        self._imageView.setImageInfo(
                            path=imgRef.path, format=EmPath.getExt(imgRef.path),
                            data_type=' ')
                        if data is not None:
                            if imgRef.axis == X_AXIS:
                                data = data[:, :, imgRef.index]
                            elif imgRef.axis == Y_AXIS:
                                imgRef.axis = data[:, imgRef.index, :]
                            elif imgRef.axis == Z_AXIS:
                                data = data[imgRef.index, :, :]

                            self._imageView.setImage(data)

                model.appendRow([item])
                label = self._model.headerData(i, Qt.Horizontal)
                if label:
                    vLabels.append(label)
            model.setHorizontalHeaderLabels(["Values"])
            model.setVerticalHeaderLabels(vLabels)
            self._itemsViewTable.horizontalHeader().setStretchLastSection(True)
            self.sigCurrentRowChanged.emit(row)

    @pyqtSlot(QModelIndex, QModelIndex)
    def __onDataChanged(self, topLeft, bottomRight):
        """ Invoked whenever the data in an existing item changes."""
        if topLeft.row() == self._row:
            self.__loadItem(self._row, self._column)

    @pyqtSlot(int)
    def __onCurrentPageChanged(self, page):
        """ Invoked when change the current page """
        self._row = page
        self.__loadItem(self._row, self._column)

    def setModelColumn(self, column):
        """ Holds the column in the model that is visible. """
        self._column = column
        self.__loadItem(self._row, self._column)

    def getModelColumn(self):
        """ Returns the column in the model that is visible. """
        return self._column

    def setModel(self, model):
        """ Sets the model """
        self._row = 0
        self._column = 0
        if self._model:
            self._model.sigPageChanged.disconnect(self.__onCurrentPageChanged)
            self._model.dataChanged.disconnect(self.__onDataChanged)

        AbstractView.setModel(self, model)

        if self._model:
            self._imageView.setVisible(self._model.hasRenderableColumn())
            self._model.sigPageChanged.connect(self.__onCurrentPageChanged)
            self._model.setupPage(1, self._row)
            self._model.dataChanged.connect(self.__onDataChanged)
        else:
            self._imageView.setVisible(False)

    def setImageCache(self, imgCache):
        """ Sets the image cache """
        self._imgCache = imgCache

    def selectRow(self, row):
        """ Selects the given row """
        if self._model and row in range(0, self._model.totalRowCount()):
            self._row = row
            self._model.loadPage(row)

    def currentRow(self):
        """ Returns the current selected row """
        if self._model is None:
            return -1
        return self._row

    def getViewDims(self):
        """ Returns a tuple (rows, columns) with the data size """
        if self._model is not None:
            return self._model.columnCount(), 1
        return 0, 0

    def setInfo(self, **kwargs):
        """
        Sets the image info that will be displayed.
        kwargs  arguments:
        path : (str) the image path
        format: (str) the image format
        data_type: (str) the image data type"""
        self._imageView.setImageInfo(**kwargs)
