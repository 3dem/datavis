#!/usr/bin/python
# -*- coding: utf-8 -*-

from PyQt5.QtCore import Qt, QObject, pyqtSlot, pyqtSignal
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QToolBar,
                             QAction, QActionGroup, QSizePolicy, QMainWindow,
                             QDockWidget, QToolButton)
import qtawesome as qta


class TriggerAction(QAction):
    """
    The TriggerAction class offers an initialization of configuration params
    not provided by Qt.
    """
    def __init__(self, parent, actionName=None, text="", faIconName=None, icon=None,
                 checkable=False, tooltip=None, slot=None, shortCut=None,
                 userData=None, **kwargs):
        """
        Creates a TriggerAction with the given name, text and icon. If slot is
        not None then the signal QAction.triggered is connected to it.
        :param actionName:   (str)The action name
        :param text:         (str)Action text
        :param faIconName:   (str)qtawesome icon name
        :param icon:         (QIcon) used if faIconName=None
        :param checkable:    (bool)if this action is checkable
        :param tooltip:      (str) The tooltip text
        :param slot:         (slot) the slot to connect QAction.triggered signal
        :param shortCut:     (QKeySequence) the short cut key
        :param userData:     User data for specific purposes
        """
        QAction.__init__(self, parent)
        if actionName:
            self.setObjectName(str(actionName))
        if faIconName:
            icon = qta.icon(faIconName)

        if icon is not None:
            self.setIcon(icon)

        self.setCheckable(checkable)
        self.setText(str(text))

        if tooltip:
            self.setToolTip(tooltip)

        if slot:
            self.triggered.connect(slot)

        if shortCut is not None:
            self.setShortcut(shortCut)

        self._userData = userData

    def getUserData(self):
        """ Getter for user data """
        return self._userData


class MultiStateAction(TriggerAction):
    """ Action handling multiple internal states.
     Each state is a tuple containing:
        (value, icon, tooltip)
    """
    # Emitted when the internal state changed
    sigStateChanged = pyqtSignal(int)

    def __init__(self, parent=None, **kwargs):
        """
        Constructor for MultiStateAction objects.
        :param parent:   (QObject) Specifies the parent object to which
                         this MultiStateAction will belong
        :param kwargs:
                states:  (list of (value, icon, tooltip)) All possible states
                         for the MultiStateAction.
               current:  (int) The initial state index in states list.
        """
        # List of internal states
        self._states = list(kwargs.pop('states') or [])
        TriggerAction.__init__(self, parent, **kwargs)
        # Current selected index
        self._current = kwargs.get('current', 0 if self._states else -1)
        self.set(self._current)
        self.triggered.connect(self.__onTriggered)

    def add(self, state, icon, tooltip=""):
        """
        Add a new state to the internal states list.
        :param state:    The state
        :param icon:     (QIcon) Icon for the specified state
        :param tooltip:  (str) The tooltip
        """
        self._states.append((state, icon, tooltip))

    def get(self):
        """ Get the currently active state. """
        return self._states[self._current][0] if self._current >= 0 else -1

    def set(self, state):
        """
        Change the current active state. Rise an Exception if the specified
        state is invalid.
        :param state: The state.
        """
        values = [s[0] for s in self._states]
        if state not in values:
            raise Exception("Invalid state %s" % state)
        self._current = values.index(state)
        _, icon, tooltip = self._states[self._current]
        self.setIcon(icon)
        self.setToolTip(tooltip)

    def __move(self, shift):
        """
        Move the current active state.
        :param shift: (int) Positions for move the current state
        """
        newIndex = (self._current + shift) % len(self._states)
        self.set(self._states[newIndex][0])

    def next(self):
        """ Move the active state to the next one. """
        self.__move(1)

    def previous(self):
        """ Move the active state to the previous one. """
        self.__move(-1)

    @pyqtSlot()
    def __onTriggered(self):
        self.next()
        self.sigStateChanged.emit(int(self.get()))


class OnOffAction(MultiStateAction):
    """ Subclass of MultiStateAction that provide just to states: on/off. """
    def __init__(self, parent=None, **kwargs):
        """
        Constructs an OnOffAction.
        :param parent: The QObject parent
        :param kwargs:
             - toolTipOn:   (str) The tooltip for On state
             - toolTipOff:  (str) The tooltip for Off state
        """
        # Set states to On/Off
        kwargs['states'] = [
            (True, qta.icon('fa.toggle-on'), kwargs.get('toolTipOn', '')),
            (False, qta.icon('fa.toggle-off'), kwargs.get('toolTipOff', ''))
        ]
        MultiStateAction.__init__(self, parent, **kwargs)


