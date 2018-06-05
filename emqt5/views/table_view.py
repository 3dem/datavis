#!/usr/bin/python
# -*- coding: utf-8 -*-


from PyQt5.QtCore import (Qt, pyqtSlot, pyqtSignal, QSize, QRectF,
                          QItemSelectionModel, QModelIndex)
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QToolBar, QAction,
                             QTableView, QSpinBox, QLabel, QStyledItemDelegate,
                             QStyle, QAbstractItemView,
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
from .model import ImageCache, TableDataModel


TABLE_VIEW_MODE = 'TABLE'
GALLERY_VIEW_MODE = 'GALLERY'
ELEMENT_VIEW_MODE = 'ELEMENT'

PIXEL_UNITS = 1
PERCENT_UNITS = 2

X_AXIS = 0
Y_AXIS = 1
Z_AXIS = 2
N_DIM = -1


class TableView(QWidget):
    """
    Widget used for display table contend
    """

    """ This signal is emitted when the current item change in TABLE mode """
    sigCurrentTableItemChanged = pyqtSignal(int, int)

    """ This signal is emitted when the current item change in GALLERY mode """
    sigCurrentGalleryItemChanged = pyqtSignal(int, int)

    """ This signal is emitted when the current item change in GALLERY mode """
    sigCurrentElementItemChanged = pyqtSignal(int, int)

    """ This signal is emitted when a mouse button is double-clicked 
        in GALLERY mode """
    sigGalleryItemDoubleClicked = pyqtSignal(int, int)

    def __init__(self, **kwargs):
        QWidget.__init__(self, kwargs.get("parent", None))
        self._calcTablePageProperties = True
        self._calcGalleryPageProperties = True

        self._defaultRowHeight = 50
        self._maxRowHeight = 50
        self._minRowHeight = 50
        self._zoomUnits = PIXEL_UNITS
        self._defaultView = TABLE_VIEW_MODE
        self._views = [TABLE_VIEW_MODE, GALLERY_VIEW_MODE, ELEMENT_VIEW_MODE]
        self._disableHistogram = None
        self._disableMenu = None
        self._disableROI = None
        self._disablePopupMenu = None
        self._disableFitToSize = None

        self._viewActionIcons = {TABLE_VIEW_MODE: "fa.table",
                                 GALLERY_VIEW_MODE: "fa.image",
                                 ELEMENT_VIEW_MODE: "fa.file-image-o"}
        self._viewActions = []
        self._tableModel = None
        self._models = None
        self._tableViewSelectionModel = QItemSelectionModel(None, self)
        self._galleryViewSelectionModel = QItemSelectionModel(None, self)
        self._currentRenderableColumn = 0  # for GALLERY mode
        self._currentRow = 0  # selected table row
        self._currentViewMode = self._defaultView
        self._currentGalleryPage = 0
        self._itemsXGalleryPage = 0
        self._galleryPageCount = 0
        self._galleryPageRows = 0
        self._galleryPageColumns = 0
        self._tablePageCount = 0
        self._itemsXTablePage = 0
        self._currentTablePage = 0
        self._currentElementPage = 0
        self._imageCache = ImageCache(50, 50)
        self._columnDelegates = {}
        self.__setupUi()
        self._defaultTableViewDelegate = self._tableView.itemDelegate()
        self._defaultGalleryViewDelegate = self._listView.itemDelegate()
        self.setup(**kwargs)
        self.__setupCurrentViewMode()

    def __setupUi(self):
        self._mainLayout = QVBoxLayout(self)
        self._toolBar = QToolBar(self)
        self._mainLayout.addWidget(self._toolBar)
        self._stackedLayoud = QStackedLayout(self._mainLayout)
        # table view
        self._tableViewContainer = QWidget(self)
        self._tableView = TableWidget(self._tableViewContainer)
        verticalLayout = QVBoxLayout(self._tableViewContainer)
        verticalLayout.addWidget(self._tableView)
        self._tableView.setSelectionBehavior(QTableView.SelectRows)
        self._tableView.verticalHeader().hide()
        self._tableView.setSortingEnabled(True)
        self._tableView.setModel(self._tableModel)
        self._tableView.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # gallery view
        self._listViewContainer = QWidget(self)
        self._listView = GalleryViewWidget(self._listViewContainer)
        self._listView.installEventFilter(self)
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
        self._listView.setModel(None)
        self._listView.doubleClicked.connect(
            self._onGalleryViewItemDoubleClicked)
        sModel = self._listView.selectionModel()
        if sModel:
            sModel.currentChanged.connect(self._onCurrentGalleryItemChanged)

        self._galleryLayout = QVBoxLayout(self._listViewContainer)
        self._galleryLayout.addWidget(self._listView)
        # element view
        self._elemViewContainer = QSplitter(self)
        self._elemViewContainer.setOrientation(Qt.Horizontal)
        self._imageView = pg.ImageView(parent=self._elemViewContainer)

        self._pixMapElem = QPixmap()
        self._pixmapItem = QGraphicsPixmapItem(self._pixMapElem)
        self._imageView.getView().addItem(self._pixmapItem)
        self._elemViewTable = TableWidget(self._elemViewContainer)
        self._elemViewTable.setModel(QStandardItemModel(self._elemViewTable))
        # pagination
        self._pagingLayout = QHBoxLayout()
        self._pagingLayout.addItem(QSpacerItem(40,
                                               20,
                                               QSizePolicy.Expanding,
                                               QSizePolicy.Minimum))
        self._pushButtonPrevPage = QPushButton(self._listViewContainer)
        self._pagingLayout.addWidget(self._pushButtonPrevPage)
        self._pushButtonPrevPage.setIcon(qta.icon('fa.angle-left'))
        self._pushButtonPrevPage.clicked.connect(self._onListPrevPage)
        self._spinBoxCurrentPage = QSpinBox(self._listViewContainer)
        self._spinBoxCurrentPage.setButtonSymbols(QSpinBox.NoButtons)
        self._spinBoxCurrentPage.editingFinished.connect(
            self._onSpinBoxCurrentPageEditingFinished)
        self._spinBoxCurrentPage.setMaximumSize(50, 25)
        self._spinBoxCurrentPage.setMinimumSize(50, 25)
        self._pagingLayout.addWidget(self._spinBoxCurrentPage)
        self._labelPageCount = QLabel(self._listViewContainer)
        self._pagingLayout.addWidget(self._labelPageCount)
        self._pushButtonNextPage = QPushButton(self._listViewContainer)
        self._pushButtonNextPage.setIcon(qta.icon('fa.angle-right'))
        self._pushButtonNextPage.clicked.connect(self._onListNextPage)
        self._pagingLayout.addWidget(self._pushButtonNextPage)
        self._pagingLayout.addItem(QSpacerItem(40,
                                               20,
                                               QSizePolicy.Expanding,
                                               QSizePolicy.Minimum))
        self._mainLayout.addLayout(self._pagingLayout)

        self._stackedLayoud.addWidget(self._tableViewContainer)
        self._stackedLayoud.addWidget(self._listViewContainer)
        self._stackedLayoud.addWidget(self._elemViewContainer)
        self._listView.sigSizeChanged.connect(self.__galleryResized)
        self._tableView.sigSizeChanged.connect(self.__tableResized)
        self._actionGroupViews = QActionGroup(self._toolBar)
        self._actionGroupViews.setExclusive(True)
        for view in self._views:
            #  create action with name=view
            a = self.__createNewAction(self._toolBar, view, view,
                                         self._viewActionIcons.get(
                                          view,
                                          "fa.info-circle"),
                                         True, self._onChangeViewTriggered)
            self._actionGroupViews.addAction(a)
            self._toolBar.addAction(a)
            if view == self._defaultView:
                a.setChecked(True)

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
        verticalHeader = self._tableView.verticalHeader()
        verticalHeader.setSectionResizeMode(QHeaderView.Fixed)

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

    def __resetGalleryView(self):
        """
        Clear the gallery model and reset the values for:
        currentGalleryPage
        galleryPageCount
        itemsXGalleryPage
        """
        self._galleryPageCount = 0
        self._currentGalleryPage = 0
        self._itemsXGalleryPage = 0

    def __getGalleryPage(self, row):
        """
        Return the corresponding gallery page for a specific table row
        First row is 0
        """
        if self._itemsXGalleryPage > 0:
            return int(row / self._itemsXGalleryPage)

        return 0

    def __getTablePage(self, row):
        """
        Return the corresponding table page for a specific row
        First row is 0
        """
        if self._itemsXTablePage > 0:
            return int(row / self._itemsXTablePage)

        return 0

    def __loadElementData(self, row, imgColumn=0):
        """
        Load the element data in the view element table for the specific row
        First row is 0.
        row: row in TableModel
        imgColumn: selected image column
        """
        if self._tableModel and row in range(0,
                                             self._tableModel.totalRowCount()):
            model = self._elemViewTable.model()
            model.clear()
            vLabels = []
            for i in range(0, self._tableModel.columnCount()):
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

    def __loadCurrentGalleryPage(self):
        """
        Load the gallery page in the gallery view
        """
        if self._tableModel and self._galleryPageCount:
            self._currentTablePage = self.__getGalleryPage(
                self._currentRow - 1)
            self._tableModel.setupPage(self._itemsXGalleryPage,
                                       self._currentGalleryPage)
        self._showCurrentPageNumber()

    def __loadCurrentTablePage(self):
        """
        Load the table page in the table view
        """
        if self._tableModel and self._tablePageCount:
            self._currentTablePage = self.__getTablePage(self._currentRow - 1)
            self._tableModel.setupPage(self._itemsXTablePage,
                                       self._currentTablePage)
        self._showCurrentPageNumber()

    def __canChangeToMode(self, mode):
        """
        Return True if mode can be changed, False if not.
        If mode == currentMode then return False
        :param mode: Possible values are: TABLE, GALLERY, ELEMENT
        """
        if self._currentViewMode == TABLE_VIEW_MODE:
            if mode == TABLE_VIEW_MODE:
                return False
            elif mode == GALLERY_VIEW_MODE or mode == ELEMENT_VIEW_MODE:
                if self._tableView:
                    for colConfig in self._tableModel.getColumnConfig():
                        if colConfig["renderable"] and \
                                colConfig["visible"]:
                            return True
                return False
        elif self._currentViewMode == GALLERY_VIEW_MODE:
            if mode == TABLE_VIEW_MODE or mode == ELEMENT_VIEW_MODE:
                return True
        elif self._currentViewMode == ELEMENT_VIEW_MODE:
            if mode == TABLE_VIEW_MODE or mode == GALLERY_VIEW_MODE:
                return True

        return False

    def __setupDelegatesForColumns(self):
        """
        Sets the corresponding Delegate for all columns
        """
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
            # table
            self._tableView.selectionModel().currentChanged.connect(
                self._onCurrentTableViewItemChanged)
            self._listView.selectionModel().currentChanged.connect(
                self._onCurrentGalleryItemChanged)

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
            for index, colConfig in \
                    enumerate(self._tableModel.getColumnConfig()):
                if colConfig["renderable"] and \
                        colConfig["visible"]:
                    item = QStandardItem(colConfig.getLabel())
                    item.setData(index, Qt.UserRole)  # use UserRole for store
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
        Configure current view mode: TABLE or GALLERY or ELEMENT
        TODO: ELEMENT VIEW MODE
        """
        if self._currentViewMode == TABLE_VIEW_MODE:
            blocked = self._tableView.selectionModel().blockSignals(True)
            self._stackedLayoud.setCurrentWidget(self._tableViewContainer)
            self._tableView.selectionModel().blockSignals(blocked)
            if self._calcTablePageProperties:
                self.__calcTablePageProperties()
            self.__loadCurrentTablePage()
        elif self._currentViewMode == GALLERY_VIEW_MODE:
            blocked = self._listView.selectionModel().blockSignals(True)
            self._stackedLayoud.setCurrentWidget(self._listViewContainer)
            self._listView.selectionModel().blockSignals(blocked)
            if self._calcGalleryPageProperties:
                self.__calcGalleryPageProperties()
            self.__loadCurrentGalleryPage()
        elif self._currentViewMode == ELEMENT_VIEW_MODE:
            self._stackedLayoud.setCurrentWidget(self._elemViewContainer)
            self.__calcElementPageProperties()

        for a in self._actionGroupViews.actions():
            if a.objectName() == self._currentViewMode:
                a.setChecked(True)
                break

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
            if mode == TABLE_VIEW_MODE or mode == GALLERY_VIEW_MODE \
                    or mode == ELEMENT_VIEW_MODE:
                self._spinBoxCurrentRow.setRange(1, self._tableModel.totalRowCount())

    def __initCurrentRenderableColumn(self):
        """
        Set the currentRenderableColumn searching the first renderable column in
        the model. If there are no renderable columns or no model, the current
        column is the first: index 0
        """
        self._currentRenderableColumn = 0

        if self._tableModel:
            for index, colConfig in \
                    enumerate(self._tableModel.getColumnConfig()):
                if colConfig["renderable"]:
                    self._currentRenderableColumn = index
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
        :param slot: the slot ti connect QAction.triggered signal
        :return: The QAction
        """
        a = QAction(parent)
        a.setObjectName(actionName)
        if faIconName:
            a.setIcon(qta.icon(faIconName))
        a.setCheckable(checkable)
        a.setText(text)

        if slot:
            a.triggered.connect(slot)
        return a

    def __scrollTableToPage(self, page):
        """
        Scroll the table to specified page. The first row of the page is
        scrolled to top.
        First index is 0
        """
        if page in range(0, self._tablePageCount):
            sb = self._tableView.verticalScrollBar()
            sb.setValue(page * sb.pageStep())

    def __goToPage(self, page, reload=False):
        """
        Show the specified page. The page number is depending of current
        view mode. If reload==True then page will be reloaded
        First index is 0.
        """
        if self._currentViewMode == TABLE_VIEW_MODE:
            reload = reload or not page == self._currentTablePage
            if reload and page in range(0, self._tablePageCount):
                self._currentTablePage = page
                if self._tableModel:
                    self._tableModel.loadPage(self._currentTablePage)
        elif self._currentViewMode == GALLERY_VIEW_MODE:
            reload = reload or not page == self._currentGalleryPage
            if reload and page in range(0, self._galleryPageCount):
                self._currentGalleryPage = page
                self.__loadCurrentGalleryPage()
        elif self._currentViewMode == ELEMENT_VIEW_MODE:
            reload = reload or not page == self._currentElementPage
            if reload and page in range(0, self._tableModel.totalRowCount()):
                self._currentElementPage = page
                self.__loadElementData(page,
                                         self._currentRenderableColumn)
                self._spinBoxCurrentRow.setValue(self._currentElementPage + 1)

    @pyqtSlot()
    def __galleryResized(self):
        """
        Invoked when gallery is resized.
        New page properties will be calculated
        """
        self.__calcGalleryPageProperties()
        self._currentGalleryPage = self.__getGalleryPage(self._currentRow)
        if self._currentViewMode == GALLERY_VIEW_MODE:
            self.__goToPage(self._currentGalleryPage, True)
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
        self._currentTablePage = self.__getTablePage(self._currentRow)

        if self._currentViewMode == TABLE_VIEW_MODE:
            self.__goToPage(self._currentTablePage, True)
            self._selectRow(self._currentRow + 1)
            self._showNumberOfPages()
            self._showCurrentPageNumber()

    @pyqtSlot()
    def __calcTablePageProperties(self):
        """
        Calculates depending of table size:
         - tablePageCount
         - itemsXTablePage
        """
        self._tablePageCount = 0
        self._itemsXTablePage = 0

        tableSize = self._tableView.viewport().size()
        rowSize = self._tableView.verticalHeader().defaultSectionSize()

        if tableSize.width() > 0 and tableSize.height() > 0 and rowSize:
            pRows = int(tableSize.height() / rowSize)
            # if tableSize.width() < rowSize.width() pRows may be 0
            if pRows == 0:
                pRows = 1

            self._itemsXTablePage = pRows

            if self._tableModel:
                self._tablePageCount = \
                    int(self._tableModel.totalRowCount() / pRows)
                if self._tableModel.totalRowCount() % pRows:
                    self._tablePageCount += 1

            if self._currentViewMode == TABLE_VIEW_MODE:
                self.__loadCurrentTablePage()
                self._spinBoxCurrentPage.setRange(1, self._tablePageCount)
                self._showNumberOfPages()
            self._calcTablePageProperties = False

    @pyqtSlot()
    def __calcElementPageProperties(self):
        """
        Calculates the element view page properties. In ELEMENT view mode,
        the number of pages is the table row count
        """
        if self._tableModel and self._currentViewMode == ELEMENT_VIEW_MODE:
            self._spinBoxCurrentPage.setRange(1,
                                              self._tableModel.totalRowCount())
            self._currentElementPage = self._currentRow
            self._showNumberOfPages()
            self._showCurrentPageNumber()

    @pyqtSlot()
    def __calcGalleryPageProperties(self):
        """
        Calculates the gallery page properties depending of gallery size:
         - galleryPageCount
         - itemsXGalleryPage
        """
        self._galleryPageCount = 0
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

            self._galleryPageRows = pRows
            self._galleryPageColumns = pCols
            self._galleryPageCount = int(pTotal)
            self._galleryPageCount += 1 if pTotal - int(pTotal) > 0 else 0
            self._itemsXGalleryPage = pRows * pCols
            if self._currentViewMode == GALLERY_VIEW_MODE:
                self.__loadCurrentGalleryPage()
                self._spinBoxCurrentPage.setRange(1, self._galleryPageCount)
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
            if self._currentViewMode == GALLERY_VIEW_MODE:
                self.__loadCurrentGalleryPage()
                self._selectRow(self._currentRow + 1)
            elif self._currentViewMode == ELEMENT_VIEW_MODE:
                self._selectRow(self._currentRow + 1)

    @pyqtSlot()
    def _onChangeCellSize(self):
        """
        This slot is invoked when the cell size need to be rearranged
        TODO:[developers]Review implementation. Change row height for the moment
        """
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

        if self._currentViewMode == GALLERY_VIEW_MODE:
            self.__calcGalleryPageProperties()
            page = self.__getGalleryPage(self._currentRow)
            self.__goToPage(page, True)
            self._calcTablePageProperties = True
        elif self._currentViewMode == TABLE_VIEW_MODE:
            self.__calcTablePageProperties()
            page = self.__getTablePage(self._currentRow)
            self.__goToPage(page, True)
            self._calcGalleryPageProperties = True
        elif self._currentViewMode == ELEMENT_VIEW_MODE:
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
        If GALLERY mode is selected and row > itemsXPage then load the new page.
        If TABLE mode is selected, and row > itemsXPagethe then load
        the new page.
        :param row: the row, 1 is the first
        """
        if self._tableModel:
            if row in range(1, self._tableModel.totalRowCount() + 1):
                self._currentRow = row - 1
                if self._currentViewMode == TABLE_VIEW_MODE:
                    page = self.__getTablePage(row - 1)
                    if not page == self._currentTablePage:
                        self.__goToPage(page)
                    if self._itemsXTablePage:
                        self._tableView.selectRow(
                            int(self._currentRow % self._itemsXTablePage))
                elif self._currentViewMode == GALLERY_VIEW_MODE:
                    if self._itemsXGalleryPage:
                        galleryRow = (row - 1) % self._itemsXGalleryPage

                        page = self.__getGalleryPage(row - 1)
                        if not page == self._currentGalleryPage:
                            self.__goToPage(page)
                        index = self._listView.model().\
                            createIndex(galleryRow,
                                        self._currentRenderableColumn)
                        if index.isValid():
                            self._listView.setCurrentIndex(index)
                elif self._currentViewMode == ELEMENT_VIEW_MODE:
                    self.__goToPage(row - 1, True)
                    self._showCurrentPageNumber()

    @pyqtSlot(QModelIndex, QModelIndex)
    def _onCurrentTableViewItemChanged(self, current, previous):
        """
        This slot is invoked when the current table item change
        """
        col = row = -1
        if current.isValid():
            row = current.row() + self._currentTablePage * self._itemsXTablePage
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
        col = row = -1
        if current.isValid():
            row = current.row()
            col = current.column()
            self._currentRow = \
                row + self._currentGalleryPage * self._itemsXGalleryPage
            if not self._spinBoxCurrentRow.value() == self._currentRow + 1:
                self._spinBoxCurrentRow.setValue(self._currentRow + 1)

        self.sigCurrentGalleryItemChanged.emit(row, col)

    @pyqtSlot(bool)
    def _onChangeViewTriggered(self, checked):
        """
        This slot is invoked when a view action is triggered
        """
        a = self._actionGroupViews.checkedAction()

        if a and checked:
            mode = a.objectName()
            if self.__canChangeToMode(mode):
                self._currentViewMode = mode
                self.__setupCurrentViewMode()

    @pyqtSlot(bool)
    def _onListNextPage(self, checked=True):
        """
        This slot is invoked when the user clicks next page in gallery view
        """
        if self._currentViewMode == GALLERY_VIEW_MODE:
            self.__goToPage(self._currentGalleryPage + 1)
            self._showCurrentPageNumber()
        elif self._currentViewMode == TABLE_VIEW_MODE:
            self.__goToPage(self._currentTablePage + 1)
            self._showCurrentPageNumber()
        elif self._currentViewMode == ELEMENT_VIEW_MODE:
            self.__goToPage(self._currentElementPage + 1)
            self._showCurrentPageNumber()

    @pyqtSlot(bool)
    def _onListPrevPage(self, checked=True):
        """
        This slot is invoked when the user clicks prev page in gallery view
        """
        if self._currentViewMode == GALLERY_VIEW_MODE:
            self.__goToPage(self._currentGalleryPage - 1)
            self._showCurrentPageNumber()
        elif self._currentViewMode == TABLE_VIEW_MODE:
            self.__goToPage(self._currentTablePage - 1)
            self._showCurrentPageNumber()
        elif self._currentViewMode == ELEMENT_VIEW_MODE:
            self.__goToPage(self._currentElementPage - 1)
            self._showCurrentPageNumber()

    @pyqtSlot()
    def _onSpinBoxCurrentPageEditingFinished(self):
        """
        Invoked when editing is finished. This happens when the spinbox loses
        focus and when enter is pressed.
        """
        page = self._spinBoxCurrentPage.value() - 1
        if self._currentViewMode == GALLERY_VIEW_MODE:
            if not self._currentGalleryPage == page and \
                    page in range(0, self._galleryPageCount):
                self.__goToPage(page)
        elif self._currentViewMode == TABLE_VIEW_MODE:
            if not self._currentTablePage == page and \
                    page in range(0, self._tablePageCount):
                self.__goToPage(page)
        elif self._currentViewMode == ELEMENT_VIEW_MODE:
            if not self._currentElementPage == page and self._tableModel and \
                    page in range(0, self._tableModel.totalRowCount()):
                self.__goToPage(page)

    @pyqtSlot()
    def _showCurrentPageNumber(self):
        """
        Show the currentPage number in the corresponding widget.
        """
        if self._currentViewMode == GALLERY_VIEW_MODE:
            self._spinBoxCurrentPage.setValue(self._currentGalleryPage + 1)
        elif self._currentViewMode == TABLE_VIEW_MODE:
            self._spinBoxCurrentPage.setValue(self._currentTablePage + 1)
        elif self._currentViewMode == ELEMENT_VIEW_MODE:
            self._spinBoxCurrentPage.setValue(self._currentElementPage + 1)

    @pyqtSlot()
    def _showNumberOfPages(self):
        """
        Show the number of pages depending of current view mode.
        Now: _labelPageCount
        """
        if self._tableModel is None:
            return 0
        if self._currentViewMode == GALLERY_VIEW_MODE:
            page = self._galleryPageCount
        elif self._currentViewMode == TABLE_VIEW_MODE:
            page = self._tablePageCount
        elif self._currentViewMode == ELEMENT_VIEW_MODE:
            page = self._tableModel.totalRowCount()
        else:
            page = 0

        self._labelPageCount.setText("of %i" % page)

    def getSelectedViewMode(self):
        """
        Return the selected mode. Possible values are: TABLE, GALLERY, ELEMENT
        """
        a = self._actionGroupViews.checkedAction()
        return a.objectName() if a else None

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
        """ Configure all properties  """
        self._defaultRowHeight = kwargs.get("defaultRowHeight", 20)
        self._maxRowHeight = kwargs.get("maxRowHeight", 250)
        self._minRowHeight = kwargs.get("minRowHeight", 5)
        self._zoomUnits = kwargs.get("zoomUnits", PIXEL_UNITS)
        self._defaultView = kwargs.get("defaultView", TABLE_VIEW_MODE)
        self._currentViewMode = self._defaultView
        views = kwargs.get("views", [TABLE_VIEW_MODE, GALLERY_VIEW_MODE,
                                     ELEMENT_VIEW_MODE])
        for v in self._actionGroupViews.actions():
            v.setVisible(v.objectName() in views)

        self._disableHistogram = kwargs.get("disableHistogram", False)
        self._disableMenu = kwargs.get("disableMenu", False)
        self._disableROI = kwargs.get("disableROI", False)
        self._disablePopupMenu = kwargs.get("disablePopupMenu", False)
        self._disableFitToSize = kwargs.get("disableFitToSize", False)

        if self._disableHistogram:
            self._imageView.ui.histogram.hide()
        if self._disableMenu:
            self._imageView.ui.menuBtn.hide()
        if self._disableROI:
            self._imageView.ui.roiBtn.hide()
        if self._disablePopupMenu:
            self._imageView.getView().setMenuEnabled(False)


class _ImageItemDelegate(QStyledItemDelegate):
    """
    _ImageItemDelegate class provides visualization and editing functions
    of image data for widgets of the TableView class
    """
    def __init__(self, parent=None, selectedStatePen=None, borderPen=None):
        """
        If selectedStatePen is None then the border will not be painted when
        the item is selected.
        If selectedStatePen has a QPen value then a border will be painted when
        the item is selected
        :param parent: the parent qt object
        :param selectedStatePen: QPen object
        """
        QStyledItemDelegate.__init__(self, parent)
        self._selectedStatePen = selectedStatePen
        self._borderPen = borderPen
        self._imgCache = ImageCache(50, 50)

    def createEditor(self, parent, option, index):
        """
        Otherwise an editor is created if the user clicks in this cell.
        """
        return None

    def paint(self, painter, option, index):
        """
        Reimplemented from QStyledItemDelegate
        """
        if index.isValid():
            pixmap = self._getThumb(index)
            if option.state & QStyle.State_Selected:
                if option.state & QStyle.State_Active:
                    colorGroup = QPalette.Active
                else:
                    colorGroup = QPalette.Inactive

                painter.fillRect(option.rect,
                                 option.palette.color(colorGroup,
                                                      QPalette.Highlight))
            if pixmap:
                rect = QStyle.alignedRect(option.direction,
                                          option.displayAlignment |
                                          Qt.AlignHCenter | Qt.AlignVCenter,
                                          pixmap.size().
                                          scaled(option.rect.width(),
                                                 option.rect.height(),
                                                 Qt.KeepAspectRatio),
                                          option.rect)
                painter.drawPixmap(rect, pixmap)

                if self._borderPen:
                    painter.save()
                    painter.setPen(self._borderPen)
                    painter.drawRect(option.rect.x(), option.rect.y(),
                                     option.rect.width() - 1,
                                     option.rect.height() - 1)
                    painter.restore()
            else:
                painter.drawRect(option.rect.x(), option.rect.y(),
                                 option.rect.width() - 1,
                                 option.rect.height() - 1)

            if self._selectedStatePen and option.state & QStyle.State_Selected:
                painter.setPen(self._selectedStatePen)
                painter.drawRect(option.rect.x(), option.rect.y(),
                                 option.rect.width() - 1,
                                 option.rect.height() - 1)

    def _getThumb(self, index, height=100):
        """
        If the thumbnail stored in Qt.UserRole + 1 is None then create a
        thumbnail by scaling the original image according to its height and
        store the new thumbnail in Qt.UserRole + 1
        :param index: the item
        :param height: height to scale the image
        :return: scaled QPixmap
        """
        imgPath = index.data(Qt.UserRole)
        pixmap = self._imgCache.getImage(imgPath)

        if not pixmap:
            #  create one and store in imgCache
            pixmap = self._imgCache.addImage(imgPath, imgPath)

        return pixmap


class EMImageItemDelegate(QStyledItemDelegate):
    """
    ImageItemDelegate class provides display and editing facilities for
    em image data items from a model.
    """
    def __init__(self, parent=None,
                 selectedStatePen=None,
                 borderPen=None,
                 iconWidth=150,
                 iconHeight=150):
        """
        If selectedStatePen is None then the border will not be painted when
        the item is selected.
        If selectedStatePen has a QPen value then a border will be painted when
        the item is selected
        :param parent: the parent qt object
        :param selectedStatePen: QPen object
        """
        QStyledItemDelegate.__init__(self, parent)
        self._selectedStatePen = selectedStatePen
        self._borderPen = borderPen
        self._imgCache = ImageCache(50, 50)
        self._imageView = pg.ImageView(view=pg.ViewBox())
        self._iconWidth = iconWidth
        self._iconHeight = iconHeight
        self._disableFitToSize = True
        self._pixmapItem = None

    def paint(self, painter, option, index):
        """
        Reimplemented from QStyledItemDelegate
        """
        if index.isValid():
            self._setupView(index)

            if option.state & QStyle.State_Selected:
                if option.state & QStyle.State_HasFocus or \
                     option.state & QStyle.State_Active:
                    colorGroup = QPalette.Active
                else:
                    colorGroup = QPalette.Inactive

                painter.fillRect(option.rect,
                                 option.palette.color(colorGroup,
                                                      QPalette.Highlight))

            self._imageView.ui.graphicsView.scene().setSceneRect(
                QRectF(9, 9, option.rect.width() - 17,
                       option.rect.height() - 17))
            self._imageView.ui.graphicsView.scene().render(painter,
                                                           QRectF(option.rect))


            if option.state & QStyle.State_HasFocus:
                pen = QPen(Qt.DashDotDotLine)
                pen.setColor(Qt.red)
                painter.setPen(pen)
                painter.drawRect(option.rect.x(), option.rect.y(),
                                 option.rect.width()-1, option.rect.height()-1)
            QApplication.style().drawPrimitive(
                QStyle.PE_FrameFocusRect, option, painter)

    def _setupView(self, index):
        """
        Configure the widget used as view to shoe the image
        """
        imgData = self._getThumb(index)

        if imgData is None:
            return

        size = index.data(Qt.SizeHintRole)
        (w, h) = (size.width(), size.height())

        v = self._imageView.getView()
        (cw, ch) = (v.width(), v.height())

        if not (w, h) == (cw, ch):
            v.setGeometry(0, 0, w, h)
            v.resizeEvent(None)

        if not isinstance(imgData, QPixmap):  # QPixmap or np.array
            if self._pixmapItem:
                self._pixmapItem.setVisible(False)

            self._imageView.setImage(imgData)
        else:
            if not self._pixmapItem:
                self._pixmapItem = QGraphicsPixmapItem(imgData)
                v.addItem(self._pixmapItem)
            else:
                self._pixmapItem.setPixmap(imgData)
            self._pixmapItem.setVisible(True)
            v.autoRange()

    def _getThumb(self, index, height=100):
        """
        If the thumbnail stored in Image Cache
        :param index: QModelIndex
        :param height: height to scale the image
        """
        imgPath = index.data(Qt.UserRole)

        imgParams = parseImagePath(imgPath)

        if imgParams is None or not len(imgParams) == 3:
            return None
        else:
            imgPath = imgParams[2]

            if EmPath.isStack(imgParams[2]):
                id = str(imgParams[0]) + '_' + imgPath
            else:
                id = imgPath

        imgData = self._imgCache.getImage(id)

        if imgData is None:
            imgData = self._imgCache.addImage(id, imgPath, imgParams[0])

        if imgData is None:
            return None
        else:
            axis = imgParams[1]
            if axis == X_AXIS:
                imgData = imgData[:, :, imgParams[0]]
            elif axis == Y_AXIS:
                imgData = imgData[:, imgParams[0], :]
            elif axis == Z_AXIS:
                 imgData = imgData[imgParams[0], :, :]

        return imgData

    def setImageCache(self, imgCache):
        """
        Set the ImageCache object to be use for this ImageDelegate
        :param imgCache: ImageCache
        """
        self._imgCache = imgCache

    def getImageCache(self):
        """ Getter for imageCache """
        return self._imgCache


class GalleryViewWidget(QListView):
    """
    The GalleryView class provides some functionality for show large numbers of
    items with simple paginate elements.
    """
    sigSizeChanged = QtCore.pyqtSignal()  # when the widget has been resized

    def __init__(self, parent=None):
        QListView.__init__(self, parent)

    def resizeEvent(self, evt):
        """
        Reimplemented from QListView
        """
        QListView.resizeEvent(self, evt)
        self.sigSizeChanged.emit()


class TableWidget(QTableView):
    """
    The Table class provides some functionality for show large numbers of
    items
    """
    sigSizeChanged = QtCore.pyqtSignal()  # when the widget has been resized

    def __init__(self, parent=None):
        QTableView.__init__(self, parent)

    def resizeEvent(self, evt):
        """
        Reimplemented from TableWidget
        """
        QTableView.resizeEvent(self, evt)
        self.sigSizeChanged.emit()


def createTableModel(path):
    """ Return the TableDataModel for the given EM table file"""
    return


def createStackModel(imagePath):
    """ Return a stack model for the given image """
    xTable = em.Table([em.Table.Column(0, "index",
                                       em.typeInt32,
                                       "Image index"),
                       em.Table.Column(1, "Stack",
                                       em.typeString,
                                       "Image stack")])
    imageIO = em.ImageIO()
    loc2 = em.ImageLocation(imagePath)
    imageIO.open(loc2.path, em.File.Mode.READ_ONLY)
    dim = imageIO.getDim()

    for i in range(0, dim.n):
        row = xTable.createRow()
        row['Stack'] = str(i) + '@' + imagePath
        row['index'] = i
        xTable.addRow(row)

    return [TableDataModel(xTable, title='Stack')], None


def createVolumeModel(imagePath):
    image = em.Image()
    loc2 = em.ImageLocation(imagePath)
    image.read(loc2)

    # Create three Tables with the volume slices
    xTable = em.Table([em.Table.Column(0, "index",
                                       em.typeInt32,
                                       "Image index"),
                       em.Table.Column(1, "X",
                                       em.typeString,
                                       "X Dimension")])
    xtableViewConfig = TableViewConfig()
    xtableViewConfig.addColumnConfig(name='index',
                                     dataType=TableViewConfig.TYPE_INT,
                                     **{'label': 'Index',
                                        'editable': False,
                                        'visible': True})
    xtableViewConfig.addColumnConfig(name='X',
                                     dataType=TableViewConfig.TYPE_STRING,
                                     **{'label': 'X',
                                        'renderable': True,
                                        'editable': False,
                                        'visible': True})

    yTable = em.Table([em.Table.Column(0, "index",
                                       em.typeInt32,
                                       "Image index"),
                       em.Table.Column(1, "Y",
                                       em.typeString,
                                       "Y Dimension")])
    ytableViewConfig = TableViewConfig()
    ytableViewConfig.addColumnConfig(name='index',
                                     dataType=TableViewConfig.TYPE_INT,
                                     **{'label': 'Index',
                                        'editable': False,
                                        'visible': True})
    ytableViewConfig.addColumnConfig(name='Y',
                                     dataType=TableViewConfig.TYPE_STRING,
                                     **{'label': 'Y',
                                        'renderable': True,
                                        'editable': False,
                                        'visible': True})
    zTable = em.Table([em.Table.Column(0, "index",
                                       em.typeInt32,
                                       "Image index"),
                       em.Table.Column(1, "Z",
                                       em.typeString,
                                       "Z Dimension")])
    ztableViewConfig = TableViewConfig()
    ztableViewConfig.addColumnConfig(name='index',
                                     dataType=TableViewConfig.TYPE_INT,
                                     **{'label': 'Index',
                                        'editable': False,
                                        'visible': True})
    ztableViewConfig.addColumnConfig(name='Z',
                                     dataType=TableViewConfig.TYPE_STRING,
                                     **{'label': 'Z',
                                        'renderable': True,
                                        'editable': False,
                                        'visible': True})

    # Get the volume dimension
    _dim = image.getDim()
    _dx = _dim.x
    _dy = _dim.y
    _dz = _dim.z

    for i in range(0, _dx):
        row = xTable.createRow()
        row['X'] = str(i) + '@' + str(X_AXIS) + '@' + imagePath
        row['index'] = i
        xTable.addRow(row)

    for i in range(0, _dy):
        row = yTable.createRow()
        row['Y'] = str(i) + '@' + str(Y_AXIS) + '@' + imagePath
        row['index'] = i
        yTable.addRow(row)

    for i in range(0, _dz):
        row = zTable.createRow()
        row['Z'] = str(i) + '@' + str(Z_AXIS) + '@' + imagePath
        row['index'] = i
        zTable.addRow(row)

    models = list()
    models.append(TableDataModel(xTable, title='X Axis (Right View)',
                                 tableViewConfig=xtableViewConfig))

    models.append(TableDataModel(yTable, title='Y Axis (Left View)',
                                 tableViewConfig=ytableViewConfig))

    models.append(TableDataModel(zTable, title='Z Axis (Front View)',
                                 tableViewConfig=ztableViewConfig))

    return models, None


def createSingleImageModel(imagePath):
    """ Return a single image model """
    if EmPath.isImage(imagePath) or EmPath.isStandardImage(imagePath):
        table = em.Table([em.Table.Column(0, "Image", em.typeString,
                                          "Image path")])
        tableViewConfig = TableViewConfig()
        tableViewConfig.addColumnConfig(name='Image',
                                        dataType=TableViewConfig.TYPE_STRING,
                                         **{'label': 'Image',
                                            'renderable': True,
                                            'editable': False,
                                            'visible': True})
        row = table.createRow()
        row['Image'] = '0@' + imagePath
        table.addRow(row)
        return [TableDataModel(table, title='IMAGE',
                               tableViewConfig=tableViewConfig)], None


