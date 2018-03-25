#!/usr/bin/python
# -*- coding: utf-8 -*-


from PyQt5.QtCore import (Qt, QVariant, pyqtSlot, QItemSelection, QSize)
from PyQt5.QtWidgets import (QWidget, QVBoxLayout,
                             QToolBar, QAction, QTableView, QSpinBox, QLabel,
                             QStyledItemDelegate, QStyle,
                             QApplication, QHeaderView,
                             QLineEdit, QActionGroup, QListView)
from PyQt5.QtGui import QPixmap, QPen, QIcon, QPalette
import qtawesome as qta

TABLE_VIEW_MODE = 'TABLE'
GALLERY_VIEW_MODE = 'GALLERY'
ELEMENT_VIEW_MODE = 'ELEMENT'


class TableView(QWidget):
    """
    Widget used for display table contend
    """

    def __init__(self, **kwargs):
        QWidget.__init__(self, kwargs.get("parent", None))
        self._defaultRowHeight = kwargs.get("defaultRowHeight", 32)
        self._maxRowHeight = kwargs.get("maxRowHeight", 512)
        self._defaultView = kwargs.get("defaultView", TABLE_VIEW_MODE)
        self._views = kwargs.get("views", [TABLE_VIEW_MODE,
                                           GALLERY_VIEW_MODE,
                                           ELEMENT_VIEW_MODE])
        self._viewActionIcons = {TABLE_VIEW_MODE: "fa.table",
                                 GALLERY_VIEW_MODE: "fa.image",
                                 ELEMENT_VIEW_MODE: "fa.file-image-o"}
        self._viewActions = []
        self._tableModel = None
        self._currentColumn = 0  # for GALLERY mode
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
        self._setupAllWidgets()
        self._connectSelectionSlots()

    def __setupUi__(self):
        self._verticalLayout = QVBoxLayout(self)
        self._toolBar = QToolBar(self)
        self._verticalLayout.addWidget(self._toolBar)
        self._tableView = QTableView(self)
        self._listView = QListView(self)
        self._listView.setViewMode(QListView.IconMode)
        self._listView.setResizeMode(QListView.Adjust)
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
        self._spinBoxRowHeight.setRange(self._defaultRowHeight,
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

    def _setupDelegatesForColumns(self):
        """
        Sets the corresponding Delegate for all columns
        """
        # we have defined one delegate for the moment: ImageItemDelegate
        if self._tableModel:
            for i, prop in enumerate(self._tableModel.getColumnProperties()):
                if prop.isRenderable():
                    self._tableView.setItemDelegateForColumn(
                        i, ImageItemDelegate(self._tableView))
                    self._listView.setItemDelegateForColumn(
                        i, ImageItemDelegate(self._listView))

    def _setupAllWidgets(self):
        """
        Configure all widgets:
           * set ImageDelegates for renderable columns
           * configure the value range for all spinboxs
           * configure the icon size for the model
           * show table dims

        Invoke this function when you needs to initialize all widgets.
        Example: when setting new model in the table view
        """
        if self._tableModel:
            # table
            self._tableView.setModel(self._tableModel)
            # list view
            self._listView.setModel(self._tableModel)

            self._showTableDims()
            self._setupDelegatesForColumns()
            self._changeCellSize(self._spinBoxRowHeight.value())
            self._setupSpinBoxCurrentRow()
            self._spinBoxCurrentRow.setValue(1)

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
        """
        if self._currentViewMode == ELEMENT_VIEW_MODE:
            return  # not implemented yet

        showTable = self._currentViewMode == TABLE_VIEW_MODE

        if self._tableModel:
            self._listView.setModelColumn(self._currentColumn)
            self._selectRow(self._spinBoxCurrentRow.value())

        self._listView.setVisible(not showTable)
        self._tableView.setVisible(showTable)

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
                    self._tableModel.index(row-1, self._currentColumn))

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
        index = index[0] if index and len(index) == 1 else None

        if index:
            self._currentColumn = index.column()
        elif self._currentViewMode == TABLE_VIEW_MODE:
            index = self._tableView.currentIndex()
        elif self._currentViewMode == GALLERY_VIEW_MODE:
            index = self._listView.currentIndex()
        else:
            return

        self._currentRow = index.row()
        print("Row: %i" % self._currentRow)
        print("Column: %i" % self._currentColumn)
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


class ImageItemDelegate(QStyledItemDelegate):
    """
    ImageItemDelegate class provides display and editing facilities for
    image data items from a model.
    """
    def __init__(self, parent=None):
        QStyledItemDelegate.__init__(self, parent)

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
            pixmap = self._getThumb(index.model().itemFromIndex(index))

            if option.state & QStyle.State_Selected:
                if option.state & QStyle.State_HasFocus or \
                     option.state & QStyle.State_Active:
                    colorGroup = QPalette.Active
                else:
                    colorGroup = QPalette.Inactive

                painter.fillRect(option.rect,
                                 option.palette.color(colorGroup,
                                                      QPalette.Highlight))

            QApplication.style().drawItemPixmap(painter,
                                                option.rect,
                                                option.displayAlignment |
                                                Qt.AlignHCenter,
                                                pixmap.scaled(
                                                    option.rect.width(),
                                                    option.rect.height(),
                                                    Qt.KeepAspectRatio))
            if option.state & QStyle.State_HasFocus:
                pen = QPen(Qt.DashDotDotLine)
                pen.setColor(Qt.gray)
                painter.setPen(pen)
                painter.drawRect(option.rect.x(), option.rect.y(),
                                 option.rect.width()-1, option.rect.height()-1)

    def _getThumb(self, item, height=100):
        """
        If the thumbnail stored in Qt.DecorationRole is None then create a
        thumbnail by scaling the original image according to its height and
        store the new thumbnail in Qt.DecorationRole
        :param item: the item
        :param height: height to scale the image
        :return: scaled QPixmap
        """
        pixmap = item.data(Qt.DecorationRole)

        if not pixmap:
            #  create one and store in Qt.DecorationRole
            pixmap = QPixmap(item.data(Qt.UserRole)).scaledToHeight(height)
            item.setData(QVariant(pixmap), Qt.DecorationRole)

        return pixmap
