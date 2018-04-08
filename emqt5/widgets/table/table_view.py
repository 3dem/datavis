#!/usr/bin/python
# -*- coding: utf-8 -*-


from PyQt5.QtCore import (Qt, QVariant, pyqtSlot, QItemSelection, QSize,
                          QSortFilterProxyModel, QEvent, QObject, QPoint,
                          QItemSelectionModel, QModelIndex)
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QStyleOptionViewItem,
                             QToolBar, QAction, QTableView, QSpinBox, QLabel,
                             QStyledItemDelegate, QStyle, QAbstractItemView,
                             QApplication, QHeaderView, QComboBox, QHBoxLayout,
                             QStackedLayout, QLineEdit, QActionGroup, QListView,
                             QSizePolicy, QSpacerItem, QPushButton)
from PyQt5.QtGui import (QPixmap, QPen, QIcon, QPalette, QStandardItemModel,
                         QStandardItem, QResizeEvent)
from PyQt5 import QtCore

import qtawesome as qta

from emqt5.widgets.table.model import TableDataModel

TABLE_VIEW_MODE = 'TABLE'
GALLERY_VIEW_MODE = 'GALLERY'
ELEMENT_VIEW_MODE = 'ELEMENT'

PIXEL_UNITS = 1
PERCENT_UNITS = 2


