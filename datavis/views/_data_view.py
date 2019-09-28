#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
from collections import OrderedDict

from PyQt5.QtCore import (pyqtSlot, pyqtSignal)
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QToolBar, QLabel, QStatusBar,
                             QComboBox, QStackedLayout, QLineEdit, QActionGroup,
                             QMessageBox, QSplitter, QSizePolicy, QPushButton,
                             QMenu, QTableWidget, QTableWidgetItem)
from PyQt5.QtGui import (QStandardItemModel, QKeySequence, QStandardItem)
import qtawesome as qta


from datavis.models import (RENDERABLE, RENDERABLE_RO, VISIBLE, VISIBLE_RO)
from datavis.widgets import (ActionsToolBar,  PlotConfigWidget, TriggerAction,
                           ZoomSpinBox, IconSpinBox)

from ..widgets import ColumnPropertyItemDelegate
from ._columns import ColumnsView
from ._gallery import GalleryView
from ._items import ItemsView
from ._paging_view import PagingView
from ._constants import *


SCIPION_HOME = 'SCIPION_HOME'


class DataView(QWidget):
    """
    Widget used for display em data
    """

    """ This signal is emitted when the current item is changed """
    sigCurrentItemChanged = pyqtSignal(int, int)

    """ This signal is emitted when the current table is changed """
    sigCurrentTableChanged = pyqtSignal()

    """ This signal is emitted when the current row is changed """
    sigCurrentRowChanged = pyqtSignal(int)

    VIEWS_DEFAULT = {
        COLUMNS: {NAME: 'Columns',  # view name
                  CLASS: ColumnsView,  # view class
                  ICON: 'fa.table',  # view icon
                  },
        GALLERY: {NAME: 'Gallery',
                  CLASS: GalleryView,
                  ICON: 'fa.th',
                  },
        ITEMS: {NAME: 'Items',
                CLASS: ItemsView,
                ICON: 'fa.columns',
                }
    }

    def __init__(self, parent=None, **kwargs):
        """
        Constructs a DataView.
        :param parent:       (QWidget) Parent widget
        :param kwargs:
             model:          (TableModel) The data model
             selectionMode:  (int) SINGLE_SELECTION(default),EXTENDED_SELECTION,
                             MULTI_SELECTION or NO_SELECTION
             views:          (dict) Specify the views that will be available.
                             Default value: [COLUMNS, GALLERY, ITEMS]
             view:           (int) The default view to be set
             size:           (int) The row height for ColumnsView and icon size
                             for GalleryView. Default value: 64
             maxCellSize:    (int) The maximum value for row height in
                             ColumnsView and icon size in GalleryView. Default
                             value: 300
             minCellSize:    (int) The minimum value for row height in
                             ColumnsView and icon size in GalleryView. Default
                             value: 20
        """
        QWidget.__init__(self, parent=parent)

        viewsDict = kwargs.get('views', {COLUMNS: {}, GALLERY: {}, ITEMS: {}})
        self._viewsDict = OrderedDict()
        config = dict()
        for k, v in viewsDict.items():
            d = dict(self.VIEWS_DEFAULT[k])
            d.update(v)
            self._viewsDict[k] = d
            config[k] = d.get(TABLE_CONFIG)

        self._model = None
        self._displayConfig = None
        self._currentRow = 0  # selected table row
        self._selection = set()
        self._selectionMode = PagingView.NO_SELECTION
        self._tablePref = dict()

        self._defaultRowHeight = kwargs.get('size', 64)
        self._maxRowHeight = kwargs.get('maxCellSize', 300)
        self._minRowHeight = kwargs.get('minCellSize', 25)
        self._zoomUnits = kwargs.get('zoomUnits', PIXEL_UNITS)
        self._viewKey = kwargs.get('defaultView', COLUMNS)
        if not self.hasView(self._viewKey):
            raise Exception("Invalid 'defaultView' value %s" % self._viewKey)
        self._selectionMode = kwargs.get('selectionMode',
                                         PagingView.MULTI_SELECTION)
        self.__setupGUI(**kwargs)
        self.__setupActions()
        self.setSelectionMode(self._selectionMode)
        self.setModel(kwargs['model'], config)

    def __setupGUI(self, **kwargs):
        """ Create the main GUI of the DataView.
         The GUI is composed by two main panels divided by a Splitter:
         1) (left) Collapsible ToolBar with several actions
         2) (right) Views container:
            - Toolbar on the top, with current table actions
            - Main view widget area
            - StatusBar (not shown now)
        """
        mainLayout = QVBoxLayout(self)
        splitter = QSplitter(self)

        # Create and add the left ToolBar
        self._leftToolBar = self.__createLeftToolbar()
        splitter.addWidget(self._leftToolBar)
        splitter.setCollapsible(0, False)

        # Create the Views container
        viewsContainer = QWidget(self)
        viewsContainerLayout = QVBoxLayout(viewsContainer)
        viewsContainerLayout.setSpacing(0)
        viewsContainerLayout.setContentsMargins(0, 0, 0, 0)

        # Add ToolBar on the Top
        self._toolBar = self.__createToolbar()
        viewsContainerLayout.addWidget(self._toolBar)
        # Create views and add to StackedLayout
        self._stackedLayout = QStackedLayout(viewsContainerLayout)
        self._stackedLayout.setSpacing(0)
        self.__createViews(**kwargs)
        # Create status bar
        self._statusBar = QStatusBar(self)
        self._statusBar.setVisible(False)  # hide for now
        viewsContainerLayout.addWidget(self._statusBar)
        splitter.addWidget(viewsContainer)

        # Add splitter to main layout and set some properties
        mainLayout.addWidget(splitter)
        self.setMinimumWidth(700)
        self.setGeometry(0, 0, 750, 800)

    def __createLeftToolbar(self):
        toolbar = ActionsToolBar(self, orientation=Qt.Vertical)
        toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.__addSelectionActions(toolbar)
        self.__addColumnsPanel(toolbar)
        self.__addPlotPanel(toolbar)
        # Show/hide left Toolbar action
        self.addAction(TriggerAction(self, 'SHToolBar',
                                     slot=self.__onShowHideToolBar,
                                     shortCut=QKeySequence(Qt.Key_T)))
        return toolbar

    def __addSelectionActions(self, toolbar):
        """ Add selection related actions to the left toolbar. """
        # selection panel
        self._selectionMenu = QMenu(self)
        self._selectionPanel = toolbar.createPanel('selectionPanel')
        self._selectionPanel.setSizePolicy(QSizePolicy.Ignored,
                                           QSizePolicy.Ignored)
        vLayout = QVBoxLayout(self._selectionPanel)

        vLayout.addWidget(QLabel(parent=self._selectionPanel,
                                 text="<strong>Actions:<strong>"))
        self._labelSelectionInfo = QLabel('Selected: 0', self._selectionPanel)

        def _addActionButton(text, icon, onTriggeredFunc):
            """
            Add an TriggerAction to the selection menu, and a QPushButton to the
            selection panel
            :param text:            (str) the action text
            :param icon:            (QIcon) the action icon
            :param onTriggeredFunc: Triggered function for the created action
            :return:                (TriggerAction, QPushButton)
            """
            act = TriggerAction(parent=None, actionName=text, text=text,
                                icon=icon, slot=onTriggeredFunc)
            self._selectionMenu.addAction(act)
            self._selectionMenu.addSeparator()
            b = QPushButton(icon, text, self._selectionPanel)
            b.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
            b.setFixedWidth(150)
            b.clicked.connect(onTriggeredFunc)
            b.setStyleSheet("text-align:left")
            vLayout.addWidget(b, Qt.AlignLeft)
            return act, b

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

        self._actSelections = TriggerAction(parent=None, actionName="ASelect",
                                            text='Selection',
                                            faIconName='fa.check-circle')
        toolbar.addAction(self._actSelections, self._selectionPanel,
                          exclusive=False)

    def __addColumnsPanel(self, toolbar):
        """ Add columns actions panel to the left toolbar. """
        self._columnsPanel = toolbar.createPanel('columnsPanel')
        self._columnsPanel.setSizePolicy(QSizePolicy.Ignored,
                                         QSizePolicy.Ignored)
        vLayout = QVBoxLayout(self._columnsPanel)
        label = QLabel(parent=self._columnsPanel,
                       text="<strong>Column properties:</strong>")
        label.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        vLayout.addWidget(label)
        cpTable = QTableWidget(self._columnsPanel)
        cpTable.setObjectName("tableColumnProp")
        cpTable.setColumnCount(3)
        cpTable.setHorizontalHeaderLabels(['', '', 'Name'])
        cpTable.setSelectionMode(QTableWidget.NoSelection)
        cpTable.setSelectionBehavior(QTableWidget.SelectRows)
        cpTable.setFocusPolicy(Qt.NoFocus)
        cpTable.setSizePolicy(QSizePolicy.Expanding,
                              QSizePolicy.MinimumExpanding)
        cpTable.itemChanged.connect(self.__onItemChanged)
        cpTable.verticalHeader().setVisible(False)
        #  setting checked and unchecked icons
        checkedIcon = qta.icon('fa5s.eye')
        unCheckedIcon = qta.icon('fa5s.eye', color='#d4d4d4')
        cpTable.setItemDelegateForColumn(
            0, ColumnPropertyItemDelegate(self,
                                          checkedIcon.pixmap(16).toImage(),
                                          unCheckedIcon.pixmap(16).toImage()))
        checkedIcon = qta.icon('fa5s.image')
        unCheckedIcon = qta.icon('fa5s.image', color='#d4d4d4')
        cpTable.setItemDelegateForColumn(
            1, ColumnPropertyItemDelegate(self,
                                          checkedIcon.pixmap(16).toImage(),
                                          unCheckedIcon.pixmap(16).toImage()))
        vLayout.addWidget(cpTable)
        self._tableColumnProp = cpTable
        self._columnsPanel.setMinimumHeight(vLayout.sizeHint().height())
        self._actColumns = TriggerAction(parent=None, actionName='AColumns',
                                         text='Columns', faIconName='fa5s.th')
        toolbar.addAction(self._actColumns, self._columnsPanel,
                          exclusive=False)

    def __addPlotPanel(self, toolbar):
        """ Add Plot panel to the left toolbar. """
        self._plotPanel = toolbar.createPanel('plotPanel')
        self._plotPanel.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        vLayout = QVBoxLayout(self._plotPanel)
        self._plotConfigWidget = PlotConfigWidget(parent=self._plotPanel)

        vLayout.addWidget(self._plotConfigWidget)
        self._plotConfigWidget.sigError.connect(self.__showMsgBox)

        plotButton = QPushButton(self._plotPanel)
        plotButton.setText('Plot')
        plotButton.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        plotButton.clicked.connect(self.__onButtonPlotClicked)
        vLayout.addWidget(plotButton, 0, Qt.AlignLeft)

        self._plotPanel.setMinimumHeight(vLayout.sizeHint().height())
        self._actPlot = TriggerAction(parent=None, actionName='APlot',
                                      text='Plot',
                                      faIconName='fa5s.file-signature')
        toolbar.addAction(self._actPlot, self._plotPanel, exclusive=False)

    def __createToolbar(self):
        toolbar = QToolBar(self)

        # Combobox for selecting current table
        self._labelCurrentTable = QLabel(parent=toolbar, text="Table ")
        toolbar.addWidget(self._labelCurrentTable)
        self._comboBoxCurrentTable = QComboBox(toolbar)
        self._comboBoxCurrentTable.currentIndexChanged.connect(
            self._onCurrentTableChanged)
        toolbar.addWidget(self._comboBoxCurrentTable)
        toolbar.addSeparator()
        toolbar.addSeparator()

        # Actions to switch from views
        self._actionGroupViews = QActionGroup(toolbar)
        self._actionGroupViews.setExclusive(True)
        for view, viewInfo in self._viewsDict.items():
            #  create action with the view name
            a = TriggerAction(parent=toolbar, actionName=viewInfo[NAME],
                              text=viewInfo[NAME], faIconName=viewInfo[ICON],
                              checkable=True, slot=self._onChangeViewTriggered,
                              userData=view)
            viewInfo[ACTION] = a
            self._actionGroupViews.addAction(a)
            toolbar.addAction(a)
            a.setChecked(view == self._viewKey)
            a.setVisible(True)

        # table rows and columns
        self._itemsLabel = QLabel(toolbar)
        self._itemsLabel.setText(" Items ")
        toolbar.addWidget(self._itemsLabel)
        toolbar.addSeparator()
        self._labelRows = QLabel(toolbar)
        self._labelRows.setText(" Rows ")
        self._actLabelRows = toolbar.addWidget(self._labelRows)
        self._lineEditRows = QLineEdit(toolbar)
        self._lineEditRows.setMaximumSize(70, 22)
        self._lineEditRows.setEnabled(False)
        self._actLineEditRows = toolbar.addWidget(self._lineEditRows)
        self._labelCols = QLabel(toolbar)
        self._labelCols.setText(" Cols ")
        self._actLabelCols = toolbar.addWidget(self._labelCols)
        self._lineEditCols = QLineEdit(toolbar)
        self._lineEditCols.setMaximumSize(70, 22)
        self._lineEditCols.setEnabled(False)
        self._actLineEditCols = toolbar.addWidget(self._lineEditCols)
        toolbar.addSeparator()

        # cell navigator
        self._spinBoxCurrentRow = IconSpinBox(toolbar, valueType=int,
                                              minValue=1, maxValue=2,
                                              iconName='fa.level-down')
        self._spinBoxCurrentRow.setMaximumWidth(50)
        self._spinBoxCurrentRow.sigValueChanged[int].connect(self._selectRow)
        self._actSpinBoxCurrentRow = toolbar.addWidget(self._spinBoxCurrentRow)
        toolbar.addSeparator()

        # cell resizing
        z = self._zoomUnits
        z = ZoomSpinBox.PIXELS if z == PIXEL_UNITS else ZoomSpinBox.PERCENT
        self._spinBoxRowHeight = ZoomSpinBox(
            toolbar, valueType=int, minValue=self._minRowHeight,
            maxValue=self._maxRowHeight, currentValue=self._defaultRowHeight,
            zoomUnits=z)
        self._spinBoxRowHeight.sigValueChanged[int].connect(
            self._onChangeCellSize)
        self._actSpinBoxHeight = toolbar.addWidget(self._spinBoxRowHeight)

        return toolbar

    def __createDefaultPreferences(self):
        """
        Creates the default preferences for the current TableModel
        :return: A dict with the default preferences
        """
        pref = dict()

        if self._model.getRowsCount() == 1 and self.hasView(ITEMS):
            pref[VIEW] = ITEMS
        elif self.hasView(COLUMNS):
            pref[VIEW] = COLUMNS
        else:
            pref[VIEW] = self._viewsDict[0] if self._viewsDict else None

        pref[TABLE_CONFIG] = {v: None for v in self._viewsDict.keys()}

        return pref

    def __savePreferencesForCurrentTable(self, tableName=None):
        """ Save preferences for the current table """
        if tableName is None:
            tableName = self._comboBoxCurrentTable.currentText()

        pref = self._tablePref.get(tableName)

        if pref is None:
            pref = self.__createDefaultPreferences()
            self._tablePref[tableName] = pref
        pref[VIEW] = self._viewKey

        d = pref[TABLE_CONFIG]
        for v in self._viewsDict.keys():
            d[v] = self.getView(v).getDisplayConfig()

    def __loadPreferencesForCurrentTable(self):
        """ Load preferences for the current table """
        tableName = self._comboBoxCurrentTable.currentText()
        pref = self._tablePref.get(tableName)

        if pref is None:
            pref = self.__createDefaultPreferences()
            self._tablePref[tableName] = pref

        self._viewKey = pref[VIEW]

    def __getTableConfig(self, tableName):
        """
        Return the TableConfig for the given table name. DataView maintains the
        preferences for all tables in the current model,
        including the TableConfig.
        :param tableName: (str) The table name
        """
        return self._tablePref[tableName].get(TABLE_CONFIG)

    def __connectViewSignals(self, viewWidget):
        """
        Connects the view widget signals to the corresponding slots
        :param viewWidget: The view widget: ColumnsView, GalleryView, ItemsView
                           or other registered widget
        """
        if viewWidget is None:
            raise Exception(
                'The view widget can not be None for signal connections')

        viewWidget.sigSizeChanged.connect(self._showViewDims)
        viewWidget.sigCurrentRowChanged.connect(self.__onViewRowChanged)
        viewWidget.getPageBar().sigPagingInfoChanged.connect(
            self.__onPageConfigChanged)
        viewWidget.sigSelectionChanged.connect(
            self.__onCurrentViewSelectionChanged)

    def __disconnectViewSignals(self, viewWidget):
        """
        Disconnects the view signals form the internal slots
        :param viewWidget: The view widget.
        """
        viewWidget.sigCurrentRowChanged.disconnect(self.__onViewRowChanged)
        viewWidget.getPageBar().sigPagingInfoChanged.disconnect(
            self.__onPageConfigChanged)
        viewWidget.sigSelectionChanged.disconnect(
            self.__onCurrentViewSelectionChanged)
        viewWidget.sigCurrentRowChanged.disconnect(self.__onViewRowChanged)

    def __createView(self, viewType, **kwargs):
        """ Create and return a view. The parent of the view will be self """
        viewClass = self._viewsDict[viewType][CLASS]
        if viewClass is None:
            raise Exception('Unregistered class for view type=%d' % viewType)

        return viewClass(self, **kwargs)

    def __createViews(self, **kwargs):
        """ Create the views if necessary. Inserts the views in the GUI. """
        for view in self.VIEWS_DEFAULT.keys():
            if self.hasView(view):
                viewInfo = self._viewsDict[view]
                if viewInfo.get(VIEW) is None:
                    viewWidget = self.__createView(view, **kwargs)
                    viewInfo[VIEW] = viewWidget
                    if viewWidget is not None:
                        viewWidget.setContextMenuPolicy(Qt.ActionsContextMenu)
                        viewWidget.addAction(self._actSelectAll)
                        viewWidget.addAction(self._actSelectFromHere)
                        viewWidget.addAction(self._actSelectToHere)
                        self._stackedLayout.addWidget(viewWidget)
                        self.__connectViewSignals(viewWidget)
            else:
                self.__removeView(view)

    def __removeView(self, view):
        """ If the given view exist in the GUI then will be removed. """
        viewInfo = self._viewsDict[view]
        viewWidget = viewInfo[VIEW]
        if viewWidget is not None:
            self._stackedLayout.removeWidget(viewWidget)
            viewInfo[VIEW] = None
            viewWidget.setParent(None)
            self.__disconnectViewSignals(viewWidget)
            del viewWidget

    def __setupAllWidgets(self):
        """
        Configure all widgets:
           * configure the value range for all spinboxs
           * show table dims

        Invoke this function when you needs to initialize all widgets.
        Example: when setting new model in the DataView
        """
        self._showViewDims()
        self.__showSelectionInfo()
        self.__setupSpinBoxCurrentRow()
        self._spinBoxCurrentRow.setValue(1)
        self.__setupActions()

    def __showSelectionInfo(self):
        """ Show the selection info in the selection panel """
        if self._model is not None:
            size = self.__getSelectionSize()
            if size:
                textTuple = ("Selected items: ",
                             "%s/%s" % (size, self._model.getRowsCount()))
            else:
                textTuple = ("No selection", "")
            text = "<br><p><strong>%s</strong></p><p>%s</p>" % textTuple
            self._labelSelectionInfo.setText(text.ljust(20))
            self._itemsLabel.setText(" Items: %d " % self._model.getRowsCount())
        else:
            self._labelSelectionInfo.setText(
                "<p><strong>Selection</strong></p>")
            self._itemsLabel.setText("")

    def __hasRenderableColumn(self, viewType=None):
        """ Returns True if the widget for the given type has renderable columns
        """
        if viewType is None:
            viewType = self._viewKey
        viewWidget = self._viewsDict[viewType][VIEW]
        config = None if viewWidget is None else viewWidget.getDisplayConfig()
        return config is not None and config.hasColumnConfig(renderable=True)

    def __setupSpinBoxRowHeigth(self):
        """ Configure the row height spinbox """
        self._spinBoxRowHeight.setValue(self._defaultRowHeight)

    def __setupComboBoxCurrentTable(self):
        """
        Configure the elements in combobox currentTable for user selection.
        """
        self._comboBoxCurrentTable.blockSignals(True)
        model = self._comboBoxCurrentTable.model()
        if not model:
            model = QStandardItemModel(self._comboBoxCurrentTable)

        model.clear()
        if self._model:
            index = -1
            tableName = self._model.getTableName()
            for i, name in enumerate(self._model.getTableNames()):
                item = QStandardItem(name)
                model.appendRow([item])
                if name == tableName:
                    index = i

            if index > -1:
                self._comboBoxCurrentTable.setCurrentIndex(index)

        self._comboBoxCurrentTable.blockSignals(False)

    def __setupToolBarForView(self, view):
        """ Show/Hide relevant info/actions for the given view """
        # row height
        rColumn = self.__hasRenderableColumn()

        self._actSpinBoxHeight.setVisible(
            (view == GALLERY or view == COLUMNS) and rColumn)
        # dims
        self._actLabelCols.setVisible(not view == ITEMS)
        self._actLineEditCols.setVisible(self._actLabelCols.isVisible())
        self._lineEditCols.setEnabled(False)

    def __setupCurrentViewMode(self):
        """
        Configure current view mode: COLUMNS or GALLERY or ITEMS
        """
        viewWidget = self.getView()
        setup = True
        if viewWidget is not None:
            if self._viewKey == GALLERY:
                gConfig = viewWidget.getDisplayConfig()
                if not gConfig.hasColumnConfig(renderable=True):
                    setup = False
                    for viewInfo in self._viewsDict.values():
                        widget = viewInfo[VIEW]
                        viewType = widget.getViewType()
                        if not viewType == GALLERY:
                            config = widget.getDisplayConfig()
                            if config is not None:
                                for i, r in config.iterColumns(renderable=True):
                                    c = gConfig.getColumnConfig(i)
                                    if not c[RENDERABLE_RO]:
                                        c[RENDERABLE] = True
                                        setup = True
                                        viewWidget.setModelColumn(i)
                                        break
                        if setup:
                            break
        else:
            setup = False

        if setup:
            row = self._currentRow
            self._stackedLayout.setCurrentWidget(viewWidget)
            self.__makeSelectionInView(self._viewKey)
            viewWidget.selectRow(row)
            a = self._viewsDict[self._viewKey][ACTION]
            if a:
                a.setChecked(True)

            self._showViewDims()
            self.__setupToolBarForView(self._viewKey)
            self.__savePreferencesForCurrentTable()
            self.__initTableColumnProp()

    def __setupModel(self, config=None):
        """
        Configure the current table model in all view modes
        """
        self.__setupAllWidgets()

        tableName = self._model.getTableName()
        self.__loadPreferencesForCurrentTable()
        d = self.__getTableConfig(tableName) if config is None else config
        for viewType in self._viewsDict.keys():
            w = self.getView(viewType)
            w.setModel(self._model, d.get(viewType))

        self.__setupCurrentViewMode()
        self.__setupSpinBoxRowHeigth()
        self._onChangeCellSize(self._spinBoxRowHeight.getValue())
        if self._selectionMode == PagingView.SINGLE_SELECTION:
            self._selection.add(0)
            self.__makeSelectionInView(self._viewKey)

    def __setupSpinBoxCurrentRow(self):
        """
        Configure the spinBox range consulting table mode and table dims
        """
        if self._model:
            self._spinBoxCurrentRow.setRange(1, self._model.getRowsCount())

    def __clearViews(self):
        """ Clear all views """
        for viewWidget in self.getAllViews():
            viewWidget.clear()

    def __setupActions(self):
        for v in self._actionGroupViews.actions():
            v.setVisible(self.hasView(v.getUserData()))
            # FIXME[phv] Hide GalleryView if there are no renderable columns
            #if self._model and view == GALLERY:
            #    v.setVisible(self.__hasRenderableColumn())

    def __makeSelectionInView(self, view):
        """ Makes the current selection in the given view """
        view = self.getView(view)

        if view is not None and self._model is not None:
            view.changeSelection(self._selection)

    def __getSelectionSize(self):
        """ Returns the current selection size """
        return len(self._selection)

    def __initPlotConfWidgets(self):
        """ Initialize the plot configurations widgets """
        if self._displayConfig is None:
            params = []
        else:
            params = [c.getName() for i, c in self._displayConfig.iterColumns()]

        self._plotConfigWidget.setParams(params=params)
        self._leftToolBar.setPanelMinSize(
            self._plotConfigWidget.sizeHint().width())

    def __initTableColumnProp(self):
        """ Initialize the columns properties widget """
        cpTable = self._tableColumnProp  # shortcut
        cpTable.blockSignals(True)
        cpTable.clear()
        cpTable.setHorizontalHeaderLabels(["", "", 'Name'])
        viewWidget = self.getView()
        dConfig = viewWidget.getDisplayConfig()

        if dConfig is not None:
            row = 0
            cpTable.setRowCount(dConfig.getColumnsCount())
            for i, colConfig in dConfig.iterColumns():
                item = QTableWidgetItem(colConfig.getName())
                itemV = QTableWidgetItem("")  # for 'visible' property
                itemR = QTableWidgetItem("")  # for 'renderable' property
                cpTable.setItem(row, 0, itemV)
                cpTable.setItem(row, 1, itemR)
                cpTable.setItem(row, 2, item)
                flags = Qt.ItemIsUserCheckable | Qt.ItemIsEnabled
                render = colConfig[RENDERABLE]
                itemR.setCheckState(Qt.Checked if render else Qt.Unchecked)
                itemR.setData(Qt.ToolTipRole, 'Render or not this column')
                itemR.setFlags(flags)
                g = self._viewKey == GALLERY
                v = i in colConfig.getLabels() if g else colConfig[VISIBLE]
                itemV.setFlags(flags)
                itemV.setCheckState(Qt.Checked if v else Qt.Unchecked)
                itemV.setData(Qt.ToolTipRole, 'Show/hide this column')
                row += 1
            cpTable.resizeColumnsToContents()
        cpTable.resizeColumnsToContents()
        cpTable.horizontalHeader().setStretchLastSection(True)
        cpTable.blockSignals(False)

    def __reverseCheckState(self, item):
        """ Reverse the check state for the given QTableWidgetItem """
        st = Qt.Checked if item.checkState() == Qt.Unchecked else Qt.Unchecked
        item.setCheckState(st)

    @pyqtSlot(QTableWidgetItem)
    def __onItemChanged(self, item):
        """ Invoked whenever the data of item has changed. """
        self._tableColumnProp.blockSignals(True)
        viewWidget = self.getView()
        dispConf = viewWidget.getDisplayConfig()
        if dispConf is not None:
            row, col = item.row(), item.column()
            colConfig = dispConf.getColumnConfig(row)
            if col == 0:  # visible
                d = item.checkState() == Qt.Checked
                if self._viewKey == GALLERY:
                    method = list.append if d else list.remove
                    labels = colConfig.getLabels()
                    method(labels, row)
                    size = self._spinBoxRowHeight.getValue()
                    viewWidget.setIconSize((size, size))
                elif not colConfig[VISIBLE_RO]:
                    if dispConf.getColumnsCount(visible=True) == 1 and not d:
                        self.__reverseCheckState(item)
                    else:
                        colConfig[VISIBLE] = d
                else:
                    self.__reverseCheckState(item)
            else:  # renderable
                r = item.checkState() == Qt.Checked
                gi = self._viewKey == GALLERY or self._viewKey == ITEMS
                hasRender = dispConf.hasColumnConfig(renderable=True)
                if colConfig[RENDERABLE_RO]:
                    self.__reverseCheckState(item)
                    if gi and colConfig[RENDERABLE]:
                        # renderable is exclusive for GALLERY and ITEMS
                        for i, cc in dispConf.iterColumns(renderable=True):
                            if not i == row:
                                if not cc[RENDERABLE_RO]:
                                    cc[RENDERABLE] = False
                                    it = self._tableColumnProp.item(i, col)
                                    it.setCheckState(Qt.Unchecked)
                        viewWidget.setModelColumn(row)
                else:
                    colConfig[RENDERABLE] = r
                    if gi and not r:
                        colConfig[RENDERABLE] = True
                        self.__reverseCheckState(item)
                    elif gi:
                        # renderable is exclusive for GALLERY and ITEMS
                        for i, cc in dispConf.iterColumns(renderable=True):
                            if not i == row:
                                if not cc[RENDERABLE_RO]:
                                    cc[RENDERABLE] = False
                                    it = self._tableColumnProp.item(i, col)
                                    it.setCheckState(Qt.Unchecked)
                        viewWidget.setModelColumn(row)

                r = dispConf.hasColumnConfig(renderable=True)
                c = self._viewKey == COLUMNS
                if c and r and not hasRender:
                    row = self._currentRow
                    size = self._spinBoxRowHeight.getValue()
                    viewWidget.setIconSize((size, size))
                    self._selectRow(row)
                elif c and not r and hasRender:
                    row = self._currentRow
                    viewWidget.setIconSize((self._minRowHeight,
                                            self._minRowHeight))
                    self._selectRow(row)

            viewWidget.updateViewConfiguration()
            self.__setupToolBarForView(self._viewKey)
        self._tableColumnProp.blockSignals(False)

    @pyqtSlot()
    def __onCurrentViewSelectionChanged(self):
        """ Invoked when the selection is changed in any view """
        self.__showSelectionInfo()

    @pyqtSlot(bool)
    def __onToHereSelectionTriggered(self, a):
        """ Invoked when the select_all action is triggered """

        if self._model is not None:
            self._selection.update(range(0, self._currentRow + 1))
            self.__makeSelectionInView(self._viewKey)

    @pyqtSlot(bool)
    def __onFromHereSelectionTriggered(self, a):
        """ Invoked when the select_all action is triggered """

        if self._model is not None:
            self._selection.update(range(self._currentRow,
                                         self._model.getRowsCount()))
            self.__makeSelectionInView(self._viewKey)

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
            columnsWidget = self.getView(COLUMNS)
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
        self._leftToolBar.setVisible(not self._leftToolBar.isVisible())

    @pyqtSlot(bool)
    def __onClearSelectionTriggered(self, a):
        """ Invoked when the clear_selection action is triggered """
        self._selection.clear()
        self.__makeSelectionInView(self._viewKey)

    @pyqtSlot(bool)
    def __onInvertSelectionTriggered(self, a):
        """ Invoked when the select_all action is triggered """

        if self._model is not None:
            allRows = set(range(self._model.getRowsCount()))
            self._selection.symmetric_difference_update(allRows)
            self.__makeSelectionInView(self._viewKey)

    @pyqtSlot(bool)
    def __onSelectAllTriggered(self, a):
        """ Invoked when the select_all action is triggered """
        if self._model is not None:
            self._selection.update(range(0, self._model.getRowsCount()))
            self.__makeSelectionInView(self._viewKey)

    @pyqtSlot()
    def __onPageConfigChanged(self):
        """ Invoked when views change his page configuration """
        self.__makeSelectionInView(self._viewKey)

    @pyqtSlot(int)
    def __onCurrentPageChanged(self, page):
        self._showViewDims()
        self.__makeSelectionInView(self._viewKey)

    @pyqtSlot(int)
    def __onViewRowChanged(self, row):
        """ Invoked when views change the current row """
        if not self._currentRow == row:
            self._currentRow = row
            self._spinBoxCurrentRow.blockSignals(True)
            self._spinBoxCurrentRow.setValue(row + 1)
            self._spinBoxCurrentRow.blockSignals(False)
            if self._selectionMode == PagingView.SINGLE_SELECTION:
                self._selection.clear()
                self._selection.add(self._currentRow)
                self.__makeSelectionInView(self._viewKey)

            self.sigCurrentRowChanged.emit(self._currentRow)

    @pyqtSlot(int)
    def _onCurrentTableChanged(self, index):
        """ Invoked when user change the current table """
        lastName = self._model.getTableName()
        name = self._comboBoxCurrentTable.currentText()
        self.__savePreferencesForCurrentTable(lastName)
        self._model.loadTable(name)
        self._currentRow = 0
        self._selection.clear()
        self.__setupModel()
        # FIXME[phv] self.__initPlotConfWidgets()??

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

    @pyqtSlot(int)
    def _onChangeCellSize(self, size):
        """
        This slot is invoked when the cell size need to be rearranged
        TODO: Review implementation. Change row height for the moment
        """
        row = self._currentRow
        for viewWidget in self.getAllViews():
            if viewWidget.getViewType() in [COLUMNS, GALLERY]:
                viewWidget.setIconSize((size, size))

        viewWidget = self.getView()
        if viewWidget is not None:
            viewWidget.selectRow(row)
        self.__makeSelectionInView(self._viewKey)

    @pyqtSlot()
    def _showViewDims(self):
        """
        Show column and row count in the QLineEdits
        """
        viewWidget = self.getView()
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
        if self._model and row in range(1, self._model.getRowsCount() + 1):
            self._currentRow = row - 1

            if self._selectionMode == PagingView.SINGLE_SELECTION:
                self._selection.clear()
                self._selection.add(self._currentRow)

            viewWidget = self.getView()

            if viewWidget is not None:
                self.__makeSelectionInView(self._viewKey)
                viewWidget.selectRow(self._currentRow)

            if not row == self._spinBoxCurrentRow.getValue():
                self._spinBoxCurrentRow.setValue(row)
            self.sigCurrentRowChanged.emit(self._currentRow)
            self.__showSelectionInfo()

    @pyqtSlot(bool)
    def _onChangeViewTriggered(self, checked):
        """
        This slot is invoked when a view action is triggered
        """
        a = self._actionGroupViews.checkedAction()

        if a and checked:
            self._viewKey = a.getUserData()
            self.__setupCurrentViewMode()

    def getSelectedViewMode(self):
        """
        Return the selected mode. Possible values are:
        COLUMNS, GALLERY, ITEMS
        """
        return self._viewKey

    def setModel(self, model, config=None):
        """ Set the table model for display. """
        self.__clearViews()
        self._model = model
        self._selection.clear()
        self._tablePref.clear()
        self.__setupComboBoxCurrentTable()
        self.__setupModel(config)
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

    def showToolBar(self, visible):
        """ Show or hide the toolbar """
        self._toolBar.setVisible(visible)

    def showPageBar(self, visible):
        """ Show or hide the page bar """
        for widget in self.getAllViews():
            widget.showPageBar(visible)

    def showStatusBar(self, visible):
        """ Show or hide the status bar """
        self._statusBar.setVisible(visible)

    def getViewKey(self):
        """ Returns the current view """
        return self._viewKey

    def getView(self, viewType=None):
        """
        If the given viewType is present in the available views then
        return the view.
        if viewType=None then return the current view.
        viewType that can be used: COLUMNS, GALLERY, ITEMS, SLICES
        """
        return self._viewsDict[viewType or self._viewKey][VIEW]

    def hasView(self, viewKey):
        """ Return True if the given viewKey is present in the DataView. """
        return viewKey in self._viewsDict

    def getAllViews(self):
        """ Returns a list with the current view widgets """
        return [v[VIEW] for v in self._viewsDict.values()]

    def setView(self, viewKey):
        """ Sets view as current view """
        if self.hasView(viewKey):
            self._viewKey = viewKey
            self.__setupCurrentViewMode()

    def selectRow(self, row):
        """
        Sets the given row as the current row for all views.
        0 will be considered as the first row.
        """
        r = self._spinBoxCurrentRow.getValue()
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
        self._leftToolBar.setVisible(visible)

        policy = Qt.NoContextMenu if not visible else Qt.ActionsContextMenu

        for viewWidget in self.getAllViews():
            viewWidget.setSelectionMode(selectionMode)
            viewWidget.setContextMenuPolicy(policy)

    def setSelectionBehavior(self, selectionBehavior):
        """
        This property holds which selection behavior the view uses.
        This property holds whether selections are done in terms of
        single items, rows or columns.

        PagingView:
                        SELECT_ITEMS, SELECT_ROWS, SELECT_COLUMNS
        """
        for viewWidget in self.getAllViews():
            viewWidget.setSelectionMode(selectionBehavior)

    def getAvailableViews(self):
        """ Return the available views """
        return self._viewsDict.keys()

    # FIXME: We need to check this method, maybe together with setModel
    def setAvailableViews(self, views):
        """ Sets the available views """
        raise Exception("FIXME: Needs revision")
        self.__createViews()

    def getPage(self):
        """ Return the current page for current view
        or -1 if current table model is None """
        if self._model is None:
            return -1
        return self.getView().getPageBar().getCurrentPage()

    def setPage(self, page):
        """ Change to page for the current view """
        if self._model is not None:
            self.getView().getPageBar().setCurrentPage(page)

    def getPageCount(self):
        """ Return the page count for the current view or -1 if current model
        is None """
        if self._model is None:
            return -1
        return self.getView().getPageBar().getPageCount()

    def getPreferredSize(self):
        """
        Returns a tuple (width, height), which represents
        the preferred dimensions to contain all the data
        """
        v = self.getView()
        w, h = v.getPreferredSize()
        return w + self._leftToolBar.width() + 180, h + self._toolBar.height()
