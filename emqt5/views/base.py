#!/usr/bin/python
# -*- coding: utf-8 -*-


from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal, QRectF, QItemSelection
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QSpinBox, QLabel,
                             QStyledItemDelegate, QStyle, QHBoxLayout,
                             QSizePolicy, QSpacerItem, QPushButton,
                             QGraphicsPixmapItem)
from PyQt5.QtGui import QPixmap, QPalette, QPen, QBrush

import qtawesome as qta
import pyqtgraph as pg

from emqt5.utils import parseImagePath, ImageRef
from .model import ImageCache, X_AXIS, Y_AXIS, Z_AXIS


class EMImageItemDelegate(QStyledItemDelegate):
    """
    ImageItemDelegate class provides display and editing facilities for
    em image data items from a model.
    """
    def __init__(self, parent=None):

        QStyledItemDelegate.__init__(self, parent)
        self._imgCache = ImageCache(50, 50)
        self._imageView = pg.ImageView(view=pg.ViewBox())
        self._imageView.getView().invertY(False)
        self._pixmapItem = None
        self._imageRef = ImageRef()
        self._sBorder = 3  # selected state border (px)
        self._focusPen = QPen(Qt.DotLine)

    def paint(self, painter, option, index):
        """
        Reimplemented from QStyledItemDelegate
        """
        if index.isValid():
            x = option.rect.x()
            y = option.rect.y()
            w = option.rect.width()
            h = option.rect.height()
            rect = QRectF()
            if option.state & QStyle.State_Selected:
                if option.state & QStyle.State_HasFocus or \
                        option.state & QStyle.State_Active:
                    colorGroup = QPalette.Active
                else:
                    colorGroup = QPalette.Inactive
                painter.fillRect(option.rect,
                                 option.palette.color(colorGroup,
                                                      QPalette.Highlight))
            self._setupView(index, w, h)
            rect.setRect(self._sBorder, self._sBorder, w - 2 * self._sBorder,
                         h - 2 * self._sBorder)
            self._imageView.ui.graphicsView.scene().setSceneRect(rect)
            rect.setRect(x + self._sBorder, y + self._sBorder,
                         w - 2 * self._sBorder, h - 2 * self._sBorder)
            self._imageView.ui.graphicsView.scene().render(painter, rect)
            if option.state & QStyle.State_HasFocus:
                painter.save()
                self._focusPen.setColor(
                    option.palette.color(QPalette.Active,
                                         QPalette.Highlight))
                painter.setPen(self._focusPen)
                painter.drawRect(rect)
                painter.restore()

    def _setupView(self, index, width, height):
        """
        Configure the widget used as view to show the image
        """
        imgData = self._getThumb(index)

        if imgData is None:
            return

        size = index.data(Qt.SizeHintRole)
        (w, h) = (size.width(), size.height())

        v = self._imageView.getView()
        (cw, ch) = (v.width(), v.height())

        if not (w, h) == (cw, ch):
            v.setGeometry(0, 0, width, height)
            v.resizeEvent(None)

        if not isinstance(imgData, QPixmap):  # QPixmap or np.array
            if self._pixmapItem:
                self._pixmapItem.setVisible(False)

            self._imageView.setImage(imgData)
        else:
            if not self._pixmapItem:
                self._pixmapItem = QGraphicsPixmapItem(imgData)
                v.addItem(self._pixmapItem)
            else:
                self._pixmapItem.setPixmap(imgData)
            self._pixmapItem.setVisible(True)
        v.autoRange(padding=0)

    def _getThumb(self, index, height=100):
        """
        If the thumbnail stored in Image Cache
        :param index: QModelIndex
        :param height: height to scale the image
        """
        imgPath = index.data(Qt.UserRole)

        imgRef = parseImagePath(imgPath, self._imageRef)

        if imgRef is None:
            return None

        if imgRef.imageType & ImageRef.SINGLE == ImageRef.SINGLE:
            imgId = imgRef.path
        elif imgRef.imageType & ImageRef.STACK == ImageRef.STACK:
            if imgRef.imageType & ImageRef.VOLUME == ImageRef.VOLUME:
                imgId = '%d-%s' % (imgRef.volumeIndex, imgRef.path)
            else:
                imgId = '%d-%s' % (imgRef.index, imgRef.path)
        else:
            return None

        imgData = self._imgCache.getImage(imgId)

        if imgData is None:  # the add the image to Cache
            if imgRef.imageType & ImageRef.VOLUME == ImageRef.VOLUME:
                imgData = self._imgCache.addImage(imgId, imgRef.path,
                                                  imgRef.volumeIndex)
            else:
                imgData = self._imgCache.addImage(imgId, imgRef.path,
                                                  imgRef.index)

        if imgData is None:
            return None
        else:
            if imgRef.axis == X_AXIS:
                imgData = imgData[:, :, imgRef.index]
            elif imgRef.axis == Y_AXIS:
                imgData = imgData[:, imgRef.index, :]
            elif imgRef.axis == Z_AXIS:
                 imgData = imgData[imgRef.index, :, :]

        return imgData

    def setImageCache(self, imgCache):
        """
        Set the ImageCache object to be use for this ImageDelegate
        :param imgCache: ImageCache
        """
        self._imgCache = imgCache

    def getImageCache(self):
        """ Getter for imageCache """
        return self._imgCache


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


class AbstractView(QWidget):
    """ The base class for a view. AbstractView contains a paging bar """

    #  Selection Behavior
    SELECT_ROWS = 1  # Selecting single items.
    SELECT_COLUMNS = 2  # Selecting only rows.
    SELECT_ITEMS = 3  # Selecting only columns.

    #  Selection Mode
    SINGLE_SELECTION = 20  # See QAbstractItemView.SingleSelection
    EXTENDED_SELECTION = 21  # See QAbstractItemView.ExtendedSelection
    MULTI_SELECTION = 22  # See QAbstractItemView.MultiSelection

    """ 
        This signal is emitted when the current selection is changed
        emit(selected, deselected) 
        """
    sigSelectionChanged = pyqtSignal()

    def __init__(self, parent=None):
        QWidget.__init__(self, parent=parent)
        self._model = None
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
        pass

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