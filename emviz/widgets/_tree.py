
import PyQt5.QtCore as qtc
import PyQt5.QtWidgets as qtw

from ._toolbar import TriggerAction


class FileBrowser(qtw.QTreeView):
    """ The FileBrowser class is an extension of the QTreeView class, allowing
    different navigation modes.
    FileBrowser is initialized with a QFileSystemModel, having the 'path' param
    as the root path of the model.

    The widget can be initialized by one of the following modes:

     - DEFAULT_MODE: All files on the initial QFileSystemModel are shown
     - DIR_MODE: Only the files on the current folder are shown
    """

    DEFAULT_MODE = 0
    DIR_MODE = 1

    # signal emitted when the view has been resized
    sigSizeChanged = qtc.pyqtSignal()

    def __init__(self, parent=None, **kwargs):
        """
        Constructs an TreeView object
        :param parent:   The parent widget
        :param kwargs:
           - mode:     (int) The TreeView mode. Possible values:
                       DEFAULT_MODE, DIR_MODE
           - navigate: (Boolean) If True, the user can navigate through
                       the directories. Valid only for DIR_MODE
           - path:     (str) Initial root path
        """
        qtw.QTreeView.__init__(self, parent=parent)
        dm = FileBrowser.DEFAULT_MODE
        self._mode = kwargs.get('mode', dm)
        self._navigate = True

        self.doubleClicked.connect(self.__onPathDoubleClick)

        self._model = None
        self.setModel(qtw.QFileSystemModel(self))
        self.header().setSectionResizeMode(0, qtw.QHeaderView.ResizeToContents)
        self._model.setRootPath(qtc.QDir.rootPath())
        path = kwargs.get('path', qtc.QDir.rootPath())

        isDefault = self._mode == dm
        if not isDefault:
            self.setRootIndex(self._model.index(path))
        else:
            self.expandTree(path)

        self._navigate = isDefault or kwargs.get('navigate', True)
        self.setItemsExpandable(isDefault)
        self.setRootIsDecorated(isDefault)
        self.sigSizeChanged.connect(self.__treeViewSizeChanged)

    def __onPathDoubleClick(self, index):
        """
        Slot invoked when the mouse is double-clicked on the specified index
        """
        if self._navigate and self._mode == FileBrowser.DIR_MODE:
            info = qtc.QFileInfo(self._model.filePath(index))
            if info.isDir():
                self.setRootIndex(index)

    def __treeViewSizeChanged(self):
        if self._mode == FileBrowser.DEFAULT_MODE:
            indexes = self.selectionModel().selectedIndexes()
            if indexes:
                index = indexes[0]
                self.expand(index)
                self.scrollTo(index)

    def __expandIndex(self, index):
        if index.isValid():
            cs = qtc.QItemSelectionModel.ClearAndSelect
            r = qtc.QItemSelectionModel.Rows
            self.selectionModel().select(index, cs | r)
            self.expand(index)
            self.scrollTo(index)

    def expandTree(self, path):
        """
        Expand the Tree View to the given path
        """
        index = self._model.index(path)
        self.__expandIndex(index)

    def setRootIndex(self, index):
        if self._navigate and index.isValid():
            qtw.QTreeView.setRootIndex(self, index)

    def setItemsExpandable(self, enable):
        qtw.QTreeView.setItemsExpandable(self, enable)

    def expand(self, index):
        if self._mode == FileBrowser.DEFAULT_MODE:
            qtw.QTreeView.expand(self, index)

    def scrollTo(self, index, hint=qtw.QAbstractItemView.EnsureVisible):
        if self._navigate:
            qtw.QTreeView.scrollTo(self, index, hint)

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

    def goHome(self):
        """ Changes current directory by moving to the home directory. """
        if self._mode == FileBrowser.DIR_MODE and self._navigate:
            self.setRootPath(qtc.QDir.homePath())
        elif self._navigate:
            self.__expandIndex(self._model.index(qtc.QDir.homePath()))

    def goUp(self):
        """ Changes directory by moving one directory up from the current
        directory."""
        if self._mode == FileBrowser.DIR_MODE and self._navigate:
            parent = self.rootIndex().parent()
            if parent.isValid():
                self.setRootIndex(parent)
        elif self._navigate:
            indexes = self.selectedIndexes()
            if indexes:
                index = indexes[0]
                parent = index.parent()
                self.__expandIndex(parent)
                self.collapse(index)

    def setRootPath(self, path):
        """
        Sets the root path to the given path
        :param path: (str) The new root path
        """
        self.setRootIndex(self._model.index(path))

    def getCurrentPath(self):
        """ Return the path from the current directory """
        if self._mode == FileBrowser.DIR_MODE:
            return self._model.filePath(self.rootIndex())
        else:
            return self._model.filePath(self.currentIndex())

    def canNavigate(self):
        """ Return True if navigation is available """
        return self._navigate


