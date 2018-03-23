#!/usr/bin/python
# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import (Qt, QVariant, pyqtSlot, QEvent, QPoint, QRect,
                          QItemSelection)
from PyQt5.QtWidgets import (QWidget, QStyledItemDelegate, QVBoxLayout,
                             QToolBar, QAction, QTableView, QSpinBox, QLabel,
                             QStyledItemDelegate, QStyleOptionButton, QStyle,
                             QApplication, QAbstractItemView, QHeaderView,
                             QLineEdit, QActionGroup, QListView)
from PyQt5.QtGui import QPixmap, QPen, QIcon, QMouseEvent, QPalette
import qtawesome as qta


class TableView(QWidget):
    """
    Widget used for display table contend
    """

    def __init__(self, **kwargs):
        QWidget.__init__(self, kwargs.get("parent", None))
        self._defaultRowHeight = kwargs.get("defaultRowHeight", 32)
        self._maxRowHeight = kwargs.get("maxRowHeight", 512)
        self._defaultView = kwargs.get("defaultView", "TABLE")
        self._views = kwargs.get("views", ["TABLE", "GALLERY", "ELEMENT"])
        self._viewActionIcons = {"TABLE": "fa.table",
                                 "GALLERY": "fa.image",
                                 "ELEMENT": "fa.file-image-o"}
        self._viewActions = []
        self._tableModel = None
        self.__setupUi__()

    def setModel(self, model):
        """
        Set the table model
        :param model: the model
        """
        self._tableModel = model
        self._tableModel.setParent(self._tableView)
        self._tableView.setModel(model)
        self._tableView.selectionModel().selectionChanged.connect(
            self._tableSelectionChanged)

        self._tableView.setItemDelegateForColumn(
            1, ImageItemDelegate(self._tableView))
        self._tableView.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._showTableDims()
        self._setupSpinBoxGoToCell()
        self._spinBoxGoToCell.setValue(1)

    def __setupUi__(self):
        self._verticalLayout = QVBoxLayout(self)
        self._toolBar = QToolBar(self)
        self._verticalLayout.addWidget(self._toolBar)
        self._tableView = QTableView(self)
        self._verticalLayout.addWidget(self._tableView)
        self._actionGroupViews = QActionGroup(self._toolBar)
        self._actionGroupViews.setExclusive(True)
        for view in self._views:
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
        verticalHeader.setDefaultSectionSize(self._defaultRowHeight)
        self._spinBoxRowHeight.valueChanged.connect(self._changeCellSize)
        self._toolBar.addWidget(self._spinBoxRowHeight)
        self._toolBar.addSeparator()

        # cell navigator
        self._labelGoToCell = QLabel(self._toolBar)
        self._labelGoToCell.setPixmap(qta.icon(
            'fa.level-down').pixmap(28, QIcon.Normal, QIcon.On))
        self._spinBoxGoToCell = QSpinBox(self._toolBar)
        self._spinBoxGoToCell.valueChanged[int].connect(self._selectCell)
        self._toolBar.addWidget(self._labelGoToCell)
        self._toolBar.addWidget(self._spinBoxGoToCell)
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


    @pyqtSlot(int)
    def _changeCellSize(self, size):
        """
        This slot is invoked when the cell size need to be rearranged
        TODO:[developers]Review implementation. Change row height for the moment
        """
        self._tableView.verticalHeader().setDefaultSectionSize(size)

    @pyqtSlot()
    def _showTableDims(self):
        """
        Show column and row count in the QLineEdits
        """
        if self._tableModel:
            self._lineEditRows.setText("%i" % self._tableModel.rowCount())
            self._lineEditCols.setText("%i" % self._tableModel.columnCount())

    @pyqtSlot(int)
    def _selectCell(self, cell):
        """
        If TABLE mode is selected then select the row corresponding to cell-1.
        If GALLRY mode is selected then set cell as selected
        :param cell: the cell
        """
        if self._tableModel:
            mode = self._getSelectedMode()
            if mode == 'TABLE':
                if cell >0 and cell <= self._tableModel.rowCount():
                    self._tableView.selectRow(cell-1)

    @pyqtSlot(QItemSelection, QItemSelection)
    def _tableSelectionChanged(self, selected, deselected):
        """
        This slot is invoked when items are selected or deselected.
        Update Cols and Rows labels in the toolbar
        :param selected: QItemSelection
        :param deselected: QItemSelection
        """
        self._spinBoxGoToCell.setValue(selected.indexes()[0].row()+1)

    @pyqtSlot(bool)
    def _changeViewTriggered(self, checked):
        """
        This slot is invoked when a view action is triggered
        """
        if checked:
            if self._actionGroupViews.checkedAction().objectName() == 'GALLERY':
                print("GALLERY ACTIVATED")

    def _getSelectedMode(self):
        """
        Return the selected mode. Possible values are: TABLE, GALLERY, ELEMENT
        """
        a = self._actionGroupViews.checkedAction()

        return a.objectName() if a else None

    def _setupSpinBoxGoToCell(self):
        """
        Configure the spinBox range consulting table mode and table dims
        """
        if self._tableModel:
            mode = self._getSelectedMode()
            if mode == 'TABLE':
                self._spinBoxGoToCell.setRange(1, self._tableModel.rowCount())

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


