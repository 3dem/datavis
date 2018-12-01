#!/usr/bin/python
# -*- coding: utf-8 -*-

from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal, QSize
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QToolBar,
                             QAction, QStackedLayout, QActionGroup, QSizePolicy)


class ToolBar(QWidget):
    """ Toolbar tha can contain a drop-down panel with additional options """

    def __init__(self, parent, **kwargs):
        """
        Construct an Toolbar to be used as part of any widget
        **kwargs: Optional arguments.
             - orientation: one of Qt.Orientation values (default=Qt.Horizontal)
        """
        QWidget.__init__(self, parent=parent)

        self._panelsDict = dict()
        self.__setupUi(**kwargs)

    def __setupUi(self, **kwargs):

        orientation = kwargs.get("orientation", Qt.Horizontal)
        if orientation == Qt.Vertical:
            self._mainLayout = QHBoxLayout(self)
        else:
            self._mainLayout = QVBoxLayout(self)

        self.setSizePolicy(QSizePolicy(QSizePolicy.Fixed,
                                       QSizePolicy.MinimumExpanding))
        self._mainLayout.setSpacing(0)
        self._mainLayout.setContentsMargins(0, 0, 0, 0)
        self._toolBar = QToolBar(self)
        self._toolBar.setOrientation(orientation)
        self._mainLayout.addWidget(self._toolBar)
        self._sidePanel = QWidget(self)
        self._stackedLayoud = QStackedLayout(self._sidePanel)
        self._stackedLayoud.setSpacing(0)
        self._emptyWidget = QWidget(self._sidePanel)
        self._stackedLayoud.addWidget(self._emptyWidget)

        self._mainLayout.addWidget(self._sidePanel)

        s = kwargs.get("show_panel", False)
        self._sidePanel.setVisible(s)

        self._actionGroup = QActionGroup(self)
        self._actionGroup.setExclusive(True)
        self._actionGroup.triggered.connect(self.__actionTriggered)
        self._lastAction = None

    @pyqtSlot(QAction)
    def __actionTriggered(self, action):
        widget = self._panelsDict.get(action)

        if action.isCheckable():
            if action == self._lastAction:
                action.setChecked(False)
                self._lastAction = None
            else:
                self._lastAction = action

            if widget is not None:
                current = self._stackedLayoud.currentWidget()
                v = not widget == current
                self._sidePanel.setVisible(v)
                if v:
                    self._stackedLayoud.setCurrentWidget(widget)
                else:
                    self._stackedLayoud.setCurrentWidget(self._emptyWidget)
            elif self._sidePanel.isVisible():
                self._sidePanel.setVisible(False)
                self._stackedLayoud.setCurrentWidget(self._emptyWidget)

    @pyqtSlot(Qt.ToolButtonStyle)
    def setToolButtonStyle(self, toolButtonStyle):
        self._toolBar.setToolButtonStyle(toolButtonStyle)

    def addAction(self, action, widget=None, exclusive=False):
        """
        Add a new action with the associated widget. This widget will be shown
        in the side panel when the action is active.
        If widget!=None then the action will be forced to be checkable.
        If exclusive==True then the action will be exclusive respect to other
        actions with associated widgets.

        * Ownership of the widget is transferred to the toolbar.
        * Ownership of the action is transferred to the toolbar.

        Rise: Exception when action is None.
        """
        if action is None:
            raise Exception("Can't add a null action.")

        self._toolBar.addAction(action)
        action.setParent(self._toolBar)

        if widget is not None:
            self._stackedLayoud.addWidget(widget)
            self._panelsDict[action] = widget
            action.setCheckable(True)
            action.setActionGroup(self._actionGroup)
            widget.setParent(self._sidePanel)
        elif exclusive:
            action.setActionGroup(self._actionGroup)

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
            self.__actionTriggered(self._lastAction)


class MultiAction(QAction):
    """ Action for multiple states """

    def __init__(self, parent=None):
        QAction.__init__(self, parent)
        self._stateIndex = -1
        self._icons = dict()
        self._states = list()

    def addState(self, state, icon):
        self._states.append(state)
        self._icons[state] = icon, len(self._states) - 1

    def getCurrentState(self):
        return self._states[self._stateIndex] if self._stateIndex >= 0 else -1

    def setState(self, state):
        s = self._icons.get(state)

        if s is not None:
            self._stateIndex = s[1]
            self.setIcon(self._icons[self._states[self._stateIndex]][0])

    def changeToNextState(self):
        if self._stateIndex >= 0:
            self._stateIndex = (self._stateIndex + 1) % len(self._states)
            self.setIcon(self._icons[self._states[self._stateIndex]][0])

    def changeToPreviousState(self):
        if self._states:
            n = len(self._states)
            self._stateIndex = (n - self._stateIndex - 1) % n
            self.setIcon(self._icons[self._states[self._stateIndex]][0])

