#!/usr/bin/python
# -*- coding: utf-8 -*-

import os

from PyQt5.QtCore import (Qt, pyqtSlot, pyqtSignal)
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QToolBar, QSpinBox,
                             QLabel, QStatusBar, QComboBox, QStackedLayout,
                             QLineEdit, QActionGroup, QMessageBox, QSplitter,
                             QSizePolicy, QPushButton, QMenu, QTableWidget,
                             QTableWidgetItem)
from PyQt5.QtGui import (QIcon, QStandardItemModel, QKeySequence)
import qtawesome as qta


from emviz.models import (RENDERABLE, RENDERABLE_RO, VISIBLE, VISIBLE_RO)
from emviz.widgets import (ActionsToolBar,  PlotConfigWidget, TriggerAction)

from ._delegates import ColumnPropertyItemDelegate
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

    def __init__(self, parent=None, **kwargs):
        """
        Constructs a DataView.
        :param parent:       (QWidget) Parent widget
        :param kwargs:
             model:          (TableModel) The data model
             selectionMode:  (int) SINGLE_SELECTION(default),EXTENDED_SELECTION,
                             MULTI_SELECTION or NO_SELECTION
             views:          (list) Specify the views that will be available.
                             Default value: [COLUMNS, GALLERY, ITEMS]
             view:           (int) The default view to be set
             size:           (int) The row height for ColumnsView and icon size
                             for GalleryView. Default value: 25
             maxCellSize:    (int) The maximum value for row height in
                             ColumnsView and icon size in GalleryView. Default
                             value: 300
             minCellSize:    (int) The minimum value for row height in
                             ColumnsView and icon size in GalleryView. Default
                             value: 20
        """
        QWidget.__init__(self, parent=parent)
        #  The following is a dict with useful information for all view type
        # TODO[phv] Register view types in a new method: registerView(**kwargs)
        self._viewData = {
            COLUMNS: {NAME: 'Columns',  # view name
                      CLASS: ColumnsView,  # view class
                      ICON: 'fa.table',  # view icon
                      ACTION: None,  # view action
                      VIEW: None,  # view widget
                      # tool tips for columns properties in display config
                      TOOLTIP: {VISIBLE_CHECKED: 'Hide this column',
                                VISIBLE_UNCHECKED: 'Show this column',
                                RENDER_CHECKED: 'Do not render this column',
                                RENDER_UNCHECKED: 'Render this column'
                                }
                      },
            GALLERY: {NAME: 'Gallery',
                      CLASS: GalleryView,
                      ICON: 'fa.th',
                      ACTION: None,
                      VIEW: None,
                      TOOLTIP: {VISIBLE_CHECKED: 'Hide this label',
                                VISIBLE_UNCHECKED: 'Show this label',
                                RENDER_CHECKED: '',
                                RENDER_UNCHECKED: 'Show this column'
                                }
                      },
            ITEMS: {NAME: 'Items',
                    CLASS: ItemsView,
                    ICON: 'fa.columns',
                    ACTION: None,
                    VIEW: None,
                    TOOLTIP: {VISIBLE_CHECKED: 'Hide this label',
                              VISIBLE_UNCHECKED: 'Show this label',
                              RENDER_CHECKED: '',
                              RENDER_UNCHECKED: 'Show this column'
                              }
                    }
        }

        self._views = kwargs.get('views', [COLUMNS, GALLERY, ITEMS])
        self._view = None
        self._model = None
        self._displayConfig = None
        self._currentRow = 0  # selected table row
        self._selection = set()
        self._selectionMode = PagingView.NO_SELECTION
        self._tablePref = dict()
        self.__initProperties(**kwargs)
        self.__setupGUI(**kwargs)
        self.__setupCurrentViewMode()
        self.__setupActions()
        self.setSelectionMode(self._selectionMode)
        self.setModel(kwargs['model'])

    def __setupGUI(self, **kwargs):
        """ This is the standard method for the GUI creation """
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
        self._selectionPanel = self._toolBarLeft.createPanel('selectionPanel')
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
        self._toolBarLeft.addAction(self._actSelections, self._selectionPanel,
                                    exclusive=False)

        self._columnsPanel = self._toolBarLeft.createPanel('columnsPanel')
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
            self.__onItemChanged)
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
        self._actColumns = TriggerAction(parent=None, actionName='AColumns',
                                         text='Columns', faIconName='fa5s.th')
        self._toolBarLeft.addAction(self._actColumns, self._columnsPanel,
                                    exclusive=False)
        # Plot panel
        self._plotPanel = self._toolBarLeft.createPanel('plotPanel')
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
        self._actPlot = TriggerAction(parent=None, actionName='APlot',
                                      text='Plot',
                                      faIconName='fa5s.file-signature')
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
        for view in self._views:
            #  create action with the view name
            v = self._viewData[view]
            a = TriggerAction(parent=self._toolBar, actionName=v[NAME],
                              text=v[NAME], faIconName=v[ICON],
                              checkable=True, slot=self._onChangeViewTriggered,
                              userData=view)
            v[ACTION] = a
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
        self.__actShowHideToolBar = TriggerAction(self, 'SHToolBar',
                                                  slot=self.__onShowHideToolBar,
                                                  shortCut=QKeySequence(
                                                      Qt.Key_T))
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

        if self._comboBoxCurrentTable.currentIndex() == -1:
            pref[VIEW] = self._view  # Preferred view
        elif self._model is not None and self._model.getRowsCount() == 1 \
                and ITEMS in self._views:
            pref[VIEW] = ITEMS
        elif COLUMNS in self._views:
            pref[VIEW] = COLUMNS
        else:
            pref[VIEW] = self._views[0] if self._views else None

        d = dict()
        for v in self._views:
            d[v] = self.getViewWidget(v).getDisplayConfig()
        pref['colConfig'] = d
        return pref

    def __savePreferencesForCurrentTable(self):
        """ Save preferences for the current table """
        tName = self._comboBoxCurrentTable.currentText()
        pref = self._tablePref.get(tName)

        if pref is None:
            pref = self.__createPreferencesForCurrentTable()
            self._tablePref[tName] = pref
        else:
            pref[VIEW] = self._view

        d = dict()
        for v in self._views:
            d[v] = self.getViewWidget(v).getDisplayConfig()
        pref['colConfig'] = d

    def __loadPreferencesForCurrentTable(self):
        """ Load preferences for the current table """
        tName = self._comboBoxCurrentTable.currentText()
        pref = self._tablePref.get(tName)

        if pref is None:
            pref = self.__createPreferencesForCurrentTable()
            self._tablePref[tName] = pref

        self._view = pref[VIEW]

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
        viewClass = self._viewData[viewType][CLASS]
        if viewClass is None:
            raise Exception('Unregistered class for view type=%d' % viewType)

        return viewClass(self, **kwargs)

    def __createViews(self, **kwargs):
        """ Create the views if necessary. Inserts the views in the GUI. """
        for v in self._viewData.keys():
            if v not in self._views:
                self.__removeView(v)
            else:
                d = self._viewData[v]
                if d.get(VIEW) is None:
                    viewWidget = self.__createView(v, **kwargs)
                    d[VIEW] = viewWidget
                    if viewWidget is not None:
                        viewWidget.setContextMenuPolicy(Qt.ActionsContextMenu)
                        viewWidget.addAction(self._actSelectAll)
                        viewWidget.addAction(self._actSelectFromHere)
                        viewWidget.addAction(self._actSelectToHere)

                        self._stackedLayoud.addWidget(viewWidget)
                        self.__connectViewSignals(viewWidget)

    def __removeView(self, view):
        """ If the given view exist in the GUI the will be removed. """
        d = self._viewData[view]
        viewWidget = d.get(VIEW)
        if viewWidget is not None:
            self._stackedLayoud.removeWidget(viewWidget)
            d[VIEW] = None
            viewWidget.setParent(None)
            self.__disconnectViewSignals(viewWidget)
            del viewWidget

    def __setupAllWidgets(self):
        """
        Configure all widgets:
           * configure the value range for all spinboxs
           * show table dims

        Invoke this function when you needs to initialize all widgets.
        Example: when setting new model in the table view
        """
        self._showViewDims()
        self.__showSelectionInfo()
        self.__setupSpinBoxRowHeigth()
        self._onChangeCellSize()
        self.__setupSpinBoxCurrentRow()
        self._spinBoxCurrentRow.setValue(1)
        self.__setupActions()

        viewWidget = self.getViewWidget(self._view)
        for viewType in self._views:
            if self._model is not None:
                tName = self._comboBoxCurrentTable.currentText()
                pref = self._tablePref.get(tName)
                w = self.getViewWidget(viewType)
                if pref is not None:
                    c = pref['colConfig'].get(viewType, None)
                    if c:
                        pass  # m.setColumnConfig(c)
                        #FIXME[phv] Restore display config
                else:
                    if not viewWidget == w and viewType == GALLERY:
                        # FIXME[phv] configure display config for GalleryView
                        #c = m.getColumnConfig()
                        #if c is not None:
                        #    for colConf in c:
                        #        colConf['visible'] = False
                        pass
            w.setModel(self._model)

        self.__loadPreferencesForCurrentTable()
        self.__setupCurrentViewMode()
        if self._model is not None and \
                self._selectionMode == PagingView.SINGLE_SELECTION:
            self._selection.add(0)
            self.__makeSelectionInView(self._view)

    def __showSelectionInfo(self):
        """ Show the selection info in the selection panel """
        if self._model is not None:
            size = self.__getSelectionSize()
            if size:
                textTuple = ("Selected items: ",
                             "%s/%s" % (size, self._model.getColumnsCount()))
            else:
                textTuple = ("No selection", "")
            text = "<br><p><strong>%s</strong></p><p>%s</p>" % textTuple
            self._labelSelectionInfo.setText(text.ljust(20))
            self._labelElements.setText(" Elements: %d " %
                                        self._model.getRowsCount())
        else:
            self._labelSelectionInfo.setText(
                "<p><strong>Selection</strong></p>")
            self._labelElements.setText("")

    def __hasRenderableColumn(self, viewType=None):
        """ Returns True if the widget for the given type has renderable columns
        """
        if viewType is None:
            viewType = self._view
        viewWidget = self._viewData[viewType][VIEW]
        config = None if viewWidget is None else viewWidget.getDisplayConfig()
        return config is not None and config.hasColumnConfig(renderable=True)

    def __setupSpinBoxRowHeigth(self):
        """ Configure the row height spinbox """
        self._spinBoxRowHeight.setRange(self._minRowHeight, self._maxRowHeight)

        if not self.__hasRenderableColumn():
            self._spinBoxRowHeight.setValue(25)
        else:
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
        # FIXME[phv] Review the table names
        #if self._model:
        #    for t in self._model.getTitles():
        #        item = QStandardItem(t)
        #        item.setData(0, Qt.UserRole)  # use UserRole for store
        #        model.appendRow([item])

        self._comboBoxCurrentTable.blockSignals(False)

    def __setupToolBarForView(self, view):
        """ Show/Hide relevant info/actions for the given view """
        # row height
        rColumn = self.__hasRenderableColumn()

        self._actLabelLupe.setVisible((view == GALLERY or
                                      view == COLUMNS) and
                                      rColumn)
        self._actSpinBoxHeight.setVisible(self._actLabelLupe.isVisible())
        # dims
        self._actLabelCols.setVisible(not view == ITEMS)
        self._actLineEditCols.setVisible(self._actLabelCols.isVisible())
        self._lineEditCols.setEnabled(False)

    def __setupCurrentViewMode(self):
        """
        Configure current view mode: COLUMNS or GALLERY or ITEMS
        """
        viewWidget = self._viewData[self._view][VIEW]

        if viewWidget is not None:
            row = self._currentRow
            self._stackedLayoud.setCurrentWidget(viewWidget)
            self.__makeSelectionInView(self._view)
            viewWidget.selectRow(row)

        a = self._viewData[self._view][ACTION]
        if a:
            a.setChecked(True)

        self._showViewDims()
        self.__setupToolBarForView(self._view)
        self.__savePreferencesForCurrentTable()
        self.__initTableColumnProp()

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
            self._spinBoxCurrentRow.setRange(1, self._model.getRowsCount())

    def __clearViews(self):
        """ Clear all views """
        for viewWidget in self.getViewWidgets():
            viewWidget.clear()

    def __initProperties(self, **kwargs):
        """ Configure all properties  """
        self._defaultRowHeight = kwargs.get('size', 150)
        self._maxRowHeight = kwargs.get('maxCellSize', 300)
        self._minRowHeight = kwargs.get('minCellSize', 20)
        self._zoomUnits = kwargs.get('zoomUnits', PIXEL_UNITS)
        self._view = kwargs.get('view', COLUMNS)
        if self._view not in self._views:
            d = self._viewData.get(self._view)
            s = d[NAME] if d else str(self._view)
            raise Exception('The default view:%s is not in supported views' % s)
        self._selectionMode = kwargs.get('selectionMode',
                                         PagingView.MULTI_SELECTION)

    def __setupActions(self):
        for v in self._actionGroupViews.actions():
            v.setVisible(v.getUserData() in self._views)
            # FIXME[phv] Hide GalleryView if there are no renderable columns
            #if self._model and view == GALLERY:
            #    v.setVisible(self.__hasRenderableColumn())

    def __makeSelectionInView(self, view):
        """ Makes the current selection in the given view """
        view = self.getViewWidget(view)

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
        self._toolBarLeft.setPanelMinSize(
            self._plotConfigWidget.sizeHint().width())

    def __initTableColumnProp(self):
        """ Initialize the columns properties widget """
        self._tableColumnProp.blockSignals(True)
        self._tableColumnProp.clear()
        self._tableColumnProp.setHorizontalHeaderLabels(["", "", 'Name'])
        viewWidget = self.getViewWidget()
        dConfig = viewWidget.getDisplayConfig()

        if dConfig is not None:
            row = 0
            self._tableColumnProp.setRowCount(dConfig.getColumnsCount())
            viewWidget = self.getViewWidget()
            for i, colConfig in dConfig.iterColumns():
                item = QTableWidgetItem(colConfig.getName())
                itemV = QTableWidgetItem("")  # for 'visible' property
                itemR = QTableWidgetItem("")  # for 'renderable' property
                self._tableColumnProp.setItem(row, 0, itemV)
                self._tableColumnProp.setItem(row, 1, itemR)
                self._tableColumnProp.setItem(row, 2, item)
                t = self._viewData[self._view][TOOLTIP]
                flags = Qt.ItemIsUserCheckable | Qt.ItemIsEnabled
                render = colConfig[RENDERABLE]
                itemR.setCheckState(Qt.Checked if render else Qt.Unchecked)
                itemR.setData(
                    Qt.ToolTipRole,
                    t.get(RENDER_CHECKED if render else RENDER_UNCHECKED, ''))
                itemR.setFlags(flags)
                g = self._view == GALLERY
                v = i in colConfig.getLabels() if g else colConfig[VISIBLE]
                itemV.setFlags(flags)
                itemV.setCheckState(Qt.Checked if v else Qt.Unchecked)
                itemV.setData(
                    Qt.ToolTipRole,
                    t.get(VISIBLE_CHECKED if v else VISIBLE_UNCHECKED, ''))
                row += 1
            self._tableColumnProp.resizeColumnsToContents()
        self._tableColumnProp.resizeColumnsToContents()
        self._tableColumnProp.horizontalHeader().setStretchLastSection(True)
        self._tableColumnProp.blockSignals(False)

    def __reverseCheckState(self, item):
        """ Reverse the check state for the given QTableWidgetItem """
        st = Qt.Checked if item.checkState() == Qt.Unchecked else Qt.Unchecked
        item.setCheckState(st)

    @pyqtSlot(QTableWidgetItem)
    def __onItemChanged(self, item):
        """ Invoked whenever the data of item has changed. """
        self._tableColumnProp.blockSignals(True)
        viewWidget = self.getViewWidget()
        dispConf = viewWidget.getDisplayConfig()
        if dispConf is not None:
            row, col = item.row(), item.column()
            colConfig = dispConf.getColumnConfig(row)
            t = self._viewData[self._view][TOOLTIP]
            if col == 0:  # visible
                d = item.checkState() == Qt.Checked
                if self._view == GALLERY:
                    method = list.append if d else list.remove
                    labels = colConfig.getLabels()
                    method(labels, row)
                    size = self._spinBoxRowHeight.value()
                    viewWidget.setIconSize((size, size))
                elif not colConfig[VISIBLE_RO]:
                    if dispConf.getColumnsCount(visible=True) == 1 and not d:
                        self.__reverseCheckState(item)
                    else:
                        colConfig[VISIBLE] = d
                else:
                    self.__reverseCheckState(item)

                d = item.checkState() == Qt.Checked
                v = VISIBLE_CHECKED if d else VISIBLE_UNCHECKED
                item.setToolTip(t.get(v, ''))
            else:  # renderable
                r = item.checkState() == Qt.Checked
                gi = self._view == GALLERY or self._view == ITEMS

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
                                    it.setToolTip(t.get(RENDER_UNCHECKED, ''))
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
                                    it.setToolTip(t.get(RENDER_UNCHECKED, ''))
                        viewWidget.setModelColumn(row)

                r = item.checkState() == Qt.Checked
                if r and not self._view == ITEMS:
                    size = self._spinBoxRowHeight.value()
                    viewWidget.setIconSize((size, size))

                ren = RENDER_CHECKED if r else RENDER_UNCHECKED
                item.setToolTip(t.get(ren, ''))

            viewWidget.updateViewConfiguration()
            self.__setupToolBarForView(self._view)
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
            columnsWidget = self.getViewWidget(COLUMNS)
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

    @pyqtSlot()
    def __onPageConfigChanged(self):
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
            self._spinBoxCurrentRow.blockSignals(True)
            self._spinBoxCurrentRow.setValue(row + 1)
            self._spinBoxCurrentRow.blockSignals(False)
            if self._selectionMode == PagingView.SINGLE_SELECTION:
                self._selection.clear()
                self._selection.add(self._currentRow)
                self.__makeSelectionInView(self._view)

            self.sigCurrentRowChanged.emit(self._currentRow)

    @pyqtSlot(int)
    def _onCurrentTableChanged(self, index):
        """ Invoked when user change the current table """
        # FIXME[phv] Review what to do when user change the current table
        pass

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
        TODO: Review implementation. Change row height for the moment
        """
        size = self._spinBoxRowHeight.value()

        row = self._currentRow
        for viewWidget in self.getViewWidgets():
            if viewWidget.getViewType() in [COLUMNS, GALLERY]:
                viewWidget.setIconSize((size, size))

        viewWidget = self.getViewWidget()
        if viewWidget is not None:
            viewWidget.selectRow(row)
        self.__makeSelectionInView(self._view)

    @pyqtSlot()
    def _showViewDims(self):
        """
        Show column and row count in the QLineEdits
        """
        viewWidget = self._viewData[self._view][VIEW]
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

            viewWidget = self._viewData[self._view][VIEW]

            if viewWidget is not None:
                self.__makeSelectionInView(self._view)
                viewWidget.selectRow(self._currentRow)

            if not row == self._spinBoxCurrentRow.value():
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
            self._view = a.getUserData()
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
        self._selection.clear()
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

    def showToolBar(self, visible):
        """ Show or hide the toolbar """
        self._toolBar.setVisible(visible)

    def showPageBar(self, visible):
        """ Show or hide the page bar """
        for widget in self.getViewWidgets():
            widget.showPageBar(visible)

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
        viewType that can be used: COLUMNS, GALLERY, ITEMS, SLICES
        """
        if viewType is None:
            viewType = self._view

        return self._viewData[viewType][VIEW]

    def getViewWidgets(self):
        """ Returns a list with the current view widgets """
        return [v[VIEW] for v in self._viewData.values() if v[VIEW] is not None]

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

        for viewWidget in self.getViewWidgets():
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
        for viewWidget in self.getViewWidgets():
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
        if self._model is None:
            return -1
        return self.getViewWidget().getPageBar().getCurrentPage()

    def setPage(self, page):
        """ Change to page for the current view """
        if self._model is not None:
            self.getViewWidget().getPageBar().setCurrentPage(page)

    def getPageCount(self):
        """ Return the page count for the current view or -1 if current model
        is None """
        if self._model is None:
            return -1
        return self.getViewWidget().getPageBar().getPageCount()

    def getPreferredSize(self):
        """
        Returns a tuple (width, height), which represents
        the preferred dimensions to contain all the data
        """
        v = self.getViewWidget()
        w, h = v.getPreferredSize()
        return w + self._toolBarLeft.width() + 180, h + self._toolBar.height()

    def setLabelIndexes(self, labels):
        """
        Initialize the indexes of the columns that will be displayed as text
        below the images
        labels (list)
        """
        # FIXME[phv] Review the label indexes
        #widget = self.getViewWidget(GALLERY)
        #if widget is not None:
        #    widget.setLabelIndexes(labels)

        #widget = self.getViewWidget(COLUMNS)
        #if widget is not None:
        #    widget.setLabelIndexes(labels)
        pass


