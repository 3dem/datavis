#!/usr/bin/python
# -*- coding: utf-8 -*-


from PyQt5.QtCore import (Qt, QVariant, pyqtSlot, QItemSelection, QSize,
                          QSortFilterProxyModel)
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QStyleOptionViewItem,
                             QToolBar, QAction, QTableView, QSpinBox, QLabel,
                             QStyledItemDelegate, QStyle, QAbstractItemView,
                             QApplication, QHeaderView, QComboBox,
                             QLineEdit, QActionGroup, QListView)
from PyQt5.QtGui import (QPixmap, QPen, QIcon, QPalette, QStandardItemModel,
                         QStandardItem)
import qtawesome as qta

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
        self._sortProxyModel = QSortFilterProxyModel(self)
        self._sortProxyModel.setSortRole(Qt.UserRole)  # Qt.UserRole by default
        self._currentRenderableColumn = 0  # for GALLERY mode
        self._currentRow = 0  # selected table row
        self._currentViewMode = self._defaultView
        self.__setupUi__()
        self._setupCurrentViewMode()

    def setModel(self, model):
        """
        Set the table model
        :param model: the model
        """
        self._disconnectSelectionSlots()
        self._tableModel = model
        self._sortProxyModel.setSourceModel(self._tableModel)
        self._setupAllWidgets()
        self._initCurrentRenderableColumn()
        self._connectSelectionSlots()

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

    def __setupUi__(self):
        self._verticalLayout = QVBoxLayout(self)
        self._toolBar = QToolBar(self)
        self._verticalLayout.addWidget(self._toolBar)
        self._tableView = QTableView(self)
        self._tableView.setSelectionBehavior(QTableView.SelectRows)
        self._tableView.verticalHeader().hide()
        self._tableView.setSortingEnabled(True)
        self._listView = QListView(self)
        self._listView.setViewMode(QListView.IconMode)
        self._listView.setResizeMode(QListView.Adjust)
        self._listView.setSpacing(5)
        self._listView.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._verticalLayout.addWidget(self._tableView)
        self._verticalLayout.addWidget(self._listView)
        self._listView.setVisible(False)
        self._actionGroupViews = QActionGroup(self._toolBar)
        self._actionGroupViews.setExclusive(True)
        for view in self._views:
            #  create action with name=view
            a = self._createNewAction(self._toolBar, view, view,
                                      self._viewActionIcons.get(
                                          view,
                                          "fa.info-circle"),
                                      True, self._changeViewTriggered)
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

        self._spinBoxRowHeight.valueChanged.connect(self._changeCellSize)
        self._changeCellSize(self._defaultRowHeight)
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
            connect(self._galleryViewColumnChanged)

    def _setupDelegatesForColumns(self):
        """
        Sets the corresponding Delegate for all columns
        """
        # we have defined one delegate for the moment: ImageItemDelegate
        if self._tableModel:
            for i, prop in enumerate(self._tableModel.getColumnProperties()):
                if prop.isRenderable():
                    self._tableView.setItemDelegateForColumn(
                        i, _ImageItemDelegate(self._tableView))
                    self._listView.setItemDelegateForColumn(
                        i, _ImageItemDelegate(self._listView, QPen(Qt.blue)))

    def _setupAllWidgets(self):
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
            self._tableView.setModel(self._sortProxyModel)
            # list view
            self._listView.setModel(self._sortProxyModel)

            self._showTableDims()
            self._setupDelegatesForColumns()
            self._changeCellSize(self._spinBoxRowHeight.value())
            self._setupSpinBoxCurrentRow()
            self._spinBoxCurrentRow.setValue(1)
            self._setupComboBoxCurrentColumn()

    def _setupComboBoxCurrentColumn(self):
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
                if columnProp.isRenderable():
                    item = QStandardItem(columnProp.getLabel())
                    item.setData(index, Qt.UserRole)  # use UserRole for store
                    model.appendRow([item])           # columnIndex
        self._comboBoxCurrentColumn.setModel(model)
        self._comboBoxCurrentColumn.blockSignals(blocked)


    def _connectSelectionSlots(self):
        """
        Connects all used selection signals to corresponding slots.
        """
        sModel = self._tableView.selectionModel()
        if sModel:
            sModel.selectionChanged.connect(self._tableSelectionChanged)
        sModel = self._listView.selectionModel()
        if sModel:
            sModel.selectionChanged.connect(self._tableSelectionChanged)

    def _disconnectSelectionSlots(self):
        """
        Disconnect all slots connected in _connectSelectionSlots
        """
        sModel = self._tableView.selectionModel()
        if sModel:
            sModel.selectionChanged.disconnect(self._tableSelectionChanged)
        sModel = self._listView.selectionModel()
        if sModel:
            sModel.selectionChanged.disconnect(self._tableSelectionChanged)

    def _setupCurrentViewMode(self):
        """
        Configure current view mode: TABLE or GALLERY or ELEMENT
        TODO: ELEMENT VIEW MODE
        """
        if self._currentViewMode == ELEMENT_VIEW_MODE:
            return  # not implemented yet

        showTable = self._currentViewMode == TABLE_VIEW_MODE

        if self._tableModel:
            self._listView.setModelColumn(self._currentRenderableColumn)
            self._selectRow(self._spinBoxCurrentRow.value())

        self._listView.setVisible(not showTable)
        self._tableView.setVisible(showTable)

    @pyqtSlot(int)
    def _galleryViewColumnChanged(self, index):
        """
         Invoked when user change the view column in gallery mode
         :param index: index in the combobox model
         """
        self._currentRenderableColumn = self._comboBoxCurrentColumn.\
            currentData(Qt.UserRole)
        self._listView.setModelColumn(self._currentRenderableColumn)
        self._selectRow(self._spinBoxCurrentRow.value())

    @pyqtSlot(int)
    def _changeCellSize(self, size):
        """
        This slot is invoked when the cell size need to be rearranged
        TODO:[developers]Review implementation. Change row height for the moment
        """
        self._tableView.verticalHeader().setDefaultSectionSize(size)
        if self._tableModel:
            self._tableModel.setIconSize(QSize(size, size))

        self._listView.setIconSize(QSize(size, size))

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
        If TABLE mode is selected then select the row corresponding to cell-1.
        If GALLERY mode is selected then set cell as selected
        :param row: the row
        """
        if self._tableModel:
            if row in range(1, self._tableModel.rowCount()+1):
                self._tableView.selectRow(row-1)
                self._listView.setCurrentIndex(
                    self._sortProxyModel.index(row - 1,
                                           self._currentRenderableColumn))

    @pyqtSlot(QItemSelection, QItemSelection)
    def _tableSelectionChanged(self, selected, deselected):
        """
        This slot is invoked when items are selected or deselected.
        Update Cols and Rows labels in the toolbar
        :param selected: QItemSelection
        :param deselected: QItemSelection
        """
        print("_tableSelectionChanged")
        index = selected.indexes()
        # change currentColumn when... only one
        index = index[0] if index else None

        if index:
            column = index.column()
            columnProp = self._tableModel.getColumnProperties(column)
            if columnProp and columnProp.isRenderable():
                blocked = self._comboBoxCurrentColumn.blockSignals(True)
                self._comboBoxCurrentColumn.setCurrentText(
                    columnProp.getLabel())
                self._comboBoxCurrentColumn.blockSignals(blocked)
                self._currentRenderableColumn = column

            self._currentRow = index.row()
            print("Row: %i" % self._currentRow)
            print("Column: %i" % self._currentRenderableColumn)
            self._spinBoxCurrentRow.setValue(self._currentRow + 1)

    @pyqtSlot(bool)
    def _changeViewTriggered(self, checked):
        """
        This slot is invoked when a view action is triggered
        """
        a = self._actionGroupViews.checkedAction()

        if a and checked:
            mode = a.objectName()
            if not self._currentViewMode == mode:
                self._currentViewMode = mode
                self._setupCurrentViewMode()

    def _getSelectedMode(self):
        """
        Return the selected mode. Possible values are: TABLE, GALLERY, ELEMENT
        """
        a = self._actionGroupViews.checkedAction()

        return a.objectName() if a else None

    def _setupSpinBoxCurrentRow(self):
        """
        Configure the spinBox range consulting table mode and table dims
        """
        if self._tableModel:
            mode = self._getSelectedMode()
            if mode == TABLE_VIEW_MODE or GALLERY_VIEW_MODE:
                self._spinBoxCurrentRow.setRange(1, self._tableModel.rowCount())

    def _initCurrentRenderableColumn(self):
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

    def _createNewAction(self, parent, actionName, text="", faIconName=None,
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


class _ImageItemDelegate(QStyledItemDelegate):
    """
    _ImageItemDelegate class provides visualization and editing functions
    of image data for widgets of the TableView class
    """
    def __init__(self, parent=None, selectedStatePen=None):
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
            rect = QStyle.alignedRect(option.direction,
                                      option.displayAlignment | Qt.AlignHCenter,
                                      pixmap.size().scaled(option.rect.width(),
                                                           option.rect.height(),
                                                           Qt.KeepAspectRatio),
                                      option.rect)
            painter.drawPixmap(rect, pixmap)

            if self._selectedStatePen and option.state & QStyle.State_Selected:
                painter.setPen(self._selectedStatePen)
                painter.drawRect(option.rect.x(), option.rect.y(),
                                 option.rect.width() - 1,
                                 option.rect.height() - 1)

    def _getThumb(self, index, height=100):
        """
        If the thumbnail stored in Qt.UserRole + 1 is None then create a
        thumbnail by scaling the original image according to its height and
        store the new thumbnail in Qt.DecorationRole
        :param index: the item
        :param height: height to scale the image
        :return: scaled QPixmap
        """
        pixmap = index.data(Qt.UserRole + 1)

        if not pixmap:
            #  create one and store in Qt.UserRole + 1
            pixmap = QPixmap(index.data(Qt.UserRole)).scaledToHeight(height)
            index.model().setData(index, pixmap, Qt.DecorationRole + 1)

        return pixmap

