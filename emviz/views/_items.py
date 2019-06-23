#!/usr/bin/python
# -*- coding: utf-8 -*-


from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtWidgets import QTableView, QSplitter, QVBoxLayout, QWidget
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5 import QtCore

from ._paging_view import PagingView
from emviz.widgets import PagingInfo
from emviz.models import RENDERABLE, VISIBLE, ImageModel, EmptyTableModel
from ._image_view import ImageView
from .model import TablePageItemModel


class ItemsView(PagingView):
    """
    The Items class provides functionality for show large numbers of
    items with simple paginate elements in items view """

    """ Signal for current row changed """
    sigCurrentRowChanged = QtCore.pyqtSignal(int)

    def __init__(self, parent=None, **kwargs):
        """
        Constructs an ItemsView
        kwargs:
           model:          The data model
           displayConfig:  Input TableModel that will control how the data
                            fetched from the TableModel will be displayed.
                            displayConfig can be None, in which case the model
                            will be taken as displayConfig.
           selectionMode:  (int) SINGLE_SELECTION(default), EXTENDED_SELECTION,
                            MULTI_SELECTION or NO_SELECTION.
           imageViewKwargs: The internal ImageView initialization parameters.
        """
        self._imageViewKwargs = kwargs.get('imageViewKwargs', dict())
        PagingView.__init__(self, parent=parent, pagingInfo=PagingInfo(1, 1),
                            **kwargs)
        self._column = 0
        self._row = 0
        self._selection = set()
        self.__selectionItem = None
        self._disableFitToSize = False
        self._pageItemModel = None
        self.setModel(kwargs['model'])

    def _createContentWidget(self):
        mainWidget = QWidget(self)
        mainWidget.setObjectName("itemsMainWidget")
        layout = QVBoxLayout(mainWidget)
        layout.setContentsMargins(2, 2, 2, 2)
        self._splitter = QSplitter(self)
        self._splitter.setOrientation(Qt.Horizontal)
        self._itemsViewTable = QTableView(self._splitter)
        model = QStandardItemModel(self._itemsViewTable)
        self._itemsViewTable.setModel(model)
        self._itemsViewTable.horizontalHeader().setHighlightSections(False)
        self._itemsViewTable.verticalHeader().setHighlightSections(False)
        model.itemChanged.connect(self.__onItemDataChanged)
        self._imageView = ImageView(self._splitter, **self._imageViewKwargs)
        layout.insertWidget(0, self._splitter)
        return mainWidget

    def __loadItem(self, row):
        """
        Show the item at (row, col)
        :param row: (int) The row index. First index is 0.
        """
        self._imageView.clear()
        model = self._itemsViewTable.model()
        model.clear()
        self.loadCurrentItems()
        self.loadImages(row)
        if self._selectionMode == PagingView.SINGLE_SELECTION:
            self._selection.clear()
            self._selection.add(row)
            self.sigSelectionChanged.emit()
        self.__updateSelectionInView()
        self.sigCurrentRowChanged.emit(row)

    def __updateSelectionInView(self):
        """ Updates the internal selection in the view widgets """
        if self._selectionMode == PagingView.MULTI_SELECTION and \
                self.__selectionItem is not None:
            if self._row in self._selection:
                self.__selectionItem.setCheckState(Qt.Checked)
            else:
                self.__selectionItem.setCheckState(Qt.Unchecked)

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

    @pyqtSlot('QStandardItem*')
    def __onItemDataChanged(self, item):
        """
        Invoked when the item data is changed. Used for selection purposes
        """
        if item == self.__selectionItem:
            if self._selectionMode == PagingView.MULTI_SELECTION:
                if item.checkState() == Qt.Checked:
                    self._selection.add(self._row)
                else:
                    self._selection.discard(self._row)
                self.sigSelectionChanged.emit()
            elif item.checkState() == Qt.Unchecked:
                item.setCheckState(Qt.Checked)

    @pyqtSlot(int)
    def __onCurrentPageChanged(self, page):
        """ Invoked when change the current page """
        self._row = page - 1
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
        if self._model is not None and 0 <= row < self._model.getRowsCount():
            self._row = row
            self.__loadItem(self._row)

    def getModelColumn(self):
        """ Returns the column in the model that is visible. """
        return self._column

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

        self._row = 0
        self._column = 0
        self.__selectionItem = None
        self.__disconnectSignals()
        self._model = model
        self._pagingInfo.numberOfItems = model.getRowsCount()
        self._pagingInfo.setPageSize(1)
        self._pagingInfo.currentPage = 1
        self._pageItemModel = TablePageItemModel(model, self._pagingInfo,
                                                 tableConfig=displayConfig,
                                                 parent=self)
        self.__connectSignals()
        self._imageView.setVisible(self._pageItemModel.hasRenderableColumn())
        self._pageBar.setPagingInfo(self._pagingInfo)

    def currentRow(self):
        """ Returns the current selected row """
        return -1 if self._model is None else self._row

    def getDisplayConfig(self):
        """ Returns the display configuration """
        if self._pageItemModel is not None:
            return self._pageItemModel.getDisplayConfig()
        return None

    def clear(self):
        """ Clear the view """
        self.setModel(EmptyTableModel())

    def getViewDims(self):
        """ Returns a tuple (rows, columns) with the data size """
        if self._model is not None:
            return self._model.getColumnsCount(), 1
        return 0, 0

    def updateViewConfiguration(self):
        """ Reimplemented from PagingView """
        self._imageView.setVisible(self._model is not None and
                                   self._model.hasColumn(**{RENDERABLE: True}))
        self.__loadItem(self._row)

    def loadImages(self, row):
        """
        Load the images referenced by the given row and all the columns marked
        as renderable.
        TODO[hv]: Now only one image is displayed, but in the future all
        renderable columns will be displayed
        """
        if self._model is not None \
                and 0 <= row < self._model.getRowsCount() \
                and 0 <= self._column < self._model.getColumnsCount():
            indexes = [i for i, c in
                       self._model.iterColumns(**{RENDERABLE: True})]
            if indexes:
                data = self._model.getData(row, self._column)
                if data is not None:
                    self._imageView.setModel(ImageModel(data))
                    self._imageView.setImageInfo(
                        path=self._model.getValue(row, self._column),
                        format=' ',  # FIXME[phv] set image format and type
                        data_type=' ')
            else:
                self._imageView.clear()

    def loadCurrentItems(self):
        """ Load the side table of values """
        model = self._itemsViewTable.model()
        model.clear()
        if self._model is not None \
                and 0 <= self._row < self._model.getRowsCount() \
                and 0 <= self._column < self._model.getColumnsCount():
            vLabels = []
            if self._selectionMode == PagingView.MULTI_SELECTION:
                vLabels = ["SELECTED"]
                self.__selectionItem = QStandardItem()
                self.__selectionItem.setCheckable(True)
                self.__selectionItem.setEditable(False)
                if self._selection is not None and self._row in self._selection:
                    self.__selectionItem.setCheckState(Qt.Checked)
                model.appendRow([self.__selectionItem])
            else:
                self.__selectionItem = None

            for i in range(self._model.getColumnsCount()):
                colConfig = self._model.getColumn(i)
                if colConfig is not None and colConfig[VISIBLE]:
                    item = QStandardItem()
                    item.setData(self._model.getValue(self._row, i),
                                 Qt.DisplayRole)
                    item.setEditable(False)
                    model.appendRow([item])
                    label = self._pageItemModel.headerData(i, Qt.Horizontal)
                    if isinstance(label, str) or isinstance(label, unicode):
                        vLabels.append(label)
            model.setHorizontalHeaderLabels(["Values"])
            model.setVerticalHeaderLabels(vLabels)
            self._itemsViewTable.horizontalHeader().setStretchLastSection(True)
