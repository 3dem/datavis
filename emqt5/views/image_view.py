#!/usr/bin/python
# -*- coding: utf-8 -*-

from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtWidgets import (QWidget, QToolBar, QAction, QHBoxLayout, QSplitter,
                             QTextEdit)
from PyQt5.QtGui import QColor, QPen

import qtawesome as qta
import pyqtgraph as pg


class ImageView(QWidget):
    """ The ImageView widget provides functionality for display images and
    performing basic operations over the view, such as: rotations, zoom, flips,
    move, levels. """

    def __init__(self, parent, **kwargs):
        """
        By default, ImageView show a toolbar for image operations.
        **Arguments**
        parent : (QWidget) Specifies the parent widget to which this ImageView
                 will belong. If None, then the ImageView is created with
                 no parent.
        tool_bar: (str) If specified, this will be used to set visible the
                  ToolBar. Possible values are "on"(by default) or "off"
        roi: (str) If specified, this will be used to set visible the
                  ROI button. Possible values are "on" or "off"(by default)
        menu: (str) If specified, this will be used to set visible the
                  Menu button. Possible values are "on" or "off"(by default)
        histogram: (str) If specified, this will be used to set visible the
                  Menu button. Possible values are "on"(by default) or "off"
        img_desc: (str) If specified, this will be used to set visible the
                  image description widget. Possible values are "on"(by default)
                  or "off"
        fit: (str) If specified, this will be used to automatically
                     auto-range the image whenever the view is resized.
                     Possible values are "on"(by default) or "off"
        back_color (str): The background color (example: '#BBAAFF')
        border_color (str): The border color (example: '#BBAAFF')

        """
        QWidget.__init__(self, parent=parent)

        self._oddFlips = False
        self._oddRotations = False
        self._isVerticalFlip = False
        self._isHorizontalFlip = False
        self._rotation_step = 90
        self._showToolBar = True
        self._showRoiBtn = False
        self._showMenuBtn = False
        self._showHistogram = False
        self._showPopup = False
        self._showImgDesc = False
        self._showXaxis = True
        self._showYaxis = True
        self._fitToSize = True
        self._autoFill = False
        self._pgButtons = None

        self.__setupUI(**kwargs)
        self.setup(**kwargs)

    def __setupUI(self, **kwargs):
        self._mainLayout = QHBoxLayout(self)
        self._mainLayout.setSpacing(0)
        self._mainLayout.setContentsMargins(1, 1, 1, 1)
        self._toolBar = QToolBar(self)
        self._toolBar.setOrientation(Qt.Vertical)
        self._fitToSizeAction = self.__createAction(parent=self,
                                                    actionName="Fit",
                                                    text="Fit to size",
                                                    faIconName="fa.crosshairs",
                                                    checkable=False,
                                                    slot=self.fitToSize)
        self._toolBar.addAction(self._fitToSizeAction)
        self._toolBar.addSeparator()
        self._rLeftAction = self.__createAction(parent=self,
                                                actionName="RLeft",
                                                text="Rotate Left",
                                                faIconName="fa.rotate-left",
                                                checkable=False,
                                                slot=self.__rotateLeft)
        self._toolBar.addAction(self._rLeftAction)
        self._mainLayout.addWidget(self._toolBar)
        self._rRightAction = self.__createAction(parent=self,
                                                 actionName="RRight",
                                                 text="Rotate Right",
                                                 faIconName="fa.rotate-right",
                                                 checkable=False,
                                                 slot=self.__rotateRight)
        self._toolBar.addAction(self._rRightAction)
        self._toolBar.addSeparator()
        self._hFlipAction = self.__createAction(parent=self,
                                                actionName="HFlip",
                                                text="Horizontal Flip",
                                                faIconName="fa.arrows-h",
                                                checkable=True,
                                                slot=self.horizontalFlip)
        self._toolBar.addAction(self._hFlipAction)
        self._vFlipAction = self.__createAction(parent=self,
                                                actionName="VFlip",
                                                text="Vertical Flip",
                                                faIconName="fa.arrows-v",
                                                checkable=True,
                                                slot=self.verticalFlip)
        self._toolBar.addAction(self._vFlipAction)
        self._toolBar.addSeparator()
        self._clearAction = self.__createAction(parent=self,
                                                actionName="Clear",
                                                text="Clear",
                                                faIconName="fa.trash-o",
                                                checkable=False,
                                                slot=self.clear)
        self._toolBar.addAction(self._clearAction)

        self._mainLayout.addWidget(self._toolBar)
        self._splitter = QSplitter(self)
        self._splitter.setOrientation(Qt.Vertical)
        self._imageView = pg.ImageView(parent=self._splitter,
                                       view=pg.PlotItem())
        v = self._imageView.getView()
        v.invertY(False)
        self._yInverted = False
        self._textEdit = QTextEdit(self._splitter)
        self._mainLayout.addWidget(self._splitter)

    def __createAction(self, parent, actionName, text="", faIconName=None,
                            checkable=False, slot=None):
        """
        Create a QAction with the given name, text and icon. If slot is not None
        then the signal QAction.triggered is connected to it
        :param actionName: The action name
        :param text: Action text
        :param faIconName: qtawesome icon name
        :param checkable: if this action is checkable
        :param slot: the slot to connect QAction.triggered signal
        :return: The QAction
        """
        a = QAction(parent)
        a.setObjectName(str(actionName))
        if faIconName:
            a.setIcon(qta.icon(faIconName))
        a.setCheckable(checkable)
        a.setText(str(text))

        if slot:
            a.triggered.connect(slot)
        return a

    def __setupImageView(self):
        """ Configure the pg.ImageView widget """
        self._imageView.ui.menuBtn.setVisible(self._showMenuBtn)
        self._imageView.ui.histogram.setVisible(self._showHistogram)
        self._imageView.ui.roiBtn.setVisible(self._showRoiBtn)
        view = self._imageView.getView()
        view.setMenuEnabled(self._showPopup)
        self._textEdit.setVisible(self._showImgDesc)
        self._toolBar.setVisible(self._showToolBar)
        plotItem = self._imageView.getView()

        if isinstance(plotItem, pg.PlotItem):
            if not self._pgButtons:
                plotItem.hideButtons()
            plotItem.setAutoFillBackground(self._autoFill)
            plotItem.showAxis('bottom', self._showXaxis)
            axis = plotItem.getAxis("bottom")
            axis.setAutoFillBackground(self._autoFill)
            axis.setZValue(0)
            plotItem.showAxis('left', self._showYaxis)
            axis = plotItem.getAxis("left")
            axis.setAutoFillBackground(self._autoFill)
            axis.setZValue(0)
            plotItem.showAxis('top', False)
            axis = plotItem.getAxis("top")
            axis.setZValue(0)
            axis.setAutoFillBackground(self._autoFill)

    def __resetOperationParams(self):
        """ Reset the image operations params """
        self._oddFlips = False
        self._oddRotations = False
        self._isVerticalFlip = False
        self._isHorizontalFlip = False
        self._vFlipAction.setChecked(False)
        self._hFlipAction.setChecked(False)

    @pyqtSlot()
    def __rotateLeft(self):
        """ Rotate the image 90 degrees to the left """
        self.rotate(-self._rotation_step)

    @pyqtSlot()
    def __rotateRight(self):
        """ Rotate the image 90 degrees to the right """
        self.rotate(self._rotation_step)

    def setup(self, **kwargs):
        """ Configure the ImageView. See constructor comments for the params """
        self._rotation_step = 90
        self._showToolBar = kwargs.get("tool_bar", "on") == "on"
        self._showRoiBtn = kwargs.get("roi", "off") == "on"
        self._showMenuBtn = kwargs.get("menu", "off") == "on"
        self._showHistogram = kwargs.get("histogram", "off") == "on"
        self._showPopup = kwargs.get("popup", "off") == "on"
        self._showImgDesc = kwargs.get("img_desc", "off") == "on"
        self._showXaxis = kwargs.get("axis", "on") == "on"
        self._showYaxis = kwargs.get("axis", "on") == "on"
        self._fitToSize = kwargs.get("fit", "on") == "on"
        self._autoFill = kwargs.get("auto_fill", "off") == "on"
        self._pgButtons = kwargs.get("hide_buttons", "off") == "on"
        self.__setupImageView()

    def setImage(self, image):
        """ Set the image to be displayed """
        self.clear()
        self._imageView.setImage(image, autoRange=self._fitToSize)

    @pyqtSlot(int)
    def rotate(self, angle):
        """
        Make a rotation according to the given angle (in degrees).
        Does not modify the image.
        """
        imgItem = self._imageView.getImageItem()
        if imgItem is not None:
            angle *= 1 if self._yInverted else -1
            self._oddRotations = not self._oddRotations
            # When only one of the flip is activated, we need to change
            # the rotation angle (XOR)
            if ((self._isHorizontalFlip and not self._isVerticalFlip) or
                    (not self._isHorizontalFlip and self._isVerticalFlip)):
                angle *= -1

            rect = imgItem.boundingRect()
            (centerX, centerY) = (rect.width()/2.0, rect.height()/2.0)
            imgItem.translate(centerX, centerY)
            imgItem.rotate(angle)
            imgItem.translate(-centerX, -centerY)

    @pyqtSlot()
    def horizontalFlip(self):
        """
        Realize a horizontally transformation-flip.
        Does not modify the image.
        """
        imgItem = self._imageView.getImageItem()
        if imgItem is not None:
            self._oddFlips = not self._oddFlips
            self._isHorizontalFlip = not self._isHorizontalFlip
            transform = imgItem.transform()
            if not self._oddRotations:
                transform.scale(-1.0, 1.0)
                transform.translate(-imgItem.boundingRect().width(), 0.0)
            else:
                transform.scale(1.0, -1.0)
                transform.translate(0.0, -imgItem.boundingRect().height())
            imgItem.setTransform(transform)

    @pyqtSlot()
    def verticalFlip(self):
        """
        Realize a vertically transformation-flip.
        Does not modify the image.
        """
        imgItem = self._imageView.getImageItem()
        if imgItem is not None:
            transform = imgItem.transform()
            self._oddFlips = not self._oddFlips
            self._isVerticalFlip = not self._isVerticalFlip
            if not self._oddRotations:
                transform.scale(1.0, -1.0)
                transform.translate(0.0, -imgItem.boundingRect().height())
            else:
                transform.scale(-1.0, 1.0)
                transform.translate(-imgItem.boundingRect().width(), 0.0)
            imgItem.setTransform(transform)

    @pyqtSlot()
    def clear(self):
        """ Clear the view, setting a null image """
        self.__resetOperationParams()
        self._imageView.clear()
        self.fitToSize()
        self._textEdit.setText("")

    @pyqtSlot()
    def fitToSize(self):
        """ Fit image to the widget size """
        self._imageView.getView().autoRange()

    def showToolBar(self, visible=True):
        """ Show or hide the tool bar """
        self._toolBar.setVisible(visible)

    def showMenuButton(self, visible=True):
        """ Show or hide the menu button """
        self._imageView.ui.menuBtn.setVisible(visible)

    def showRoiButton(self, visible=True):
        """ Show or hide the ROI button """
        self._imageView.ui.menuBtn.setVisible(visible)

    def showHistogram(self, visible=True):
        """ Show or hide the histogram widget """
        self._imageView.ui.histogram.setVisible(visible)

    def showImageDescription(self, visible=True):
        """ Show or hide the image description widget """
        self._textEdit.setVisible(visible)

    def setImageDescription(self, text):
        """
        Sets the image description that will be displayed in the lower part
        of the widget. The text may be in HTML format.
        """
        self._textEdit.setText(text)

    def getViewRect(self):
        """ Returns the view rect area """
        view = self._imageView.getView()
        if isinstance(view, pg.PlotItem):
            view = view.getViewBox()

        return view.viewRect()

    def getView(self):
        """ Retuens the internal widget used for display image """
        return self._imageView.getView()
