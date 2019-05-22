#!/usr/bin/python
# -*- coding: utf-8 -*-

import os

from PyQt5.QtCore import Qt, pyqtSlot, QModelIndex
from PyQt5.QtWidgets import QTableView, QSplitter, QVBoxLayout, QWidget
from PyQt5.QtGui import QStandardItemModel, QStandardItem

from PyQt5 import QtCore

from emqt5.widgets._delegates import AbstractView
from ..utils import EmPath, parseImagePath, ImageRef, ImageManager
from ._image_view import ImageView


class ItemsView(AbstractView):
    """
    The Items class provides functionality for show large numbers of
    items with simple paginate elements in items view """

    sigCurrentRowChanged = QtCore.pyqtSignal(int)  # For current row changed

    def __init__(self, parent, **kwargs):
        """
        kwargs:
         - imageManager: the ImageManager for internal read/manage
                         image operations.
        """
        AbstractView.__init__(self, parent)
        self._column = 0
        self._row = 0
        self._selection = set()
        self.__selectionItem = None
        self._disableFitToSize = False
        self._imageManager = kwargs.get('imageManager') or ImageManager(50)
        self._imageRef = ImageRef()
        self.__setupUI(**kwargs)

    def __setupUI(self, **kwargs):
        self._mainWidget = QWidget(self)
        self._mainWidget.setObjectName("itemsMainWidget")
        self._layout = QVBoxLayout(self._mainWidget)
        self._layout.setContentsMargins(2, 2, 2, 2)
        self._splitter = QSplitter(self)
        self._splitter.setOrientation(Qt.Horizontal)
        self._itemsViewTable = QTableView(self._splitter)
        model = QStandardItemModel(self._itemsViewTable)
        self._itemsViewTable.setModel(model)
        self._itemsViewTable.horizontalHeader().setHighlightSections(False)
        self._itemsViewTable.verticalHeader().setHighlightSections(False)
        model.itemChanged.connect(self.__onItemDataChanged)
        self._imageView = ImageView(self._splitter, **kwargs)
        self._mainLayout.insertWidget(0, self._mainWidget)
        self._layout.insertWidget(0, self._splitter)

    def __loadItem(self, row):
        """ Show the item at (row,col)"""
        self._imageView.clear()
        model = self._itemsViewTable.model()
        model.clear()
        self.loadCurrentItems()
        self.loadImages(row)
        if self._selectionMode == AbstractView.SINGLE_SELECTION:
            self._selection.clear()
            self._selection.add(row)
            self.sigSelectionChanged.emit()
        self.__updateSelectionInView()
        self.sigCurrentRowChanged.emit(row)

    def __updateSelectionInView(self):
        if self._selectionMode == AbstractView.MULTI_SELECTION and \
                self.__selectionItem is not None:
            if self._row in self._selection:
                self.__selectionItem.setCheckState(Qt.Checked)
            else:
                self.__selectionItem.setCheckState(Qt.Unchecked)

    @pyqtSlot('QStandardItem*')
    def __onItemDataChanged(self, item):
        """
        Invoked when the item data is changed. Used for selection purposes
        """
        if item == self.__selectionItem:
            if self._selectionMode == AbstractView.MULTI_SELECTION:
                if item.checkState() == Qt.Checked:
                    self._selection.add(self._row)
                else:
                    self._selection.discard(self._row)
                self.sigSelectionChanged.emit()
            elif item.checkState() == Qt.Unchecked:
                item.setCheckState(Qt.Checked)

    @pyqtSlot(QModelIndex, QModelIndex)
    def __onDataChanged(self, topLeft, bottomRight):
        """ Invoked whenever the data in an existing item changes."""
        row = self._model.getPage() * self._model.getPageSize() + topLeft.row()
        if row == self._row:
            self.__loadItem(self._row)

    @pyqtSlot(int)
    def __onCurrentPageChanged(self, page):
        """ Invoked when change the current page """
        self._row = page
        self.__loadItem(self._row)

    @pyqtSlot(set)
    def changeSelection(self, selection):
        """ Invoked when the selection is changed """
        self._selection = selection
        self.__updateSelectionInView()

    def setModelColumn(self, column):
        """ Holds the column in the model that is visible. """
        self._column = column
        self.updateViewConfiguration()

    def selectRow(self, row):
        """ Selects the given row """
        if self._model is not None and \
                row in range(0, self._model.totalRowCount()):
            self._row = row
            self.__loadItem(self._row)

    def getModelColumn(self):
        """ Returns the column in the model that is visible. """
        return self._column

    def setModel(self, model):
        """ Sets the model """
        self._row = 0
        self._column = 0
        self.__selectionItem = None
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

    def setImageManager(self, imageManager):
        """ Sets the image cache """
        self._imageManager = imageManager

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

    def updateViewConfiguration(self):
        """ Reimplemented from AbstractView """
        self._imageView.setVisible(self._model is not None and
                                   self._model.hasRenderableColumn())
        self.__loadItem(self._row)

    def loadImages(self, row):
        """
        Load the images referenced by the given row and all the columns marked
        as renderable.
        TODO[hv]: Now only one image is displayed, but in the future all
        renderable columns will be displayed
        """
        if self._model is not None \
                and row in range(0, self._model.totalRowCount()) \
                and self._column in range(0, self._model.columnCount()):
            indexes = self._model.getColumnConfig().getIndexes('renderable',
                                                               True)
            if indexes:
                imgPath = self._model.getTableData(row, indexes[0])
                imgRef = parseImagePath(
                    imgPath, self._imageRef,
                    os.path.split(self._model.getDataSource())[0])
                if imgRef is not None:
                    data = self._imageManager.addImage(imgRef)
                    self._imageView.setImageInfo(
                        path=imgRef.path,
                        format=EmPath.getExt(imgRef.path),
                        data_type=' ')
                    if data is not None:
                        self._imageView.setImage(data)

    def loadCurrentItems(self):
        """ Load the side table of values """
        model = self._itemsViewTable.model()
        model.clear()
        if self._model is not None \
                and self._row in range(0, self._model.totalRowCount()) \
                and self._column in range(0, self._model.columnCount()):
            vLabels = []
            if self._selectionMode == AbstractView.MULTI_SELECTION:
                vLabels = ["SELECTED"]
                self.__selectionItem = QStandardItem()
                self.__selectionItem.setCheckable(True)
                self.__selectionItem.setEditable(False)
                if self._selection is not None and self._row in self._selection:
                    self.__selectionItem.setCheckState(Qt.Checked)
                model.appendRow([self.__selectionItem])
            else:
                self.__selectionItem = None

            for i in range(0, self._model.columnCount()):
                colConfig = self._model.getColumnConfig(i)
                if colConfig['visible']:
                    item = QStandardItem()
                    item.setData(self._model.getTableData(self._row, i),
                                 Qt.DisplayRole)
                    item.setEditable(False)
                    model.appendRow([item])
                    label = self._model.headerData(i, Qt.Horizontal)
                    if isinstance(label, str) or isinstance(label, unicode):
                        vLabels.append(label)
            model.setHorizontalHeaderLabels(["Values"])
            model.setVerticalHeaderLabels(vLabels)
            self._itemsViewTable.horizontalHeader().setStretchLastSection(True)
