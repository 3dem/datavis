
import PyQt5.QtCore as qtc
import PyQt5.QtWidgets as qtw

from datavis.utils import getExt

from ._toolbar import TriggerAction


class TreeModelView(qtw.QTreeView):
    """ The TreeModelView class is an extension of the QTreeView class, allowing
        different navigation modes.
        It can be initialized by one of the following modes:

        * TREE_MODE: All files on the initial QFileSystemModel are shown
        * DIR_MODE: Only the files on the current folder are shown
        """
    TREE_MODE = 0
    DIR_MODE = 1

    # signal emitted when the view has been resized
    sigSizeChanged = qtc.pyqtSignal()

    def __init__(self, parent=None, **kwargs):
        """ Constructs a TreeModelView object.

        Args:
            parent:  The parent widget

        Keyword Args:
            model   The tree model for the view to present.
            mode:   The TreeView mode. Possible values:
                    TREE_MODE, DIR_MODE
            navigate: (bool) If True, the user can navigate through
                    the directories
        """
        qtw.QTreeView.__init__(self, parent)

        self._mode = kwargs.get('mode', TreeModelView.TREE_MODE)
        self._navigate = kwargs.get('navigate', True)
        self._model = None

        self.setModel(kwargs.get('model'))
        self.header().setSectionResizeMode(0, qtw.QHeaderView.ResizeToContents)

        isTreeMode = self._mode == TreeModelView.TREE_MODE
        self.setItemsExpandable(isTreeMode)
        self.setRootIsDecorated(isTreeMode)
        self.sigSizeChanged.connect(self.__treeViewSizeChanged)
        self.doubleClicked.connect(self.__onPathDoubleClick)

    def __onPathDoubleClick(self, index):
        """
        Slot invoked when the mouse is double-clicked on the specified index
        """
        if (self._navigate and self._mode == TreeModelView.DIR_MODE
                and self._model.hasChildren(index)):
            self.setRootIndex(index)

    def __treeViewSizeChanged(self):
        if self._mode == TreeModelView.TREE_MODE:
            indexes = self.selectionModel().selectedIndexes()
            if indexes:
                index = indexes[0]
                self.expand(index)
                self.scrollTo(index)

    def _expandIndex(self, index):
        if index.isValid():
            self.expand(index)
            self.scrollTo(index)

    def setModel(self, model):
        if not model == self._model:
            self._model = model
            qtw.QTreeView.setModel(self, model)

    def resizeEvent(self, evt):
        qtw.QTreeView.resizeEvent(self, evt)
        self.sigSizeChanged.emit()

    def getMode(self):
        """ Return the current mode """
        return self._mode

    def expand(self, index):
        if self._mode == TreeModelView.TREE_MODE:
            qtw.QTreeView.expand(self, index)

    def scrollTo(self, index, hint=qtw.QAbstractItemView.EnsureVisible):
        if self._navigate:
            qtw.QTreeView.scrollTo(self, index, hint)

    def setRootIndex(self, index):
        if self._navigate and index.isValid():
            qtw.QTreeView.setRootIndex(self, index)

    def goHome(self):
        """ Changes current index by moving to the root model index """
        if self._navigate:
            root = self.model().index(0, 0)
            self.setRootIndex(root)
            self.setCurrentIndex(root)

    def goUp(self):
        """ Changes directory by moving one directory up from the current
        directory."""
        if self._navigate:
            parent = self.currentIndex().parent()
            rootIndex = self.rootIndex()
            index = self.currentIndex()
            isDirMode = self._mode == TreeModelView.DIR_MODE
            if index == rootIndex or parent == rootIndex or isDirMode:
                self.selectIndex(parent)
            else:
                self._expandIndex(parent)

    def selectIndex(self, index):
        """ Set the given index as selected. If mode is DIR_MODE then the root
        path will be the root of the given index."""
        if index.isValid():
            self.setRootIndex(index.parent())
            if self._mode == TreeModelView.TREE_MODE:
                self._expandIndex(index)

            self.setCurrentIndex(index)

    def canNavigate(self):
        """ Return True if navigation is available """
        return self._navigate


