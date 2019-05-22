
from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QSpacerItem,
                             QSizePolicy, QPushButton, QSpinBox, QLabel)
import qtawesome as qta


# TODO: Review methods, global variables, documentation, etc
# In the whole file

class PageBar(QWidget):

    """
    This signal is emitted when the current page change
    emit(currentPage)
    """
    sigPageChanged = pyqtSignal(int)

    """ 
    This signal is emitted when the page configuration change.
    emit(page, firstPage, lastPage, step) 
    """
    sigPageConfigChanged = pyqtSignal(int, int, int, int)

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self._page = 0
        self._firstPage = 0
        self._lastPage = 0
        self._step = 1
        self.__setupUI()

    def __setupUI(self):
        self.setMinimumHeight(40)
        self.setMaximumHeight(40)
        self._mainLayout = QHBoxLayout(self)
        self._mainLayout.setContentsMargins(1, 1, 1, 1)
        self._mainLayout.addItem(QSpacerItem(40,
                                             20,
                                             QSizePolicy.Expanding,
                                             QSizePolicy.Minimum))
        self._pushButtonPrevPage = QPushButton(self)
        self._mainLayout.addWidget(self._pushButtonPrevPage)
        self._pushButtonPrevPage.setIcon(qta.icon('fa.angle-left'))
        self._pushButtonPrevPage.clicked.connect(self._onPrevPage)
        self._spinBoxCurrentPage = QSpinBox(self)
        self._spinBoxCurrentPage.setButtonSymbols(QSpinBox.NoButtons)
        self._spinBoxCurrentPage.editingFinished.connect(
            self._onSpinBoxCurrentPageEditingFinished)
        self._spinBoxCurrentPage.setMaximumSize(50, 25)
        self._spinBoxCurrentPage.setMinimumSize(50, 25)
        self._mainLayout.addWidget(self._spinBoxCurrentPage)
        self._labelPageCount = QLabel(self)
        self._mainLayout.addWidget(self._labelPageCount)
        self._pushButtonNextPage = QPushButton(self)
        self._pushButtonNextPage.setIcon(qta.icon('fa.angle-right'))
        self._pushButtonNextPage.clicked.connect(self._onNextPage)
        self._mainLayout.addWidget(self._pushButtonNextPage)
        self._mainLayout.addItem(QSpacerItem(40,
                                             20,
                                             QSizePolicy.Expanding,
                                             QSizePolicy.Minimum))

    def __showPageCount(self):
        """ Show page count """
        t = " of %d" % (self._lastPage - self._firstPage + 1)
        self._labelPageCount.setText(t)

    @pyqtSlot()
    def _onPrevPage(self):
        self.setPage(self._page - 1)

    @pyqtSlot()
    def _onNextPage(self):
        self.setPage(self._page + 1)

    @pyqtSlot()
    def _onSpinBoxCurrentPageEditingFinished(self):
        """
        This slot is invoked when the user edit the page number and press ENTER
        """
        self.setPage(self._spinBoxCurrentPage.value() - 1)

    def setPage(self, page):
        """
        Sets page as current page.
        Emit the sigPageChanged signal
        """
        if not page == self._page and page in range(self._firstPage,
                                                    self._lastPage + 1):
            self._page = page
            self._spinBoxCurrentPage.setValue(page + 1)
            self.sigPageChanged.emit(self._page)

    def getPage(self):
        """ Return the current page """
        return self._page

    def setup(self, page, firstPage, lastPage, step=1):
        """ Setups the paging params """
        if firstPage <= lastPage and page in range(firstPage, lastPage + 1):
            self._page = page
            self._firstPage = firstPage
            self._lastPage = lastPage
            self._step = step
            self._spinBoxCurrentPage.setRange(firstPage + 1, lastPage + 1)
            self._spinBoxCurrentPage.setSingleStep(step)
            self._spinBoxCurrentPage.setValue(page + 1)
            self.__showPageCount()
            self.sigPageConfigChanged.emit(self._page, self._firstPage,
                                           self._lastPage, self._step)


class PagingView(QWidget):
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
        QWidget.__init__(self, parent=parent)
        self._model = None
        self._selectionMode = self.NO_SELECTION
        self.__setupUI()

    def __setupUI(self):
        self._mainLayout = QVBoxLayout(self)
        self._mainLayout.setSpacing(0)
        self._mainLayout.setContentsMargins(1, 1, 1, 1)
        self._pageBar = PageBar(self)
        self._mainLayout.addWidget(self._pageBar)

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