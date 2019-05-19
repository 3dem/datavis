#!/usr/bin/python
# -*- coding: utf-8 -*-

import pyqtgraph as pg
import qtawesome as qta
from PyQt5.QtCore import Qt, pyqtSlot, QEvent, QLineF
from PyQt5.QtWidgets import (QWidget, QLabel, QAction, QHBoxLayout, QSplitter,
                             QToolBar, QVBoxLayout, QPushButton, QSizePolicy,
                             QTextEdit, QDoubleSpinBox)

from emqt5.widgets import ActionsToolBar, MultiStateAction, OnOffAction


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
        parent :   (QWidget) Specifies the parent widget to which this ImageView
                   will belong. If None, then the ImageView is created with
                   no parent.
        toolBar:   (Bool) If specified, this will be used to set visible the
                   ToolBar. By default, the toolbar is visible.
        roi:       (Bool) If specified, this will be used to set visible the
                   ROI button. False by default.
        menu:      (Bool) If specified, this will be used to set visible the
                   Menu button. False by default.
        histogram: (Bool) If specified, this will be used to set visible the
                   Menu button. True by default.
        fit:       (Bool) If specified, this will be used to automatically
                   auto-range the image whenever the view is resized.
                   True by default.
        autoFill:  (Bool) This property holds whether the widget background
                   is filled automatically. The color used is defined by
                   the QPalette::Window color role from the widget's palette.
                   False by default.
        hideButtons: (Bool) Hide/show the internal pg buttons. For example,
                     the button used to center an image. False by default.
        axisPos:   (Bool) The axis position.
                   Possible values:  AXIS_TOP_LEFT, AXIS_TOP_RIGHT,
                   AXIS_BOTTOM_RIGHT, AXIS_BOTTOM_LEFT
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
        self._showXaxis = True
        self._showYaxis = True
        self._fitToSize = True
        self._autoFill = False
        self._pgButtons = None
        self._axisPos = self.AXIS_BOTTOM_LEFT
        self._scale = 1

        self.__setupUI()
        self.setup(**kwargs)

    def __readKwargs(self, **kwargs):
        """
        Reads all kwargs params. This is the standard function for read kwargs
        in all classes.
        :param kwargs: See the constructor params
        """
        self._rotation_step = 90
        self._showToolBar = kwargs.get("toolBar", True)
        self._showRoiBtn = kwargs.get("roi", False)
        self._showMenuBtn = kwargs.get("menu", False)
        self._showHistogram = kwargs.get("histogram", False)
        self._showPopup = kwargs.get("popup", False)
        self._showXaxis = kwargs.get("axis", True)
        self._showYaxis = kwargs.get("axis", True)
        self._fitToSize = kwargs.get("fit", True)
        self._autoFill = kwargs.get("autoFill", False)
        self._pgButtons = kwargs.get("hideButtons", False)
        self._axisPos = kwargs.get("axisPos", self.AXIS_BOTTOM_LEFT)

    def __setupUI(self):
        """
        Setups the user interface
        """
        self._mainLayout = QHBoxLayout(self)
        self._mainLayout.setSpacing(0)
        self._mainLayout.setContentsMargins(1, 1, 1, 1)

        self._imageView = pg.ImageView(parent=self,
                                       view=pg.PlotItem())
        self._imageView.installEventFilter(self)
        self._splitter = QSplitter(self)
        self._toolBar = ActionsToolBar(self, orientation=Qt.Vertical)
        self._splitter.addWidget(self._toolBar)
        self._splitter.setCollapsible(0, False)
        self._splitter.addWidget(self._imageView)

        displayPanel = self._toolBar.createPanel('displayPanel')
        vLayout = QVBoxLayout(displayPanel)
        self._labelScale = QLabel('Scale: ', displayPanel)
        hLayout = QHBoxLayout()
        hLayout.addWidget(self._labelScale)
        self._spinBoxScale = QDoubleSpinBox(displayPanel)
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

        # --Histogram On/Off--
        toolbar = QToolBar(displayPanel)
        toolbar.addWidget(QLabel('Histogram ', toolbar))
        self._actHistOnOff = OnOffAction()
        self._actHistOnOff.set(self._showHistogram)
        self._actHistOnOff.stateChanged.connect(self.__actHistOnOffChanged)
        toolbar.addAction(self._actHistOnOff)
        vLayout.addWidget(toolbar)

        # -- Axis --
        toolbar = QToolBar(displayPanel)
        toolbar.addWidget(QLabel('Axis ', toolbar))
        actAxis = MultiStateAction(
            toolbar, states=[(self.AXIS_BOTTOM_LEFT,
                              qta.icon('fa.long-arrow-up',
                                       'fa.long-arrow-right',
                                       options=[{'offset': (-0.3, 0),
                                                 'scale_factor': 0.8},
                                                {'offset': (0, 0.3),
                                                 'scale_factor': 0.8}
                                                ]), ''),
                             (self.AXIS_TOP_LEFT,
                              qta.icon('fa.long-arrow-down',
                                       'fa.long-arrow-right',
                                       options=[{'offset': (-0.3, 0),
                                                 'scale_factor': 0.8},
                                                {'offset': (0, -0.3),
                                                 'scale_factor': 0.8}
                                                ]), '')])
        actAxis.setText('Axis origin')
        actAxis.set(self.AXIS_BOTTOM_LEFT)
        actAxis.stateChanged.connect(self.__actAxisTriggered)
        toolbar.addAction(actAxis)

        # -- Axis On/Off --
        actAxisOnOff = OnOffAction(toolbar)
        actAxisOnOff.set(self._showXaxis)
        actAxisOnOff.stateChanged.connect(self.__actAxisOnOffTriggered)
        toolbar.addAction(actAxisOnOff)
        vLayout.addWidget(toolbar)

        # -- Flip --
        toolbar = QToolBar(displayPanel)
        toolbar.addWidget(QLabel('Flip ', toolbar))
        self._actHorFlip = self.__createAction(
            parent=toolbar, actionName="HFlip", text="Horizontal Flip",
            icon=qta.icon('fa.long-arrow-right', 'fa.long-arrow-left',
                          options=[{'offset': (0, 0.2)},
                                   {'offset': (0, -0.2)}]),
            checkable=True, slot=self.horizontalFlip)

        self._actVerFlip = self.__createAction(
            parent=toolbar, actionName="VFlip", text="Vertical Flip",
            icon=qta.icon('fa.long-arrow-up', 'fa.long-arrow-down',
                          options=[{'offset': (0.2, 0)},
                                   {'offset': (-0.2, 0)}]),
            checkable=True, slot=self.verticalFlip)
        vLayout.addWidget(toolbar)

        # --Rotate--
        toolbar = QToolBar(displayPanel)
        toolbar.addWidget(QLabel('Rotate ', toolbar))
        self.__createAction(parent=toolbar, actionName="RRight",
                            text="Rotate Right", faIconName="fa.rotate-right",
                            checkable=False, slot=self.__rotateRight)
        self.__createAction(parent=toolbar, actionName="RLeft",
                            text="Rotate Left", faIconName="fa.rotate-left",
                            checkable=False, slot=self.__rotateLeft)
        vLayout.addWidget(toolbar)

        # --Adjust--
        btnAdjust = QPushButton(displayPanel)
        btnAdjust.setText('Adjust')
        btnAdjust.setIcon(qta.icon('fa.crosshairs'))
        btnAdjust.setToolTip('Adjust image to the view')
        btnAdjust.pressed.connect(self.fitToSize)
        vLayout.addWidget(btnAdjust)

        # --Reset--
        btnReset = QPushButton(displayPanel)
        btnReset.setText('Reset')
        btnReset.setToolTip('Reset image operations')
        btnReset.setIcon(qta.icon('fa.mail-reply-all'))
        btnReset.pressed.connect(self.__resetView)
        vLayout.addWidget(btnReset)

        vLayout.addStretch()
        displayPanel.setFixedHeight(260)
        actDisplay = QAction(None)
        actDisplay.setIcon(qta.icon('fa.adjust'))
        actDisplay.setText('Display')

        self._toolBar.addAction(actDisplay, displayPanel, exclusive=False)
        # --File-Info--
        fileInfoPanel = self._toolBar.createPanel('fileInfoPanel')
        fileInfoPanel.setSizePolicy(QSizePolicy.Ignored,
                                    QSizePolicy.Minimum)
        vLayout = QVBoxLayout(fileInfoPanel)
        self._textEditPath = QTextEdit(fileInfoPanel)
        self._textEditPath.viewport().setAutoFillBackground(False)

        vLayout.addWidget(self._textEditPath)
        fileInfoPanel.setMinimumHeight(30)

        actFileInfo = QAction(None)
        actFileInfo.setIcon(qta.icon('fa.info-circle'))
        actFileInfo.setText('File Info')
        self._toolBar.addAction(actFileInfo, fileInfoPanel, exclusive=False)
        # --End-File-Info--

        self._mainLayout.addWidget(self._splitter)

    def __createAction(self, parent, actionName, text="", faIconName=None,
                       icon=None, checkable=False, slot=None):
        """
        Create a QAction with the given name, text and icon. If slot is not None
        then the signal QAction.triggered is connected to it
        :param actionName:   (str) The action name
        :param text:         (str) Action text
        :param faIconName:   (str) qtawesome icon name
        :param icon:         (QIcon) used if faIconName=None
        :param checkable:    (Bool) if this action is checkable
        :param slot:         (slot) the slot to connect QAction.triggered signal
        :return: The created QAction
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

        parent.addAction(a)
        return a

    def __setupAxis(self):
        """
        Setups the axis according to the axis orientation.
        See setAxisOrientation method.
        """
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

            if self._pgButtons:
                plotItem.hideButtons()
            else:
                plotItem.showButtons()

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
        """ Handles the key press event """
        if ev.key() == Qt.Key_H:
            self.__actHistOnOffChanged(True)

        if ev.key() == Qt.Key_A:
            self.__actAxisOnOffTriggered(True)

    def __setupImageView(self):
        """
        Setups the pg.ImageView widget according to the internal
        configuration params
        """
        self._imageView.ui.menuBtn.setVisible(self._showMenuBtn)
        self._imageView.ui.histogram.setVisible(self._showHistogram)
        self._imageView.ui.roiBtn.setVisible(self._showRoiBtn)
        view = self._imageView.getView()
        view.setMenuEnabled(self._showPopup)
        self._toolBar.setVisible(self._showToolBar)
        self.__setupAxis()

    def __resetOperationParams(self):
        """ Reset the image operations params (rotations and flips) """
        self._oddFlips = False
        self._oddRotations = False
        self._isVerticalFlip = False
        self._isHorizontalFlip = False
        self._actVerFlip.setChecked(False)
        self._actHorFlip.setChecked(False)

    @pyqtSlot()
    def __resetView(self):
        """
        Resets the view. The image operations (flips, rotations)
        will be reverted to their initial state
        """
        self.__resetOperationParams()
        self.setImage(self._imageView.image)

    @pyqtSlot(int)
    def __actAxisTriggered(self, state):
        """ This slot is invoked when the action histogram is triggered """
        self.setAxisOrientation(state)

    @pyqtSlot(int)
    def __actHistOnOffChanged(self, state):
        """ This slot is invoked when the action histogram is triggered """
        self._imageView.ui.histogram.setVisible(bool(state))

    @pyqtSlot(int)
    def __actAxisOnOffTriggered(self, state):
        """ This slot is invoked when the action histogram is triggered """
        self._showYaxis = self._showXaxis = bool(state)
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
        """
        This slot is invoked when the spinbox value for image scale is changed
        """
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

    def setAxisOrientation(self, orientation):
        """
        Sets the axis orientation for this ImageView.
        Possible values are:
            AXIS_TOP_LEFT :axis in top-left
            AXIS_TOP_RIGHT :axis in top-right
            AXIS_BOTTOM_RIGHT :axis in bottom-right
            AXIS_BOTTOM_LEFT :axis in bottom-left
         """
        self._axisPos = orientation
        self.__setupAxis()

    def setup(self, **kwargs):
        """ Configure the ImageView. See constructor comments for the params """
        self.__readKwargs(**kwargs)
        self.__setupImageView()

    def getViewBox(self):
        """ Return the pyqtgraph.ViewBox """
        view = self._imageView.getView()
        if isinstance(view, pg.PlotItem):
            view = view.getViewBox()
        return view

    def setImage(self, image):
        """
        Set the image to be displayed
        :param image: (numpy array) The image to be displayed
        """
        self.clear()
        self._imageView.setImage(image, autoRange=self._fitToSize)
        self.fitToSize()

    @pyqtSlot(int)
    def rotate(self, angle):
        """
        Make a rotation according to the given angle.
        Does not modify the image.
        :param angle: (int) The angle(in degrees)
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
        """
        Show or hide the tool bar
        :param visible: (Bool) Visible state
        """
        self._toolBar.setVisible(visible)

    def showMenuButton(self, visible=True):
        """
        Show or hide the menu button
        :param visible: (Bool) Visible state
        """
        self._imageView.ui.menuBtn.setVisible(visible)

    def showRoiButton(self, visible=True):
        """
        Show or hide the ROI button
        :param visible: (Bool) Visible state
        """
        self._imageView.ui.menuBtn.setVisible(visible)

    def showHistogram(self, visible=True):
        """
        Show or hide the histogram widget
        :param visible: (Bool) Visible state
        """
        self._imageView.ui.histogram.setVisible(visible)

    def setImageInfo(self, **kwargs):
        """
        Sets the image info that will be displayed.
        **kwargs:
            text:     (str) if passed, it will be used as the info
                      to be displayed, if not, other arguments are considered
            path :    (str) the image path
            format:   (str) the image format
            dataType: (str) the image data type
        """
        text = kwargs.get('text', None)
        if text is None:
            text = ("<p><strong>Path: </strong>%s</p>"
                    "<p><strong>Format: </strong>%s</p>"
                    "<p><strong>Type: </strong>%s</p>")
            text = text % (kwargs.get('path', ''),
                           kwargs.get('format', ''),
                           kwargs.get('dataType', '').replace("<", "&lt;").
                           replace(">", "&gt;"))
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
        """ Getter for left toolbar """
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