class Browser(qtw.QWidget):
    """ Browser is the base class for browsers that allow users to select paths
    from a TreeModelView. It will contain a left panel with the TreeModelView,
    navigation buttons and a completer to facilitate the search. A  right panel
    with ViewPanel (top) and InfoPanel (bottom).
    """

    # signal emitted when the current index is changed
    sigIndexChanged = qtc.pyqtSignal(qtc.QModelIndex)

    def __init__(self, **kwargs):
        """
        Constructs a new Browser object

        Keyword Args:
            parent:      The parent widget
            model        The tree model for the view to present.
            mode:        (int) The TreeView mode. Possible values:
                         TREE_MODE, DIR_MODE
            navigate:    (Boolean) If True, the user can navigate through
                         the directories
            readOnly     (Boolean) If True, all navigation buttons and completer
                         will be disabled
        """
        qtw.QWidget.__init__(self, kwargs.get('parent'))
        self.__setupUi(kwargs)
        self.sigIndexChanged.connect(self.__onCurrentIndexChanged)

    def __setupUi(self, kwargs):
        """ Create the main GUI of the Browser. """
        mainLayout = qtw.QHBoxLayout(self)
        mainLayout.setSpacing(0)
        mainLayout.setContentsMargins(1, 1, 1, 1)
        self._splitter = qtw.QSplitter(orientation=qtc.Qt.Horizontal,
                                       parent=self)
        leftWidget = qtw.QWidget(self)
        layout = qtw.QVBoxLayout(leftWidget)
        self._toolBar = self.__createToolBar()
        layout.addWidget(self._toolBar)
        self._completer = qtw.QCompleter(parent=self)
        self._lineCompleter = qtw.QLineEdit(self)
        boxLayout = qtw.QBoxLayout(qtw.QBoxLayout.LeftToRight)
        boxLayout.addWidget(qtw.QLabel(text='Path', parent=self))
        self._lineCompleter.setCompleter(self._completer)
        boxLayout.addWidget(self._lineCompleter)
        layout.addLayout(boxLayout)

        readOnly = kwargs.get('readOnly', False)
        if readOnly:
            kwargs['navigate'] = False

        self._treeModelView = self._createTreeModelView(**kwargs)
        self.__enableActions(not readOnly)
        self._lineCompleter.setReadOnly(readOnly)
        self._lineCompleter.returnPressed.connect(self._onReturnPressed)
        self._lineCompleter.textChanged.connect(self._onTextChanged)
        layout.addWidget(self._treeModelView)
        self._completer.setModel(self._treeModelView.model())
        self._treeModelView.selectionModel().selectionChanged.connect(
            self._onSelectionChanged)

        self._splitter.addWidget(leftWidget)
        rightPanel = self._createRightPanel(**kwargs)
        if rightPanel is not None:
            self._splitter.addWidget(rightPanel)
            self._splitter.setStretchFactor(0, 5)
            self._splitter.setStretchFactor(1, 3)

        mainLayout.addWidget(self._splitter)

    def __createToolBar(self):
        """ Create the tool bar and the navigation actions """
        toolBar = qtw.QToolBar(self)
        toolBar.setToolButtonStyle(qtc.Qt.ToolButtonIconOnly)
        self._homeAct = TriggerAction(parent=toolBar, actionName='home',
                                      text='Home', faIconName='fa.home',
                                      checkable=False, slot=self._onHomeAction)
        toolBar.addAction(self._homeAct)
        self._upAct = TriggerAction(parent=toolBar, actionName='up',
                                    text='Up', faIconName='fa.arrow-up',
                                    checkable=False, slot=self._onUpAction)
        toolBar.addAction(self._upAct)
        self._refreshAct = TriggerAction(parent=toolBar, actionName='refresh',
                                         text='Refresh',
                                         faIconName='fa.refresh',
                                         checkable=False,
                                         slot=self._onRefreshAction)
        toolBar.addAction(self._refreshAct)
        return toolBar

    def __enableActions(self, v):
        """ Enable/Disable actions"""
        self._homeAct.setEnabled(v)
        self._upAct.setEnabled(v)
        self._refreshAct.setEnabled(v)

    def __onCurrentIndexChanged(self, index):
        """ Invoked when the current index has been changed.
        Updates the ViewPanel """
        self.updateViewPanel()

    def _onSelectionChanged(self, selected, deselected):
        """ Invoked when the selection change in the tree view """
        if not selected.isEmpty():
            index = selected.indexes()[0]
            if not self._lineCompleter.hasFocus():
                self.sigIndexChanged.emit(index)

    def _createTreeModelView(self, **kwargs):
        """
        Create the TreeModelView. Subclasses must implement this method for the
        tree model view creation
        """
        raise Exception('Not implemented yet. ')

    def _createRightPanel(self, **kwargs):
        """
        Build the right panel: (Top) ViewPanel, (Bottom) InfoPanel. Subclasses
        might create different widgets.
        """
        viewPanel = self._createViewPanel(**kwargs)
        infoPanel = self._createInfoPanel(**kwargs)
        if viewPanel is None:
            return infoPanel
        if infoPanel is None:
            return viewPanel

        splitter = qtw.QSplitter()
        splitter.setOrientation(qtc.Qt.Vertical)
        splitter.addWidget(viewPanel)
        splitter.addWidget(infoPanel)

        return splitter

    def _createViewPanel(self, **kwargs):
        """ Build the top right panel. Subclasses must implement this method for
        the ViewPanel creation """
        raise Exception('Not implemented yet. ')

    def _createInfoPanel(self, **kwargs):
        """ Build the bottom right panel for additional information.  Subclasses
        must implement this method for the InfoPanel creation, usually doing
        nothing """
        raise Exception('Not implemented yet. ')

    def _onHomeAction(self):
        """ This slot leads the TreeModelView to the root model index """
        self._treeModelView.goHome()
        self.sigIndexChanged.emit(self._treeModelView.currentIndex())

    def _onUpAction(self):
        """ Changes the current index by moving one index up from the current
        index. """
        self._treeModelView.goUp()
        self.sigIndexChanged.emit(self._treeModelView.currentIndex())

    def _onRefreshAction(self):
        """ Refreshes the TreeModelView information. Subclasses can
        implement this method for custom tasks """
        pass

    def _onReturnPressed(self):
        """ Invoked when the user press Enter on line completer. Subclasses can
        implement this method for custom tasks """
        pass

    def _onTextChanged(self, text):
        """ Invoked when the text change on line completer. Subclasses can
        implement this method for custom tasks """
        pass

    def getModel(self):
        """ Return the current model """
        return self._treeModelView.model()

    def getCurrentIndex(self):
        """ Return the current index """
        return self._treeModelView.currentIndex()

    def updateViewPanel(self):
        """
        Update the information of the view panel. Implement this method in
        subclasses for file data visualization
        """
        pass


