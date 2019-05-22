#!/usr/bin/python
# -*- coding: utf-8 -*-

import os

from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal, QRectF, QVariant, QLocale
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QSpinBox, QLabel,
                             QStyledItemDelegate, QStyle, QHBoxLayout, QSlider,
                             QSizePolicy, QSpacerItem, QPushButton, QCheckBox,
                             QGraphicsPixmapItem, QRadioButton, QButtonGroup,
                             QComboBox, QItemDelegate, QColorDialog,
                             QTableWidget, QFormLayout, QTableWidgetItem,
                             QLineEdit, QGridLayout, QWidgetItem)
from PyQt5.QtGui import (QPixmap, QPalette, QPen, QColor, QIntValidator,
                         QDoubleValidator)

import pyqtgraph as pg

from emqt5.utils import ImageManager, ImageRef, parseImagePath


class EMImageItemDelegate(QStyledItemDelegate):
    """
    ImageItemDelegate class provides display and editing facilities for
    em image data items from a model.
    """
    def __init__(self, parent=None, **kwargs):
        """
        kwargs:
          - imageManager: the ImageManager for internal read/manage
                          image operations.
        """
        QStyledItemDelegate.__init__(self, parent)
        self._imageManager = kwargs.get('imageManager') or ImageManager(150)
        self._imageView = pg.ImageView(view=pg.ViewBox())
        self._imageView.getView().invertY(False)
        self._pixmapItem = None
        self._noImageItem = pg.TextItem("NO IMAGE")
        self._labelText = []
        self._imageView.getView().addItem(self._noImageItem)
        self._noImageItem.setVisible(False)
        self._imageRef = ImageRef()
        self._sBorder = 3  # selected state border (px)
        self._textHeight = 16
        self._focusPen = QPen(Qt.DotLine)
        self.__labelIndexes = []
        self._thumbSize = 64

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
            else:
                colorGroup = QPalette.Active
                painter.fillRect(option.rect,
                                 option.palette.color(colorGroup,
                                                      QPalette.HighlightedText))
            if self.__labelIndexes:
                h -= self._textHeight * len(self.__labelIndexes)
                self._setupText(index)
            else:
                self._labelText = []

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
                rect.setRect(x, y, w - 1, h - 1)
                if self._labelText:
                    rect.setHeight(
                        h + self._textHeight * len(self.__labelIndexes) - 1)
                painter.drawRect(rect)
                painter.restore()
            for i, text in enumerate(self._labelText):
                rect.setRect(x + self._sBorder, y + h + i * self._textHeight,
                             w - 2 * self._sBorder, self._textHeight)
                painter.drawText(rect, Qt.AlignLeft, text)

    def _setupText(self, index):
        """ Configure the label text """
        model = index.model()
        self._labelText = []
        if model is not None and self.__labelIndexes:
            for lIndex in self.__labelIndexes:
                value = model.data(
                    model.createIndex(index.row(), lIndex))
                if isinstance(value, QVariant):
                    value = value.value()
                self._labelText.append("%s=%s" %
                                       (model.getColumnConfig(lIndex).getName(),
                                        str(value)))

    def _setupView(self, index, width, height):
        """
        Configure the widget used as view to show the image
        """
        imgData = self._getThumb(index, self._thumbSize)

        if imgData is None:
            self._imageView.clear()
            v = self._imageView.getView()
            v.addItem(self._noImageItem)
            self._noImageItem.setVisible(True)
            v.autoRange(padding=0)
            return
        self._noImageItem.setVisible(False)
        size = index.data(Qt.SizeHintRole)
        if size is not None:
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

    def _getThumb(self, index, height=64):
        """
        If the thumbnail stored in Image Cache
        :param index: QModelIndex
        :param height: height to scale the image
        """
        imgPath = index.data(Qt.UserRole)
        if imgPath is None:
            return None

        imgRef = parseImagePath(imgPath, self._imageRef,
                                os.path.split(index.model().getDataSource())[0])

        if imgRef is None:
            return None

        return self._imageManager.addImage(imgRef, (height, height))

    def setImageManager(self, imageManager):
        """
        Set the ImageCache object to be use for this ImageDelegate
        :param imageManager: ImageManager
        """
        self._imageManager = imageManager

    def getImageManager(self):
        """ Getter for ImageManager """
        return self._imageManager

    def setLabelIndexes(self, indexes):
        """
        Initialize the indexes of the columns that will be displayed as text
        below the images
        labels : (list)
        """
        self.__labelIndexes = indexes

    def getTextHeight(self):
        """ The height of text """
        return self._textHeight