class ActionsToolBar(QWidget):
    """ Toolbar that can contain a drop-down panel with additional options """

    def __init__(self, parent, **kwargs):
        """
        Construct an ActionsToolBar to be used as part of any widget
        :param parent:
        **kwargs: Optional arguments.
             orientation:   one of Qt.Orientation values (default=Qt.Horizontal)
             panelMinWidth: (int): the minimum side panel width
             panelMaxWidth: (int): the maximum side panel width
        """
        QWidget.__init__(self, parent=parent)

        self._panelsDict = dict()
        self._panelMinWidth = kwargs.get("panelMinWidth", 160)
        self._panelMaxWidth = kwargs.get('panelMaxWidth', 300)
        self._orientation = kwargs.get("orientation", Qt.Vertical)
        self._buttonWidth = 0
        self._docks = []
        self.__setupUi()

    def __setupUi(self):
        if self._orientation == Qt.Vertical:
            layout = QHBoxLayout(self)
        else:
            layout = QVBoxLayout(self)

        self.setSizePolicy(QSizePolicy(QSizePolicy.Fixed,
                                       QSizePolicy.Fixed))
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self._toolBar = QToolBar(self)
        self._toolBar.setOrientation(self._orientation)
        layout.addWidget(self._toolBar)
        self._sidePanel = QMainWindow(None)
        layout.addWidget(self._sidePanel)
        self._actionGroup = QActionGroup(self)
        self._actionGroup.setExclusive(True)
        self._lastAction = None
        self._visibleDocks = []

        # Set default buttons style
        self.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

        self.destroyed.connect(self.__destroySidePanel)

    def __visibilityChanged(self, action, dock):
        """
        Invoked when the visibility is changed for the given dock widget
        :param action: The parent action for the dock
        :param dock:   (QDockWidget) The dock widget
        """
        action.setChecked(dock.isVisible())
        self.__dockShowHide(dock)

    def __dockShowHide(self, dock):
        """
        Show or hide the specified dock widget according to the current state
        :param dock: (QDockWidget)
        """
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
        """
        Invoked when the ActionsToolBar will be destroyed.
        We need to destroy the side panel
        """
        # FIXME[phv]: Review if self.destroyed can be connected to deleteLater
        self._sidePanel.deleteLater()

    @pyqtSlot(bool)
    def __actionTriggered(self, checked):
        """ Invoked when an action is triggered. """
        action = self.sender()
        if isinstance(action, QAction):
            dock = self._panelsDict.get(action)
            if dock is not None:
                dock.setVisible(checked)

    @pyqtSlot(bool)
    def __groupActionTriggered(self, checked):
        """ Invoked when an exclusive action is triggered """
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
        """
        Set the button style for this MultiStateAction
        :param toolButtonStyle: (Qt.ToolButtonStyle) The style for all buttons
        """
        self._toolBar.setToolButtonStyle(toolButtonStyle)

    def addAction(self, action, widget=None, index=None, exclusive=True,
                  showTitle=True, checked=False, floating=False):
        """
        Add a new action with the associated widget(side panel). This widget
        will be shown in the side panel when the action is active.
        If exclusive=True then the action will be exclusive respect to other
        actions.
        if showTitle=True then the action text will be visible as title in the
        side panel
        if checked=True then it will be activated and the corresponding  action
        will be triggered.
        if floating=True then the dock widget can be detached from the toolbar
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
            features = \
                QDockWidget.DockWidgetClosable | QDockWidget.DockWidgetMovable
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

    def setPanelMinSize(self, width):
        """ Sets the side panel minimum width """
        self._panelMinWidth = width
        for dock in self._docks:
            dock.setMinimumWidth(width)

    def getPanelMaxWidth(self):
        """ Returns the side panel maximum width """
        m = self._panelMaxWidth
        for dock in self._docks:
            m = max(m, dock.width())
        print('maximum width: ', m)
        return m

    def setPanelMaxSize(self, width):
        """ Sets the side panel maximum width """
        self._panelMaxWidth = width
        for dock in self._docks:
            dock.setMaximumWidth(width)

    def createPanel(self, name, style=None):
        """
        Create a widget with the preferred width.
        :param name:   (str) The panel name
        :param style:  (str) The panel style
        """
        widget = QWidget()
        # FIXME: If the toolbar can be either vertical or horizontal
        # then this needs to be taken into account for the geometry
        # (it should be either width or height)
        if style is None:
            style = 'QWidget#%s{border-left:1px solid lightgray;}' % name
        widget.setGeometry(0, 0, self._panelMinWidth, widget.height())
        widget.setObjectName(name)
        widget.setStyleSheet(style)
        widget.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        return widget

    def hasVisiblePanel(self):
        """
        Return True if has any panel visible
        """
        for action in self._toolBar.actions():
            if action.isCheckable():
                actWidget = self._toolBar.widgetForAction(action)
                if actWidget is not None:
                    return True
        return False

    def getIconSize(self):
        """ Return the maximum size an icon can have """
        return self._toolBar.iconSize()