class FileModelView(TreeModelView):
    """ The FileModelView class is an extension of the TreeModelView class,
    allowing the file system navigation. FileBrowser is initialized with
    a QFileSystemModel, having the 'rootPath' param as the root path of
    the model and the 'selectedPath' as the current selected path.
    """

    def __init__(self, **kwargs):
        """
        Constructs an FileBrowser instance

        Keyword Args:
            parent:       The parent widget
            mode:         (int) The TreeView mode. Possible values:
                          TREE_MODE, DIR_MODE
            navigate:     (Boolean) If True, the user can navigate through
                          the directories
            rootPath:     (str) Initial root path
            selectedPath: (str) The selected path
        """

        TreeModelView.__init__(self, **kwargs)
        self._mode = kwargs.get('mode', TreeModelView.TREE_MODE)
        self._navigate = True

        self._model = None
        self.setModel(kwargs.get('model', qtw.QFileSystemModel(self)))
        self.header().setSectionResizeMode(0, qtw.QHeaderView.ResizeToContents)
        rootPath = kwargs.get('rootPath', qtc.QDir.rootPath())
        self._model.setRootPath(qtc.QDir.rootPath())
        rootIndex = self._model.index(rootPath)

        self.setRootIndex(rootIndex)
        self.setCurrentIndex(rootIndex)
        self.selectPath(kwargs.get('selectedPath'))
        self._navigate = kwargs.get('navigate', True)

    def _createViewPanel(self, **kwargs):
        return None

    def _createInfoPanel(self, **kwargs):
        """ Build the bottom right panel for additional information """
        return None

    def expandTree(self, path):
        """
        Expand the Tree View to the given path
        """
        index = self._model.index(path)
        self._expandIndex(index)

    def setRootIndex(self, index):
        """ Reimplemented from QTreeView """
        if self._navigate and index.isValid():
            qtw.QTreeView.setRootIndex(self, index)

    def goHome(self):
        """ Changes current directory by moving to the home directory. """
        if self._navigate:
            self.setRootPath(qtc.QDir.homePath())
            self.setCurrentIndex(self.rootIndex())

    def goUp(self):
        """ Changes directory by moving one directory up from the current
        directory."""
        if self._navigate:
            parent = self.currentIndex().parent()
            rootIndex = self.rootIndex()
            index = self.currentIndex()
            isDirMode = self._mode == TreeModelView.DIR_MODE
            if index == rootIndex or parent == rootIndex or isDirMode:
                self.selectPath(self._model.filePath(parent))
            else:
                self.expandTree(self._model.filePath(parent))
                self.setCurrentIndex(parent)

    def setRootPath(self, path):
        """
        Sets the root path to the given path

        Args:
            path: (str) The new root path
        """
        if self._navigate:
            self.setRootIndex(self._model.index(path))

    def getRootPath(self):
        """ Return the root path """
        return self._model.rootPath()

    def getSelectedPath(self):
        """ Return the current selected path. If selected index is None then
        return the root path """
        index = self.currentIndex()
        if not index.isValid():
            index = self.rootIndex()

        return self._model.filePath(index)

    def selectPath(self, path):
        """ Set the given path as selected. If mode is DIR_MODE then the root
        path will be the root of the given path."""
        if path is not None:
            index = self._model.index(path)
            if index.isValid():
                self.setRootIndex(index.parent())
                if self._mode == TreeModelView.TREE_MODE:
                    self._expandIndex(index)

                self.setCurrentIndex(index)


