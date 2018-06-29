#!/usr/bin/python
# -*- coding: utf-8 -*-


from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtWidgets import QTableView, QGraphicsPixmapItem, QSplitter
from PyQt5.QtGui import QPixmap, QStandardItemModel, QStandardItem

from PyQt5 import QtCore

from .model import ImageCache, X_AXIS, Y_AXIS, Z_AXIS
from .base import AbstractView
from emqt5.utils import EmPath, parseImagePath

import pyqtgraph as pg


class ItemsView(AbstractView):
    """
    The Items class provides functionality for show large numbers of
    items with simple paginate elements in items view """

    sigCurrentRowChanged = QtCore.pyqtSignal(int)  # For current row changed

    def __init__(self, parent=None):
        AbstractView.__init__(self, parent)
        self._column = 0
        self._row = 0
        self._imgCache = ImageCache(50)
        self.__setupUI()

    def __setupUI(self):
        self._splitter = QSplitter(self)
        self._splitter.setOrientation(Qt.Horizontal)
        self._imageView = pg.ImageView(self._splitter)
        self._pixMapElem = QPixmap()
        self._pixmapItem = QGraphicsPixmapItem(self._pixMapElem)
        self._imageView.getView().addItem(self._pixmapItem)
        self._itemsViewTable = QTableView(self._splitter)
        self._itemsViewTable.setModel(QStandardItemModel(self._itemsViewTable))
        self._mainLayout.insertWidget(0, self._splitter)
        self._pageBar.sigPageChanged.connect(self.__onCurrentPageChanged)

    def __loadItem(self, row, col):
        """ Show the item at (row,col)"""
        if self._model and row in range(0, self._model.totalRowCount()) and \
                col in range(0, self._model.columnCount()):
            model = self._itemsViewTable.model()
            model.clear()
            vLabels = []
            for i in range(0, self._model.columnCount()):
                item = QStandardItem()
                item.setData(self._model.getTableData(row, i),
                             Qt.DisplayRole)
                if i == col:
                    imgPath = self._model.getTableData(row, i)
                    imgParams = parseImagePath(imgPath)
                    if imgParams is not None and len(imgParams) == 3:
                        imgPath = imgParams[2]
                        if EmPath.isImage(imgPath):
                            self._pixMapElem.load(imgPath)
                            self._pixmapItem.setPixmap(self._pixMapElem)
                            self._pixmapItem.setVisible(True)
                            v = self._imageView.getView()
                            if not self._disableFitToSize:
                                v.autoRange()
                        else:
                            if self._pixmapItem:
                                self._pixmapItem.setVisible(False)

                            if EmPath.isStack(imgPath):
                                id = str(imgParams[0]) + '_' + imgPath
                                index = imgParams[0]
                            else:
                                id = imgPath
                                index = 0

                            data = self._imgCache.addImage(id, imgPath, index)
                            if data is not None:
                                axis = imgParams[1]
                                if axis == X_AXIS:
                                    data = data[:, :, imgParams[0]]
                                elif axis == Y_AXIS:
                                    data = data[:, imgParams[0], :]
                                elif axis == Z_AXIS:
                                    data = data[imgParams[0], :, :]

                                self._imageView.setImage(data)
                            else:
                                self._imageView.clear()
                    else:
                        self._imageView.clear()

                model.appendRow([item])
                label = self._model.headerData(i, Qt.Horizontal)
                if label:
                    vLabels.append(label)
            model.setHorizontalHeaderLabels(["Values"])
            model.setVerticalHeaderLabels(vLabels)
            self._itemsViewTable.horizontalHeader().setStretchLastSection(True)
            self.sigCurrentRowChanged.emit(row)

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
        AbstractView.setModel(self, model)
        if self._model:
            self._model.setupPage(1, self._row)

    def setImageCache(self, imgCache):
        """ Sets the image cache """
        self._imgCache = imgCache

    def selectRow(self, row):
        """ Selects the given row """
        if self._model and row in range(0, self._model.totalRowCount()):
            self._model.loadPage(row)
