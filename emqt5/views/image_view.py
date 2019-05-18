#!/usr/bin/python
# -*- coding: utf-8 -*-

from PyQt5.QtCore import Qt, pyqtSlot, QEvent, QLineF
from PyQt5.QtWidgets import (QWidget, QLabel, QAction, QHBoxLayout, QSplitter,
                             QToolBar, QVBoxLayout, QPushButton, QSizePolicy,
                             QTextEdit, QDoubleSpinBox)

import qtawesome as qta
import pyqtgraph as pg

from emqt5.widgets import ToolBar, MultiStateAction


class ImageView(QWidget):
    """ The ImageView widget provides functionality for display images and
    performing basic operations over the view, such as: rotations, zoom, flips,
    move, levels. """

    AXIS_TOP_LEFT = 0  # axis in top-left
    AXIS_TOP_RIGHT = 1  # axis in top-right
    AXIS_BOTTOM_RIGHT = 2  # axis in bottom-right
    AXIS_BOTTOM_LEFT = 3  # axis in bottom-left
    AXIS_ON = 4  # axis is on (visible)
    AXIS_OFF = 5  # axis is off (not visible)

    HIST_ON = 1  # histogram is on (visible)
    HIST_OFF = 2  # histogram is off (not visible)

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
        auto_fill: (str) This property holds whether the widget background
                         is filled automatically. The color used is defined by
                         the QPalette::Window color role from the widget's
                         palette. Possible values are "on" or "off" (by default)
        hide_buttons: (str) Hide/show the internal pg buttons. For example,
                            the button used to center an image. Possible values
                            are "on" or "off" (by default)
        axis_pos: (str) The axis position. Possible values: bottom-left,
                        bottom-right, top-left, top-right
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
        self._axisPos = self.AXIS_BOTTOM_LEFT
        self._scale = 1

        self.__setupUI(**kwargs)
        self.setup(**kwargs)

    def __setupUI(self, **kwargs):

        self._mainLayout = QHBoxLayout(self)
        self._mainLayout.setSpacing(0)
        self._mainLayout.setContentsMargins(1, 1, 1, 1)

        self._imageView = pg.ImageView(parent=self,
                                       view=pg.PlotItem())
        self._imageView.installEventFilter(self)
        self._splitter = QSplitter(self)
        self._toolBar = ToolBar(self, orientation=Qt.Vertical)
        self._splitter.addWidget(self._toolBar)
        self._splitter.setCollapsible(0, False)
        self._splitter.addWidget(self._imageView)

        self._toolBar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self._displayPanel = self._toolBar.createSidePanel()
        self._displayPanel.setObjectName('displayPanel')
        self._displayPanel.setStyleSheet(
            'QWidget#displayPanel{border-left: 1px solid lightgray;}')
        self._displayPanel.setSizePolicy(QSizePolicy.Ignored,
                                         QSizePolicy.Ignored)
        vLayout = QVBoxLayout(self._displayPanel)
        self._labelScale = QLabel('Scale: ', self._displayPanel)
        hLayout = QHBoxLayout()
        hLayout.addWidget(self._labelScale)
        self._spinBoxScale = QDoubleSpinBox(self._displayPanel)
        self._spinBoxScale.setSuffix(" %")
        self._spinBoxScale.setRange(0, 10000)
        self._spinBoxScale.editingFinished.connect(
            self.__onSpinBoxScaleValueChanged)
        hLayout.addWidget(self._spinBoxScale)
        hLayout.addStretch()
        vLayout.addLayout(hLayout)
        view = self.getView().getViewBox()
        view.sigStateChanged.connect(
            self.__onImageScaleChanged)
        # --Histogram--
        toolbar = QToolBar(self._displayPanel)
        toolbar.addWidget(QLabel('Histogram ', toolbar))
        self._actHistOnOff = MultiStateAction(
            toolbar, states=[(True, qta.icon('fa.toggle-on'), 'On'),
                             (False, qta.icon('fa.toggle-off'), 'Off')])
        self._actHistOnOff.set(self._showHistogram)
        self._actHistOnOff.stateChanged.connect(
            self.__actHistogramOnOffTriggered)

        toolbar.addAction(self._actHistOnOff)
        maxWidth = toolbar.sizeHint().width() + toolbar.iconSize().width()
        vLayout.addWidget(toolbar)
        # --End-Histogram--
        # --Axis--
        toolbar = QToolBar(self._displayPanel)
        toolbar.addWidget(QLabel('Axis ', toolbar))
        self._actAxis = MultiStateAction(toolbar)
        self._actAxis.add(self.AXIS_BOTTOM_LEFT,
                          qta.icon('fa.long-arrow-up',
                                        'fa.long-arrow-right',
                                        options=[{'offset': (-0.3, 0),
                                                  'scale_factor': 0.8},
                                                 {'offset': (0, 0.3),
                                                  'scale_factor': 0.8}
                                                 ]))
        self._actAxis.add(self.AXIS_TOP_LEFT,
                          qta.icon('fa.long-arrow-down',
                                        'fa.long-arrow-right',
                                        options=[{'offset': (-0.3, 0),
                                                  'scale_factor': 0.8},
                                                 {'offset': (0, -0.3),
                                                  'scale_factor': 0.8}
                                                 ]))
        self._actAxis.setText('Axis origin')
        self._actAxis.set(self.AXIS_BOTTOM_LEFT)
        self._actAxis.triggered.connect(self.__actAxisTriggered)
        toolbar.addAction(self._actAxis)
        self._actAxisOnOff = MultiStateAction(toolbar)
        self._actAxisOnOff.add(self.AXIS_ON, qta.icon('fa.toggle-on'))
        self._actAxisOnOff.add(self.AXIS_OFF, qta.icon('fa.toggle-off'))

        if self._showXaxis:
            self._actAxisOnOff.set(self.AXIS_ON)
            self._actAxisOnOff.setToolTip("On")
        else:
            self._actAxisOnOff.set(self.AXIS_OFF)
            self._actAxisOnOff.setToolTip("Off")

        self._actAxisOnOff.triggered.connect(self.__actAxisOnOffTriggered)
        toolbar.addAction(self._actAxisOnOff)
        maxWidth = max(maxWidth,
                       toolbar.sizeHint().width() + toolbar.iconSize().width())
        vLayout.addWidget(toolbar)
        # --End-Axis--
        # --Flip--
        toolbar = QToolBar(self._displayPanel)
        toolbar.addWidget(QLabel('Flip ', toolbar))
        self._actHorFlip = self.__createAction(parent=toolbar,
                                               actionName="HFlip",
                                               text="Horizontal Flip",
                                               icon=qta.icon(
                                                   'fa.long-arrow-right',
                                                   'fa.long-arrow-left',
                                                   options=[
                                                       {'offset': (0, 0.2)},
                                                       {'offset': (0, -0.2)}]),
                                               checkable=True,
                                               slot=self.horizontalFlip)

        toolbar.addAction(self._actHorFlip)
        self._actVerFlip = self.__createAction(parent=toolbar,
                                               actionName="VFlip",
                                               text="Vertical Flip",
                                               icon=qta.icon(
                                                   'fa.long-arrow-up',
                                                   'fa.long-arrow-down',
                                                   options=[
                                                       {'offset': (0.2, 0)},
                                                       {'offset': (-0.2, 0)}]),
                                               checkable=True,
                                               slot=self.verticalFlip)
        toolbar.addAction(self._actVerFlip)
        maxWidth = max(maxWidth,
                       toolbar.sizeHint().width()) + toolbar.iconSize().width()
        vLayout.addWidget(toolbar)
        # --End-Flip--
        # --Rotate--
        toolbar = QToolBar(self._displayPanel)
        toolbar.addWidget(QLabel('Rotate ', toolbar))
        self._actRightRot = self.__createAction(parent=toolbar,
                                                actionName="RRight",
                                                text="Rotate Right",
                                                faIconName="fa.rotate-right",
                                                checkable=False,
                                                slot=self.__rotateRight)
        toolbar.addAction(self._actRightRot)
        self._actLeftRot = self.__createAction(parent=toolbar,
                                               actionName="RLeft",
                                               text="Rotate Left",
                                               faIconName="fa.rotate-left",
                                               checkable=False,
                                               slot=self.__rotateLeft)
        toolbar.addAction(self._actLeftRot)
        maxWidth = max(maxWidth,
                       toolbar.sizeHint().width() + toolbar.iconSize().width())
        vLayout.addWidget(toolbar)
        # --End-Rotate--
        # --Adjust--
        self._btnAdjust = QPushButton(self._displayPanel)
        self._btnAdjust.setText('Adjust')
        self._btnAdjust.setIcon(qta.icon('fa.crosshairs'))
        self._btnAdjust.setToolTip('Adjust image to the view')
        self._btnAdjust.pressed.connect(self.fitToSize)
        vLayout.addWidget(self._btnAdjust)
        # --End-Adjust--
        # --Reset--
        self._btnReset = QPushButton(self._displayPanel)
        self._btnReset.setText('Reset')
        self._btnReset.setToolTip('Reset image operations')
        self._btnReset.setIcon(qta.icon('fa.mail-reply-all'))
        self._btnReset.pressed.connect(self.__resetView)
        vLayout.addWidget(self._btnReset)
        # --End-Reset--
        vLayout.addStretch()
        self._displayPanel.setFixedHeight(260)
        self._actDisplay = QAction(None)
        self._actDisplay.setIcon(qta.icon('fa.adjust'))
        self._actDisplay.setText('Display')
        #  setting a reasonable width for display panel
        self._displayPanel.setGeometry(0, 0, maxWidth,
                                       self._displayPanel.height())
        self._toolBar.addAction(self._actDisplay, self._displayPanel,
                                exclusive=False)
        # --File-Info--
        self._fileInfoPanel = self._toolBar.createSidePanel()
        self._fileInfoPanel.setObjectName('fileInfoPanel')
        self._fileInfoPanel.setStyleSheet(
            'QWidget#fileInfoPanel{border-left: 1px solid lightgray;}')
        self._fileInfoPanel.setSizePolicy(QSizePolicy.Ignored,
                                          QSizePolicy.Minimum)
        vLayout = QVBoxLayout(self._fileInfoPanel)
        self._textEditPath = QTextEdit(self._fileInfoPanel)
        self._textEditPath.viewport().setAutoFillBackground(False)

        vLayout.addWidget(self._textEditPath)
        self._fileInfoPanel.setMinimumHeight(30)

        self._actFileInfo = QAction(None)
        self._actFileInfo.setIcon(qta.icon('fa.info-circle'))
        self._actFileInfo.setText('File Info')
        self._toolBar.addAction(self._actFileInfo, self._fileInfoPanel,
                                exclusive=False)
        # --End-File-Info--

        self._mainLayout.addWidget(self._splitter)

    def __createAction(self, parent, actionName, text="", faIconName=None,
                       icon=None, checkable=False, slot=None):
        """
        Create a QAction with the given name, text and icon. If slot is not None
        then the signal QAction.triggered is connected to it
        :param actionName: The action name
        :param text: Action text
        :param faIconName: qtawesome icon name
        :param icon: QIcon (used if faIconName=None)
        :param checkable: if this action is checkable
        :param slot: the slot to connect QAction.triggered signal
        :return: The QAction
        """
        a = QAction(parent)
        a.setObjectName(str(actionName))
        if faIconName:
            a.setIcon(qta.icon(faIconName))
        elif icon is not None:
            a.setIcon(icon)

        a.setCheckable(checkable)
        a.setText(str(text))

        if slot:
            a.triggered.connect(slot)
        return a

    def setAxisOrientation(self, orientation):
        """
        Sets the axis orientation for this ImageView. Possible values are:
         AXIS_TOP_LEFT :axis in top-left
         AXIS_TOP_RIGHT :axis in top-right
         AXIS_BOTTOM_RIGHT :axis in bottom-right
         AXIS_BOTTOM_LEFT :axis in bottom-left
         """
        self._axisPos = orientation
        self.__setupAxis()

    def __setupAxis(self):
        plotItem = self._imageView.getView()
        viewBox = plotItem

        if isinstance(plotItem, pg.PlotItem):
            viewBox = viewBox.getViewBox()
            if self._axisPos == self.AXIS_BOTTOM_LEFT:
                if viewBox.yInverted():
                    plotItem.invertY(False)
                    viewBox.sigYRangeChanged.emit(
                        viewBox, tuple(viewBox.state['viewRange'][1]))
                if viewBox.xInverted():
                    plotItem.invertX(False)
                bottom = True and self._showXaxis
                left = True and self._showYaxis
                right = False
                top = False
            elif self._axisPos == self.AXIS_TOP_LEFT:
                if not viewBox.yInverted():
                    plotItem.invertY(True)
                    viewBox.sigYRangeChanged.emit(
                        viewBox, tuple(viewBox.state['viewRange'][1]))
                if viewBox.xInverted():
                    plotItem.invertX(False)
                bottom = False
                left = True and self._showYaxis
                right = False
                top = True and self._showXaxis
            elif self._axisPos == self.AXIS_TOP_RIGHT:
                if not viewBox.xInverted():
                    plotItem.invertX(True)
                bottom = False
                left = False
                right = True and self._showYaxis
                top = True and self._showXaxis
            else:  # self.AXIS_BOTTOM_RIGHT:
                if viewBox.yInverted():
                    plotItem.invertY(False)
                    viewBox.sigYRangeChanged.emit(
                        viewBox, tuple(viewBox.state['viewRange'][0]))
                bottom = True and self._showXaxis
                left = False
                right = True and self._showYaxis
                top = False

            if not self._pgButtons:
                plotItem.hideButtons()

            plotItem.setAutoFillBackground(self._autoFill)

            plotItem.showAxis('bottom', bottom)
            if bottom:
                axis = plotItem.getAxis("bottom")
                axis.setAutoFillBackground(self._autoFill)
                axis.setZValue(0)
                axis.linkedViewChanged(viewBox)

            plotItem.showAxis('left', left)
            if left:
                axis = plotItem.getAxis("left")
                axis.setAutoFillBackground(self._autoFill)
                axis.setZValue(0)
                axis.linkedViewChanged(viewBox)

            plotItem.showAxis('top', top)
            if top:
                axis = plotItem.getAxis("top")
                axis.setZValue(0)
                axis.setAutoFillBackground(self._autoFill)
                axis.linkedViewChanged(viewBox)

            plotItem.showAxis('right', right)
            if right:
                axis = plotItem.getAxis("right")
                axis.setZValue(0)
                axis.setAutoFillBackground(self._autoFill)
                axis.linkedViewChanged(viewBox)

    def __imageViewKeyPressEvent(self, ev):
        if ev.key() == Qt.Key_H:
            self.__actHistogramOnOffTriggered(True)

        if ev.key() == Qt.Key_A:
            self.__actAxisOnOffTriggered(True)

    def __setupImageView(self):
        """ Configure the pg.ImageView widget """
        self._imageView.ui.menuBtn.setVisible(self._showMenuBtn)
        self._imageView.ui.histogram.setVisible(self._showHistogram)
        self._imageView.ui.roiBtn.setVisible(self._showRoiBtn)
        view = self._imageView.getView()
        view.setMenuEnabled(self._showPopup)
        self._toolBar.setVisible(self._showToolBar)
        self.__setupAxis()

    def __resetOperationParams(self):
        """ Reset the image operations params """
        self._oddFlips = False
        self._oddRotations = False
        self._isVerticalFlip = False
        self._isHorizontalFlip = False
        self._actVerFlip.setChecked(False)
        self._actHorFlip.setChecked(False)

    @pyqtSlot()
    def __resetView(self):
        self.__resetOperationParams()
        self.setImage(self._imageView.image)

    @pyqtSlot(bool)
    def __actAxisTriggered(self, checked):
        """ This slot is invoked when the action histogram is triggered """
        self._actAxis.next()
        self.setAxisOrientation(self._actAxis.get())

    @pyqtSlot(int)
    def __actHistogramOnOffTriggered(self, state):
        """ This slot is invoked when the action histogram is triggered """
        self._imageView.ui.histogram.setVisible(bool(state))

    @pyqtSlot(bool)
    def __actAxisOnOffTriggered(self, checked):
        """ This slot is invoked when the action histogram is triggered """
        self._actAxisOnOff.next()
        self._showXaxis = self._actAxisOnOff.get() == self.AXIS_ON
        self._showYaxis = self._showXaxis
        self._actAxisOnOff.setToolTip("On" if self._showXaxis else "Off")
        self.__setupAxis()

    @pyqtSlot()
    def __rotateLeft(self):
        """ Rotate the image 90 degrees to the left """
        self.rotate(-self._rotation_step)

    @pyqtSlot()
    def __rotateRight(self):
        """ Rotate the image 90 degrees to the right """
        self.rotate(self._rotation_step)

    @pyqtSlot()
    def __onSpinBoxScaleValueChanged(self):
        viewBox = self.getViewBox()
        val = self._spinBoxScale.value() * 0.01
        if val == 0:
            self._spinBoxScale.setValue(self._scale * 100)
        else:
            viewBox.scaleBy(x=self._scale, y=self._scale)  # restore to 100 %
            viewBox.scaleBy(x=1/val, y=1/val)  # to current scale

    @pyqtSlot(object)
    def __onImageScaleChanged(self, view):
        """ Invoked when the image scale has changed """
        rect = self._imageView.imageItem.boundingRect()
        if isinstance(view, pg.ViewBox) and rect.width() > 0:
            p1 = pg.Point(0, 0)
            p2 = pg.Point(0, 1)
            p1v = view.mapFromView(p1)
            p2v = view.mapFromView(p2)
            linev = QLineF(p1v.x(), p1v.y(), p2v.x(), p2v.y())
            self._scale = abs(linev.dy())
            self._spinBoxScale.setValue(self._scale * 100)

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

        pos = {
            "bottom-left": self.AXIS_BOTTOM_LEFT,
            "bottom-right": self.AXIS_BOTTOM_RIGHT,
            "top-left": self.AXIS_TOP_LEFT,
            "top-right": self.AXIS_TOP_RIGHT
        }

        self._axisPos = pos.get(kwargs.get("axis_pos", "bottom-left"),
                                self.AXIS_BOTTOM_LEFT)
        self.__setupImageView()

    def getViewBox(self):
        """ Return the pyqtgraph.ViewBox """
        view = self._imageView.getView()
        if isinstance(view, pg.PlotItem):
            view = view.getViewBox()
        return view

    def setImage(self, image):
        """ Set the image to be displayed """
        self.clear()
        self._imageView.setImage(image, autoRange=self._fitToSize)
        self.fitToSize()

    @pyqtSlot(int)
    def rotate(self, angle):
        """
        Make a rotation according to the given angle (in degrees).
        Does not modify the image.
        """
        imgItem = self._imageView.getImageItem()

        if imgItem is not None:
            angle *= 1 if self.getViewBox().yInverted() else -1
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
        self._textEditPath.setText("")

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

    def setImageInfo(self, **kwargs):
        """
        Sets the image info that will be displayed.
        **kwargs:
            text: (str) if passed, it will be used as the info
                to be displayed, if not, other arguments are considered
            path : (str) the image path
            format: (str) the image format
            data_type: (str) the image data type
        """
        text = kwargs.get('text', None)
        if text is None:
            text = ("<p><strong>Path: </strong>%s</p>"
                    "<p><strong>Format: </strong>%s</p>"
                    "<p><strong>Type: </strong>%s</p>")
            text = text % (kwargs.get('path', ''),
                           kwargs.get('format', ''),
                           kwargs.get('data_type', '').replace("<", "&lt;").
                           replace(">", "&gt;"))
        print("Setting text: %s" % text)
        self._textEditPath.setText(text)

    def getViewRect(self):
        """ Returns the view rect area """
        view = self._imageView.getView()
        if isinstance(view, pg.PlotItem):
            view = view.getViewBox()

        return view.viewRect()

    def getView(self):
        """ Returns the internal widget used for display image """
        return self._imageView.getView()

    def setViewSize(self, x, y, width, height):
        """ Sets the view size """
        # TODO review
        tw = self._toolBar.width() if self._showToolBar else 0
        th = self._toolBar.height() if self._showToolBar else 0
        hw = self._imageView.ui.histogram.item.width() \
            if self._showHistogram else 0

        plot = self._imageView.getView()
        if isinstance(plot, pg.PlotItem):
            if self._showXaxis:
                height += plot.getAxis("bottom").height()
            if self._showYaxis:
                width += plot.getAxis("left").height()

        self._imageView.setGeometry(x, y, width, height)

    def getViewSize(self):
        """ Returns the image view size. """
        hw = self._imageView.ui.histogram.item.width() \
            if self._showHistogram else 0

        plot = self._imageView.getView()
        width = plot.width() - hw
        height = plot.height()
        if isinstance(plot, pg.PlotItem):
            if self._showXaxis:
                height -= plot.getAxis("bottom").height()
            if self._showYaxis:
                width -= plot.getAxis("left").height()

        return width, height

    def getImageItem(self):
        """ See pyqtgraph.ImageView.getImageItem """
        return self._imageView.getImageItem()

    def getToolBar(self):
        return self._toolBar

    def eventFilter(self, obj, event):
        """
        Filters events if this object has been installed as an event filter for
        the watched object
        :param obj: watched object
        :param event: event
        :return: True if this object has been installed, False i.o.c
        """

        if event.type() == QEvent.KeyPress:
            self.__imageViewKeyPressEvent(event)
            return True

        return QWidget.eventFilter(self, obj, event)
