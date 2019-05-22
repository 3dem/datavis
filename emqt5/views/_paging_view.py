
from PyQt5.QtCore import pyqtSignal, pyqtSlot
import PyQt5.QtWidgets as qtw

from emqt5.widgets import PageBar


class PagingView(qtw.QWidget):
    """ The base class for a view. AbstractView contains a paging bar """

    #  Selection Behavior
    SELECT_ROWS = 1  # Selecting single items.
    SELECT_COLUMNS = 2  # Selecting only rows.
    SELECT_ITEMS = 3  # Selecting only columns.

    #  Selection Mode
    SINGLE_SELECTION = 20  # See QAbstractItemView.SingleSelection
    EXTENDED_SELECTION = 21  # See QAbstractItemView.ExtendedSelection
    MULTI_SELECTION = 22  # See QAbstractItemView.MultiSelection
    NO_SELECTION = 23  # See QAbstractItemView.NoSelection

    """ 
        This signal is emitted when the current selection is changed
        emit(selected, deselected) 
        """
    sigSelectionChanged = pyqtSignal()

    def __init__(self, parent=None):
        qtw.QWidget.__init__(self, parent=parent)
        self._model = None
        self._selectionMode = self.NO_SELECTION
        self.__setupUI()

    def __setupUI(self):
        layout = qtw.QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(1, 1, 1, 1)
        self._pageBar = PageBar(self)
        layout.addWidget(self._pageBar)

    def __connectModelSignals(self, model):
        """ Connect all signals needed from the given model """
        if model:
            model.sigPageConfigChanged.connect(self.__onPageConfigChanged)
            model.sigPageChanged.connect(self.__onPageChanged)
            self._pageBar.sigPageChanged.connect(self._model.loadPage)

    def __disconnectModelSignals(self, model):
        """ Connect all signals needed from the given model """
        if model:
            model.sigPageConfigChanged.disconnect(self.__onPageConfigChanged)
            model.sigPageChanged.disconnect(self.__onPageChanged)
            self._pageBar.sigPageChanged.disconnect(self._model.loadPage)

    @pyqtSlot(int, int, int)
    def __onPageConfigChanged(self, page, pageCount, pageSize):
        """ Invoked when the model change his page configuration """
        self._pageBar.setup(page, 0, pageCount - 1, 1)

    @pyqtSlot(int)
    def __onPageChanged(self, page):
        """ Invoked when the model change his current page """
        self._pageBar.setPage(page)

    @pyqtSlot(set)
    def changeSelection(self, selection):
        """
        Invoked when the selection.
        This method must be reimplemented in inherited classes
        """
        pass

    def setModel(self, model):
        """ Sets the model for the this abstract view """
        self.__disconnectModelSignals(self._model)
        self._model = model
        self.__connectModelSignals(model)

        if model:
            self.__onPageConfigChanged(model.getPage(), model.getPageCount(),
                                       model.getPageSize())
        else:
            self.__onPageConfigChanged(0, 0, 0)

    def getModel(self):
        return self._model

    def showPageBar(self, visible):
        """ Show or hide the paging bar """
        self._pageBar.setVisible(visible)

    def getPageBar(self):
        """ Returns the page bar widget """
        return self._pageBar

    def getViewDims(self):
        """ Returns a tuple (rows, columns) with the data size """
        return 0, 0

    def setSelectionMode(self, selectionMode):
        """
        Indicates how the view responds to user selections:
        SINGLE_SELECTION, EXTENDED_SELECTION, MULTI_SELECTION.
        This method must be reimplemented in inherited classes
        """
        self._selectionMode = selectionMode

    def getSelectionMode(self):
        """ Returns the selection mode """
        return self._selectionMode

    def setSelectionBehavior(self, selectionBehavior):
        """
        This property holds which selection behavior the view uses.
        This property holds whether selections are done in terms of
        single items, rows or columns.

        Possible values:
                        SELECT_ITEMS, SELECT_ROWS, SELECT_COLUMNS
        This method must be reimplemented in inherited classes
        """
        pass

    def updateViewConfiguration(self):
        """
        It must be invoked when you need to update any change in the view
        according to modifications made to the model.
        If necessary, implement in inherited classes.
        AbstractView does not call this method.
        """
        pass