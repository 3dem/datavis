#!/usr/bin/python
# -*- coding: utf-8 -*-


from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtWidgets import QTableView, QSplitter, QVBoxLayout, QWidget
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5 import QtCore

from ._paging_view import PagingView
from ._constants import ITEMS
from datavis.widgets import PagingInfo
from datavis.models import ImageModel, EmptyTableModel
from ._image_view import ImageView
from .model import TablePageItemModel


class ItemsView(PagingView):
    """
    The Items class provides functionality for show large numbers of
    items with simple paginate elements in items view """

    """ Signal for current row changed """
    sigCurrentRowChanged = QtCore.pyqtSignal(int)
    """ Signal for size changed """
    sigSizeChanged = QtCore.pyqtSignal()

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
        self._row = -1
        self._selection = set()
        self.__selectionItem = None
        self._disableFitToSize = False
        self._model = None
        self._config = None
        self._pageItemModel = None
        self.setModel(kwargs['model'], kwargs.get('config', None))

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

    def __updateSelectionInView(self):
        """ Updates the internal selection in the view widgets """
        if self.isMultiSelection() and self.__selectionItem is not None:
            if self._row in self._selection:
                self.__selectionItem.setCheckState(Qt.Checked)
            else:
                self.__selectionItem.setCheckState(Qt.Unchecked)

    def __updatePagingInfo(self):
        self._pagingInfo.numberOfItems = self._model.getRowsCount()
        self._pagingInfo.setPageSize(1)
        self._pagingInfo.currentPage = 1

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

    def __loadRow(self, row):
        """
        Show the item at (row, col)
        :param row: (int) The row index. First index is 0.
        """
        self._imageView.clear()
        model = self._itemsViewTable.model()
        model.clear()
        self._row = row
        self._loadRowValues()
        self.__loadRowImages()
        if self.isSingleSelection():
            self._selection.clear()
            self._selection.add(row)
            self.sigSelectionChanged.emit()
        self.__updateSelectionInView()
        self.sigCurrentRowChanged.emit(row)

    def __loadRowImages(self):
        """
        Load the images referenced by the given row and all the columns marked
        as renderable.
        TODO[hv]: Now only one image is displayed, but in the future all
        renderable columns could be displayed
        """
        indexes = self._config.getColumnsCount(renderable=True)
        if indexes > 0:
            data = self._model.getData(self._row, self._column)
            if data is not None:
                self._imageView.setModel(ImageModel(data))
                self._imageView.setImageInfo(
                    path=self._model.getValue(self._row, self._column),
                    format=' ',  # FIXME[phv] set image format and type
                    data_type=' ')
        else:
            self._imageView.clear()

    @pyqtSlot('QStandardItem*')
    def __onItemDataChanged(self, item):
        """
        Invoked when the item data is changed. Used for selection purposes
        """
        if item == self.__selectionItem:
            if self.isMultiSelection():
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
        self.__loadRow(page - 1)

    def _loadRowValues(self):
        """ Load the table values for the current row.
         Values will be displayed as rows of this view.
         """
        model = self._itemsViewTable.model()
        model.clear()
        # FIXME: (Important) Every time that we change the selected row
        # FIXME: do we need to create new QStandardItems() ?????
        # FIXME: This might be the cause of some noticeable flickering
        # FIXME: If the model haven't changed, we can populate the model once
        # FIXME: and then set the values
        vLabels = []

        if self.isMultiSelection():
            vLabels.append('SELECTED')
            self.__selectionItem = QStandardItem()
            self.__selectionItem.setCheckable(True)
            self.__selectionItem.setEditable(False)
            if self._selection is not None and self._row in self._selection:
                self.__selectionItem.setCheckState(Qt.Checked)
            model.appendRow([self.__selectionItem])
        else:
            self.__selectionItem = None

        for i, colConfig in self._config.iterColumns(visible=True):
            item = QStandardItem()
            item.setData(
                self._pageItemModel.data(self._pageItemModel.createIndex(
                    self._row, i)), Qt.DisplayRole)
            item.setEditable(False)
            model.appendRow([item])
            label = self._pageItemModel.headerData(i, Qt.Horizontal)
            if isinstance(label, str) or isinstance(label, unicode):
                vLabels.append(label)
        model.setHorizontalHeaderLabels(["Values"])
        model.setVerticalHeaderLabels(vLabels)
        self._itemsViewTable.horizontalHeader().setStretchLastSection(True)

    @pyqtSlot(set)
    def changeSelection(self, selection):
        """ Invoked when the selection is changed """
        self._selection = selection
        self.__updateSelectionInView()

    @pyqtSlot()
    def modelChanged(self):
        """Slot for model data changed notification """
        self.__updatePagingInfo()
        self._imageView.setVisible(self._pageItemModel.hasRenderableColumn())
        self._pageBar.setPagingInfo(self._pagingInfo)

    def selectRow(self, row):
        """ Selects the given row """
        self._pageBar.setCurrentPage(row + 1)

    def setModel(self, model, displayConfig=None):
        """
        Set the model for this view.
        Raise Exception when the model is None
        :param model:         (datavis.model.TableModel) The data model
        :param displayConfig: (datavis.model.TableConfig) control how the data
            fetched from the TableModel will be displayed.
        """
        if model is None:
            raise Exception('Invalid model: None')

        self._row = 0
        self._column = 0
        self.__selectionItem = None
        self._model = model
        self._config = displayConfig or model.createDefaultConfig()

        if self._pageItemModel is None:
            self._pageItemModel = TablePageItemModel(model, self._pagingInfo,
                                                     parent=self,
                                                     tableConfig=self._config)
            self.__connectSignals()
        else:
            self._pageItemModel.setModelConfig(tableModel=model,
                                               tableConfig=self._config,
                                               pagingInfo=self._pagingInfo)
        self.modelChanged()

    def currentRow(self):
        """ Returns the current selected row """
        return self._row

    def getDisplayConfig(self):
        """ Returns the display configuration """
        return self._config

    def clear(self):
        """ Clear the view """
        self.setModel(EmptyTableModel())

    def getViewDims(self):
        """ Returns a tuple (rows, columns) with the data size """
        return self._config.getColumnsCount(), 1

    def getViewType(self):
        """ Returns the view type
        """
        return ITEMS

    def updateViewConfiguration(self):
        """ Reimplemented from PagingView """
        self._imageView.setVisible(
            self._config.hasColumnConfig(renderable=True))
        self.__loadRow(self._row)

    def getPreferredSize(self):
        """ Returns a tuple (width, height), which represents the preferred
        dimensions to contain all the data
        """
        w, h = self._imageView.getPreferredSize()
        return 2*w, 2*h

    def setModelColumn(self, column):
        """
        Holds the column in the model that is visible.
        :param column: (int) Column index. 0 is the first index.
        """
        self._column = column
