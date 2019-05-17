#!/usr/bin/python
# -*- coding: utf-8 -*-

from collections import OrderedDict

from PyQt5.QtCore import Qt, QObject, pyqtSlot, pyqtSignal
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QToolBar,
                             QAction, QActionGroup, QSizePolicy, QMainWindow,
                             QDockWidget, QToolButton)


class MultiStateAction(QAction):
    """ Action handling multiple internal states.
     Each state is a tuple containing:
        (value, icon, tooltip)
    """
    # Emitted when the internal state changed
    stateChanged = pyqtSignal(int)

    def __init__(self, parent=None, **kwargs):
        QAction.__init__(self, parent)
        self._states = OrderedDict()
        for state, icon, tooltip in kwargs.get('states', []):
            self.add(state, icon, tooltip)
        self._current = kwargs.get('current', -1)
        self.triggered.connect(self.__onTriggered)

    def add(self, state, icon, tooltip=""):
        """ Add a new state. """
        self._states[state] = (icon, tooltip)

    def get(self):
        """ Get the currently active state. """
        return self._states[self._current] if self._current >= 0 else -1

    def set(self, state):
        """ Change the current active state. """
        if state not in self._states:
            raise Exception("Invalid state %s" % state)
        icon, tooltip = self._states(state)
        self.setIcon(icon)
        self.setToolTip(tooltip)

    def __move(self, shift):
        """ Move the current active state.
        """
        keys = list(self._states.keys())
        currentIndex = keys.index(self._current)
        newIndex = (currentIndex + shift) % len(keys)
        self.set(keys[newIndex])

    def next(self):
        """ Move the active state to the next one. """
        self.__move(1)

    def previous(self):
        """ Move the active state to the previous one. """
        self.__move(-1)

    @pyqtSlot
    def __onTriggered(self):
        self.next()
        self.stateChanged.emit(int(self.get()))


