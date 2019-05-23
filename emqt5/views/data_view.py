#!/usr/bin/python
# -*- coding: utf-8 -*-

import traceback
import os

from PyQt5.QtCore import (Qt, pyqtSlot, pyqtSignal, QSize, QModelIndex)
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QToolBar, QAction, QSpinBox,
                             QLabel, QStatusBar, QComboBox, QStackedLayout,
                             QLineEdit, QActionGroup, QMessageBox, QSplitter,
                             QSizePolicy, QPushButton, QMenu, QTableWidget,
                             QTableWidgetItem)
from PyQt5.QtGui import (QIcon, QStandardItemModel, QStandardItem, QKeySequence)
import qtawesome as qta


from emqt5.models import TableViewConfig
from emqt5.widgets import (ActionsToolBar, ColumnPropertyItemDelegate,
                           PlotConfigWidget)

from .model import (VolumeDataModel, TableDataModel, AXIS_X, AXIS_Y, AXIS_Z)
from .columns import ColumnsView
from .gallery import GalleryView
from .items import ItemsView
from ._paging_view import PagingView


PIXEL_UNITS = 1
PERCENT_UNITS = 2
SCIPION_HOME = 'SCIPION_HOME'


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

    """ This signal is emitted when the current row is changed """
    sigCurrentRowChanged = pyqtSignal(int)

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
        self.__toolTip = dict()
        self.__toolTip[self.COLUMNS] = {
            'visibleChecked': 'Hide this column',
            'visibleUnchecked': 'Show this column',
            'renderChecked': 'Do not render this column',
            'renderUnchecked': 'Render this column'
        }
        self.__toolTip[self.GALLERY] = {
            'visibleChecked': 'Hide this label',
            'visibleUnchecked': 'Show this label',
            'renderChecked': '',
            'renderUnchecked': 'Show this column'
        }
        self.__toolTip[self.ITEMS] = {
            'visibleChecked': 'Hide this label',
            'visibleUnchecked': 'Show this label',
            'renderChecked': '',
            'renderUnchecked': 'Show this column'
        }
        self._views = []
        self._view = None
        self._model = None
        self._currentRow = 0  # selected table row
        # FIXME: The following import is here because it cause a cyclic dependency
        # FIXME: we should remove the use of ImageManager and  ImageRef or find another way
        # FIXME: Check if we want ImageManager or other data model here
        from emqt5.core import ImageManager
        self._imageManager = kwargs.get('imageManager') or ImageManager(50)
        self._selection = set()
        self._selectionMode = PagingView.NO_SELECTION
        self._tablePref = dict()
        self.__initProperties(**kwargs)
        self.__setupUi(**kwargs)
        self.__setupCurrentViewMode()
        self.__setupActions()
        self.setSelectionMode(self._selectionMode)

    def __setupUi(self, **kwargs):

        self._mainLayout = QVBoxLayout(self)
        self._mainContainer = QWidget(self)
        self._mainContainerLayout = QVBoxLayout(self._mainContainer)
        self._mainContainerLayout.setSpacing(0)
        self._mainContainerLayout.setContentsMargins(0, 0, 0, 0)

        self._toolBar = QToolBar(self)
        self._mainContainerLayout.addWidget(self._toolBar)
        self._stackedLayoud = QStackedLayout(self._mainContainerLayout)
        self._stackedLayoud.setSpacing(0)

        # toolbar
        self._toolBarLeft = ActionsToolBar(self, orientation=Qt.Vertical)
        self._toolBarLeft.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self._splitter = QSplitter(self)
        self._splitter.addWidget(self._toolBarLeft)
        self._splitter.setCollapsible(0, False)
        self._splitter.addWidget(self._mainContainer)
        # selection panel
        self._selectionMenu = QMenu(self)
        self._selectionPanel = self._toolBarLeft.createPanel()
        self._selectionPanel.setObjectName('selectionPanel')
        self._selectionPanel.setStyleSheet(
            'QWidget#selectionPanel{border-left: 1px solid lightgray;}')
        self._selectionPanel.setSizePolicy(QSizePolicy.Ignored,
                                           QSizePolicy.Ignored)
        vLayout = QVBoxLayout(self._selectionPanel)

        vLayout.addWidget(QLabel(parent=self._selectionPanel,
                                 text="<strong>Actions:<strong>"))
        self._labelSelectionInfo = QLabel('Selected: 0', self._selectionPanel)

        def _addActionButton(text, icon, onTriggeredFunc):
            a = QAction(None)
            a.setText(text)
            a.setIcon(icon)
            a.triggered.connect(onTriggeredFunc)
            self._selectionMenu.addAction(a)
            self._selectionMenu.addSeparator()
            b = QPushButton(icon, text, self._selectionPanel)
            b.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
            b.setFixedWidth(150)
            b.clicked.connect(onTriggeredFunc)
            b.setStyleSheet("text-align:left")
            vLayout.addWidget(b, Qt.AlignLeft)
            return a, b

        selectAllIcon = qta.icon('fa.chevron-up', 'fa.chevron-down',
                                 options=[{'offset': (0, -0.3),
                                           'scale_factor': 0.85},
                                          {'offset': (0, 0.3),
                                           'scale_factor': 0.85}])

        self._actSelectAll, self._buttonSelectAll = _addActionButton(
            "Select all", selectAllIcon, self.__onSelectAllTriggered)

        self._actSelectToHere, self._buttonSelectTo = _addActionButton(
            "Select to here", qta.icon('fa.chevron-up'),
            self.__onToHereSelectionTriggered)

        self._actSelectFromHere, self._buttonSelectFrom = _addActionButton(
            "Select from here", qta.icon('fa.chevron-down'),
            self.__onFromHereSelectionTriggered)

        self._actInvSelection, self._buttonInvSelection = _addActionButton(
            "Invert selection", qta.icon('fa5s.exchange-alt'),
            self.__onInvertSelectionTriggered)

        self._actClearSelection, self._buttonClearSelection = _addActionButton(
            "Clear selection", qta.icon('fa.eraser'),
            self.__onClearSelectionTriggered)

        vLayout.addWidget(self._labelSelectionInfo)
        self._selectionPanel.setFixedHeight(
            vLayout.sizeHint().height() + self._labelSelectionInfo.height() * 3)

        self._actSelections = QAction(None)
        self._actSelections.setIcon(qta.icon('fa.check-circle'))
        self._actSelections.setText('Selection')
        self._toolBarLeft.addAction(self._actSelections, self._selectionPanel,
                                    exclusive=False)

        self._columnsPanel = self._toolBarLeft.createPanel()
        self._columnsPanel.setObjectName('columnsPanel')
        self._columnsPanel.setStyleSheet(
            'QWidget#columnsPanel{border-left: 1px solid lightgray;}')
        self._columnsPanel.setSizePolicy(QSizePolicy.Ignored,
                                         QSizePolicy.Ignored)
        vLayout = QVBoxLayout(self._columnsPanel)
        label = QLabel(parent=self._columnsPanel,
                       text="<strong>Column properties:</strong>")
        label.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        vLayout.addWidget(label)
        self._tableColumnProp = QTableWidget(self._columnsPanel)
        self._tableColumnProp.setObjectName("tableColumnProp")
        self._tableColumnProp.setColumnCount(3)
        self._tableColumnProp.setHorizontalHeaderLabels(['', '', 'Name'])
        self._tableColumnProp.setSelectionMode(QTableWidget.NoSelection)
        self._tableColumnProp.setSelectionBehavior(QTableWidget.SelectRows)
        self._tableColumnProp.setFocusPolicy(Qt.NoFocus)
        self._tableColumnProp.setSizePolicy(QSizePolicy.Expanding,
                                            QSizePolicy.MinimumExpanding)
        self._tableColumnProp.itemChanged.connect(
            self.__onColumnPropertyChanged)
        self._tableColumnProp.verticalHeader().setVisible(False)
        #  setting checked and unchecked icons
        checkedIcon = qta.icon('fa5s.eye')
        unCheckedIcon = qta.icon('fa5s.eye', color='#d4d4d4')
        self._tableColumnProp.setItemDelegateForColumn(
            0, ColumnPropertyItemDelegate(self,
                                          checkedIcon.pixmap(16).toImage(),
                                          unCheckedIcon.pixmap(16).toImage()))
        checkedIcon = qta.icon('fa5s.image')
        unCheckedIcon = qta.icon('fa5s.image', color='#d4d4d4')
        self._tableColumnProp.setItemDelegateForColumn(
            1, ColumnPropertyItemDelegate(self,
                                          checkedIcon.pixmap(16).toImage(),
                                          unCheckedIcon.pixmap(16).toImage()))
        vLayout.addWidget(self._tableColumnProp)
        self._columnsPanel.setMinimumHeight(vLayout.sizeHint().height())
        self._actColumns = QAction(None)
        self._actColumns.setIcon(qta.icon('fa5s.th'))
        self._actColumns.setText('Columns')
        self._toolBarLeft.addAction(self._actColumns, self._columnsPanel,
                                    exclusive=False)
        # Plot panel
        self._plotPanel = self._toolBarLeft.createPanel()
        self._plotPanel.setObjectName('plotPanel')
        self._plotPanel.setStyleSheet(
            'QWidget#plotPanel{border-left: 1px solid lightgray;}')
        self._plotPanel.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        vLayout = QVBoxLayout(self._plotPanel)
        self._plotConfigWidget = PlotConfigWidget(parent=self._plotPanel)

        vLayout.addWidget(self._plotConfigWidget)
        self._plotConfigWidget.sigError.connect(self.__showMsgBox)

        self._buttonPlot = QPushButton(self._plotPanel)
        self._buttonPlot.setText('Plot')
        self._buttonPlot.setSizePolicy(QSizePolicy.Fixed,
                                       QSizePolicy.Fixed)
        self._buttonPlot.clicked.connect(self.__onButtonPlotClicked)
        vLayout.addWidget(self._buttonPlot, 0, Qt.AlignLeft)

        self._plotPanel.setMinimumHeight(vLayout.sizeHint().height())
        self._actPlot = QAction(None)
        self._actPlot.setIcon(qta.icon('fa5s.file-signature'))
        self._actPlot.setText('Plot')
        self._toolBarLeft.addAction(self._actPlot, self._plotPanel,
                                    exclusive=False)
        # combobox current table
        self._labelCurrentTable = QLabel(parent=self._toolBar, text="Table ")
        self._toolBar.addWidget(self._labelCurrentTable)
        self._comboBoxCurrentTable = QComboBox(self._toolBar)
        self._comboBoxCurrentTable.currentIndexChanged. \
            connect(self._onCurrentTableChanged)
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
        #  dataview actions
        self.__actShowHideToolBar = QAction(self)
        self.__actShowHideToolBar.setShortcut(QKeySequence(Qt.Key_T))
        self.__actShowHideToolBar.triggered.connect(self.__onShowHideToolBar)
        self.addAction(self.__actShowHideToolBar)

        self._statusBar = QStatusBar(self)
        self._mainContainerLayout.addWidget(self._statusBar)
        self.__createViews(**kwargs)
        self._statusBar.setVisible(False)  # hide for now
        self.setMinimumWidth(700)
        self.setGeometry(0, 0, 750, 800)
        self._mainLayout.addWidget(self._splitter)

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

        galleryModel = self.getViewWidget(self.GALLERY).getModel()
        columnsModel = self.getViewWidget(self.COLUMNS).getModel()
        itemsModel = self.getViewWidget(self.ITEMS).getModel()

        pref['colConfig'] = {
            self.GALLERY: galleryModel.getColumnConfig()
            if galleryModel is not None else None,
            self.COLUMNS: columnsModel.getColumnConfig()
            if columnsModel is not None else None,
            self.ITEMS: itemsModel.getColumnConfig()
            if itemsModel is not None else None
        }
        return pref

    def __savePreferencesForCurrentTable(self):
        """ Save preferences for the current table """
        tName = self._comboBoxCurrentTable.currentText()
        pref = self._tablePref.get(tName)

        if pref is None:
            pref = self.__createPreferencesForCurrentTable()
            self._tablePref[tName] = pref
        else:
            pref["view"] = self._view

        galleryModel = self.getViewWidget(self.GALLERY).getModel()
        columnsModel = self.getViewWidget(self.COLUMNS).getModel()
        itemsModel = self.getViewWidget(self.ITEMS).getModel()

        pref['colConfig'] = {
            self.GALLERY: galleryModel.getColumnConfig()
            if galleryModel is not None else None,
            self.COLUMNS: columnsModel.getColumnConfig()
            if columnsModel is not None else None,
            self.ITEMS: itemsModel.getColumnConfig()
            if itemsModel is not None else None
        }

    def __loadPreferencesForCurrentTable(self):
        """ Load preferences for the current table """
        tName = self._comboBoxCurrentTable.currentText()
        pref = self._tablePref.get(tName)

        if pref is None:
            pref = self.__createPreferencesForCurrentTable()
            self._tablePref[tName] = pref

        self._view = pref["view"]

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
                    viewWidget.setImageManager(self._imageManager)
                    if isinstance(viewWidget, ColumnsView):
                        view = viewWidget.getTableView()
                    elif isinstance(viewWidget, GalleryView):
                        view = viewWidget.getListView()
                    else:
                        view = viewWidget

                    view.setContextMenuPolicy(Qt.ActionsContextMenu)
                    view.addAction(self._actSelectAll)
                    view.addAction(self._actSelectFromHere)
                    view.addAction(self._actSelectToHere)

                    self._stackedLayoud.addWidget(viewWidget)
                    viewWidget.sigCurrentRowChanged.connect(
                        self.__onViewRowChanged)
                    viewWidget.getPageBar().sigPageConfigChanged.connect(
                        self.__onPageConfigChanged)
                    viewWidget.sigSelectionChanged.connect(
                        self.__onCurrentViewSelectionChanged)

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
        self.__setupActions()

        viewWidget = self.getViewWidget(self._view)
        for w in self._viewsDict.values():
            m = w.getModel()
            if m is not None:
                m.sigPageChanged.disconnect(self.__onCurrentPageChanged)
            if self._model is not None:
                m = self._model.clone()
                m.sigPageChanged.connect(self.__onCurrentPageChanged)
                tName = self._comboBoxCurrentTable.currentText()
                pref = self._tablePref.get(tName)
                if pref is not None:
                    if isinstance(w, GalleryView):
                        viewType = self.GALLERY
                    elif isinstance(w, ColumnsView):
                        viewType = self.COLUMNS
                    else:
                        viewType = self.ITEMS
                    c = pref['colConfig'].get(viewType, None)
                    if c:
                        m.setColumnConfig(c)
                else:
                    if not viewWidget == w and isinstance(w, GalleryView):
                        c = m.getColumnConfig()
                        if c is not None:
                            for colConf in c:
                                colConf['visible'] = False
            w.setModel(m)

        self.__loadPreferencesForCurrentTable()
        self.__setupCurrentViewMode()
        if self._model is not None and \
                self._selectionMode == PagingView.SINGLE_SELECTION:
            self._selection.add(0)
            self.__makeSelectionInView(self._view)

    def __showTableSize(self):
        if self._model is not None:
            size = self.__getSelectionSize()
            if size:
                textTuple = ("Selected items: ",
                             "%s/%s" % (size, self._model.totalRowCount()))
            else:
                textTuple = ("No selection", "")
            text = "<br><p><strong>%s</strong></p><p>%s</p>" % textTuple
            self._labelSelectionInfo.setText(text.ljust(20))
            self._labelElements.setText(" Elements: %d " %
                                        self._model.totalRowCount())
        else:
            self._labelSelectionInfo.setText(
                "<p><strong>Selection</strong></p>")
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
            model = QStandardItemModel(self._comboBoxCurrentTable)

        model.clear()
        if self._model:
            for t in self._model.getTitles():
                item = QStandardItem(t)
                item.setData(0, Qt.UserRole)  # use UserRole for store
                model.appendRow([item])

        self._comboBoxCurrentTable.blockSignals(blocked)

    def __setupToolBarForView(self, view):
        """ Show/Hide relevant info/actions for the given view """
        # row height
        model = self.getViewWidget(view).getModel()

        rColumn = model is not None and model.hasRenderableColumn()

        self._actLabelLupe.setVisible((view == self.GALLERY or
                                      view == self.COLUMNS) and
                                      rColumn)
        self._actSpinBoxHeight.setVisible(self._actLabelLupe.isVisible())
        # dims
        self._actLabelCols.setVisible(not view == self.ITEMS)
        self._actLineEditCols.setVisible(self._actLabelCols.isVisible())
        self._lineEditCols.setEnabled(False)

    def __setupCurrentViewMode(self):
        """
        Configure current view mode: COLUMNS or GALLERY or ITEMS
        """
        viewWidget = self._viewsDict.get(self._view)

        if viewWidget is not None:
            row = self._currentRow
            self._stackedLayoud.setCurrentWidget(viewWidget)
            self.__makeSelectionInView(self._view)
            viewWidget.selectRow(row)

        a = self._viewActions[self._view].get("action", None)
        if a:
            a.setChecked(True)

        self._showViewDims()
        self.__setupToolBarForView(self._view)
        self.__savePreferencesForCurrentTable()
        self.__initTableColumnProp()

    def __clearSelections(self):
        """ Clear all selections in the views """
        self._selection.clear()

    def __setupModel(self):
        """
        Configure the current table model in all view modes
        """
        self.__setupAllWidgets()

    def __setupSpinBoxCurrentRow(self):
        """
        Configure the spinBox range consulting table mode and table dims
        """
        if self._model:
            self._spinBoxCurrentRow.setRange(1, self._model.totalRowCount())

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
        self._selectionMode = kwargs.get("selection_mode",
                                         PagingView.MULTI_SELECTION)

    def __setupActions(self):
        for v in self._actionGroupViews.actions():
            view = self._viewTypes[v.objectName()]
            v.setVisible(view in self._views)
            if self._model and view == DataView.GALLERY:
                v.setVisible(self._model.hasRenderableColumn())

    def __makeSelectionInView(self, view):
        """ Makes the current selection in the given view """
        view = self.getViewWidget(view)

        if view is not None:
            model = view.getModel()
            if model:
                view.changeSelection(self._selection)

    def __getSelectionSize(self):
        """ Returns the current selection size """
        return len(self._selection)

    def __initPlotConfWidgets(self):
        """ Initialize the plot configurations widgets """
        if self._model is None:
            params = []
        else:
            params = [col.getName() for col in self._model.getColumnConfig()]

        self._plotConfigWidget.setParams(params=params)
        self._toolBarLeft.setPanelMinSize(
            self._plotConfigWidget.sizeHint().width())

    def __initTableColumnProp(self):
        """ Initialize the columns properties widget """
        blocked = self._tableColumnProp.blockSignals(True)
        self._tableColumnProp.clear()
        self._tableColumnProp.setHorizontalHeaderLabels(["", "", 'Name'])
        viewWidget = self.getViewWidget(self._view)
        viewModel = viewWidget.getModel()

        if viewModel is not None:
            row = 0
            self._tableColumnProp.setRowCount(viewModel.columnCount())

            for colConfig in viewModel.getColumnConfig():
                item = QTableWidgetItem(colConfig.getName())
                itemV = QTableWidgetItem("")  # for 'visible' property
                itemR = QTableWidgetItem("")  # for 'renderable' property
                self._tableColumnProp.setItem(row, 0, itemV)
                self._tableColumnProp.setItem(row, 1, itemR)
                self._tableColumnProp.setItem(row, 2, item)
                if not colConfig['renderableReadOnly']:
                    flags = Qt.ItemIsEnabled | Qt.ItemIsUserCheckable
                else:
                    flags = Qt.NoItemFlags
                render = colConfig['renderable']
                if flags & Qt.ItemIsUserCheckable == Qt.ItemIsUserCheckable:
                    itemR.setCheckState(Qt.Checked if render else Qt.Unchecked)
                itemR.setData(
                    Qt.ToolTipRole,
                    self.__toolTip[self._view]
                    ['renderChecked' if render else 'renderUnchecked'])
                itemR.setFlags(flags)
                visible = colConfig['visible']
                if not colConfig['visibleReadOnly']:
                    flags = Qt.ItemIsEnabled | Qt.ItemIsUserCheckable
                else:
                    flags = Qt.NoItemFlags
                itemV.setFlags(flags)
                if flags & Qt.ItemIsUserCheckable == Qt.ItemIsUserCheckable:
                    itemV.setCheckState(Qt.Checked if visible else Qt.Unchecked)
                itemV.setData(
                    Qt.ToolTipRole,
                    self.__toolTip[self._view]
                    ['visibleChecked' if visible else 'visibleUnchecked'])
                row += 1
            self._tableColumnProp.resizeColumnsToContents()
        self._tableColumnProp.resizeColumnsToContents()
        self._tableColumnProp.horizontalHeader().setStretchLastSection(True)
        self._tableColumnProp.blockSignals(blocked)

    @pyqtSlot(QTableWidgetItem)
    def __onColumnPropertyChanged(self, item):
        """ Invoked whenever the data of item has changed. """
        viewWidget = self.getViewWidget(self._view)
        model = viewWidget.getModel()
        if model is not None:
            colConfig = model.getColumnConfig(item.row())

            if item.column() == 0:  # visible
                display = item.checkState() == Qt.Checked
                colConfig['visible'] = display
                item.setData(Qt.ToolTipRole,
                             self.__toolTip[self._view]['visibleChecked'
                             if display else 'visibleUnchecked'])
                if self._view == self.GALLERY:
                    viewWidget.setLabelIndexes(
                        model.getColumnConfig().getIndexes('visible', True))
                    viewWidget.setIconSize((self._spinBoxRowHeight.value(),
                                           self._spinBoxRowHeight.value()))
                    viewWidget.resetGallery()
                elif self._view == self.COLUMNS:
                    viewWidget.setupVisibleColumns()
                    viewWidget.resetTable()
                else:
                    viewWidget.loadCurrentItems()
            else:  # renderable
                render = item.checkState() == Qt.Checked
                if not render:
                    colConfig['renderable'] = render
                    state = \
                        Qt.Checked if self._view == self.GALLERY or \
                                      self._view == self.ITEMS else Qt.Unchecked
                    item.setCheckState(state)
                else:
                    col = item.column()
                    row = item.row()
                    if self._view == self.GALLERY or self._view == self.ITEMS:
                        # renderable is exclusive for GALLERY and ITEMS
                        blocked = self._tableColumnProp.blockSignals(True)
                        for i in range(self._tableColumnProp.rowCount()):
                            if not i == row:
                                colConfig1 = model.getColumnConfig(i)
                                if not colConfig1['renderableReadOnly']:
                                    colConfig1['renderable'] = False
                                    it = self._tableColumnProp.item(i, col)
                                    it.setCheckState(Qt.Unchecked)
                                    it.setData(
                                        Qt.ToolTipRole,
                                        self.__toolTip[self._view]
                                        ['renderUnchecked'])

                        self._tableColumnProp.blockSignals(blocked)
                    colConfig['renderable'] = render
                    ren = 'renderChecked' if render else 'renderUnchecked'
                    item.setData(Qt.ToolTipRole,
                                 self.__toolTip[self._view][ren])
                viewWidget.updateViewConfiguration()
                self.__setupToolBarForView(self._view)

    @pyqtSlot()
    def __onCurrentViewSelectionChanged(self):
        """ Invoked when the selection is changed in any view """
        self.__showTableSize()

    @pyqtSlot(bool)
    def __onToHereSelectionTriggered(self, a):
        """ Invoked when the select_all action is triggered """

        if self._model is not None:
            self._selection.update(range(0, self._currentRow + 1))
            self.__makeSelectionInView(self._view)

    @pyqtSlot(bool)
    def __onFromHereSelectionTriggered(self, a):
        """ Invoked when the select_all action is triggered """

        if self._model is not None:
            self._selection.update(range(self._currentRow,
                                         self._model.totalRowCount()))
            self.__makeSelectionInView(self._view)

    @pyqtSlot()
    def __onButtonPlotClicked(self):
        """ Invoked when the plot button is clicked """
        config = self._plotConfigWidget.getConfiguration()
        if config is not None:
            scipion = os.environ.get(SCIPION_HOME, 'scipion')
            pwplot = os.path.join(scipion, 'pyworkflow', 'apps',
                                  'pw_plot.py')
            fileName = self._model.getDataSource()
            plotConfig = config['config']
            params = config['params']
            plotType = plotConfig['plot-type']
            labels = ""
            colors = ""
            styles = ""
            markers = ""
            for key in params.keys():
                p = params[key]
                labels += ' %s' % key
                colors += ' %s' % p['color']
                styles += ' %s' % p['line-style']
                markers += ' %s' % p['marker']

            # sorted column
            columnsWidget = self.getViewWidget(self.COLUMNS)
            sOrder = None
            if columnsWidget is not None:
                hHeader = columnsWidget.getHorizontalHeader()
                sortOrder = hHeader.sortIndicatorOrder()
                sortColumn = hHeader.sortIndicatorSection()
                if sortColumn >= 0:
                    sortColumn = \
                        self._model.getColumnConfig(sortColumn).getName()
                    if sortOrder == Qt.AscendingOrder:
                        sOrder = 'ASC'
                    elif sortOrder == Qt.DescendingOrder:
                        sOrder = 'DESC'
                # If no section has a sort indicator the return value of
                # sortIndicatorOrder() is undefined.

            cmd = '%s --file %s --type %s --columns %s ' \
                  '--colors %s --styles %s --markers %s ' % \
                  (pwplot, fileName, plotType, labels, colors, styles,
                   markers)
            if sOrder is not None:
                cmd += ' --orderColumn %s --orderDir %s ' % (sortColumn,
                                                            sOrder)
            xLabel = plotConfig.get('x-label')
            yLabel = plotConfig.get('y-label')
            title = plotConfig.get('title')
            xAxis = plotConfig.get('x-axis')
            block = self._comboBoxCurrentTable.currentText()

            if xAxis:
                cmd += ' --xcolumn %s ' % xAxis
            if len(block):
                cmd += ' --block %s ' % block
            if title:
                cmd += ' --title %s ' % title
            if xLabel:
                cmd += ' --xtitle %s ' % xLabel
            if yLabel:
                cmd += ' --ytitle %s ' % yLabel
            if plotType == 'Histogram':
                cmd += ' --bins %d ' % plotConfig.get('bins', 0)

            print('Plot command: ', cmd)
        else:
            print("Invalid plot configuration")

    @pyqtSlot()
    def __onShowHideToolBar(self):
        self._toolBarLeft.setVisible(not self._toolBarLeft.isVisible())

    @pyqtSlot(bool)
    def __onClearSelectionTriggered(self, a):
        """ Invoked when the clear_selection action is triggered """
        self._selection.clear()
        self.__makeSelectionInView(self._view)

    @pyqtSlot(bool)
    def __onInvertSelectionTriggered(self, a):
        """ Invoked when the select_all action is triggered """

        if self._model is not None:
            allRows = set(range(self._model.totalRowCount()))
            self._selection.symmetric_difference_update(allRows)
            self.__makeSelectionInView(self._view)

    @pyqtSlot(bool)
    def __onSelectAllTriggered(self, a):
        """ Invoked when the select_all action is triggered """
        if self._model is not None:
            self._selection.update(range(0, self._model.totalRowCount()))
            self.__makeSelectionInView(self._view)

    @pyqtSlot(int, int, int, int)
    def __onPageConfigChanged(self, page, fist, last, step):
        """ Invoked when views change his page configuration """
        self.__makeSelectionInView(self._view)

    @pyqtSlot(int)
    def __onCurrentPageChanged(self, page):
        self._showViewDims()
        self.__makeSelectionInView(self._view)

    @pyqtSlot(int)
    def __onViewRowChanged(self, row):
        """ Invoked when views change the current row """
        if not self._currentRow == row:
            self._currentRow = row
            block = self._spinBoxCurrentRow.blockSignals(True)
            self._spinBoxCurrentRow.setValue(row + 1)
            self._spinBoxCurrentRow.blockSignals(block)
            if self._selectionMode == PagingView.SINGLE_SELECTION:
                self._selection.clear()
                self._selection.add(self._currentRow)
                self.__makeSelectionInView(self._view)

            self.sigCurrentRowChanged.emit(self._currentRow)

    @pyqtSlot(int)
    def _onCurrentTableChanged(self, index):
        """ Invoked when user change the current table """
        try:
            if self._model:
                self._selection.clear()
                if isinstance(self._model, VolumeDataModel):
                    t = self._comboBoxCurrentTable.currentText().split("(")
                    length = len(t)
                    if length > 1:
                        s = t[length-1]
                        axis = AXIS_X
                        if s == "X)":
                            axis = AXIS_X
                        elif s == "Y)":
                            axis = AXIS_Y
                        elif s == "Z)":
                            axis = AXIS_Z

                        for viewWidget in self._viewsDict.values():
                            model = viewWidget.getModel()
                            model.setAxis(axis)
                        self._selectRow(1)
                elif isinstance(self._model, TableDataModel):
                    name = self._comboBoxCurrentTable.currentText()
                    path = self._model.getDataSource()
                    if path is not None:
                        # FIXME: The following import is here because it cause a cyclic dependency
                        # FIXME: we should remove the use of EmTable
                        from emqt5.core import EmTable
                        t = self._model.getEmTable()
                        EmTable.load(path, name, t)
                        self._model.setColumnConfig(
                            TableViewConfig.fromTable(t))
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

    @pyqtSlot(QModelIndex, int, int)
    def __onRowsInserted(self, parent, first, last):
        """ Invoked when rows are inserted """
        for viewWidget in self._viewsDict.values():
            model = viewWidget.getModel()
            if model is not None:
                model.setupPage(model.getPageSize(), model.getPage())
                self._showViewDims()
                self.__showTableSize()
                self.__setupSpinBoxRowHeigth()
                self.__setupSpinBoxCurrentRow()

    @pyqtSlot(QModelIndex, QModelIndex)
    def __onDataChanged(self, topLeft, bottomRight):
        """ Invoked whenever the data in an existing item changes."""
        viewWidget = self._viewsDict.get(self._view)

        if viewWidget is not None:
            model = viewWidget.getModel()
            if model is not None:
                model.dataChanged.emit(model.createIndex(topLeft.row(),
                                                         topLeft.column()),
                                       model.createIndex(bottomRight.row(),
                                                         bottomRight.column()))

    @pyqtSlot(str)
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

    @pyqtSlot()
    def _onChangeCellSize(self):
        """
        This slot is invoked when the cell size need to be rearranged
        TODO:[developers]Review implementation. Change row height for the moment
        """
        size = self._spinBoxRowHeight.value()

        row = self._currentRow
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

        viewWidget = self._viewsDict.get(self._view)
        if viewWidget is not None:
            viewWidget.selectRow(row)
        self.__makeSelectionInView(self._view)

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

                if self._selectionMode == PagingView.SINGLE_SELECTION:
                    self._selection.clear()
                    self._selection.add(self._currentRow)

                viewWidget = self._viewsDict.get(self._view)

                if viewWidget is not None:
                    self.__makeSelectionInView(self._view)
                    viewWidget.selectRow(self._currentRow)

                if not row == self._spinBoxCurrentRow.value():
                    self._spinBoxCurrentRow.setValue(row)
                self.sigCurrentRowChanged.emit(self._currentRow)
                self.__showTableSize()

    @pyqtSlot(bool)
    def _onChangeViewTriggered(self, checked):
        """
        This slot is invoked when a view action is triggered
        """
        a = self._actionGroupViews.checkedAction()

        if a and checked:
            view = self._viewTypes[a.objectName()]
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
        if self._model is not None:
            self._model.rowsInserted.disconnect(self.__onRowsInserted)
            self._model.dataChanged.disconnect(self.__onDataChanged)
        self._model = model
        if self._model is not None:
            self._model.rowsInserted.connect(self.__onRowsInserted)
            self._model.dataChanged.connect(self.__onDataChanged)

        self.__clearSelections()
        self._tablePref.clear()
        self.__setupComboBoxCurrentTable()
        self.__setupModel()
        self.__initTableColumnProp()
        self.__initPlotConfWidgets()

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
        if view in self._views:
            self._view = view
            self.__setupCurrentViewMode()

    def selectRow(self, row):
        """
        Sets the given row as the current row for all views.
        0 will be considered as the first row.
        """
        r = self._spinBoxCurrentRow.value()
        if r == row + 1:
            self.sigCurrentRowChanged.emit(self._currentRow)
        else:
            self._spinBoxCurrentRow.setValue(row + 1)

    def getCurrentRow(self):
        """ Returns the current row """
        return self._currentRow

    def setSelectionMode(self, selectionMode):
        """
        Indicates how the view responds to user selections:
        PagingView:
                    SINGLE_SELECTION, EXTENDED_SELECTION, MULTI_SELECTION.
        """

        self._selectionMode = selectionMode

        visible = not (selectionMode == PagingView.NO_SELECTION
                       or selectionMode == PagingView.SINGLE_SELECTION)
        self._actSelections.setVisible(visible)
        self._toolBarLeft.setVisible(visible)

        policy = Qt.NoContextMenu if not visible else Qt.ActionsContextMenu

        for viewWidget in self._viewsDict.values():
            viewWidget.setSelectionMode(selectionMode)
            if isinstance(viewWidget, ColumnsView):
                viewWidget = viewWidget.getTableView()
            elif isinstance(viewWidget, GalleryView):
                viewWidget = viewWidget.getListView()

            viewWidget.setContextMenuPolicy(policy)

    def setSelectionBehavior(self, selectionBehavior):
        """
        This property holds which selection behavior the view uses.
        This property holds whether selections are done in terms of
        single items, rows or columns.

        PagingView:
                        SELECT_ITEMS, SELECT_ROWS, SELECT_COLUMNS
        """
        for viewWidget in self._viewsDict.values():
            viewWidget.setSelectionMode(selectionBehavior)

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
            return w + self._toolBarLeft.width() + 180, h + self._toolBar.height()

        return 800, 600

    def setDataInfo(self, **kwargs):
        """ Sets the data info """
        widget = self.getViewWidget(self.ITEMS)
        if widget is not None:
            widget.setInfo(**kwargs)

    def setLabelIndexes(self, labels):
        """
        Initialize the indexes of the columns that will be displayed as text
        below the images
        labels (list)
        """
        widget = self.getViewWidget(self.GALLERY)
        if widget is not None:
            widget.setLabelIndexes(labels)

        widget = self.getViewWidget(self.COLUMNS)
        if widget is not None:
            widget.setLabelIndexes(labels)


