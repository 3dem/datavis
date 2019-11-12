
import PyQt5.QtCore as qtc
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
    sigSelectionChanged = qtc.pyqtSignal()

    # TODO: Check to document this kind of things for Sphinx
    """
    Signal emitted when change page configuration
    emit (page, pageCount, pageSize)
    """
    sigPageConfigChanged = qtc.pyqtSignal(int, int, int)

    # TODO: Check to document this kind of things for Sphinx
    """
    Signal emitted when change the current page
    emit (page)
    """
    sigPageChanged = qtc.pyqtSignal(int)

    def __init__(self, **kwargs):
        """
        Construct an PageBar instance

        Keyword Args:
            parent:         The parent widget
            pagingInfo:     :class:`PagingInfo <datavis.widgets.PagingInfo>`
                            The initial paging configuration
            selectionMode:  (int) The selection mode: SINGLE_SELECTION,
                            EXTENDED_SELECTION, MULTI_SELECTION or NO_SELECTION
        """
        qtw.QWidget.__init__(self, parent=kwargs.get('parent'))
        self._pagingInfo = kwargs['pagingInfo']
        self._selectionMode = kwargs.get('selectionMode',
                                         PagingView.NO_SELECTION)
        self.__setupGUI()

    def __setupGUI(self):
        """ Setups the GUI """
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

    @qtc.pyqtSlot(set)
    def changeSelection(self, selection):
        """
        Invoked when you need to change the current selection. The selection
        will be stored in a set, containing the indexes of the selected rows.
        This method must be reimplemented in inherited classes.
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
        """
        self._selectionMode = selectionMode

    def getSelectionMode(self):
        """ Returns the selection mode. Possible values:  SINGLE_SELECTION,
        EXTENDED_SELECTION, MULTI_SELECTION. """
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
