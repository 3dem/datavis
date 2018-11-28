#!/usr/bin/python
# -*- coding: utf-8 -*-

import traceback

from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal, QSize
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QToolBar, QAction, QSpinBox,
                             QLabel, QStatusBar, QComboBox, QStackedLayout,
                             QLineEdit, QActionGroup, QMessageBox)
from PyQt5.QtGui import QIcon, QStandardItemModel, QStandardItem
import qtawesome as qta

from .model import (ImageCache, VolumeDataModel, TableDataModel, X_AXIS, Y_AXIS,
                    Z_AXIS)
from .columns import ColumnsView
from .gallery import GalleryView
from .items import ItemsView
from .config import TableViewConfig

from emqt5.utils.functions import EmTable

PIXEL_UNITS = 1
PERCENT_UNITS = 2


class DataView(QWidget):
    """
    Widget used for display em data
    """
    COLUMNS = 1
    GALLERY = 2
    ITEMS = 4
    SLICES = 8

    """ This signal is emitted when the current item is changed """
    sigCurrentItemChanged = pyqtSignal(int, int)

    """ This signal is emitted when the current table is changed """
    sigCurrentTableChanged = pyqtSignal()

    def __init__(self, parent, **kwargs):
        QWidget.__init__(self, parent=parent)

        self._viewActions = {self.COLUMNS: {"name": "Columns",
                                            "icon": "fa.table",
                                            "action": None,
                                            "view": None},
                             self.GALLERY: {"name": "Gallery",
                                            "icon": "fa.th",
                                            "action": None,
                                            "view": None},
                             self.ITEMS: {"name": "Items",
                                          "icon": "fa.columns",
                                          "action": None,
                                          "view": None}}
        self._viewTypes = {"Columns": self.COLUMNS,
                           "Gallery": self.GALLERY,
                           "Items": self.ITEMS}
        self._views = []
        self._view = None
        self._model = None
        self._currentRenderableColumn = 0  # for GALLERY and ITEMS mode
        self._currentRow = 0  # selected table row
        self._imageCache = ImageCache(100)
        self._thumbCache = ImageCache(500, (100, 100))

        self._tablePref = dict()
        self.__initProperties(**kwargs)
        self.__setupUi(**kwargs)
        self.__setupCurrentViewMode()
        self.__setupActions()

    def __setupUi(self, **kwargs):
        self._mainLayout = QVBoxLayout(self)
        self._mainLayout.setSpacing(0)
        self._mainLayout.setContentsMargins(0, 0, 0, 0)
        self._toolBar = QToolBar(self)
        self._mainLayout.addWidget(self._toolBar)
        self._stackedLayoud = QStackedLayout(self._mainLayout)
        self._stackedLayoud.setSpacing(0)

        # combobox current table
        self._labelCurrentTable = QLabel(parent=self._toolBar, text="Table ")
        self._toolBar.addWidget(self._labelCurrentTable)
        self._comboBoxCurrentTable = QComboBox(self._toolBar)
        self._comboBoxCurrentTable.currentIndexChanged. \
            connect(self._onAxisChanged)
        self._toolBar.addWidget(self._comboBoxCurrentTable)
        self._toolBar.addSeparator()

        # actions
        self._actionGroupViews = QActionGroup(self._toolBar)
        self._actionGroupViews.setExclusive(True)
        for view in self._viewTypes.values():
            #  create action with name=view
            v = self._viewActions[view]
            a = self.__createNewAction(self._toolBar, v["name"], v["name"],
                                       v["icon"], True,
                                       self._onChangeViewTriggered)
            v["action"] = a
            self._actionGroupViews.addAction(a)
            self._toolBar.addAction(a)
            a.setChecked(view == self._view)
            a.setVisible(view in self._views)

        self._toolBar.addSeparator()
        # table rows and columns
        self._labelElements = QLabel(self._toolBar)
        self._labelElements.setText(" Elements ")
        self._toolBar.addWidget(self._labelElements)
        self._toolBar.addSeparator()
        self._labelRows = QLabel(self._toolBar)
        self._labelRows.setText(" Rows ")
        self._actLabelRows = self._toolBar.addWidget(self._labelRows)
        self._lineEditRows = QLineEdit(self._toolBar)
        self._lineEditRows.setMaximumSize(70, 22)
        self._lineEditRows.setEnabled(False)
        self._actLineEditRows = self._toolBar.addWidget(self._lineEditRows)
        self._labelCols = QLabel(self._toolBar)
        self._labelCols.setText(" Cols ")
        self._actLabelCols = self._toolBar.addWidget(self._labelCols)
        self._lineEditCols = QLineEdit(self._toolBar)
        self._lineEditCols.setMaximumSize(70, 22)
        self._lineEditCols.setEnabled(False)
        self._actLineEditCols = self._toolBar.addWidget(self._lineEditCols)
        self._toolBar.addSeparator()
        # cell navigator
        self._labelCurrentRow = QLabel(self._toolBar)
        self._labelCurrentRow.setPixmap(qta.icon(
            'fa.level-down').pixmap(28, QIcon.Normal, QIcon.On))
        self._spinBoxCurrentRow = QSpinBox(self._toolBar)
        self._spinBoxCurrentRow.setMaximumWidth(50)
        self._spinBoxCurrentRow.valueChanged[int].connect(self._selectRow)
        self._actLabelCurrentRow = self._toolBar.addWidget(
            self._labelCurrentRow)
        self._actSpinBoxCurrentRow = self._toolBar.addWidget(
            self._spinBoxCurrentRow)
        self._toolBar.addSeparator()
        # cell resizing
        self._labelLupe = QLabel(self._toolBar)
        self._labelLupe.setPixmap(qta.icon('fa.search').pixmap(28,
                                                               QIcon.Normal,
                                                               QIcon.On))
        self._actLabelLupe = self._toolBar.addWidget(self._labelLupe)
        self._spinBoxRowHeight = QSpinBox(self._toolBar)
        self._spinBoxRowHeight.setSuffix(' px' if self._zoomUnits == PIXEL_UNITS
                                         else ' %')
        self._spinBoxRowHeight.setRange(self._minRowHeight,
                                        self._maxRowHeight)
        self._spinBoxRowHeight.setValue(self._defaultRowHeight)
        self._spinBoxRowHeight.editingFinished.connect(self._onChangeCellSize)
        self._spinBoxRowHeight.setValue(self._defaultRowHeight)
        self._actSpinBoxHeight = self._toolBar.addWidget(self._spinBoxRowHeight)
        self._toolBar.addSeparator()
        # gallery view
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
        self.__createViews(**kwargs)
        self._statusBar.setVisible(False)  # hide for now
        self.setMinimumWidth(700)
        self.setGeometry(0, 0, 750, 800)

    def __createPreferencesForCurrentTable(self):
        """
        Creates a dict with the preferences for the current table(model).
        """
        pref = dict()
        pref["view"] = self._view  # Preferred view

        if self._model is not None and self._model.totalRowCount() == 1 \
                and self.ITEMS in self._views:
            pref["view"] = self.ITEMS
        elif self.COLUMNS in self._views:
            pref["view"] = self.COLUMNS
        else:
            pref["view"] = self._views[0] if self._views else None
        print("Preferences = ", pref)
        return pref

    def __savePreferencesForCurrentTable(self):
        """ Save preferences for the current table """
        tName = self._comboBoxCurrentTable.currentText()
        pref = self._tablePref.get(tName)

        if pref is None:
            self._tablePref[tName] = self.__createPreferencesForCurrentTable()
        else:
            pref["view"] = self._view

    def __loadPreferencesForCurrentTable(self):
        """ Load preferences for the current table """
        tName = self._comboBoxCurrentTable.currentText()
        pref = self._tablePref.get(tName)

        if pref is not None:
            self._view = pref["view"]
        else:
            self._tablePref[tName] = self.__createPreferencesForCurrentTable()
            pref = self._tablePref.get(tName)
            self._view = pref["view"]

        self.__setupCurrentViewMode()

    def __createView(self, viewType, **kwargs):
        """ Create and return a view. The parent of the view will be self """
        if viewType == self.COLUMNS:
            columns = ColumnsView(self, **kwargs)
            columns.sigTableSizeChanged.connect(self._showViewDims)
            return columns
        if viewType == self.GALLERY:
            gallery = GalleryView(self, **kwargs)
            gallery.sigPageSizeChanged.connect(self._showViewDims)
            return gallery
        if viewType == self.ITEMS:
            return ItemsView(self, **kwargs)

        return None

    def __createViews(self, **kwargs):
        """ Create the views if necessary. Inserts the views in the GUI. """
        for v in self._viewTypes.values():
            if v not in self._views:
                self.__removeView(v)
            elif self._viewsDict.get(v) is None:
                viewWidget = self.__createView(v, **kwargs)
                self._viewsDict[v] = viewWidget
                if viewWidget is not None:
                    viewWidget.setImageCache(self._imageCache)
                    if isinstance(viewWidget, ColumnsView) \
                            or isinstance(viewWidget, GalleryView):
                        viewWidget.setThumbCache(self._thumbCache)

                    self._stackedLayoud.addWidget(viewWidget)
                    viewWidget.sigCurrentRowChanged.connect(
                        self.__onViewRowChanged)
                    viewWidget.getPageBar().sigPageConfigChanged.connect(
                        self.__onPageConfigChanged)
                    viewWidget.getPageBar().sigPageChanged.connect(
                        self.__onCurrentPageChanged)

                a = self._viewActions[v]
                a["view"] = viewWidget

    def __removeView(self, view):
        """ If the given view exist in the GUI the will be removed. """
        viewWidget = self._viewsDict.get(view)
        if viewWidget is not None:
            self._stackedLayoud.removeWidget(viewWidget)
            self._viewsDict.pop(view)
            a = self._viewActions[view]
            a["view"] = None
            viewWidget.setParent(None)
            viewWidget.sigCurrentRowChanged.disconnect(
                self.__onViewRowChanged)
            viewWidget.getPageBar().sigPageConfigChanged.disconnect(
                self.__onPageConfigChanged)
            if isinstance(viewWidget, GalleryView):
                viewWidget.sigPageSizeChanged.disconnect(self._showViewDims)
            view.setModel(None)
            del viewWidget

    def __canChangeToView(self, view):
        """
        Return True if mode can be changed, False if not.
        If mode == currentMode then return False
        :param mode: Possible values are: COLUMNS, GALLERY, ITEMS
        """
        if view not in self._views or view == self._view:
            return False
        if self._view == self.COLUMNS:
            if view == self.GALLERY:
                if self._model:
                    for colConfig in self._model.getColumnConfig():
                        if colConfig["renderable"] and colConfig["visible"]:
                            return True
                return False
            elif view == self.ITEMS:
                return True
        elif self._view == self.GALLERY:
            if view == self.COLUMNS or view == self.ITEMS:
                return True
        elif self._view == self.ITEMS:
            if view == self.COLUMNS:
                return True
            elif view == self.GALLERY:
                if self._model:
                    for colConfig in self._model.getColumnConfig():
                        if colConfig["renderable"] and colConfig["visible"]:
                            return True
                return False

        return False

    def __setupAllWidgets(self):
        """
        Configure all widgets:
           * configure the value range for all spinboxs
           * configure the icon size for the model
           * show table dims

        Invoke this function when you needs to initialize all widgets.
        Example: when setting new model in the table view
        """
        self._showViewDims()
        self.__showTableSize()
        self.__setupSpinBoxRowHeigth()
        self._onChangeCellSize()
        self.__setupSpinBoxCurrentRow()
        self._spinBoxCurrentRow.setValue(1)
        self.__setupComboBoxCurrentColumn()
        self.__initCurrentRenderableColumn()
        self.__setupActions()
        if self._model is not None:
            for w in self._viewsDict.values():
                w.setModel(self._model.clone())
        self.__loadPreferencesForCurrentTable()
        self._onGalleryViewColumnChanged(0)

    def __showTableSize(self):
        if self._model is not None:
            self._labelElements.setText(" Elements: %d " %
                                        self._model.totalRowCount())
        else:
            self._labelElements.setText("")

    def __setupSpinBoxRowHeigth(self):
        """ Configure the row height spinbox """
        self._spinBoxRowHeight.setRange(self._minRowHeight, self._maxRowHeight)

        if self._model is not None and not self._model.hasRenderableColumn():
            self._spinBoxRowHeight.setValue(25)
        else:
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
        if self._model:
            for t in self._model.getTitles():
                item = QStandardItem(t)
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

        if self._model:
            for i, colConfig in enumerate(self._model.getColumnConfig()):
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

    def __setupToolBarForView(self, view):
        """ Show/Hide relevant info/actions for the given view """
        # row height
        rColumn = self._model is not None and self._model.hasRenderableColumn()

        self._actLabelLupe.setVisible((view == self.GALLERY or
                                      view == self.COLUMNS) and
                                      rColumn)
        self._actSpinBoxHeight.setVisible(self._actLabelLupe.isVisible())
        # dims
        self._actLabelCols.setVisible(not view == self.ITEMS)
        self._actLineEditCols.setVisible(self._actLabelCols.isVisible())
        self._lineEditCols.setEnabled(False)
        # render column in gallery
        self.__showCurrentColumnWidgets(
            not view == self.COLUMNS and
            rColumn and self._comboBoxCurrentColumn.model().rowCount() > 1)

    def __setupCurrentViewMode(self):
        """
        Configure current view mode: COLUMNS or GALLERY or ITEMS
        """
        viewWidget = self._viewsDict.get(self._view)

        if viewWidget is not None:
            self._stackedLayoud.setCurrentWidget(viewWidget)

        a = self._viewActions[self._view].get("action", None)
        if a:
            a.setChecked(True)

        self._selectRow(self._currentRow + 1)
        self._showViewDims()
        self.__setupToolBarForView(self._view)
        self.__savePreferencesForCurrentTable()

    def __setupModel(self):
        """
        Configure the current table model in all view modes
        """
        self.__setupAllWidgets()
        #self.__setupCurrentViewMode()

    def __setupSpinBoxCurrentRow(self):
        """
        Configure the spinBox range consulting table mode and table dims
        """
        if self._model:
            self._spinBoxCurrentRow.setRange(1, self._model.totalRowCount())

    def __initCurrentRenderableColumn(self):
        """
        Set the currentRenderableColumn searching the first renderable column in
        the model. If there are no renderable columns or no model, the current
        column is the first: index 0
        """
        self._currentRenderableColumn = 0

        if self._model:
            for i, colConfig in enumerate(self._model.getColumnConfig()):
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

    def __clearViews(self):
        """ Clear all views """
        for viewWidget in self._viewsDict.values():
            if viewWidget is not None:
                m = viewWidget.getModel()
                viewWidget.setModel(None)
                if m is not None:
                    m.setParent(None)
                    del m

    def __initProperties(self, **kwargs):
        """ Configure all properties  """
        self._defaultRowHeight = kwargs.get("size", 25)
        self._maxRowHeight = kwargs.get("max_cell_size", 300)
        self._minRowHeight = kwargs.get("min_cell_size", 20)
        self._zoomUnits = kwargs.get("zoom_units", PIXEL_UNITS)
        self._view = kwargs.get("view", self.COLUMNS)
        # The following dict is a map between views(COLUMNS, GALLERY, ITEMS) and
        # view widgets (GalleryView, ColumnsView, ItemsView)
        self._viewsDict = {}
        # List of configured views
        self._views = kwargs.get("views", [self.COLUMNS, self.GALLERY,
                                           self.ITEMS])

    def __setupActions(self):
        for v in self._actionGroupViews.actions():
            view = self._viewTypes[v.objectName()]
            v.setVisible(view in self._views)
            if self._model and view == DataView.GALLERY:
                v.setVisible(self._model.hasRenderableColumn())

    @pyqtSlot(int, int, int, int)
    def __onPageConfigChanged(self, page, fist, last, step):
        """ Invoked when views change his page configuration """
        self._selectRow(self._currentRow + 1)

    @pyqtSlot(int)
    def __onCurrentPageChanged(self, page):
        self._showViewDims()

    @pyqtSlot(int)
    def __onViewRowChanged(self, row):
        """ Invoked when views change the current row """
        if not self._currentRow == row:
            self._selectRow(row + 1)

    @pyqtSlot(int)
    def _onAxisChanged(self, index):
        """ Invoked when user change the axis in volumes """
        try:
            if self._model:
                if isinstance(self._model, VolumeDataModel):
                    t = self._comboBoxCurrentTable.currentText().split("(")
                    l = len(t)
                    if l > 1:
                        s = t[l-1]
                        axis = X_AXIS
                        if s == "X)":
                            axis = X_AXIS
                        elif s == "Y)":
                            axis = Y_AXIS
                        elif s == "Z)":
                            axis = Z_AXIS

                        for viewWidget in self._viewsDict.values():
                            model = viewWidget.getModel()
                            model.setAxis(axis)
                        self._selectRow(1)
                elif isinstance(self._model, TableDataModel):
                    name = self._comboBoxCurrentTable.currentText()
                    path = self._model.getDataSource()
                    if path is not None:
                        t = self._model.getEmTable()
                        EmTable.load(path, name, t)
                        self._model.setColumnConfig(TableViewConfig.fromTable(t))
                        self.__clearViews()
                        self.__setupModel()
                        self.sigCurrentTableChanged.emit()
        except Exception as ex:
            self.__showMsgBox("Can't perform the action", QMessageBox.Critical,
                              str(ex))
            print(traceback.format_exc())

        except RuntimeError as ex:
            self.__showMsgBox("Can't perform the action", QMessageBox.Critical,
                              str(ex))
            print(traceback.format_exc())
        except ValueError as ex:
            self.__showMsgBox("Can't perform the action", QMessageBox.Critical,
                              str(ex))
            print(traceback.format_exc())

    @pyqtSlot()
    def __showMsgBox(self, text, icon=None, details=None):
        """
        Show a message box with the given text, icon and details.
        The icon of the message box can be specified with one of the Qt values:
            QMessageBox.NoIcon
            QMessageBox.Question
            QMessageBox.Information
            QMessageBox.Warning
            QMessageBox.Critical
        """
        msgBox = QMessageBox()
        msgBox.setText(text)
        msgBox.setStandardButtons(QMessageBox.Ok)
        msgBox.setDefaultButton(QMessageBox.Ok)
        if icon is not None:
            msgBox.setIcon(icon)
        if details is not None:
            msgBox.setDetailedText(details)

        msgBox.exec_()

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

        if self._model:
            if self._comboBoxCurrentColumn.model().rowCount():
                viewWidget = self._viewsDict.get(self.GALLERY)
                if viewWidget is not None:
                    viewWidget.setModelColumn(self._currentRenderableColumn)

                viewWidget = self._viewsDict.get(self.ITEMS)
                if viewWidget is not None:
                    viewWidget.setModelColumn(self._currentRenderableColumn)
            else:
                viewWidget = self._viewsDict.get(self.ITEMS)
                if viewWidget is not None:
                    viewWidget.setModelColumn(0)

    @pyqtSlot()
    def _onChangeCellSize(self):
        """
        This slot is invoked when the cell size need to be rearranged
        TODO:[developers]Review implementation. Change row height for the moment
        """
        size = self._spinBoxRowHeight.value()

        for viewWidget in self._viewsDict.values():
            model = viewWidget.getModel()
            if model is not None:
                model.setIconSize(QSize(size, size))
            if isinstance(viewWidget, ColumnsView):
                viewWidget.setRowHeight(size)
                if self._model is not None:
                    cConfig = self._model.getColumnConfig()
                    if cConfig:
                        for i, colConfig in enumerate(cConfig):
                            if colConfig["renderable"] and \
                                    colConfig["visible"] and \
                                    viewWidget.getColumnWidth(i) < size:
                                viewWidget.setColumnWidth(i, size)
            elif isinstance(viewWidget, GalleryView):
                viewWidget.setIconSize((size, size))

        self._selectRow(self._currentRow + 1)

    @pyqtSlot()
    def _showViewDims(self):
        """
        Show column and row count in the QLineEdits
        """

        viewWidget = self._viewsDict.get(self._view)
        if viewWidget is None:
            rows = "0"
            cols = "0"
        else:
            dims = viewWidget.getViewDims()
            rows = "%i" % dims[0]
            cols = "%i" % dims[1]

        self._lineEditRows.setText(rows)
        self._lineEditCols.setText(cols)

    @pyqtSlot(int)
    def _selectRow(self, row):
        """
        This slot is invoked when the value of the current spinbox changes.
        :param row: the row, 1 is the first
        """
        if self._model and row in range(1, self._model.totalRowCount() + 1):
                self._currentRow = row - 1
                viewWidget = self._viewsDict.get(self._view)

                if viewWidget is not None:
                    viewWidget.selectRow(self._currentRow)

                if not row == self._spinBoxCurrentRow.value():
                    self._spinBoxCurrentRow.setValue(row)

    @pyqtSlot(bool)
    def _onChangeViewTriggered(self, checked):
        """
        This slot is invoked when a view action is triggered
        """
        a = self._actionGroupViews.checkedAction()

        if a and checked:
            view = self._viewTypes[a.objectName()]
            if self.__canChangeToView(view):
                self._view = view
                self.__setupCurrentViewMode()

    def getSelectedViewMode(self):
        """
        Return the selected mode. Possible values are:
        COLUMNS, GALLERY, ITEMS
        """
        return self._view

    def setModel(self, model):
        """ Set the table model for display. """
        self.__clearViews()
        self._model = model
        self._tablePref.clear()
        self.__setupComboBoxCurrentTable()
        self.__setupModel()

    def getModel(self):
        """
        Return the model for this table
        """
        return self._model

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

    def setup(self, **kwargs):
        """ TODO: Reconfigure the views, eliminating those that will not be used
                  and creating the new ones.
        """
        self.__initProperties(**kwargs)
        self.__createViews(**kwargs)
        self.__setupActions()

    def showToolBar(self, visible):
        """ Show or hide the toolbar """
        self._toolBar.setVisible(visible)

    def showPageBar(self, visible):
        """ Show or hide the page bar """
        for w in self._viewsDict.values():
            w.showPageBar(visible)

    def showStatusBar(self, visible):
        """ Show or hide the status bar """
        self._statusBar.setVisible(visible)

    def getView(self):
        """ Returns the current view """
        return self._view

    def getViewWidget(self, viewType=None):
        """
        If the given viewType is present in the available views then
        return the view.
        if viewType=None then return the current view.
        viewType that can be used:
        DataView.COLUMNS
        DataView.GALLERY
        DataView.ITEMS
        DataView.SLICES
        """
        if viewType is None:
            return self._viewsDict.get(self._view)

        return self._viewsDict.get(viewType)

    def setView(self, view):
        """ Sets view as current view """
        if view in self._views and self.__canChangeToView(view):
            self._view = view
            self.__setupCurrentViewMode()

    def getAvailableViews(self):
        """ Return the available views """
        return self._views

    def setAvailableViews(self, views):
        """ Sets the available views """
        self._views = views
        self.__createViews()

    def getPage(self):
        """ Return the current page for current view
        or -1 if current table model is None """
        return -1 if self._model is None \
            else self._viewsDict.get(self._view).getModel().getCurrentPage()

    def setPage(self, page):
        """ Change to page for the current view """
        if self._model is not None:
            self._viewsDict.get(self._view).getModel().loadPage(page)

    def getPageCount(self):
        """ Return the page count for the current view or -1 if current model
        is None """
        return -1 if self._model is None else \
            self._viewsDict.get(self._view).getModel().getPageCount()

    def getPreferedSize(self):
        """
        Returns a tuple (width, height), which represents
        the preferred dimensions to contain all the data
        """
        v = self.getViewWidget()
        if isinstance(v, ColumnsView) or isinstance(v, GalleryView):
            w, h = v.getPreferedSize()
            return w, h + self._toolBar.height()

        return 800, 600