class ToolBar(QWidget):
    """ Toolbar tha can contain a drop-down panel with additional options """

    def __init__(self, parent, **kwargs):
        """
        Construct an Toolbar to be used as part of any widget
        **kwargs: Optional arguments.
             - orientation: one of Qt.Orientation values (default=Qt.Horizontal)
             - panel_width (int): the minimum side panel width
        """
        QWidget.__init__(self, parent=parent)

        self._panelsDict = dict()
        self._panelMinWidth = kwargs.get("panel_min_width", 160)
        self._panelMaxWidth = kwargs.get('panel_max_width', 300)
        self._buttonWidth = 0
        self._docks = []
        self.__setupUi(**kwargs)

    def __setupUi(self, **kwargs):

        orientation = kwargs.get("orientation", Qt.Horizontal)
        if orientation == Qt.Vertical:
            self._mainLayout = QHBoxLayout(self)
        else:
            self._mainLayout = QVBoxLayout(self)

        self.setSizePolicy(QSizePolicy(QSizePolicy.Fixed,
                                       QSizePolicy.Fixed))
        self._mainLayout.setSpacing(0)
        self._mainLayout.setContentsMargins(0, 0, 0, 0)
        self._toolBar = QToolBar(self)
        self._toolBar.setOrientation(orientation)
        self._mainLayout.addWidget(self._toolBar)
        self._sidePanel = QMainWindow(None)
        self._mainLayout.addWidget(self._sidePanel)
        # TODO[hv]: review the next lines
        #s = kwargs.get("show_panel", False)
        #self._sidePanel.setVisible(s)

        self._actionGroup = QActionGroup(self)
        self._actionGroup.setExclusive(True)
        self._lastAction = None
        self._visibleDocks = []

        self.destroyed.connect(self.__destroySidePanel)

    def __visibilityChanged(self, action, dock):
        action.setChecked(dock.isVisible())
        self.__dockShowHide(dock)

    def __dockShowHide(self, dock):
        if not dock.isVisible() and dock in self._visibleDocks:
            self._visibleDocks.remove(dock)
        else:
            self._visibleDocks.append(dock)
            if len(self._visibleDocks) == 1:
                self.setMaximumWidth(1000000)

        if not self._visibleDocks:
            self.setMaximumWidth(self._toolBar.width())

    @pyqtSlot(QObject)
    def __destroySidePanel(self, obj):
        self._sidePanel.deleteLater()

    @pyqtSlot(bool)
    def __actionTriggered(self, checked):
        action = self.sender()
        if isinstance(action, QAction):
            dock = self._panelsDict.get(action)
            if dock is not None:
                dock.setVisible(checked)

    @pyqtSlot(bool)
    def __groupActionTriggered(self, checked):
        action = self.sender()
        dock = self._panelsDict.get(action)
        if action.isCheckable():
            if self._lastAction:
                d = self._panelsDict.get(self._lastAction)
                if d is not None:
                    d.setVisible(False)

            if action == self._lastAction:
                action.setChecked(False)
                self._lastAction = None
            else:
                self._lastAction = action

            if dock is not None:
                dock.setVisible(checked)

    @pyqtSlot(Qt.ToolButtonStyle)
    def setToolButtonStyle(self, toolButtonStyle):
        self._toolBar.setToolButtonStyle(toolButtonStyle)

    def addAction(self, action, widget=None, index=None, exclusive=True,
                  showTitle=True, checked=False, floating=False):
        """
        Add a new action with the associated widget. This widget will be shown
        in the side panel when the action is active.
        If exclusive=True then the action will be exclusive respect to other
        actions
        if showTitle=True then the action text will be visible as title in the
        side panel
        if checked=True then it will be activated and the corresponding  action
        will be executed.
        if floating=True then the dock widget can be detached from the toolbar,
        and floated as an independent window.

        * Ownership of the widget is transferred to the toolbar.
        * Ownership of the action is transferred to the toolbar.

        Rise: Exception when action is None.
        """
        if action is None:
            raise Exception("Can't add a null action.")

        if index is not None and index >= 0:
            actions = self._toolBar.actions()
            before = actions[index] if index in range(len(actions)) else None
        else:
            before = None

        self._toolBar.insertAction(before, action)

        actWidget = self._toolBar.widgetForAction(action)
        if isinstance(actWidget, QToolButton):
            w = actWidget.width()
            if w > self._buttonWidth:
                for a in self._toolBar.actions():
                    self._toolBar.widgetForAction(a).setFixedWidth(w)
                self._buttonWidth = w
            else:
                actWidget.setFixedWidth(w)

        action.setParent(self._toolBar)

        if exclusive:
            action.triggered.connect(self.__groupActionTriggered)

        if widget is not None:
            width = widget.width()
            if width > self._panelMinWidth:
                self._panelMinWidth = width
                for d in self._docks:
                    d.setMinimumWidth(self._panelMinWidth)

            dock = QDockWidget(action.text() if showTitle else "",
                               self._sidePanel)
            dock.setFloating(floating)
            dock.setAllowedAreas(Qt.LeftDockWidgetArea)
            features = QDockWidget.DockWidgetClosable | \
                       QDockWidget.DockWidgetMovable
            if floating:
                features |= QDockWidget.DockWidgetFloatable
            dock.setFeatures(features)
            dock.setWidget(widget)
            dock.setMinimumWidth(self._panelMinWidth)
            dock.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
            dock.hide()
            dock.visibilityChanged.connect(
                lambda visible: self.__visibilityChanged(action, dock))
            self._sidePanel.addDockWidget(Qt.LeftDockWidgetArea, dock)
            if before:
                # moving the dock widgets to the correct position
                for i in range(len(actions) - 1, index - 1, -1):
                    act = actions[i]
                    dock2 = self._panelsDict.get(act)
                    if dock2:
                        self._sidePanel.splitDockWidget(
                            dock, dock2, self._toolBar.orientation())

            self._panelsDict[action] = dock
            self._docks.append(dock)
            action.setCheckable(True)
            action.triggered.connect(self.__actionTriggered)
            widget.setParent(dock)
        if checked:
            action.triggered.emit(True)

    def addSeparator(self):
        """ Adds a separator to the end of the toolbar. """
        self._toolBar.addSeparator()

    def addWidget(self, widget):
        """
        Adds the given widget to the toolbar as the toolbar's last item.
        The toolbar takes ownership of widget.
        Returns the action associated to the widget.
        Rise an exception when widget is None.
        """
        if widget is None:
            raise Exception("Can' add a null widget.")
        return self._toolBar.addWidget(widget)

    def getCurrentAction(self):
        """ Returns the current active action """
        return self._lastAction

    def hideSidePanel(self):
        """ Hide the side panel."""
        if self._lastAction is not None:
            self.__groupActionTriggered(self._lastAction)

    def setSidePanelMinimumWidth(self, width):
        """ Sets the side panel minimum width """
        self._panelMinWidth = width
        for dock in self._docks:
            dock.setMinimumWidth(width)

    def getSidePanelMinimumWidth(self):
        """ Returns the side panel minimum width """
        return self._panelMinWidth

    def setSidePanelMaximumWidth(self, width):
        """ Sets the side panel maximum width """
        self._panelMaxWidth = width
        for dock in self._docks:
            dock.setMaximumWidth(width)

    def createSidePanel(self):
        """ Create a widget with the preferred width"""
        widget = QWidget()
        widget.setGeometry(0, 0, self._panelMinWidth, widget.height())
        return widget

