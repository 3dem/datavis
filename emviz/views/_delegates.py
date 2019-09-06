#!/usr/bin/python
# -*- coding: utf-8 -*-

from PyQt5.QtCore import Qt, QRectF, QVariant
from PyQt5.QtWidgets import (QStyledItemDelegate, QStyle, QGraphicsPixmapItem,
                             QComboBox, QItemDelegate, QColorDialog)
from PyQt5.QtGui import (QPixmap, QPalette, QPen)

from emviz.models import ImageModel
from ._constants import LABEL_ROLE, DATA_ROLE
from ._image_view import ImageView

import pyqtgraph as pg


class EMImageItemDelegate(QStyledItemDelegate):
    """
    ImageItemDelegate class provides display and editing facilities for
    em image data items from a model.
    """
    def __init__(self, parent=None):
        """
        Constructs a EMImageItemDelegate.
        :param parent:  (QObject) The parent object
        """
        QStyledItemDelegate.__init__(self, parent)
        self._imageView = ImageView(None, toolBar=False, axis=False, mask=1,
                                    maskColor='#154BBC23',
                                    maskSize=20,
                                    showHandles=False)
        self._pgImageView = self._imageView._imageView  #pg.ImageView(view=pg.ViewBox())
        self._pgImageView.getView().invertY(False)
        self._pixmapItem = None
        self._noImageItem = pg.TextItem("NO IMAGE")
        self._pgImageView.getView().addItem(self._noImageItem)
        self._noImageItem.setVisible(False)
        self._sBorder = 3  # selected state border (px)
        self._textHeight = 16
        self._focusPen = QPen(Qt.DotLine)
        self._thumbSize = 64
        self._levels = None

    def paint(self, painter, option, index):
        """
        Reimplemented from QStyledItemDelegate
        """
        if not index.isValid():
            return

        x = option.rect.x()
        y = option.rect.y()
        w = option.rect.width()
        h = option.rect.height()
        rect = QRectF()
        selected = option.state & QStyle.State_Selected
        hasFocus = option.state & QStyle.State_HasFocus
        active = option.state & QStyle.State_Active

        colorGroup = QPalette.Active
        palette = QPalette.HighlightedText

        if selected:
            if not (hasFocus or active):
                colorGroup = QPalette.Inactive
            palette = QPalette.Highlight

        painter.fillRect(option.rect, option.palette.color(colorGroup, palette))
        labels = index.data(LABEL_ROLE)
        labelsCount = len(labels)
        if labels:
            h -= self._textHeight * labelsCount

        self._setupView(index, w, h, labelsCount)
        rect.setRect(self._sBorder, self._sBorder, w - 2 * self._sBorder,
                     h - 2 * self._sBorder)
        self._pgImageView.ui.graphicsView.scene().setSceneRect(rect)
        rect.setRect(x + self._sBorder, y + self._sBorder,
                     w - 2 * self._sBorder, h - 2 * self._sBorder)
        self._pgImageView.ui.graphicsView.scene().render(painter, rect)

        if hasFocus:
            painter.save()
            self._focusPen.setColor(
                option.palette.color(QPalette.Active,
                                     QPalette.Highlight))
            painter.setPen(self._focusPen)
            rect.setRect(x, y, w - 1, h - 1)
            if labels:
                rect.setHeight(h + self._textHeight * labelsCount - 1)
            painter.drawRect(rect)
            painter.restore()

        for i, text in enumerate(labels):
            rect.setRect(x + self._sBorder, y + h + i * self._textHeight,
                         w - 2 * self._sBorder, self._textHeight)
            painter.drawText(rect, Qt.AlignLeft, text)

    def _setupView(self, index, width, height, labelsCount):
        """
        Configure the widget used as view to show the image
        """
        imgData = self._getThumb(index, self._thumbSize)

        if imgData is None:
            self._pgImageView.clear()
            v = self._pgImageView.getView()
            v.addItem(self._noImageItem)
            self._noImageItem.setVisible(True)
            v.autoRange(padding=0)
            return
        self._noImageItem.setVisible(False)
        size = index.data(Qt.SizeHintRole)
        if size is not None:
            (w, h) = (size.width(), size.height())
            h -= labelsCount

            v = self._pgImageView.getView()
            (cw, ch) = (v.width(), v.height())
            self._imageView.setGeometry(0, 0, width, height)
            if not (w, h) == (cw, ch):
                #v.setGeometry(0, 0, width, height)
                self._imageView.setGeometry(0, 0, width, height)
                #v.resizeEvent(None)

            if not isinstance(imgData, QPixmap):  # QPixmap or np.array
                if self._pixmapItem:
                    self._pixmapItem.setVisible(False)
                self._imageView.setModel(ImageModel(imgData))
                #self._pgImageView.setImage(imgData, levels=self._levels)
            else:
                if not self._pixmapItem:
                    self._pixmapItem = QGraphicsPixmapItem(imgData)
                    v.addItem(self._pixmapItem)
                else:
                    self._pixmapItem.setPixmap(imgData)
                self._pixmapItem.setVisible(True)
            v.autoRange(padding=0)
            print(self._imageView.geometry())

    def _getThumb(self, index, height=64):
        """
        If the thumbnail stored in Image Cache
        :param index: QModelIndex
        :param height: height to scale the image
        """
        imgData = index.data(DATA_ROLE)

        return imgData

    def setLevels(self, levels):
        """
        Set levels for the image configuration.
        :param levels: (tupple) Minimum an maximum pixel values
        """
        self._levels = levels

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
    MarkerStyleItemDelegate class provides display and editing facilities for
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