class _ViewProperties:
    """
    Simple class that holds values dynamically as key=value pairs
    """
    def __init__(self, view, **kwargs):
        self.view = view
        self.set(**kwargs)

    def __eq__(self, other):
        """ Equality comparison between _ViewProperties objects """
        return other and self.view == other.view

    def __hash__(self):
        return hash(self.view)

    def set(self, **kwargs):
        """
        Set different properties of _ViewProperties.
        Example:
            p = _ViewProperties(view='TextView', icon='qta.some-icon')
            p.set(toolTip='help...', color='#344567')

        """
        for k, v in kwargs.items():
            setattr(self, k, v)


class FileBrowser(Browser):
    """ The FileBrowser is an extension of Browser class for file navigation
    """
    VIEWS = 0
    CURRENT = 1

    def __init__(self, **kwargs):
        """ Creates a FileBrowser instance

        Keyword Args:
            model   The tree model for the view to present.
            mode:   (int) The TreeView mode. Possible values:
                    TREE_MODE, DIR_MODE
            navigate: (Boolean) If True, the user can navigate through
                      the directories
        """
        Browser.__init__(self, **kwargs)
        self._views = {}  # see registerView method for details

        self._group = qtw.QActionGroup(self)
        self._group.triggered.connect(self.__viewActionTriggered)

        self._toolBarActions = []
        self._toolBar.addSeparator()

        model = self._treeModelView.model()
        self._lineCompleter.setText(
            model.filePath(self._treeModelView.currentIndex()))

    def __addAction(self, a, current, view):
        a.setChecked(current == view)
        self._toolBar.addAction(a)
        self._group.addAction(a)
        self._toolBarActions.append(a)

    def __viewActionTriggered(self, action):
        if action.isChecked():
            model = self._treeModelView.model()
            path = model.filePath(self._treeModelView.currentIndex())
            ext = getExt(path)
            d = self._views.get(ext, {})
            d[FileBrowser.CURRENT] = action.getUserData()

            self.updateViewPanel()

    def __updateToolBar(self, ext):
        """
        Update the toolbar actions according to the given file extension.
        """
        vd = self._views.get(ext, {})
        views = vd.get(FileBrowser.VIEWS, {}).values()
        current = vd.get(FileBrowser.CURRENT)

        for a in self._toolBarActions:
            self._toolBar.removeAction(a)
            self._group.removeAction(a)

        for v in views:
            a = getattr(v, 'action', None)
            if a is None:
                a = TriggerAction(self, faIconName=v.icon, checkable=True,
                                  userData=v.view)
                v.action = a

            a.setChecked(False)
            self.__addAction(a, current, v.view)

    def _createTreeModelView(self, **kwargs):
        """ Create the FileModelView """
        model = kwargs.get('model')
        if model is None:
            kwargs['model'] = qtw.QFileSystemModel(self)
        elif not isinstance(model, qtw.QFileSystemModel):
            raise Exception('Specify a QFileSystemModel instance.')

        view = FileModelView(**kwargs)
        view.setSortingEnabled(True)
        return view

    def _createViewPanel(self, **kwargs):
        return None

    def _createInfoPanel(self, **kwargs):
        return None

    def _onReturnPressed(self):
        """ Invoked when the user press Enter on line completer """
        if self._treeModelView.canNavigate():
            path = self._lineCompleter.text()
            index = self._treeModelView.model().index(path)
            # FIXME[hv] self._completer.currentIndex() could be sufficient
            if index.isValid():
                self._treeModelView.selectIndex(index)
                self.sigIndexChanged.emit(index)

    def _onSelectionChanged(self, selected, deselected):
        Browser._onSelectionChanged(self, selected, deselected)
        if not selected.isEmpty():
            index = selected.indexes()[0]
            model = self._treeModelView.model()
            path = model.filePath(index)
            self.__updateToolBar(getExt(path))
            self._lineCompleter.setText(path)

    def registerView(self, ext, view, icon, current, **kwargs):
        """
        Add additional views for the given file extension. An image icon should
        be provided for the corresponding action that will be added to the upper
        toolbar.

        Args:
            ext:  (str) The file extension. Example: '.xmd'
            view: (int) A unique identifier for the view
            icon: (str) icon name. Example: 'fa.home'
            current: (boolean) If True, the specified view will be the current

        Keyword Args:
            Additional properties. Example: tooltip='help text ...'
        """
        d = self._views.get(ext, {})
        vd = d.get(FileBrowser.VIEWS, {})
        v = vd.get(view)

        if v is None:
            v = _ViewProperties(view, icon=icon, **kwargs)
        else:
            v.set(icon=icon, **kwargs)

        vd[view] = v
        if current or FileBrowser.CURRENT not in d:
            d[FileBrowser.CURRENT] = view

        d[FileBrowser.VIEWS] = vd
        self._views[ext] = d

    def getCurrentView(self, ext):
        """ Return the current registered view for the given file extension or
        None if no view has been registered.

        Returns:
            (int) The current view identifier or None.
        """
        d = self._views.get(ext, {})
        return d.get(FileBrowser.CURRENT)
