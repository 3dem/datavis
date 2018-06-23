#!/usr/bin/python
# -*- coding: utf-8 -*-


from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal, QSize, QRectF, QModelIndex
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QToolBar, QAction,
                             QTableView, QSpinBox, QLabel, QStyledItemDelegate,
                             QStyle, QAbstractItemView, QStatusBar,
                             QApplication, QHeaderView, QComboBox, QHBoxLayout,
                             QStackedLayout, QLineEdit, QActionGroup, QListView,
                             QSizePolicy, QSpacerItem, QPushButton, QSplitter,
                             QGraphicsPixmapItem)
from PyQt5.QtGui import (QPixmap, QPen, QIcon, QPalette, QStandardItemModel,
                         QStandardItem)
from PyQt5 import QtCore
import qtawesome as qta
import pyqtgraph as pg

import em
from emqt5.utils import EmPath, EmTable, parseImagePath
from .config import TableViewConfig
from .model import ImageCache, TableDataModel, X_AXIS, Y_AXIS, Z_AXIS
from .base import EMImageItemDelegate
from .columns import ColumnsView
from .gallery import GalleryView


PIXEL_UNITS = 1
PERCENT_UNITS = 2


class DataView(QWidget):
    """
    Widget used for display em data
    """
    COLUMNS = 1
    GALLERY = 2
    ITEMS = 4

    """ This signal is emitted when the current item change in TABLE mode """
    sigCurrentTableItemChanged = pyqtSignal(int, int)

    """ This signal is emitted when the current item change in GALLERY mode """
    sigCurrentGalleryItemChanged = pyqtSignal(int, int)

    """ This signal is emitted when the current item change in ELEMENT mode """
    sigCurrentElementItemChanged = pyqtSignal(int, int)

    """ This signal is emitted when a mouse button is double-clicked 
        in GALLERY mode """
    sigGalleryItemDoubleClicked = pyqtSignal(int, int)

    def __init__(self, **kwargs):
        QWidget.__init__(self, kwargs.get("parent", None))
        self._calcTablePageProperties = True
        self._calcGalleryPageProperties = True

        self._viewActions = {self.COLUMNS: {"name": "Columns",
                                            "icon": "fa.table",
                                            "action": None},
                             self.GALLERY: {"name": "Gallery",
                                            "icon": "fa.th",
                                            "action": None},
                             self.ITEMS: {"name": "Items",
                                          "icon": "fa.columns",
                                          "action": None}}
        self._viewTypes = {"Columns": self.COLUMNS,
                           "Gallery": self.GALLERY,
                           "Items": self.ITEMS}
        self._tableModel = None
        self._models = None
        self._currentRenderableColumn = 0  # for GALLERY and ITEMS mode
        self._currentRow = 0  # selected table row

        # FIXME: The following variables are not needed and should be
        # managed by the view
        self._itemsXGalleryPage = 0
        self._itemsXTablePage = 0
        self._itemsXItemPage = 1

        self._imageCache = ImageCache(50, 50)
        self._columnDelegates = {}

        self.__initProperties(**kwargs)
        self.__setupUi()
        self._defaultTableViewDelegate = self._tableView.itemDelegate()
        self.__setupCurrentViewMode()
        self.__setupImageView()

    def __setupUi(self):
        self._mainLayout = QVBoxLayout(self)
        self._toolBar = QToolBar(self)
        self._mainLayout.addWidget(self._toolBar)
        self._stackedLayoud = QStackedLayout(self._mainLayout)
        # table view
        self._tableViewContainer = QWidget(self)
        self._tableView = ColumnsView(self._tableViewContainer)
        verticalLayout = QVBoxLayout(self._tableViewContainer)
        verticalLayout.addWidget(self._tableView)
        # self._tableView.setSelectionBehavior(QTableView.SelectRows)
        # self._tableView.verticalHeader().hide()
        # self._tableView.setSortingEnabled(True)
        # self._tableView.setModel(self._tableModel)
        # self._tableView.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # gallery view
        self._listViewContainer = QWidget(self)
        self._listView = GalleryView(self._listViewContainer)
        self._listView.installEventFilter(self)

        # FIXME: Think how to connect the signal and what is the best way to expose it from the internal View
        #self._listView.doubleClicked.connect(
        #    self._onGalleryViewItemDoubleClicked)
        #sModel = self._listView.selectionModel()
        #if sModel:
        #    sModel.currentChanged.connect(self._onCurrentGalleryItemChanged)

        self._galleryLayout = QVBoxLayout(self._listViewContainer)
        self._galleryLayout.addWidget(self._listView)

        # FIXME: change the following with the proper view
        # element view
        #self._elemViewContainer = QSplitter(self)
        #self._elemViewContainer.setOrientation(Qt.Horizontal)
        # self._imageView = pg.ImageView(parent=self._elemViewContainer)
        #
        # self._pixMapElem = QPixmap()
        # self._pixmapItem = QGraphicsPixmapItem(self._pixMapElem)
        # self._imageView.getView().addItem(self._pixmapItem)

        # self._elemViewTable = ColumnsView(self._elemViewContainer)
        # self._elemViewTable.setModel(QStandardItemModel(self._elemViewTable))
        # # pagination
        # self._pageContainer = QWidget(self)
        # self._pagingLayout = QHBoxLayout(self._pageContainer)
        # self._pagingLayout.setContentsMargins(1, 1, 1, 1)
        # self._pagingLayout.addItem(QSpacerItem(40,
        #                                        20,
        #                                        QSizePolicy.Expanding,
        #                                        QSizePolicy.Minimum))
        # self._pushButtonPrevPage = QPushButton(self._listViewContainer)
        # self._pagingLayout.addWidget(self._pushButtonPrevPage)
        # self._pushButtonPrevPage.setIcon(qta.icon('fa.angle-left'))
        # self._pushButtonPrevPage.clicked.connect(self._onListPrevPage)
        # self._spinBoxCurrentPage = QSpinBox(self._listViewContainer)
        # self._spinBoxCurrentPage.setButtonSymbols(QSpinBox.NoButtons)
        # self._spinBoxCurrentPage.editingFinished.connect(
        #     self._onSpinBoxCurrentPageEditingFinished)
        # self._spinBoxCurrentPage.setMaximumSize(50, 25)
        # self._spinBoxCurrentPage.setMinimumSize(50, 25)
        # self._pagingLayout.addWidget(self._spinBoxCurrentPage)
        # self._labelPageCount = QLabel(self._listViewContainer)
        # self._pagingLayout.addWidget(self._labelPageCount)
        # self._pushButtonNextPage = QPushButton(self._listViewContainer)
        # self._pushButtonNextPage.setIcon(qta.icon('fa.angle-right'))
        # self._pushButtonNextPage.clicked.connect(self._onListNextPage)
        # self._pagingLayout.addWidget(self._pushButtonNextPage)
        # self._pagingLayout.addItem(QSpacerItem(40,
        #                                        20,
        #                                        QSizePolicy.Expanding,
        #                                        QSizePolicy.Minimum))
        # self._mainLayout.addWidget(self._pageContainer)

        self._stackedLayoud.addWidget(self._tableViewContainer)
        self._stackedLayoud.addWidget(self._listViewContainer)
        # self._stackedLayoud.addWidget(self._elemViewContainer)

        # FIXME
        #self._listView.sigSizeChanged.connect(self.__galleryResized)
        #self._tableView.sigSizeChanged.connect(self.__tableResized)

        self._actionGroupViews = QActionGroup(self._toolBar)
        self._actionGroupViews.setExclusive(True)
        for view in [self.COLUMNS, self.GALLERY, self.ITEMS]:
            #  create action with name=view
            v = self._viewActions[view]
            a = self.__createNewAction(self._toolBar, v["name"], v["name"],
                                       v["icon"],
                                       True, self._onChangeViewTriggered)
            v["action"] = a
            self._actionGroupViews.addAction(a)
            self._toolBar.addAction(a)
            a.setChecked(view == self._viewName)
            a.setVisible(view in self._views)

        self._toolBar.addSeparator()
        # cell resizing
        self._labelLupe = QLabel(self._toolBar)
        self._labelLupe.setPixmap(qta.icon('fa.search').pixmap(28,
                                                               QIcon.Normal,
                                                               QIcon.On))
        self._toolBar.addWidget(self._labelLupe)
        self._spinBoxRowHeight = QSpinBox(self._toolBar)
        self._spinBoxRowHeight.setSuffix(' px' if self._zoomUnits == PIXEL_UNITS
                                         else ' %')
        self._spinBoxRowHeight.setRange(self._minRowHeight,
                                        self._maxRowHeight)
        self._spinBoxRowHeight.setValue(self._defaultRowHeight)

        #TODO: CHECK THIS
        #verticalHeader = self._tableView.verticalHeader()
        #verticalHeader.setSectionResizeMode(QHeaderView.Fixed)

        self._spinBoxRowHeight.editingFinished.connect(self._onChangeCellSize)
        self._spinBoxRowHeight.setValue(self._defaultRowHeight)
        self._toolBar.addWidget(self._spinBoxRowHeight)
        self._toolBar.addSeparator()
        # cell navigator
        self._labelCurrentRow = QLabel(self._toolBar)
        self._labelCurrentRow.setPixmap(qta.icon(
            'fa.level-down').pixmap(28, QIcon.Normal, QIcon.On))
        self._spinBoxCurrentRow = QSpinBox(self._toolBar)
        self._spinBoxCurrentRow.valueChanged[int].connect(self._selectRow)
        self._toolBar.addWidget(self._labelCurrentRow)
        self._toolBar.addWidget(self._spinBoxCurrentRow)
        self._toolBar.addSeparator()
        # table rows and columns
        self._labelRows = QLabel(self._toolBar)
        self._labelRows.setText(" Rows ")
        self._toolBar.addWidget(self._labelRows)
        self._lineEditRows = QLineEdit(self._toolBar)
        self._lineEditRows.setMaximumSize(80, 22)
        self._lineEditRows.setEnabled(False)
        self._toolBar.addWidget(self._lineEditRows)
        self._labelCols = QLabel(self._toolBar)
        self._labelCols.setText(" Cols ")
        self._toolBar.addWidget(self._labelCols)
        self._lineEditCols = QLineEdit(self._toolBar)
        self._lineEditCols.setMaximumSize(80, 22)
        self._lineEditCols.setEnabled(False)
        self._toolBar.addWidget(self._lineEditCols)
        self._toolBar.addSeparator()

        self._labelCurrentTable = QLabel(parent=self._toolBar, text="Table ")
        self._toolBar.addWidget(self._labelCurrentTable)
        self._comboBoxCurrentTable = QComboBox(self._toolBar)
        self._comboBoxCurrentTable.currentIndexChanged. \
            connect(self._onCurrentTableChanged)
        self._toolBar.addWidget(self._comboBoxCurrentTable)
        self._toolBar.addSeparator()

        #gallery view
        self._labelCurrentColumn = QLabel(parent=self._toolBar,
                                          text="Gallery in ")
        self._actLabelCurrentColumn = self._toolBar.addWidget(
            self._labelCurrentColumn)
        self._comboBoxCurrentColumn = QComboBox(self._toolBar)
        self._actComboBoxCurrentColumn = self._toolBar.addWidget(
            self._comboBoxCurrentColumn)
        self._comboBoxCurrentColumn.currentIndexChanged.\
            connect(self._onGalleryViewColumnChanged)

        self._statusBar = QStatusBar(self)
        self._mainLayout.addWidget(self._statusBar)
        self._statusBar.setVisible(False)  # hide for now

    def __getViewPage(self, row, pageSize):
        """
        Return the corresponding page for a specific row where pageSize is
        the number of items for one page.
        First row is 0.
        First page is 0.
        """
        return int(row / pageSize) if pageSize > 0 else 0

    def __loadElementData(self, row, imgColumn=0):
        """
        Load the element data in the view element table for the specific row
        First row is 0.
        row: row in current model
        imgColumn: selected image column
        """
        if self._tableModel and row in range(self._tableModel.totalRowCount()):
            model = self._elemViewTable.model()
            model.clear()
            vLabels = []
            for i in range(self._tableModel.columnCount()):
                item = QStandardItem()
                item.setData(self._tableModel.getTableData(row, i),
                             Qt.DisplayRole)
                if i == imgColumn:
                    imgPath = self._tableModel.getTableData(row, i)
                    imgParams = parseImagePath(imgPath)
                    if imgParams is not None and len(imgParams) == 3:
                        imgPath = imgParams[2]
                        if EmPath.isStandardImage(imgPath):
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

                            data = self._imageCache.addImage(id, imgPath,
                                                             index)
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
                label = self._tableModel.headerData(i, Qt.Horizontal)
                if label:
                    vLabels.append(label)
            model.setHorizontalHeaderLabels(["Values"])
            model.setVerticalHeaderLabels(vLabels)
            self._elemViewTable.horizontalHeader().setStretchLastSection(True)
            self.sigCurrentElementItemChanged.emit(row, imgColumn)

    def __loadViewPage(self, page):
        """ Load the current view page """

        if self._tableModel:
            if self._viewName == self.ITEMS:
                self.__loadElementData(page,
                                       self._currentRenderableColumn)
                self._spinBoxCurrentRow.setValue(page + 1)
                self._tableModel.setupPage(self._itemsXItemPage, page)
            else:
                pageSize = self._itemsXTablePage \
                    if self._viewName == self.COLUMNS else self._itemsXGalleryPage
                self._tableModel.setupPage(pageSize, page)
            self._showCurrentPageNumber()

    def __canChangeToView(self, view):
        """
        Return True if mode can be changed, False if not.
        If mode == currentMode then return False
        :param mode: Possible values are: COLUMNS, GALLERY, ITEMS
        """
        if self._viewName == self.COLUMNS:
            if view == self.COLUMNS:
                return False
            elif view == self.GALLERY or view == self.ITEMS:
                if self._tableView:
                    for colConfig in self._tableModel.getColumnConfig():
                        if colConfig["renderable"] and colConfig["visible"]:
                            return True
                return False
        elif self._viewName == self.GALLERY:
            if view == self.COLUMNS or view == self.ITEMS:
                return True
        elif self._viewName == self.ITEMS:
            if view == self.COLUMNS or view == self.GALLERY:
                return True

        return False

    def __setupDelegatesForColumns(self):
        """
        Sets the corresponding Delegate for all columns
        """
        return  # FIXME
        # we have defined one delegate for the moment: ImageItemDelegate
        if self._tableModel:
            createDelegates = not self._columnDelegates or \
                              self._columnDelegates.get(
                                  self._tableModel.getTitle()) is None
            for i, colConfig in enumerate(self._tableModel.getColumnConfig()):
                delegate = self._defaultTableViewDelegate
                if colConfig["renderable"] and \
                        colConfig["visible"]:
                    if createDelegates:
                        delegate = EMImageItemDelegate(self._tableView)
                        delegate.setImageCache(self._imageCache)
                        if self._columnDelegates is None:
                            self._columnDelegates = dict()

                        tableDelegates = self._columnDelegates.get(
                            self._tableModel.getTitle())
                        if tableDelegates is None:
                            tableDelegates = dict()
                            self._columnDelegates[
                                self._tableModel.getTitle()] = tableDelegates

                        tableDelegates[i] = delegate
                    else:
                        tableDelegates = self._columnDelegates.get(
                            self._tableModel.getTitle())
                        delegate = tableDelegates.get(i)

                    self._listView.setItemDelegateForColumn(i, delegate)
                #  Restore the default item delegate for column i
                self._tableView.setItemDelegateForColumn(i, delegate)

    def __setupVisibleColumns(self):
        """
        Hide the columns with visible property=True or allowSetVisible=False
        """
        for i, colConfig in enumerate(self._tableModel.getColumnConfig()):
            if not colConfig["visible"]:
                self._tableView.hideColumn(i)

    def __setupAllWidgets(self):
        """
        Configure all widgets:
           * set model for qtableview and qlistview widgets
           * set ImageDelegates for renderable columns
           * configure the value range for all spinboxs
           * configure the icon size for the model
           * show table dims

        Invoke this function when you needs to initialize all widgets.
        Example: when setting new model in the table view
        """

        self._tableView.setModel(self._tableModel)
        self._listView.setModel(self._tableModel)
        if self._tableModel:
            # FIXME
            # # ColumnView
            # self._tableView.selectionModel().currentChanged.connect(
            #     self._onCurrentTableViewItemChanged)
            # # GalleryView
            # self._listView.selectionModel().currentChanged.connect(
            #     self._onCurrentGalleryItemChanged)

            self._showTableDims()
            self.__setupVisibleColumns()
            self.__setupDelegatesForColumns()
            self.__setupSpinBoxRowHeigth()
            self._onChangeCellSize()
            self.__setupSpinBoxCurrentRow()
            self._spinBoxCurrentRow.setValue(1)
            self.__setupComboBoxCurrentColumn()

        self.__initCurrentRenderableColumn()
        self._onGalleryViewColumnChanged(0)

    def __setupSpinBoxRowHeigth(self):
        """ Configure the row height spinbox """
        self._spinBoxRowHeight.setRange(self._minRowHeight, self._maxRowHeight)
        self._spinBoxRowHeight.setValue(self._defaultRowHeight)

    def __setupComboBoxCurrentTable(self):
        """
        Configure the elements in combobox currentTable for user selection.
        """
        blocked = self._comboBoxCurrentTable.blockSignals(True)
        model = self._comboBoxCurrentTable.model()
        if not model:
            model = QStandardItemModel(self._comboBoxCurrentColumn)

        model.clear()
        if self._models and len(self._models):
            for i, currentModel in enumerate(self._models):
                item = QStandardItem(currentModel.getTitle())
                item.setData(0, Qt.UserRole)  # use UserRole for store
                model.appendRow([item])
        elif self._tableModel:
            item = QStandardItem(self._tableModel.getTitle())
            item.setData(0, Qt.UserRole)  # use UserRole for store
            model.appendRow([item])

        self._comboBoxCurrentTable.blockSignals(blocked)

    def __setupComboBoxCurrentColumn(self):
        """
        Configure the elements in combobox currentColumn for gallery vew mode
        """
        blocked = self._comboBoxCurrentColumn.blockSignals(True)
        model = self._comboBoxCurrentColumn.model()
        if not model:
            model = QStandardItemModel(self._comboBoxCurrentColumn)
        model.clear()

        if self._tableModel:
            for i, colConfig in enumerate(self._tableModel.getColumnConfig()):
                if colConfig["renderable"] and colConfig["visible"]:
                    item = QStandardItem(colConfig.getLabel())
                    item.setData(i, Qt.UserRole)  # use UserRole for store
                    model.appendRow([item])           # columnIndex

        self._comboBoxCurrentColumn.setModel(model)
        self._comboBoxCurrentColumn.blockSignals(blocked)

        self.__showCurrentColumnWidgets(not model.rowCount() == 0)

    def __showCurrentColumnWidgets(self, visible):
        """
        Set visible all current column widgets
        """
        self._actLabelCurrentColumn.setVisible(visible)
        self._actComboBoxCurrentColumn.setVisible(visible)

    def __setupCurrentViewMode(self):
        """
        Configure current view mode: COLUMN or GALLERY or ELEMENT
        """
        if self._viewName == self.COLUMNS:
            blocked = self._tableView.blockSignals(True)
            self._stackedLayoud.setCurrentWidget(self._tableViewContainer)
            self._tableView.blockSignals(blocked)

            if self._calcTablePageProperties:
                self.__calcTablePageProperties()
                page = self.__getViewPage(self._currentRow,
                                          self._itemsXTablePage)
                self.__loadViewPage(page)
            else:
                page = self.__getViewPage(self._currentRow,
                                          self._itemsXTablePage)
                self._tableModel.setupPage(self._itemsXTablePage, page)

        elif self._viewName == self.GALLERY:
            blocked = self._listView.blockSignals(True)
            self._stackedLayoud.setCurrentWidget(self._listViewContainer)
            self._listView.blockSignals(blocked)
            if self._calcGalleryPageProperties:
                self.__calcGalleryPageProperties()
                page = self.__getViewPage(self._currentRow,
                                          self._itemsXGalleryPage)
                self.__loadViewPage(page)
            else:
                page = self.__getViewPage(self._currentRow,
                                          self._itemsXTablePage)
                self._tableModel.setupPage(self._itemsXGalleryPage, page)

        elif self._viewName == self.ITEMS:
            pass
            # self._stackedLayoud.setCurrentWidget(self._elemViewContainer)
            # self.__calcElementPageProperties()
            # page = self.__getViewPage(self._currentRow,
            #                           self._itemsXItemPage)
            #
            # self._tableModel.setupPage(self._itemsXItemPage, page)
            # self.__loadViewPage(page)

        a = self._viewActions[self._viewName].get("action", None)
        if a:
            a.setChecked(True)

        self._selectRow(self._currentRow + 1)
        self._showCurrentPageNumber()
        self._showNumberOfPages()

    def __setupTableModel(self):
        """
        Configure the current table model in all view modes
        """
        self.__setupAllWidgets()
        self.__setupCurrentViewMode()

    def __setupSpinBoxCurrentRow(self):
        """
        Configure the spinBox range consulting table mode and table dims
        """
        if self._tableModel:
            mode = self.getSelectedViewMode()
            if mode == self.COLUMNS or mode == self.GALLERY or mode == self.ITEMS:
                self._spinBoxCurrentRow.setRange(1,
                                                 self._tableModel.totalRowCount())

    def __initCurrentRenderableColumn(self):
        """
        Set the currentRenderableColumn searching the first renderable column in
        the model. If there are no renderable columns or no model, the current
        column is the first: index 0
        """
        self._currentRenderableColumn = 0

        if self._tableModel:
            for i, colConfig in enumerate(self._tableModel.getColumnConfig()):
                if colConfig["renderable"]:
                    self._currentRenderableColumn = i
                    return

    def __createNewAction(self, parent, actionName, text="", faIconName=None,
                            checkable=False, slot=None):
        """
        Create a QAction with the given name, text and icon. If slot is not None
        then the signal QAction.triggered is connected to it
        :param actionName: The action name
        :param text: Action text
        :param faIconName: qtawesome icon name
        :param checkable: if this action is checkable
        :param slot: the slot to connect QAction.triggered signal
        :return: The QAction
        """
        a = QAction(parent)
        a.setObjectName(str(actionName))
        if faIconName:
            a.setIcon(qta.icon(faIconName))
        a.setCheckable(checkable)
        a.setText(str(text))

        if slot:
            a.triggered.connect(slot)
        return a

    def __goToPage(self, page):
        """
        Show the given page. The page number is depending of current
        view mode.
        First index is 0.
        """

        if self._tableModel and page in range(0,
                                              self._tableModel.getPageCount()):
            self.__loadViewPage(page)

    @pyqtSlot()
    def __galleryResized(self):
        """
        Invoked when gallery is resized.
        New page properties will be calculated
        """
        self.__calcGalleryPageProperties()
        if self._viewName == self.GALLERY:
            page = self.__getViewPage(self._currentRow,
                                      self._itemsXGalleryPage)
            self.__goToPage(page)
            self._selectRow(self._currentRow + 1)

    @pyqtSlot()
    def __elementTableResized(self):
        """
        Invoked when element table is resized
        """
        self._elemViewTable.resizeColumnsToContents()

    @pyqtSlot()
    def __tableResized(self):
        """
        Invoked when table is resized.
        New page properties will be calculated
        """
        self.__calcTablePageProperties()

        if self._viewName == self.COLUMNS:
            page = self.__getViewPage(self._currentRow,
                                      self._itemsXTablePage)
            self.__goToPage(page)
            self._selectRow(self._currentRow + 1)
            self._showNumberOfPages()
            self._showCurrentPageNumber()

    @pyqtSlot()
    def __calcTablePageProperties(self):
        """
        Calculates depending of table size:
         - itemsXTablePage
         If current view is COLUMS then load the current page
        """
        return   # FIXME

        self._itemsXTablePage = 0

        tableSize = self._tableView.viewport().size()
        rowSize = self._tableView.verticalHeader().defaultSectionSize()

        if tableSize.width() > 0 and tableSize.height() > 0 and rowSize:
            pRows = int(tableSize.height() / rowSize)
            # if tableSize.width() < rowSize.width() pRows may be 0
            if pRows == 0:
                pRows = 1

            self._itemsXTablePage = pRows

            if self._tableModel and self._viewName == self.COLUMNS:
                page = self.__getViewPage(self._currentRow,
                                          self._itemsXTablePage)
                self._tableModel.setupPage(self._itemsXTablePage, page)
                self.__loadViewPage(page)
                self._spinBoxCurrentPage.setRange(1,
                                                  self._tableModel.
                                                  getPageCount())
                self._showNumberOfPages()
            self._calcTablePageProperties = False

    @pyqtSlot()
    def __calcElementPageProperties(self):
        """
        Calculates the element view page properties. In ITEMS view mode,
        the number of pages is the table row count.
        If current view is ITEMS then load the current item
        """
        return  # FIXME

        if self._tableModel and self._viewName == self.ITEMS:
            self._tableModel.setupPage(self._itemsXItemPage, self._currentRow)
            self._spinBoxCurrentPage.setRange(1,
                                              self._tableModel.totalRowCount())
            self.__loadViewPage(self._currentRow)
            self._showNumberOfPages()
            self._showCurrentPageNumber()

    @pyqtSlot()
    def __calcGalleryPageProperties(self):
        """
        Calculates the gallery page properties depending of gallery size:
         - itemsXGalleryPage
        If current view is GALLERY then load the current page
        """
        return

        self._itemsXGalleryPage = 0

        gallerySize = self._listView.viewport().size()
        iconSize = self._listView.iconSize()
        spacing = self._listView.spacing()

        if gallerySize.width() > 0 and gallerySize.height() > 0 \
                and iconSize.width() > 0 and iconSize.height() > 0:
            pCols = int((gallerySize.width() - spacing - 1)
                        / (iconSize.width() + spacing))
            pRows = int((gallerySize.height() - 1) /
                        (iconSize.height() + spacing))
            # if gallerySize.width() < iconSize.width() pRows may be 0
            if pRows == 0:
                pRows = 1
            if pCols == 0:
                pCols = 1

            pTotal = self._tableModel.totalRowCount() / (pCols * pRows)

            galleryPageCount = int(pTotal)
            galleryPageCount += 1 if pTotal - int(pTotal) > 0 else 0
            self._itemsXGalleryPage = pRows * pCols
            if self._tableModel and self._viewName == self.GALLERY:
                page = self.__getViewPage(self._currentRow,
                                          self._itemsXGalleryPage)
                self._tableModel.setupPage(self._itemsXGalleryPage, page)
                self.__loadViewPage(page)
                self._spinBoxCurrentPage.setRange(1,
                                                  self._tableModel.
                                                  getPageCount())
                self._showNumberOfPages()
            self._calcGalleryPageProperties = False

    def _onGalleryViewItemDoubleClicked(self, qModelIndex):
        """
        Invoked when a mouse button is double-clicked over a item
        :param qModelIndex:
        """
        self.sigGalleryItemDoubleClicked.emit(self._currentRow,
                                              qModelIndex.column())

    @pyqtSlot(int)
    def _onCurrentTableChanged(self, index):
        """
        Invoked when user change the current table for display content
        """
        self._currentTable = self._comboBoxCurrentTable.\
            currentData(Qt.UserRole)

        if self._models and len(self._models) > 0 \
                and self._currentTable in range(0, len(self._models)):
            self._tableModel = self._models[
                self._comboBoxCurrentTable.currentIndex()]
            self.__setupTableModel()

    @pyqtSlot(int)
    def _onGalleryViewColumnChanged(self, index):
        """
         Invoked when user change the view column in gallery mode
         :param index: index in the combobox model
         """
        if self._comboBoxCurrentColumn.model().rowCount():
            self._currentRenderableColumn = self._comboBoxCurrentColumn. \
                currentData(Qt.UserRole)
        else:
            self._currentRenderableColumn = 0

        if self._tableModel:
            if self._comboBoxCurrentColumn.model().rowCount():
                self._listView.setModelColumn(self._currentRenderableColumn)
            if self._viewName == self.GALLERY:
                page = self.__getViewPage(self._currentRow,
                                          self._itemsXGalleryPage)
                self.__loadViewPage(page)
                self._selectRow(self._currentRow + 1)
            elif self._viewName == self.ITEMS:
                page = self.__getViewPage(self._currentRow,
                                          self._itemsXItemPage)
                self.__loadViewPage(page)
                self._selectRow(self._currentRow + 1)

    @pyqtSlot()
    def _onChangeCellSize(self):
        """
        This slot is invoked when the cell size need to be rearranged
        TODO:[developers]Review implementation. Change row height for the moment
        """
        return # FIXME

        size = self._spinBoxRowHeight.value()

        qsize = QSize(size, size)
        self._tableView.verticalHeader().setDefaultSectionSize(size)
        if self._models:
            for model in self._models:
                model.setIconSize(qsize)
        if self._tableModel:
            self._tableModel.setIconSize(qsize)
            cConfig = self._tableModel.getColumnConfig()
            if cConfig:
                for i, colConfig in enumerate(cConfig):
                    if colConfig["renderable"] and \
                            colConfig["visible"]:
                        self._tableView.setColumnWidth(i, size)

        self._listView.setIconSize(qsize)

        if self._viewName == self.GALLERY:
            self.__calcGalleryPageProperties()
            page = self.__getViewPage(self._currentRow, self._itemsXGalleryPage)
            self.__goToPage(page)
            self._calcTablePageProperties = True
        elif self._viewName == self.COLUMNS:
            self.__calcTablePageProperties()
            page = self.__getViewPage(self._currentRow, self._itemsXTablePage)
            self.__goToPage(page)
            self._calcGalleryPageProperties = True
        elif self._viewName == self.ITEMS:
            self._calcGalleryPageProperties = True
            self._calcTablePageProperties = True

        self._selectRow(self._currentRow + 1)
        self._showNumberOfPages()
        self._showCurrentPageNumber()

    @pyqtSlot()
    def _showTableDims(self):
        """
        Show column and row count in the QLineEdits
        """
        if self._tableModel:
            self._lineEditRows.setText("%i" % self._tableModel.totalRowCount())
            self._lineEditCols.setText("%i" % self._tableModel.columnCount(None))

    @pyqtSlot(int)
    def _selectRow(self, row):
        """
        This slot is invoked when the value of the current spinbox changes.
        If GALLERY mode is selected and row > pageSize then load the new page.
        If TABLE mode is selected, and row > pageSize the then load
        the new page.
        :param row: the row, 1 is the first
        """
        if self._tableModel:
            if row in range(1, self._tableModel.totalRowCount() + 1):
                self._currentRow = row - 1
                if self._viewName == self.COLUMNS:
                    page = self.__getViewPage(row - 1, self._itemsXTablePage)
                    if not page == self._tableModel.getCurrentPage():
                        self.__goToPage(page)
                    if self._itemsXTablePage:
                        self._tableView.selectRow(
                            int(self._currentRow % self._itemsXTablePage))
                elif self._viewName == self.GALLERY:
                    if self._itemsXGalleryPage:
                        galleryRow = (row - 1) % self._itemsXGalleryPage

                        page = self.__getViewPage(row - 1,
                                                  self._itemsXGalleryPage)
                        if not page == self._tableModel.getCurrentPage():
                            self.__goToPage(page)
                        index = self._listView.model().\
                            createIndex(galleryRow,
                                        self._currentRenderableColumn)
                        if index.isValid():
                            self._listView.setCurrentIndex(index)
                elif self._viewName == self.ITEMS:
                    page = self.__getViewPage(row - 1, self._itemsXItemPage)
                    self.__goToPage(page)
                    self._showCurrentPageNumber()

    @pyqtSlot(QModelIndex, QModelIndex)
    def _onCurrentTableViewItemChanged(self, current, previous):
        """
        This slot is invoked when the current table item change
        """
        return  #FIXME
        col = row = -1
        if current.isValid():
            row = current.row() + self._tableModel.getCurrentPage() \
                  * self._itemsXTablePage
            col = current.column()
            if not row == self._currentRow:
                self._currentRow = row
                if not self._spinBoxCurrentRow.value() == row + 1:
                    self._spinBoxCurrentRow.setValue(self._currentRow + 1)
            self._showCurrentPageNumber()

        self.sigCurrentTableItemChanged.emit(row, col)

    @pyqtSlot(QModelIndex, QModelIndex)
    def _onCurrentGalleryItemChanged(self, current, previous):
        """
        This slot is invoked when the current gallery item change.
        """
        return  # FIXME
        col = row = -1
        if current.isValid():
            row = current.row()
            col = current.column()
            self._currentRow = \
                row + self._tableModel.getCurrentPage() \
                * self._itemsXGalleryPage
            if not self._spinBoxCurrentRow.value() == self._currentRow + 1:
                self._spinBoxCurrentRow.setValue(self._currentRow + 1)

        self.sigCurrentGalleryItemChanged.emit(row, col)

    @pyqtSlot(bool)
    def _onChangeViewTriggered(self, checked):
        """
        This slot is invoked when a view action is triggered
        """
        return  # FIXME
        a = self._actionGroupViews.checkedAction()

        if a and checked:
            view = self._viewTypes[a.objectName()]
            if self.__canChangeToView(view):
                self._viewName = view
                self.__setupCurrentViewMode()

    @pyqtSlot(bool)
    def _onListNextPage(self, checked=True):
        """ This slot is invoked when the user clicks next page """
        if self._tableModel:
            self.__goToPage(self._tableModel.getCurrentPage() + 1)
            self._showCurrentPageNumber()

    @pyqtSlot(bool)
    def _onListPrevPage(self, checked=True):
        """ This slot is invoked when the user clicks prev page """
        if self._tableModel:
            self.__goToPage(self._tableModel.getCurrentPage() - 1)
            self._showCurrentPageNumber()

    @pyqtSlot()
    def _onSpinBoxCurrentPageEditingFinished(self):
        """
        Invoked when editing is finished. This happens when the spinbox loses
        focus and when enter is pressed.
        """
        if self._tableModel:
            page = self._spinBoxCurrentPage.value() - 1
            if not self._tableModel.getCurrentPage() == page and \
                    page in range(0, self._tableModel.getPageCount()):
                self.__goToPage(page)

    @pyqtSlot()
    def _showCurrentPageNumber(self):
        """
        Show the currentPage number in the corresponding widget.
        """
        pass  # FIXME
        # if self._tableModel:
        #     self._spinBoxCurrentPage.setValue(
        #         self._tableModel.getCurrentPage() + 1)

    @pyqtSlot()
    def _showNumberOfPages(self):
        """
        Show the number of pages depending of current view mode.
        Now: _labelPageCount
        """
        pass  # FIXME
        # if self._tableModel:
        #     self._labelPageCount.setText(
        #         "of %i" % self._tableModel.getPageCount())

    def getSelectedViewMode(self):
        """
        Return the selected mode. Possible values are: TABLE, GALLERY, ELEMENT
        """
        a = self._actionGroupViews.checkedAction()
        return self._viewTypes[a.objectName()] if a else None

    def setModel(self, model, delegates=None):
        """
        Set the table model or models for display.

        model: list of models or a TableDataModel for single table

        delegates: dict<str,dict<int, EMImageItemDelegate>>.
                   delegates keys: table model title
        """
        self._models = None
        self._tableModel = None
        self._columnDelegates = delegates

        if isinstance(model, list):
            if len(model) > 0:
                self._tableModel = model[0]

            self._models = model
        elif isinstance(model, TableDataModel):
            self._tableModel = model

        self.__setupComboBoxCurrentTable()
        self.__setupTableModel()

    def getModel(self):
        """
        Return the model for this table
        """
        return self._tableModel

    def setSortRole(self, role):
        """
        Set the item role that is used to query the source model's data
        when sorting items
        :param role:
                    Qt.DisplayRole
                    Qt.DecorationRole
                    Qt.EditRole
                    Qt.ToolTipRole
                    Qt.StatusTipRole
                    Qt.WhatsThisRole
                    Qt.SizeHintRole
        """
        self._sortRole = role

    def setItemDelegateForColumn(self, column, delegate, modelIndex=-1):
        """
        Sets the given item delegate used by this table view and model
        for the given column. All items on column will be drawn and managed
        by delegate instead of using the default delegate. Any existing column
        delegate for column will be removed, but not deleted. TableView does not
        take ownership of delegate.
        First column index is 0.
        """
        if self._models:
            if modelIndex == -1:
                for model in self._models:
                    self._columnDelegates[model.getTitle()] = delegate
            else:
                self._columnDelegates[
                    self._models[modelIndex].getTitle()] = delegate

            model = self._models[modelIndex] if not modelIndex == -1 \
                else self._tableModel
            if self._tableModel == model:
                self._listView.setItemDelegateForColumn(
                    column,
                    self._columnDelegates[model.getTitle()])
        else:
            self._tableView.setItemDelegateForColumn(column, delegate)
            self._listView.setItemDelegateForColumn(column, delegate)

    def setup(self, **kwargs):
        self.__initProperties(**kwargs)
        self.__setupImageView()

    def showToolBar(self, visible):
        """ Show or hide the toolbar """
        self._toolBar.setVisible(visible)

    def showPageBar(self, visible):
        """ Show or hide the page bar """
        self._pagingLayout.setVisible(visible)

    def showStatusBar(self, visible):
        """ Show or hide the status bar """
        self._statusBar.setVisible(visible)

    def getViewName(self):
        """ Return the current view """
        return self._viewName

    def setView(self, view):
        """ Sets view as current view """
        if view in self._views and self.__canChangeToView(view):
            self._viewName = view
            self.__setupCurrentViewMode()

    def getAvailableViews(self):
        """ Return the available views """
        return self._views

    def setAvailableViews(self, views):
        """ Sets the available views
        TODO: If current view not in views?"""
        li = [self.COLUMNS, self.GALLERY, self.ITEMS]
        n = []
        for v in views:
            va = self._viewActions[v]
            action = va["action"]
            if v in li:
                n.append(v)
                action.setVisible(True)
            else:
                action.setVisible(False)
        if n:
            self._views = n

    def getPage(self):
        """ Return the current page for current view
        or -1 if current table model is None """
        return -1 if self._tableModel is None \
            else self._tableModel.getCurrentPage()

    def setPage(self, page):
        """ Change to page for the current view """
        self.__goToPage(page)

    def getPageCount(self):
        """ Return the page count for the current view or -1 if current model
        is None """
        return -1 if self._tableModel is None else self._tableModel.getPageCount()

    def __initProperties(self, **kwargs):
        """ Configure all properties  """
        self._defaultRowHeight = kwargs.get("defaultRowHeight", 20)
        self._maxRowHeight = kwargs.get("maxRowHeight", 250)
        self._minRowHeight = kwargs.get("minRowHeight", 5)
        self._zoomUnits = kwargs.get("zoomUnits", PIXEL_UNITS)
        self._viewName = kwargs.get("view", self.COLUMNS)
        self._views = kwargs.get("views", [self.COLUMNS, self.GALLERY,
                                           self.ITEMS])

        self._disableHistogram = kwargs.get("disableHistogram", False)
        self._disableMenu = kwargs.get("disableMenu", False)
        self._disableROI = kwargs.get("disableROI", False)
        self._disablePopupMenu = kwargs.get("disablePopupMenu", False)
        self._disableFitToSize = kwargs.get("disableFitToSize", False)

    def __setupImageView(self):
        for v in self._actionGroupViews.actions():
            v.setVisible(self._viewTypes[v.objectName()] in self._views)

        if self._disableHistogram:
            self._imageView.ui.histogram.hide()
        if self._disableMenu:
            self._imageView.ui.menuBtn.hide()
        if self._disableROI:
            self._imageView.ui.roiBtn.hide()
        if self._disablePopupMenu:
            self._imageView.getView().setMenuEnabled(False)

