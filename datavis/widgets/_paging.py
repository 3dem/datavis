
import qtawesome as qta

import PyQt5.QtCore as qtc
import PyQt5.QtWidgets as qtw


class PagingInfo:
    """ Very simple class to store information about paging logic of
    a group of items (usually rows) and ease some calculations.
    """
    def __init__(self, numberOfItems, pageSize, currentPage=1):
        """
        Construct a PagingInfo instance.

        Args:
            numberOfItems:  (int ) Total number of items that will be taken
                            into account for paging.
            pageSize:       (int) Number of items will be in one page.
            currentPage:    (int) Current page (first page is 1).
        """
        self.numberOfItems = numberOfItems
        self.currentPage = 1
        self.pageSize = 1
        self.setPageSize(pageSize)
        self.setCurrentPage(currentPage)

    def setCurrentPage(self, value):
        """
        Set the current page.

        Args:
            value: (int) The page number(1 is the first).

        Returns:
            True if the current page is changed.
        """
        if self.currentPage == value:
            return False

        if value < 1 or value > self.numberOfItems:
            raise Exception("Page number %s, is out of bounds" % value)

        self.currentPage = value
        return True

    def setPageSize(self, pageSize):
        """
        Sets the page size. Changing the page size implies changing
        the current page.

        Args:
            pageSize:  (int) The number of items per page
        """
        # Calculating the current row: first index from the current page
        row = (self.currentPage - 1) * self.pageSize
        self.pageSize = pageSize
        self.numberOfPages = int(self.numberOfItems / pageSize)
        self.itemsInLastPage = self.numberOfItems % pageSize
        if self.itemsInLastPage > 0:
            self.numberOfPages += 1  # add page with items left
        else:
            self.itemsInLastPage = pageSize
        # Preserving the current row
        self.setCurrentPage(int(row / pageSize) + 1)

    def nextPage(self):
        """ Increase the current page by one. If the current page is the last
        one, it will not be changed. Return True if the currentPage was changed.
        """
        if self.currentPage < self.numberOfPages:
            self.currentPage += 1
            return True
        return False

    def prevPage(self):
        """ Decrease the current page by one. If the current page is 1, it will
        not be changed. Return True if the currentPage was changed.
        """
        if self.currentPage > 1:
            self.currentPage -= 1
            return True
        return False

    def isLastPage(self):
        """ Returns True if the current page is the last. """
        return self.currentPage == self.numberOfPages

    def getPage(self, index):
        """ Return the page where index are located or -1 if it can not be
        calculated.

        Args:
            index: (int) The index. 0 is the first

        Returns:
            (int) The page index. 0 is the first
        """
        if self.pageSize <= 0:
            return -1
        return int(index / self.pageSize) if index >= 0 else -1


class PageBar(qtw.QWidget):
    """
    Paging bar that will allow users to navigate through pages
    """

    """
    This signal is emitted when the current page is changed
    emit(currentPage)
    """
    sigPageChanged = qtc.pyqtSignal(int)

    """ This signal is emitted when the paging info is changed """
    sigPagingInfoChanged = qtc.pyqtSignal()

    def __init__(self, parent=None, **kwargs):
        """
        Construct an PageBar instance

        Args:
            parent: Parent widget

        Keyword Args:
            pagingInfo: :class:`PagingInfo <datavis.widgets.PagingInfo>`
        """
        qtw.QWidget.__init__(self, parent)
        self.__setupGUI()
        self.setPagingInfo(kwargs['pagingInfo'])

    def __setupGUI(self):
        """ Setups the GUI """
        self.setMinimumHeight(40)
        self.setMaximumHeight(40)
        layout = qtw.QHBoxLayout(self)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.addItem(
            qtw.QSpacerItem(40, 20, qtw.QSizePolicy.Expanding,
                            qtw.QSizePolicy.Minimum))

        # Previous page button
        self._btnPagePrev = qtw.QPushButton(self)
        self._btnPagePrev.setIcon(qta.icon('fa.angle-left'))
        self._btnPagePrev.clicked.connect(self._onPrevPage)
        layout.addWidget(self._btnPagePrev)

        # Create a spinBox with the current page value
        self._spinBox = qtw.QSpinBox(self)
        self._spinBox.setButtonSymbols(qtw.QSpinBox.NoButtons)
        self._spinBox.editingFinished.connect(
            self._onSpinBoxCurrentPageEditingFinished)
        self._spinBox.setMaximumSize(50, 25)
        self._spinBox.setMinimumSize(50, 25)
        layout.addWidget(self._spinBox)
        self._label = qtw.QLabel(self)
        layout.addWidget(self._label)

        # Next button
        self._btnPageNext = qtw.QPushButton(self)
        self._btnPageNext.setIcon(qta.icon('fa.angle-right'))
        self._btnPageNext.clicked.connect(self._onNextPage)
        layout.addWidget(self._btnPageNext)

        layout.addItem(
            qtw.QSpacerItem(40, 20, qtw.QSizePolicy.Expanding,
                            qtw.QSizePolicy.Minimum))

    @qtc.pyqtSlot()
    def _onPrevPage(self):
        """ Change to the previous page. """
        if self._pagingInfo.prevPage():
            self._updateCurrentPage()

    @qtc.pyqtSlot()
    def _onNextPage(self):
        """ Change to the next page. """
        if self._pagingInfo.nextPage():
            self._updateCurrentPage()

    @qtc.pyqtSlot()
    def _onSpinBoxCurrentPageEditingFinished(self):
        """
        This slot is invoked when the user edit the page number and press ENTER
        """
        self.setCurrentPage(self._spinBox.value())

    def _updateCurrentPage(self):
        """
        Setups the PageBar according to the current page.
        This method should be called after self._pagingInfo is updated.
        Emits the sigPageChanged signal.
        """
        value = self._pagingInfo.currentPage
        self._spinBox.setValue(value)
        self._btnPagePrev.setEnabled(value != 1)
        self._btnPageNext.setEnabled(not self._pagingInfo.isLastPage())
        self.sigPageChanged.emit(value)

    def setCurrentPage(self, page):
        """
        Sets page as current page. Emits the sigPageChanged signal
        """
        # Only take actions if the setPage really change the current page
        if self._pagingInfo.setCurrentPage(page):
            self._updateCurrentPage()

    def getCurrentPage(self):
        """ Returns the current page """
        return self._pagingInfo.currentPage

    def getPageCount(self):
        """ Returns the number of pages """
        return self._pagingInfo.numberOfPages

    def setPagingInfo(self, pagingInfo, step=1):
        """ Setups the paging params """
        self._pagingInfo = pagingInfo
        self._spinBox.setRange(1, pagingInfo.numberOfPages)
        self._spinBox.setSingleStep(step)
        self._label.setText(" of %d" % self._pagingInfo.numberOfPages)
        self._updateCurrentPage()
