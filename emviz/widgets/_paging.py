
from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QSpacerItem,
                             QSizePolicy, QPushButton, QSpinBox, QLabel)
import qtawesome as qta


class PagingInfo:
    """ Very simple class to store information about paging logic of
    a group of items (usually rows) and ease some calculations.
    """
    def __init__(self, numberOfItems, pageSize, currentPage=1):
        """
        Initialize a PagingInfo instance.
        :param numberOfItems: Total number of items that will be taken into
            account for paging.
        :param pageSize: Number of items will be in one page.
        :param currentPage: Current page (first page is 1).
        """
        self.numberOfItems = numberOfItems
        self.currentPage = -1
        self.setPageSize(pageSize, currentPage)

    def setCurrentPage(self, value):
        """ Set the current page.
        Return True if the current page is changed. """
        if self.currentPage == value:
            return False

        if value < 1 or value > self.numberOfItems:
            raise Exception("Page number %s, is out of bounds" % value)

        self.currentPage = value
        return True

    def setPageSize(self, pageSize, currentPage=1):
        self.pageSize = pageSize
        self.numberOfPages = self.numberOfItems / pageSize
        self.itemsInLastPage = self.numberOfItems % pageSize
        if self.itemsInLastPage > 0:
            self.numberOfPages += 1  # add page with items left
        self.setCurrentPage(currentPage)

    def nextPage(self):
        """ Increase the current page by one.
        If the current page is the last one, it will not be changed.
        Return True if the currentPage was changed.
        """
        if self.currentPage < self.numberOfPages:
            self.currentPage += 1
            return True
        return False

    def prevPage(self):
        """ Decreate the current page by one.
        If the current page is 1, it will not be changed.
        Return True if the currentPage was changed.
        """
        if self.currentPage > 1:
            self.currentPage -= 1
            return True
        return False

    def isLastPage(self):
        return self.currentPage == self.numberOfPages


# TODO: Review methods, global variables, documentation, etc
# In the whole file

class PageBar(QWidget):

    """
    This signal is emitted when the current page change
    emit(currentPage)
    """
    sigPageChanged = pyqtSignal(int)

    def __init__(self, parent=None, **kwargs):
        """
        :param parent: Parent QWidget
        :param kwargs: pagingInfo should be passed
        """
        QWidget.__init__(self, parent)
        self._pagingInfo = kwargs['pagingInfo']
        self.__setupUI()
        self.setPagingInfo(self._pagingInfo)

    def __setupUI(self):
        self.setMinimumHeight(40)
        self.setMaximumHeight(40)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.addItem(
            QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        # Previous page button
        self._btnPagePrev = QPushButton(self)
        self._btnPagePrev.setIcon(qta.icon('fa.angle-left'))
        self._btnPagePrev.clicked.connect(self._onPrevPage)
        layout.addWidget(self._btnPagePrev)

        # Create a spinBox with the current page value
        self._spinBox = QSpinBox(self)
        self._spinBox.setButtonSymbols(QSpinBox.NoButtons)
        self._spinBox.editingFinished.connect(
            self._onSpinBoxCurrentPageEditingFinished)
        self._spinBox.setMaximumSize(50, 25)
        self._spinBox.setMinimumSize(50, 25)
        layout.addWidget(self._spinBox)
        self._label = QLabel(self)
        layout.addWidget(self._label)

        # Next button
        self._btnPageNext = QPushButton(self)
        self._btnPageNext.setIcon(qta.icon('fa.angle-right'))
        self._btnPageNext.clicked.connect(self._onNextPage)
        layout.addWidget(self._btnPageNext)

        layout.addItem(
            QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

    @pyqtSlot()
    def _onPrevPage(self):
        if self._pagingInfo.prevPage():
            self._updateCurrentPage()

    @pyqtSlot()
    def _onNextPage(self):
        if self._pagingInfo.nextPage():
            self._updateCurrentPage()

    @pyqtSlot()
    def _onSpinBoxCurrentPageEditingFinished(self):
        """
        This slot is invoked when the user edit the page number and press ENTER
        """
        self.setCurrentPage(self._spinBox.value())

    def _updateCurrentPage(self):
        """ This method should be called after self._pagingInfo is updated. """
        value = self._pagingInfo.currentPage
        self._spinBox.setValue(value)
        self.sigPageChanged.emit(value)
        self._btnPagePrev.setEnabled(value != 1)
        self._btnPageNext.setEnabled(not self._pagingInfo.isLastPage())

    def setCurrentPage(self, page):
        """
        Sets page as current page.
        Emit the sigPageChanged signal
        """
        # Only take actions if the setPage really change the current page
        if self._pagingInfo.setCurrentPage(page):
            self._updateCurrentPage()

    def getCurrentPage(self):
        """ Return the current page """
        return self._pagingInfo.currentPage

    def setPagingInfo(self, pagingInfo, step=1):
        """ Setups the paging params """
        self._pagingInfo = pagingInfo
        self._spinBox.setRange(1, pagingInfo.numberOfPages)
        self._spinBox.setSingleStep(step)
        self._label.setText(" of %d" % self._pagingInfo.numberOfPages)
        self._updateCurrentPage()