class TableView(QWidget):
    """
    Widget used for display table contend
    """

    def __init__(self, **kwargs):
        QWidget.__init__(self, kwargs.get("parent", None))
        self._defaultRowHeight = kwargs.get("defaultRowHeight", 20)
        self._maxRowHeight = kwargs.get("maxRowHeight", 250)
        self._minRowHeight = kwargs.get("minRowHeight", 5)
        self._zoomUnits = kwargs.get("zoomUnits", PIXEL_UNITS)
        self._defaultView = kwargs.get("defaultView", TABLE_VIEW_MODE)
        self._views = kwargs.get("views", [TABLE_VIEW_MODE,
                                           GALLERY_VIEW_MODE,
                                           ELEMENT_VIEW_MODE])
        self._viewActionIcons = {TABLE_VIEW_MODE: "fa.table",
                                 GALLERY_VIEW_MODE: "fa.image",
                                 ELEMENT_VIEW_MODE: "fa.file-image-o"}
        self._viewActions = []
        self._tableModel = None
        self._galleryModel = TableDataModel(self)
        self._sortProxyModel = QSortFilterProxyModel(self)
        self._sortProxyModel.setSortRole(Qt.UserRole)  # Qt.UserRole by default
        self._tableViewSelectionModel = QItemSelectionModel(None, self)
        self._galleryViewSelectionModel = QItemSelectionModel(None, self)
        self._currentRenderableColumn = 0  # for GALLERY mode
        self._currentRow = 0  # selected table row
        self._currentViewMode = self._defaultView
        self._currentGalleryPage = 0
        self._itemsXGalleryPage = 0
        self._galleryPageCount = 0
        self._currentPage = 0
        self._pageRows = 0
        self._pageColumns = 0
        self.__setupUi__()
        self.__setupCurrentViewMode__()

    def __setupUi__(self):
        self._verticalLayout = QVBoxLayout(self)
        self._toolBar = QToolBar(self)
        self._verticalLayout.addWidget(self._toolBar)
        self._stackedLayoud = QStackedLayout(self._verticalLayout)
        # table view
        self._tableView = QTableView(self)
        self._tableView.setSelectionBehavior(QTableView.SelectRows)
        self._tableView.verticalHeader().hide()
        self._tableView.setSortingEnabled(True)
        self._tableView.setModel(self._sortProxyModel)
        self._tableView.setSelectionModel(self._tableViewSelectionModel)
        self._tableViewSelectionModel.setModel(self._sortProxyModel)
        # gallery view
        self._listViewContainer = QWidget(self)
        self._listView = GalleryView(self._listViewContainer)
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
        self._listView.setModel(self._galleryModel)
        sModel = self._listView.selectionModel()
        if sModel:
            sModel.currentChanged.connect(self._onCurrentGalleryItemChanged)

        self._verticalLayout_2 = QVBoxLayout(self._listViewContainer)
        self._verticalLayout = QVBoxLayout()
        self._verticalLayout.addWidget(self._listView)
        self._horizontalLayout = QHBoxLayout()
        spacerItem = QSpacerItem(40, 20, QSizePolicy.Expanding,
                                 QSizePolicy.Minimum)
        self._horizontalLayout.addItem(spacerItem)
        self._pushButtonPrevPage = QPushButton(self._listViewContainer)
        self._horizontalLayout.addWidget(self._pushButtonPrevPage)
        self._pushButtonPrevPage.setIcon(qta.icon('fa.angle-left'))
        self._pushButtonPrevPage.clicked.connect(self._onListPrevPage)
        self._lineEditCurrentPage = QLineEdit(self._listViewContainer)
        self._lineEditCurrentPage.setMaximumSize(50, 25)
        self._lineEditCurrentPage.setMinimumSize(50, 25)
        self._horizontalLayout.addWidget(self._lineEditCurrentPage)
        self._labelPageCount = QLabel(self._listViewContainer)
        self._horizontalLayout.addWidget(self._labelPageCount)
        self._pushButtonNextPage = QPushButton(self._listViewContainer)
        self._pushButtonNextPage.setIcon(qta.icon('fa.angle-right'))
        self._pushButtonNextPage.clicked.connect(self._onListNextPage)
        self._horizontalLayout.addWidget(self._pushButtonNextPage)
        spacerItem1 = QSpacerItem(40, 20, QSizePolicy.Expanding,
                                  QSizePolicy.Minimum)
        self._horizontalLayout.addItem(spacerItem1)
        self._verticalLayout.addLayout(self._horizontalLayout)
        self._verticalLayout_2.addLayout(self._verticalLayout)

        self._stackedLayoud.addWidget(self._tableView)
        self._stackedLayoud.addWidget(self._listViewContainer)
        self._listView.sigSizeChanged.connect(self.__galleryResized__)
        self._actionGroupViews = QActionGroup(self._toolBar)
        self._actionGroupViews.setExclusive(True)
        for view in self._views:
            #  create action with name=view
            a = self.__createNewAction__(self._toolBar, view, view,
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
        #gallery view
        self._labelCurrentColumn = QLabel(parent=self._toolBar,
                                          text="Gallery in ")
        self._toolBar.addWidget(self._labelCurrentColumn)
        self._comboBoxCurrentColumn = QComboBox(self._toolBar)
        self._toolBar.addWidget(self._comboBoxCurrentColumn)
        self._comboBoxCurrentColumn.currentIndexChanged.\
            connect(self._onGalleryViewColumnChanged)

    def __resetGalleryView__(self):
        """
        Clear the gallery model and reset the values for:
        currentGalleryPage
        galleryPageCount
        itemsXGalleryPage
        """
        self._galleryModel.clear()
        self._galleryPageCount = 0
        self._currentGalleryPage = 0
        self._itemsXGalleryPage = 0

    def __getGalleryPage__(self, row):
        """
        Return the corresponding gallery page for a specific table row
        First row is 0
        """
        if self._itemsXGalleryPage > 0:
            return int(row / self._itemsXGalleryPage)

        return 0

    def __loadCurrentGalleryPage__(self):
        """
        Load the gallery page in the gallery view
        """
        if self._tableModel and self._galleryPageCount:
            self._galleryModel.clear()
            first = self._currentGalleryPage * self._itemsXGalleryPage

            if self._currentGalleryPage == self._galleryPageCount - 1:
                last = self._tableModel.rowCount()
            else:
                last = first + self._itemsXGalleryPage

            for i in range(first, last):
                sourceIndex = self._sortProxyModel.mapToSource(
                    self._sortProxyModel.index(i,
                                               self._currentRenderableColumn))
                item = QStandardItem()
                item.setData(self._tableModel.data(sourceIndex, Qt.UserRole),
                             Qt.UserRole)
                item.setData(self._tableModel.data(sourceIndex,
                                                   Qt.UserRole + 1),
                             Qt.UserRole + 1)
                self._galleryModel.appendRow([item])
            self._listView.setModelColumn(0)
        self._showCurrentPapeNumber()

    def __canChangeToMode__(self, mode):
        """
        Return True if mode can be changed, False if not.
        If mode == currentMode then return False
        :param mode: Possible values are: TABLE, GALLERY, ELEMENT
        """
        if self._currentViewMode == TABLE_VIEW_MODE:
            if mode == TABLE_VIEW_MODE:
                return False
            elif mode == GALLERY_VIEW_MODE:
                if self._tableView:
                    for colProp in self._tableModel.getColumnProperties():
                        if colProp.isRenderable() and \
                                colProp.isAllowSetVisible() and \
                                colProp.isVisible():
                            return True
                return False
        elif self._currentViewMode == GALLERY_VIEW_MODE:
            if mode == TABLE_VIEW_MODE:
                return True
        return False

    def __setupDelegatesForColumns__(self):
        """
        Sets the corresponding Delegate for all columns
        """
        # we have defined one delegate for the moment: ImageItemDelegate
        if self._tableModel:
            for i, prop in enumerate(self._tableModel.getColumnProperties()):
                if prop.isRenderable() and prop.isAllowSetVisible() and \
                        prop.isVisible():
                    self._tableView.setItemDelegateForColumn(
                        i, _ImageItemDelegate(self._tableView))

        self._listView.setItemDelegate(
            _ImageItemDelegate(parent=self._listView,
                               selectedStatePen=QPen(Qt.red)))

    def __setupVisibleColumns__(self):
        """
        Hide the columns with visible property=True or allowSetVisible=False
        """
        for i, prop in enumerate(self._tableModel.getColumnProperties()):
            if not prop.isAllowSetVisible() or not prop.isVisible():
                self._tableView.hideColumn(i)

    def __setupAllWidgets__(self):
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
        if self._tableModel:
            # table
            self._galleryModel.clear()
            self._galleryModel.setColumnProperties(None)
            self._tableView.selectionModel().currentChanged.connect(
                self._onCurrentTableViewItemChanged)
            self._showTableDims()
            self.__setupVisibleColumns__()
            self.__setupDelegatesForColumns__()
            self._onChangeCellSize()
            self.__setupSpinBoxCurrentRow__()
            self._spinBoxCurrentRow.setValue(1)
            self.__setupComboBoxCurrentColumn__()

    def __setupComboBoxCurrentColumn__(self):
        """
        Configure the elements in combobox currentColumn for gallery vew mode
        """
        blocked = self._comboBoxCurrentColumn.blockSignals(True)
        model = self._comboBoxCurrentColumn.model()
        if not model:
            model = QStandardItemModel(self._comboBoxCurrentColumn)
        model.clear()

        if self._tableModel:
            for index, columnProp in \
                    enumerate(self._tableModel.getColumnProperties()):
                if columnProp.isRenderable() and columnProp.isAllowSetVisible()\
                         and columnProp.isVisible():
                    item = QStandardItem(columnProp.getLabel())
                    item.setData(index, Qt.UserRole)  # use UserRole for store
                    model.appendRow([item])           # columnIndex
        self._comboBoxCurrentColumn.setModel(model)
        self._comboBoxCurrentColumn.blockSignals(blocked)

    def __setupCurrentViewMode__(self):
        """
        Configure current view mode: TABLE or GALLERY or ELEMENT
        TODO: ELEMENT VIEW MODE
        """
        if self._currentViewMode == ELEMENT_VIEW_MODE:
            return  # not implemented yet

        if self._tableModel:
            if self._currentViewMode == TABLE_VIEW_MODE:
                self._stackedLayoud.setCurrentWidget(self._tableView)
            elif self._currentViewMode == GALLERY_VIEW_MODE:
                self._stackedLayoud.setCurrentWidget(self._listViewContainer)

            self._selectRow(self._currentRow + 1)

    def __setupSpinBoxCurrentRow__(self):
        """
        Configure the spinBox range consulting table mode and table dims
        """
        if self._tableModel:
            mode = self.getSelectedViewMode()
            if mode == TABLE_VIEW_MODE or GALLERY_VIEW_MODE:
                self._spinBoxCurrentRow.setRange(1, self._tableModel.rowCount())

    def __initCurrentRenderableColumn__(self):
        """
        Set the currentRenderableColumn searching the first renderable column in
        the model. If there are no renderable columns or no model, the current
        column is the first: index 0
        """
        self._currentRenderableColumn = 0

        if self._tableModel:
            for index, columnProp in \
                    enumerate(self._tableModel.getColumnProperties()):
                if columnProp.isRenderable():
                    self._currentRenderableColumn = index
                    return

    def __createNewAction__(self, parent, actionName, text="", faIconName=None,
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

    @pyqtSlot()
    def __galleryResized__(self):
        """
        Invoked when gallery is resized.
        New page properties will be calculated
        """
        self.__calcGalleryPageProperties__()
        self._currentGalleryPage = self.__getGalleryPage__(self._currentRow)
        self.__loadCurrentGalleryPage__()
        self._selectRow(self._currentRow + 1)

    @pyqtSlot()
    def __calcGalleryPageProperties__(self):
        """
        Calculates depending of gallery size:
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

            pTotal = self._tableModel.rowCount() / (pCols * pRows)

            self._pageRows = pRows
            self._pageColumns = pCols
            self._galleryPageCount = int(pTotal)
            self._galleryPageCount += 1 if pTotal - int(pTotal) > 0 else 0
            self._itemsXGalleryPage = pRows * pCols

        self._showNumberOfGalleryPage()

    @pyqtSlot(int)
    def _onGalleryViewColumnChanged(self, index):
        """
         Invoked when user change the view column in gallery mode
         :param index: index in the combobox model
         """
        self._currentRenderableColumn = self._comboBoxCurrentColumn.\
            currentData(Qt.UserRole)

        if self._tableModel:
            cp = self._tableModel.getColumnProperties(
                self._currentRenderableColumn)
            if cp:
                self._galleryModel.setColumnProperties([cp])
                if self._currentViewMode == GALLERY_VIEW_MODE:
                    self.__loadCurrentGalleryPage__()
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
        if self._tableModel:
            self._tableModel.setIconSize(qsize)

        self._listView.setIconSize(qsize)
        self._galleryModel.setIconSize(qsize)
        self.__calcGalleryPageProperties__()

        if self._currentViewMode == GALLERY_VIEW_MODE:
            self._currentGalleryPage = self.__getGalleryPage__(self._currentRow)
            self.__loadCurrentGalleryPage__()
            self._selectRow(self._currentRow + 1)

    @pyqtSlot()
    def _showTableDims(self):
        """
        Show column and row count in the QLineEdits
        """
        if self._tableModel:
            self._lineEditRows.setText("%i" % self._tableModel.rowCount())
            self._lineEditCols.setText("%i" % self._tableModel.columnCount())

    @pyqtSlot(int)
    def _selectRow(self, row):
        """
        If GALLERY mode is selected and row > itemsXPage then load the new page
        :param row: the row, 1 is the first
        """
        if self._tableModel:
            if row in range(1, self._tableModel.rowCount()+1):
                self._currentRow = row - 1
                if self._currentViewMode == TABLE_VIEW_MODE:
                    self._tableView.selectRow(row-1)
                elif self._currentViewMode == GALLERY_VIEW_MODE:
                    galleryRow = (row - 1) % self._itemsXGalleryPage
                    page = self.__getGalleryPage__(row - 1)
                    self._currentGalleryPage = page
                    self.__loadCurrentGalleryPage__()
                    index = self._listView.model().createIndex(galleryRow, 0)
                    if index.isValid():
                        self._listView.setCurrentIndex(index)

    @pyqtSlot(QModelIndex, QModelIndex)
    def _onCurrentTableViewItemChanged(self, current, previous):
        """
        This slot is invoked when the current table item change
        """
        if current.isValid():
            row = current.row()
            if not row == self._currentRow:
                self._currentRow = row
                if not self._spinBoxCurrentRow.value() == row + 1:
                    self._spinBoxCurrentRow.setValue(self._currentRow + 1)

    @pyqtSlot(QModelIndex, QModelIndex)
    def _onCurrentGalleryItemChanged(self, current, previous):
        """
        This slot is invoked when the current gallery item change.
        """
        if current.isValid():
            row = current.row()
            self._currentRow = \
                row + self._currentGalleryPage * self._itemsXGalleryPage
            if not self._spinBoxCurrentRow.value() == self._currentRow + 1:
                self._spinBoxCurrentRow.setValue(self._currentRow + 1)

    @pyqtSlot(bool)
    def _onChangeViewTriggered(self, checked):
        """
        This slot is invoked when a view action is triggered
        """
        a = self._actionGroupViews.checkedAction()

        if a and checked:
            mode = a.objectName()
            if self.__canChangeToMode__(mode):
                self._currentViewMode = mode
                self.__setupCurrentViewMode__()

    @pyqtSlot(bool)
    def _onListNextPage(self, checked=True):
        """
        This slot is invoked when the user clicks next page in gallery view
        """
        if self._currentGalleryPage < self._galleryPageCount - 1:
            self._currentGalleryPage += 1
            self.__loadCurrentGalleryPage__()
            self._showCurrentPapeNumber()

    @pyqtSlot(bool)
    def _onListPrevPage(self, checked=True):
        """
        This slot is invoked when the user clicks prev page in gallery view
        """
        if self._currentGalleryPage > 0:
            self._currentGalleryPage -= 1
            self.__loadCurrentGalleryPage__()

    @pyqtSlot()
    def _showCurrentPapeNumber(self):
        """
        Show the currentPage number in the corresponding widget.
        Now: self._lineEditCurrentPage
        """
        self._lineEditCurrentPage.setText("%i" % (self._currentGalleryPage + 1))

    @pyqtSlot()
    def _showNumberOfGalleryPage(self):
        """
        Show the number of gallery page in the corresponding widget.
        Now: _labelPageCount
        """
        self._labelPageCount.setText("of %i" % self._galleryPageCount)

    def getSelectedViewMode(self):
        """
        Return the selected mode. Possible values are: TABLE, GALLERY, ELEMENT
        """
        a = self._actionGroupViews.checkedAction()
        return a.objectName() if a else None

    def setModel(self, model):
        """
        Set the table model
        :param model: the model
        """
        self._tableModel = model
        self._sortProxyModel.setSourceModel(self._tableModel)
        self.__setupAllWidgets__()
        self.__initCurrentRenderableColumn__()
        self._onGalleryViewColumnChanged(0)

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
        self._sortProxyModel.setSortRole(role)


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
        pixmap = index.data(Qt.UserRole + 1)

        if not pixmap:
            #  create one and store in Qt.UserRole + 1
            pixmap = QPixmap(index.data(Qt.UserRole)).scaledToHeight(height)
            index.model().setData(index, pixmap, Qt.UserRole + 1)

        return pixmap


class GalleryView(QListView):
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