class ColorItemDelegate(QStyledItemDelegate):
    """
    ColorItemDelegate class provides display and editing facilities for
    QColor selections.
    """
    def createEditor(self, parent, option, index):
        return QColorDialog(parent=parent)

    def setEditorData(self, editor, index):
        color = index.data(Qt.BackgroundRole)
        if color is not None:
            editor.setCurrentColor(color)

    def setModelData(self, editor, model, index):
        color = editor.currentColor()
        model.setData(index, color, Qt.BackgroundRole)


class ComboBoxStyleItemDelegate(QStyledItemDelegate):
    """
    ComboBoxStyleItemDelegate class provides display and editing facilities for
    text list selection.
    """
    def __init__(self, parent=None, values=None):
        QStyledItemDelegate.__init__(self, parent=parent)
        self._values = []
        self.setValues(values)

    def setValues(self, values):
        if isinstance(values, list):
            index = 0
            for text in values:
                self._values.append((text, index))
                index += 1

    def createEditor(self, parent, option, index):
        return QComboBox(parent=parent)

    def setEditorData(self, editor, index):
        index = index.data(Qt.UserRole)
        for text, value in self._values:
            editor.addItem(text, QVariant(value))
        if index is not None:
            editor.setCurrentIndex(index)

    def setModelData(self, editor, model, index):
        data = editor.currentData()
        model.setData(index, data, Qt.UserRole)
        text = editor.currentText()
        model.setData(index, text, Qt.DisplayRole)


class MarkerStyleItemDelegate(QStyledItemDelegate):
    """
    PenStyleItemDelegate class provides display and editing facilities for
    QPen style selection.
    """
    def createEditor(self, parent, option, index):
        return QComboBox(parent=parent)

    def setEditorData(self, editor, index):
        index = index.data(Qt.UserRole)
        editor.addItem('Solid', QVariant(Qt.SolidLine))
        editor.addItem('Dashed', QVariant(Qt.DashLine))
        editor.addItem('Dotted', QVariant(Qt.DotLine))
        if index is not None:
            editor.setCurrentIndex(index)

    def setModelData(self, editor, model, index):
        data = editor.currentData()
        model.setData(index, data, Qt.UserRole)
        text = editor.currentText()
        model.setData(index, text, Qt.DisplayRole)


class ColumnPropertyItemDelegate(QItemDelegate):
    """ Class used to provide custom display features for column properties """
    def __init__(self, parent=None, checkedIcon=None, uncheckedIcon=None,
                 partiallyCheckedIcon=None):
        QItemDelegate.__init__(self, parent=parent)
        self.__checkedIcon = checkedIcon
        self.__uncheckedIcon = uncheckedIcon
        self.__partiallyCheckedIcon = partiallyCheckedIcon

    def drawCheck(self, painter, option, rect, state):
        if rect is not None and rect.isValid():
            icon = None

            if state == Qt.Checked and self.__checkedIcon is not None:
                icon = self.__checkedIcon
            elif state == Qt.Unchecked and self.__uncheckedIcon is not None:
                icon = self.__uncheckedIcon
            elif state == Qt.PartiallyChecked and \
                    self.__partiallyCheckedIcon is not None:
                icon = self.__partiallyCheckedIcon

            if icon is not None:
                painter.drawImage(rect.x(), rect.y(), icon)
            else:
                QItemDelegate.drawCheck(self, painter, option, rect, state)


