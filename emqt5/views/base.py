#!/usr/bin/python
# -*- coding: utf-8 -*-


from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal, QRectF
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QSpinBox, QLabel,
                             QStyledItemDelegate, QStyle, QHBoxLayout,
                             QSizePolicy, QSpacerItem, QPushButton,
                             QGraphicsPixmapItem)
from PyQt5.QtGui import QPixmap, QPalette, QPen

import qtawesome as qta
import pyqtgraph as pg

from emqt5.utils import EmPath, parseImagePath
from .model import ImageCache, X_AXIS, Y_AXIS, Z_AXIS


class EMImageItemDelegate(QStyledItemDelegate):
    """
    ImageItemDelegate class provides display and editing facilities for
    em image data items from a model.
    """
    def __init__(self, parent=None,
                 selectedStatePen=None,
                 borderPen=None):
        """
        If selectedStatePen is None then the border will not be painted when
        the item is selected.
        If selectedStatePen has a QPen value then a border will be painted when
        the item is selected
        :param parent: the parent qt object
        :param selectedStatePen: QPen object
        """
        QStyledItemDelegate.__init__(self, parent)
        if selectedStatePen is None:
            self._selectedStatePen = QPen(Qt.red, 2, Qt.DashLine)
        else:
            self._selectedStatePen = selectedStatePen

        self._borderPen = borderPen
        self._imgCache = ImageCache(50, 50)
        self._imageView = pg.ImageView(view=pg.ViewBox())
        self._imageView.getView().invertY(False)
        self._pixmapItem = None

    def paint(self, painter, option, index):
        """
        Reimplemented from QStyledItemDelegate
        """
        if index.isValid():
            self._setupView(index)
            self._imageView.ui.graphicsView.scene().setSceneRect(
                QRectF(0, 0, option.rect.width(),
                       option.rect.height()))
            self._imageView.ui.graphicsView.scene().render(painter,
                                                           QRectF(option.rect))
            if option.state & QStyle.State_Selected:
                painter.setPen(self._selectedStatePen)
                penWidth = self._selectedStatePen.width()
                painter.drawRect(QRectF(option.rect.x() + penWidth,
                                        option.rect.y() + penWidth,
                                        option.rect.width() - 2 * penWidth,
                                        option.rect.height() - 2 * penWidth))

    def _setupView(self, index):
        """
        Configure the widget used as view to shoe the image
        """
        imgData = self._getThumb(index)

        if imgData is None:
            return

        size = index.data(Qt.SizeHintRole)
        (w, h) = (size.width(), size.height())

        v = self._imageView.getView()
        (cw, ch) = (v.width(), v.height())

        if not (w, h) == (cw, ch):
            v.setGeometry(0, 0, w, h)
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

        imgParams = parseImagePath(imgPath)

        if imgParams is None or not len(imgParams) == 3:
            return None
        else:
            imgPath = imgParams[2]

            if EmPath.isStack(imgParams[2]):
                id = str(imgParams[0]) + '_' + imgPath
            else:
                id = imgPath

        imgData = self._imgCache.getImage(id)

        if imgData is None:
            imgData = self._imgCache.addImage(id, imgPath, imgParams[0])

        if imgData is None:
            return None
        else:
            axis = imgParams[1]
            if axis == X_AXIS:
                imgData = imgData[:, :, imgParams[0]]
            elif axis == Y_AXIS:
                imgData = imgData[:, imgParams[0], :]
            elif axis == Z_AXIS:
                 imgData = imgData[imgParams[0], :, :]

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