class FileNavigatorPanel(qtw.QWidget):
    """ The FileNavigatorPanel class allow users to select files or directories.
     It incorporates a completer to facilitate the search."""

    # signal emitted when new index is selected
    sigIndexSelected = qtc.pyqtSignal(qtc.QModelIndex)

    def __init__(self, parent=None, **kwargs):
        """
         Constructs a new FileNavigator object
        :param parent: The parent widget
        :param kwargs: The FileTreeView kwargs and the following:
         - readOnly  (Boolean) If True, all navigation buttons and completer
                     will be disabled
        """
        qtw.QWidget.__init__(self, parent)
        self.__setupUi(kwargs)

    def __setupUi(self, kwargs):
        """ Create the main GUI of the FileNavigator. The GUI is composed by a
        tool bar with navigation actions and a FileTreeView.
         """
        layout = qtw.QVBoxLayout(self)
        layout.addWidget(self.__createToolBar())
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

        self._view = FileBrowser(self, **kwargs)
        self._view.setSortingEnabled(True)
        self.__enableActions(not readOnly)
        self._lineCompleter.setReadOnly(readOnly)
        self._lineCompleter.returnPressed.connect(self._onReturnPressed)
        self._lineCompleter.textChanged.connect(self._view.expandTree)
        layout.addWidget(self._view)
        self._completer.setModel(self._view.model())
        self._lineCompleter.setText(self._view.getCurrentPath())
        self._view.selectionModel().selectionChanged.connect(
            self.__onSelectionChanged)
        if self._view.getMode() == FileBrowser.DEFAULT_MODE:
            root = qtc.QDir.rootPath()
            path = kwargs.get('path', root)
            if not path == root and qtc.QFileInfo.exists(path):
                self._lineCompleter.setText(path)

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

    def __onSelectionChanged(self, selected, deselected):
        """ Invoked when the selection change in the tree view """
        if not selected.isEmpty():
            index = selected.indexes()[0]
            self._lineCompleter.setText(self._view.model().filePath(index))
            if not self._lineCompleter.hasFocus():
                self.sigIndexSelected.emit(index)

    def _onHomeAction(self):
        """ This slot leads the FileTreeView to the user home directory """
        self._view.goHome()
        m = self._view.getMode()
        if m == FileBrowser.DIR_MODE and self._view.canNavigate():
            self.sigIndexSelected.emit(qtc.QModelIndex())

    def _onUpAction(self):
        """ Changes directory by moving one directory up from the current
        directory. """
        self._view.goUp()
        m = self._view.getMode()
        if m == FileBrowser.DIR_MODE and self._view.canNavigate():
            self.sigIndexSelected.emit(qtc.QModelIndex())

    def _onRefreshAction(self):
        """ Refreshes the directory information """
        d = qtc.QDir(self._view.getCurrentPath())
        d.refresh()

    def _onReturnPressed(self):
        """ Invoked when the user press Enter on line completer """
        navigate = self._view.canNavigate()
        text = self._lineCompleter.text()
        if self._view.getMode() == FileBrowser.DIR_MODE:
            if qtc.QFileInfo.exists(text):
                info = qtc.QFileInfo(text)
                if navigate and info.isDir():
                    self._view.setRootPath(text)
                else:
                    path = info.dir().absolutePath()
                    index = self._view.model().index(text)
                    self._view.setRootPath(path)
                    self._view.expandTree(text)
                    self.sigIndexSelected.emit(index)
        else:
            self._view.expandTree(self._lineCompleter.text())
            if navigate:
                self.sigIndexSelected.emit(self._view.model().index(text))

    def getModel(self):
        """ Return the current model """
        return self._view.model()

    def getCurrentIndex(self):
        """ Return the current index """
        return self._view.currentIndex()
