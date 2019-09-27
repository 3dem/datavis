
from PyQt5.QtCore import pyqtSignal, pyqtSlot
import PyQt5.QtWidgets as qtw

from datavis.widgets import PageBar


class PagingView(qtw.QWidget):
    """
    Base class that contains paging logic and incorporates the
    paging widgets. It will also emit signals related to the modification
    of the current page or the page configuration (e.g rows per page)
    """

    #  Selection Behavior
    SELECT_ROWS = 1  # Selecting single items.
    SELECT_COLUMNS = 2  # Selecting only rows.
    SELECT_ITEMS = 3  # Selecting only columns.

    #  Selection Mode
    SINGLE_SELECTION = 20  # See QAbstractItemView.SingleSelection
    EXTENDED_SELECTION = 21  # See QAbstractItemView.ExtendedSelection
    MULTI_SELECTION = 22  # See QAbstractItemView.MultiSelection
    NO_SELECTION = 23  # See QAbstractItemView.NoSelection

    # TODO: Check to document this kind of things for Sphinx
    """ 
    This signal is emitted when the current selection is changed
    emit(selected, deselected)
    """
    sigSelectionChanged = pyqtSignal()

    # TODO: Check to document this kind of things for Sphinx
    """
    Signal emitted when change page configuration
    emit (page, pageCount, pageSize)
    """
    sigPageConfigChanged = pyqtSignal(int, int, int)

    # TODO: Check to document this kind of things for Sphinx
    """
    Signal emitted when change the current page
    emit (page)
    """
    sigPageChanged = pyqtSignal(int)

    def __init__(self, parent=None, **kwargs):
        """
        Constructor
        :param parent:      (QWidget) The parent widget
        :param kwargs:
            pagingInfo:     (PagingInfo) The initial paging configuration
            selectionMode:  (int) The selection mode: SINGLE_SELECTION,
                            EXTENDED_SELECTION, MULTI_SELECTION or NO_SELECTION
        """
        qtw.QWidget.__init__(self, parent=parent)
        self._pagingInfo = kwargs['pagingInfo']
        self._selectionMode = kwargs.get('selectionMode',
                                         PagingView.NO_SELECTION)
        self.__setupGUI()

    def __setupGUI(self):
        layout = qtw.QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.addWidget(self._createContentWidget())
        self._pageBar = PageBar(parent=self, pagingInfo=self._pagingInfo)
        layout.addWidget(self._pageBar)

    def _createContentWidget(self):
        """ Should be implemented in subclasses to build the content widget
        and return it. """
        return None

    @pyqtSlot(set)
    def changeSelection(self, selection):
        """
        Invoked when the selection.
        This method must be reimplemented in inherited classes
        """
        pass

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

    def isSingleSelection(self):
        """ Shortcut to check whether the selection mode is SINGLE_SELECTION
        """
        return self._selectionMode == self.SINGLE_SELECTION

    def isMultiSelection(self):
        """ Shortcut to check whether the selection mode is MULTI_SELECTION
        """
        return self._selectionMode == self.MULTI_SELECTION

    def isNoSelection(self):
        """ Shortcut to check whether the selection mode is NO_SELECTION
        """
        return self._selectionMode == self.NO_SELECTION

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