class CheckBoxDelegate(QStyledItemDelegate):
    """
    Delegate that places a fully functioning QCheckBox in every
    cell of the column to which it's applied
    """
    def __init__(self, parent):
        QStyledItemDelegate.__init__(self, parent)

    def createEditor(self, parent, option, index):
        """
        Otherwise an editor is created if the user clicks in this cell.
        """
        return None

    def paint(self, painter, option, index):
        """
        Paint a checkbox without the label.
        """
        checked = index.data(Qt.UserRole)

        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect,
                             option.palette.color(QPalette.Highlight))

        cbStyleOpt = QStyleOptionButton()

        cbStyleOpt.state |= QStyle.State_Enabled \
            if index.flags() & Qt.ItemIsEditable else QStyle.State_ReadOnly

        cbStyleOpt.state |= QStyle.State_On if checked else QStyle.State_Off

        cbStyleOpt.rect = self._getCheckBoxRect(option)

        QApplication.style().drawControl(QStyle.CE_CheckBox,
                                         cbStyleOpt, painter)

    def editorEvent(self, event, model, option, index):
        """
        Change the data in the model and the state of the checkbox
        if the user presses the left mouse button """
        print(event)
        if isinstance(event, QMouseEvent):
            evType = event.type()
            # print only for debug. Will disappear in the future
            print('Check Box editor Event detected : ')
            print(evType)
            if not (index.flags() & Qt.ItemIsEditable):
                return False

            if evType == QEvent.MouseButtonPress or evType == QEvent.MouseMove:
                return False
            if evType == QEvent.MouseButtonRelease or \
                    evType == QEvent.MouseButtonDblClick:
                if event.button() != Qt.LeftButton or \
                        not self._getCheckBoxRect(option).contains(event.pos()):
                    return False
                if event.type() == QEvent.MouseButtonDblClick:
                    self.setModelData(None, model, index)
                    return True

            # Change the checkbox-state
            self.setModelData(None, model, index)
            return True

        return False

    def setModelData(self, editor, model, index):
        """
        The user wanted to change the old state in the opposite.
        """
        print('SetModelData')  # only for debug. Will disappear in the future
        model.setData(index, not index.data(Qt.UserRole), Qt.UserRole)

    def _getCheckBoxRect(self, option):
        check_box_style_option = QStyleOptionButton()
        check_box_rect = QApplication.style().\
            subElementRect(QStyle.SE_CheckBoxIndicator,
                           check_box_style_option, None)
        check_box_point = QPoint(option.rect.x() +
                                 option.rect.width() / 2 -
                                 check_box_rect.width() / 2,
                                 option.rect.y() +
                                 option.rect.height() / 2 -
                                 check_box_rect.height() / 2)
        return QRect(check_box_point, check_box_rect.size())


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
                painter.fillRect(option.rect,
                                 option.palette.color(QPalette.Highlight))

            painter.setBrush(option.backgroundBrush)
            QApplication.style().drawItemPixmap(painter,
                                                option.rect,
                                                option.displayAlignment |
                                                Qt.AlignHCenter,
                                                pixmap.scaled(
                                                    option.rect.width(),
                                                    option.rect.height(),
                                                    Qt.KeepAspectRatio))
            if option.state & QStyle.State_HasFocus:
                pen = QPen(Qt.SolidLine)
                pen.setColor(Qt.blue)
                painter.setPen(pen)
                painter.drawRect(option.rect.x(), option.rect.y(),
                                 option.rect.width()-1, option.rect.height()-1)

    def _getThumb(self, item, height=100):
        """
        If thumbnail is stored in Qt.DecorationRole then create another
        thumbnail by scaling the original image according to its height.
        Then store the new thumbnail in the to height. Store the
        thumbnail in the Qt.DecorationRole
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
