#!/usr/bin/python
# -*- coding: utf-8 -*-

import pyqtgraph as pg
from pyqtgraph.exporters import ImageExporter as pgImageExporter
from pyqtgraph import functions as fn
from pyqtgraph import USE_PYSIDE

import qtawesome as qta
import numpy as np

import PyQt5.QtCore as qtc
import PyQt5.QtWidgets as qtw
import PyQt5.QtGui as qtg

from .. import widgets
from .. import models
from ._constants import (AXIS_BOTTOM_LEFT, AXIS_TOP_LEFT, AXIS_TOP_RIGHT,
                         CIRCLE_ROI)


class ImageView(qtw.QWidget):
    """ The ImageView widget provides functionality for display images and
    performing basic operations over the view, such as: rotations, zoom, flips,
    move, levels. """

    """ Signal emitted when the image scale is changed """
    sigScaleChanged = qtc.pyqtSignal(float)

    """ Signal for roi mask size changed"""
    sigMaskSizeChanged = qtc.pyqtSignal(int)

    def __init__(self, parent, model=None, **kwargs):
        """
        By default, ImageView show a toolbar for image operations.
        **Arguments**
        parent :   (qtw.QWidget) Specifies the parent widget to which this
                   ImageView will belong. If None, then the ImageView is
                   created with no parent.
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
                   the qtg.QPalette::Window color role from the widget's palette.
                   False by default.
        hideButtons: (Bool) Hide/show the internal pg buttons. For example,
                     the button used to center an image. False by default.
        axisPos:   (Bool) The axis position.
                   Possible values:  AXIS_TOP_LEFT, AXIS_TOP_RIGHT,
                   AXIS_BOTTOM_RIGHT, AXIS_BOTTOM_LEFT
        axisColor  (str) The axis color. Example: '#00FFAF'
        axis:      (Bool) Show/hide de view's axes
        labelX:    (dict) Dictionary with label properties, like CSS style, text
                   Keys for dict:
                      - labelStyle: (dict) CSS style. Example:
                                          {'color': '#FFF', 'font-size': '14pt'}
                      - labelText:  (str) The label text
        labelY:    Same as labelY.
        levels:    (min, max) Pass the min and max range that will be used for
                   image display. By default is None, so the data from the
                   pixel values will be used. Passing a different range is
                   useful for normalization of the slices in volumes.
        maskColor: (str) The mask color (#ARGB). Example: #2200FF55
        mask:      (int) Roi type: RECT_ROI or CIRCLE_ROI(default) or
                   (numpyarray) Image mask where 0 will be painted with
                   the specified maskColor and 255 will be transparent
        maskSize:  (int) The roi radius
        showHandles: (boolean) Enable/Disable the ROI handles

        preferredSize: (list of tuples). The first element is the image size and
                       the second element is the preferred size.
        """
        qtw.QWidget.__init__(self, parent=parent)
        self._model = None
        self._oddFlips = False
        self._oddRotations = False
        self._isVerticalFlip = False
        self._isHorizontalFlip = False
        self._rotationStep = 90
        self._scale = 1
        self._sizePref = kwargs.get('preferredSize', (128, 1000))
        self._exporter = None

        self._showToolBar = kwargs.get('toolBar', True)
        self._showRoiBtn = kwargs.get('roi', False)
        self._showMenuBtn = kwargs.get('menu', False)
        self._showHistogram = kwargs.get('histogram', False)
        self._showPopup = kwargs.get('popup', False)
        self._xAxisArgs = {
            'label': kwargs.get('labelX', {}),
            'visible': kwargs.get('axis', True)
        }
        self._yAxisArgs = {
            'label': kwargs.get('labelY', {}),
            'visible': kwargs.get('axis', True)
        }
        self._fitToSize = kwargs.get('fit', True)
        self._autoFill = kwargs.get('autoFill', False)
        self._pgButtons = kwargs.get('hideButtons', False)
        self._axisPos = kwargs.get('axisPos', AXIS_BOTTOM_LEFT)
        self._axisColor = kwargs.get('axisColor')
        self._levels = kwargs.get('levels', None)
        # mask params
        self.__updatingImage = False
        self.__setupGUI()
        self.__setupImageView()
        self._maskItem = None
        self._roi = None
        self.setModel(model)
        self.setViewMask(**kwargs)

    def __setupGUI(self):
        """ This is the standard method for the GUI creation """
        self._mainLayout = qtw.QHBoxLayout(self)
        self._mainLayout.setSpacing(0)
        self._mainLayout.setContentsMargins(1, 1, 1, 1)
        self._imageView = pg.ImageView(parent=self, view=pg.PlotItem())
        self.__viewRect = None
        self._imageView.installEventFilter(self)
        self._splitter = qtw.QSplitter(self)
        self._toolBar = widgets.ActionsToolBar(self, orientation=qtc.Qt.Vertical)
        self._splitter.addWidget(self._toolBar)
        self._splitter.setCollapsible(0, False)
        self._splitter.addWidget(self._imageView)

        displayPanel = self._toolBar.createPanel('displayPanel')
        vLayout = qtw.QVBoxLayout(displayPanel)
        self._labelScale = qtw.QLabel('Scale: ', displayPanel)
        hLayout = qtw.QHBoxLayout()
        hLayout.addWidget(self._labelScale)
        self._spinBoxScale = widgets.ZoomSpinBox(displayPanel,
                                         valueType=float,
                                         minValue=0,
                                         maxValue=10000,
                                         zoomUnits=widgets.ZoomSpinBox.PERCENT,
                                         iconSize=25)
        self._spinBoxScale.sigValueChanged[float].connect(
            self.__onSpinBoxScaleValueChanged)
        hLayout.addWidget(self._spinBoxScale)
        hLayout.addStretch()
        vLayout.addLayout(hLayout)
        view = self.getView().getViewBox()
        view.sigTransformChanged.connect(self.__onImageScaleChanged)

        # --Histogram On/Off--
        toolbar = qtw.QToolBar(displayPanel)
        toolbar.addWidget(qtw.QLabel('Histogram ', toolbar))
        self._actHistOnOff = widgets.OnOffAction()
        self._actHistOnOff.set(self._showHistogram)
        self._actHistOnOff.sigStateChanged.connect(self.__actHistOnOffChanged)
        toolbar.addAction(self._actHistOnOff)
        vLayout.addWidget(toolbar)

        # -- Axis --
        toolbar = qtw.QToolBar(displayPanel)
        toolbar.addWidget(qtw.QLabel('Axis ', toolbar))
        actAxis = widgets.MultiStateAction(
            toolbar, states=[(AXIS_BOTTOM_LEFT,
                              qta.icon('fa.long-arrow-up',
                                       'fa.long-arrow-right',
                                       options=[{'offset': (-0.3, 0),
                                                 'scale_factor': 0.8},
                                                {'offset': (0, 0.3),
                                                 'scale_factor': 0.8}
                                                ]), ''),
                             (AXIS_TOP_LEFT,
                              qta.icon('fa.long-arrow-down',
                                       'fa.long-arrow-right',
                                       options=[{'offset': (-0.3, 0),
                                                 'scale_factor': 0.8},
                                                {'offset': (0, -0.3),
                                                 'scale_factor': 0.8}
                                                ]), '')])
        actAxis.setText('Axis origin')
        actAxis.set(AXIS_BOTTOM_LEFT)
        actAxis.sigStateChanged.connect(self.__actAxisTriggered)
        toolbar.addAction(actAxis)

        # -- Axis On/Off --
        actAxisOnOff = widgets.OnOffAction(toolbar)
        actAxisOnOff.set(self._xAxisArgs['visible'])
        actAxisOnOff.sigStateChanged.connect(self.__actAxisOnOffTriggered)
        toolbar.addAction(actAxisOnOff)
        vLayout.addWidget(toolbar)

        # -- Flip --
        toolbar = qtw.QToolBar(displayPanel)
        toolbar.addWidget(qtw.QLabel('Flip ', toolbar))
        self._actHorFlip = widgets.TriggerAction(parent=toolbar, actionName="HFlip",
                                         text="Horizontal Flip",
                                         icon=qta.icon('fa.long-arrow-right',
                                                       'fa.long-arrow-left',
                                                       options=[
                                                           {'offset': (0, 0.2)},
                                                           {'offset': (0, -0.2)}
                                                       ]),
                                         checkable=True,
                                         slot=self.horizontalFlip)
        toolbar.addAction(self._actHorFlip)
        self._actVerFlip = widgets.TriggerAction(parent=toolbar, actionName="VFlip",
                                         text="Vertical Flip",
                                         icon=qta.icon('fa.long-arrow-up',
                                                       'fa.long-arrow-down',
                                                       options=[
                                                           {'offset': (0.2, 0)},
                                                           {'offset': (-0.2, 0)}
                                                       ]),
                                         checkable=True, slot=self.verticalFlip)
        toolbar.addAction(self._actVerFlip)
        vLayout.addWidget(toolbar)

        # --Rotate--
        toolbar = qtw.QToolBar(displayPanel)
        toolbar.addWidget(qtw.QLabel('Rotate ', toolbar))
        act = widgets.TriggerAction(parent=toolbar, actionName="RRight",
                            text="Rotate Right", faIconName="fa.rotate-right",
                            checkable=False, slot=self.__rotateRight)
        toolbar.addAction(act)
        act = widgets.TriggerAction(parent=toolbar, actionName="RLeft",
                            text="Rotate Left", faIconName="fa.rotate-left",
                            checkable=False, slot=self.__rotateLeft)
        toolbar.addAction(act)
        vLayout.addWidget(toolbar)

        # --Adjust--
        btnAdjust = qtw.QPushButton(displayPanel)
        btnAdjust.setText('Adjust')
        btnAdjust.setIcon(qta.icon('fa.crosshairs'))
        btnAdjust.setToolTip('Adjust image to the view')
        btnAdjust.pressed.connect(self.fitToSize)
        vLayout.addWidget(btnAdjust)

        # --Reset--
        btnReset = qtw.QPushButton(displayPanel)
        btnReset.setText('Reset')
        btnReset.setToolTip('Reset image operations')
        btnReset.setIcon(qta.icon('fa.mail-reply-all'))
        btnReset.pressed.connect(self.__resetView)
        vLayout.addWidget(btnReset)

        vLayout.addStretch()
        displayPanel.setFixedHeight(260)
        actDisplay = widgets.TriggerAction(parent=self._toolBar, actionName="ADisplay",
                                   text='Display', faIconName='fa.adjust')
        self._toolBar.addAction(actDisplay, displayPanel, exclusive=False)
        # --File-Info--
        fileInfoPanel = self._toolBar.createPanel('fileInfoPanel')
        fileInfoPanel.setSizePolicy(qtw.QSizePolicy.Ignored,
                                    qtw.QSizePolicy.Minimum)
        vLayout = qtw.QVBoxLayout(fileInfoPanel)
        self._textEditPath = qtw.QTextEdit(fileInfoPanel)
        self._textEditPath.viewport().setAutoFillBackground(False)

        vLayout.addWidget(self._textEditPath)
        fileInfoPanel.setMinimumHeight(30)

        actFileInfo = widgets.TriggerAction(parent=self._toolBar, actionName='FInfo',
                                    text='File Info',
                                    faIconName='fa.info-circle')
        self._toolBar.addAction(actFileInfo, fileInfoPanel, exclusive=False)
        # --End-File-Info--

        self._mainLayout.addWidget(self._splitter)

    def __setupAxis(self):
        """
        Setups the axis according to the axis orientation.
        See setAxisOrientation method.
        """
        plotItem = self._imageView.getView()

        if isinstance(plotItem, pg.PlotItem):
            # Shortcut notation
            axisMap = {}
            axisList = ['bottom', 'left', 'top', 'right']
            B, L, T, R = axisList

            viewBox = plotItem.getViewBox()
            if self._axisPos == AXIS_BOTTOM_LEFT:
                axisMap = {L: self._yAxisArgs,
                           B: self._xAxisArgs}
            elif self._axisPos == AXIS_TOP_LEFT:
                axisMap = {L: self._yAxisArgs,
                           T: self._xAxisArgs}
            elif self._axisPos == AXIS_TOP_RIGHT:
                axisMap = {R: self._yAxisArgs,
                           T: self._xAxisArgs}
            else:  # AXIS_BOTTOM_RIGHT:
                axisMap = {R: self._yAxisArgs,
                           B: self._xAxisArgs}

            if self._pgButtons:
                plotItem.hideButtons()
            else:
                plotItem.showButtons()

            plotItem.setAutoFillBackground(self._autoFill)

            # TODO: Check if the  viewBox.sigYRangeChanged.emit is needed
            viewBox.invertY(T in axisMap)

            # TODO: Check if the  viewBox.sigXRangeChanged.emit is needed
            viewBox.invertX(R in axisMap)  # should invert X if needed

            for a in axisList:
                d = axisMap.get(a, None)
                v = d is not None and d['visible']
                plotItem.showAxis(a, v)
                if v:  # Proceed if visible
                    axis = plotItem.getAxis(a)
                    if self._axisColor:
                        axis.setPen({'color': self._axisColor})
                    labelDict = d['label']
                    s = labelDict.get('labelStyle', {})
                    if a in [L, R]:
                        axis.label.rotate(90)  # a bit annoying as shown
                    axis.setLabel(text=labelDict.get('labelText', ''),
                                  units=None, unitPrefix=None, **s)
                    axis.setAutoFillBackground(self._autoFill)
                    axis.setZValue(0)
                    axis.linkedViewChanged(viewBox)

    def __getPreferredImageSize(self, width, height):
        """
        Return the preferred image size for the given size
        :param width: (int)
        :param height: (int)
        """
        size = max(width, height)
        if size < self._sizePref[0]:
            p = self._sizePref[0]
        elif size > self._sizePref[1]:
            p = self._sizePref[1]
        else:
            return width, height

        c = p / float(size)
        return int(width * c), int(height * c)

    def __imageViewKeyPressEvent(self, ev):
        """ Handles the key press event """
        if ev.key() == qtc.Qt.Key_H:
            self.__actHistOnOffChanged(True)

        if ev.key() == qtc.Qt.Key_A:
            self.__actAxisOnOffTriggered(True)

        if ev.key() == qtc.Qt.Key_E:
            ctrl = qtc.Qt.ControlModifier
            if ev.modifiers() & ctrl == ctrl:
                self.export()

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

    def __destroyGroup(self, group):
        """
        Reparents all items in group to group's parent item, then removes group
        from the scene, and finally deletes it. The items' positions and
        transformations are mapped from the group to the group's parent.
        :param group: (QGraphicsItemGroup)
        """
        v = self.getViewBox()
        scene = v.scene()
        for item in group.childItems():
            if item.isVisible():
                group.removeFromGroup(item)
                v.addItem(item)
        scene.destroyItemGroup(group)

    def __groupVisibleItems(self):
        """
        Groups all visible items into a new QGraphicsItemGroup.
        :param axis: (boolean) if True then inserts the visible axis items
                               into the group.
        :return: (QGraphicsItemGroup)
        """
        v = self.getViewBox()
        scene = v.scene()
        group = scene.createItemGroup([])
        boundingRect = qtc.QRectF()
        for item in v.addedItems:
            if item.isVisible():
                itemTransform, _ = item.itemTransform(group)
                boundingRect |= itemTransform.mapRect(item.boundingRect())

        scene.destroyItemGroup(group)
        return boundingRect

    def __calcImageScale(self):
        """ Return the image scale """
        viewBox = self.getViewBox()
        bounds = viewBox.rect()
        vr = viewBox.viewRect()
        if vr.width() == 0:
            return 0
        scale = bounds.width() / float(vr.width())
        return scale

    def __onRoiRegionChanged(self, roi):
        """ Slot for roi region changed """
        self.__updateMaskTextPos()
        width = roi.boundingRect().width()
        b = self._imageView.getImageItem().boundingRect()
        imgWidth = min(b.width(), b.height())
        if width <= imgWidth:
            self._textItem.setText("%d" % int(width/2))
            self.sigMaskSizeChanged.emit(int(width))
        else:
            self.setRoiMaskSize(imgWidth)
        self._textItem.setVisible(True)

    def __onRoiRegionChangedStarted(self, o):
        self.__updateMaskTextPos()
        self._textItem.setVisible(True)

    def __onRoiRegionChangedFinished(self, o):
        self._textItem.setVisible(False)

    def __updateMaskTextPos(self):
        """
        Update the mask text position according to the mask-roi.
        """
        pos = self._roi.pos()
        size = self._roi.size()
        rect2 = self._textItem.boundingRect()
        rect2 = self._textItem.mapRectToView(rect2)
        self._textItem.setPos(pos.x() + size[0] / 2 - rect2.width(),
                              pos.y() + size[0] / 2)

    def __removeMask(self):
        """ Remove the mask item """
        if self._maskItem is not None:
            vb = self.getViewBox()
            vb.removeItem(self._maskItem)
            if self._roi is not None:
                self._roi.sigRegionChanged.disconnect(self.__onRoiRegionChanged)
                self._roi.sigRegionChangeStarted.disconnect(
                    self.__onRoiRegionChangedStarted)
                self._roi.sigRegionChangeFinished.disconnect(
                    self.__onRoiRegionChangedFinished)
                vb.removeItem(self._roi)
                vb.removeItem(self._textItem)
            self._maskItem = None
            self._textItem = None

    @qtc.pyqtSlot()
    def __resetView(self):
        """
        Resets the view. The image operations (flips, rotations)
        will be reverted to their initial state
        """
        self.__resetOperationParams()
        self.setModel(self._model)

    @qtc.pyqtSlot(int)
    def __actAxisTriggered(self, state):
        """ This slot is invoked when the action histogram is triggered """
        self.setAxisOrientation(state)

    @qtc.pyqtSlot(int)
    def __actHistOnOffChanged(self, state):
        """ This slot is invoked when the action histogram is triggered """
        self._imageView.ui.histogram.setVisible(bool(state))

    @qtc.pyqtSlot(int)
    def __actAxisOnOffTriggered(self, state):
        """ This slot is invoked when the action histogram is triggered """
        self._yAxisArgs['visible'] = self._xAxisArgs['visible'] = bool(state)
        self.__setupAxis()

    @qtc.pyqtSlot()
    def __rotateLeft(self):
        """ Rotate the image 90 degrees to the left """
        self.rotate(-self._rotationStep)

    @qtc.pyqtSlot()
    def __rotateRight(self):
        """ Rotate the image 90 degrees to the right """
        self.rotate(self._rotationStep)

    @qtc.pyqtSlot(float)
    def __onSpinBoxScaleValueChanged(self, value):
        """
        This slot is invoked when the spinbox value for image scale is changed
        """
        self.setScale(value * 0.01)

    @qtc.pyqtSlot(object)
    def __onImageScaleChanged(self, view):
        """ Invoked when the image scale has changed """

        if not self.__updatingImage:
            self.__viewRect = self.getViewRect()
            scale = self.__calcImageScale()
            if not round(scale, 2) == round(self._scale, 2):
                self._scale = scale
                self._spinBoxScale.setValue(self._scale * 100)
                self.sigScaleChanged.emit(self._scale)

    def setRoiMaskSize(self, size):
        """
        Set size for the roi mask
        :param size: (int) The roi size
        """
        if isinstance(self._maskItem, _MaskItem):
            width = self._roi.boundingRect().width()
            b = self._imageView.getImageItem().boundingRect()
            w = min(b.width(), b.height())
            if not size == width and 0 < size <= w:
                d = (width - size)/2
                self._roi.setPos(self._roi.pos() + (d, d), update=False,
                                 finish=False)
                self._roi.setSize((size, size), update=True, finish=False)
                self._textItem.setVisible(False)

    def setRoiMaskSizeVisible(self, visible):
        """ Show or hide the TextItem used for the roi mask size """
        self._textItem.setVisible(visible)

    def getMask(self):
        """ Return mask """
        return self._maskItem.getMask() if self._maskItem else None

    def getMaskSize(self):
        """
        Return the mask size
        """
        if self._roi:
            return int(self._roi.boundingRect().width())
        return None

    def getMaskColor(self):
        """ Return the mask color """
        return self._maskItem.getMaskColor() if self._maskItem else None

    def setMaskColor(self, color):
        """
        Set the mask color
        :param color: (str) The color in #ARGB format. Example: #22AAFF00
                      or (qtg.QColor)
        """
        if self._maskItem:
            self._maskItem.setMaskColor(qtg.QColor(color))

    def setViewMask(self, **kwargs):
        """
        Set the mask to use in this ImageView. If mask=None, the current mask
        will be removed.
        :param kwargs:
         - maskColor:   (str) The color in #ARGB format. Example: #22AAFF00
                        or (qtg.QColor). Default value: '#2200FF55'
         - mask:        (int) The roi type (CIRCLE_ROI or RECT_ROI) for roi mask
                        (numpy array) for image mask.
         - maskSize:    (int) The roi radius in case of CIRCLE_ROI or RECT_ROI.
                        Default value: 100
         - showHandles: (boolean) Enable/Disable the ROI handles
        """
        self.__removeMask()  # remove previous mask
        maskColor = kwargs.get('maskColor', '#2200FF55')
        mask = kwargs.get('mask')
        size = kwargs.get('maskSize', 100)
        showHandles = kwargs.get('showHandles', True)
        vb = self.getViewBox()
        imgItem = self._imageView.getImageItem()

        if isinstance(mask, int):
            maskItem = _MaskItem(imgItem, imgItem, mask, size, showHandles)
            maskItem.setMaskColor(maskColor)
            self._roi = maskItem.getRoi()

            maskItem.setMaxBounds(self._roi.boundingRect())
            self._textItem = pg.TextItem(text="", color=(220, 220, 0),
                                         fill=pg.mkBrush(color=(0, 0, 0, 128)))
            vb.addItem(self._roi)
            vb.addItem(self._textItem)
            self._roi.sigRegionChanged.connect(self.__onRoiRegionChanged)
            self._roi.sigRegionChangeStarted.connect(
                self.__onRoiRegionChangedStarted)
            self._roi.sigRegionChangeFinished.connect(
                self.__onRoiRegionChangedFinished)
            vb.addItem(maskItem)
        elif mask is not None:
            maskItem = _CustomMaskItem(imgItem, maskColor, mask)
            vb.addItem(maskItem)
        else:
            maskItem = None

        self._maskItem = maskItem

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

    def getViewBox(self):
        """ Return the pyqtgraph.ViewBox """
        view = self._imageView.getView()
        if isinstance(view, pg.PlotItem):
            view = view.getViewBox()
        return view

    def getImageView(self):
        """ Return the internal pyqtgraph.ImageView """
        return self._imageView

    def setModel(self, imageModel, fitToSize=True):
        """
        Set the image model to be used for this ImageView
        :param imageModel: (datavis.models.ImageModel) The image model
        """
        dim = (0, 0) if self._model is None else self._model.getDim()
        self.clear()

        if imageModel:
            self.__updatingImage = True
            rect = self.getViewRect() if self._model else None
            self._imageView.setImage(imageModel.getData(),
                                     autoRange=True,
                                     levels=self._levels)
            if self._roi:
                imgItem = self._imageView.getImageItem()
                b = imgItem.boundingRect()
                r = self._roi.boundingRect()
                self._maskItem.setMaxBounds(b)
                self._roi.setPos(imgItem.pos() +
                                 pg.Point((b.width() - r.width()) / 2,
                                          (b.height() - r.height()) / 2))
            if not fitToSize and dim == imageModel.getDim():
                self.setViewRect(rect or self.getViewRect())
            else:
                self.fitToSize()
            self.__updatingImage = False

            self.updateImageScale()

        self._model = imageModel
        self.sigScaleChanged.emit(self._scale)

    def updateImageScale(self):
        """ Update the image scale """
        self.__viewRect = self.getViewRect()
        self._scale = self.__calcImageScale()

    def setLevels(self, levels):
        """ Set levels for the display. """
        self._levels = levels

    @qtc.pyqtSlot()
    def imageModelChanged(self):
        """
        Call this function when the image model has been modified externally.
        In this case, the ImageView will need to be notified so that the view
        can be updated.
        """
        data = None if self._model is None else self._model.getData()
        # conserve image QTransform
        t = self._imageView.getImageItem().transform()
        # For image change, not emit sigScaleChanged
        self.__updatingImage = True
        self._imageView.setImage(data, transform=t, levels=self._levels)
        self._imageView.getView().setRange(rect=self.__viewRect, padding=0.0)
        self.__updatingImage = False

    def setViewRect(self, rect):
        """
        Set the current view rect
        :param rect: (qtc.QRect) The view rect
        """
        self._imageView.getView().setRange(rect=rect, padding=0.0)

    @qtc.pyqtSlot(int)
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

    @qtc.pyqtSlot()
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

    @qtc.pyqtSlot()
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

    @qtc.pyqtSlot()
    def clear(self):
        """ Clear the view, setting a null image """
        self.__updatingImage = True
        self.__resetOperationParams()
        self._imageView.clear()
        self._scale = 0
        self._textEditPath.setText("")
        self.__updatingImage = True

    @qtc.pyqtSlot()
    def fitToSize(self):
        """ Fit image to the widget size """
        self._imageView.autoRange()
        self.updateImageScale()

    def isEmpty(self):
        """ Return True if the ImageView is empty """
        return self._model is None

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
        view = self.getViewBox()

        return view.viewRect()

    def getView(self):
        """ Returns the internal widget used for display image """
        return self._imageView.getView()

    def setViewSize(self, x, y, width, height):
        """ Sets the view size """
        # TODO review
        plot = self._imageView.getView()
        if isinstance(plot, pg.PlotItem):
            if self._xAxisArgs['visible']:
                height += plot.getAxis("bottom").height()
            if self._yAxisArgs['visible']:
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
            if self._xAxisArgs['visible']:
                height -= plot.getAxis("bottom").height()
            if self._yAxisArgs['visible']:
                width -= plot.getAxis("left").height()

        return width, height

    def getImageItem(self):
        """ See pyqtgraph.ImageView.getImageItem """
        return self._imageView.getImageItem()

    def getToolBar(self):
        """ Getter for left toolbar """
        return self._toolBar

    def getPreferredSize(self):
        """ Returns a tuple (width, height), which represents the preferred
        dimensions to contain all the image """
        if self._model is None:
            return 800, 600
        hw = self._imageView.ui.histogram.item.width() \
            if self._showHistogram else 0

        plot = self._imageView.getView()
        dim = self._model.getDim()
        width, height = self.__getPreferredImageSize(dim[0], dim[1])
        padding = 100
        width += hw + padding
        height += padding

        if isinstance(plot, pg.PlotItem):
            bottomAxis = plot.getAxis("bottom")
            topAxis = plot.getAxis("top")
            leftAxis = plot.getAxis("left")
            rightAxis = plot.getAxis("right")

            if bottomAxis is not None and bottomAxis.isVisible():
                height += bottomAxis.height()
            if topAxis is not None and topAxis.isVisible():
                height += topAxis.height()
            if leftAxis is not None and leftAxis.isVisible():
                width += leftAxis.width()
            if rightAxis is not None and rightAxis.isVisible():
                width += rightAxis.width()

        return width + self._toolBar.width(), height

    def eventFilter(self, obj, event):
        """
        Filters events if this object has been installed as an event filter for
        the watched object
        :param obj: watched object
        :param event: event
        :return: True if this object has been installed, False i.o.c
        """
        t = event.type()
        if t == qtc.QEvent.KeyPress:
            self.__imageViewKeyPressEvent(event)
            return True

        return qtw.QWidget.eventFilter(self, obj, event)

    def getScale(self):
        """ Return the image scale """
        return self.__calcImageScale()

    def setScale(self, scale):
        """
         Set de image scale
        :param scale: (float) The image scale
        """
        viewBox = self.getViewBox()
        if scale == 0:
            self._spinBoxScale.setValue(self._scale * 100)
        elif not round(scale, 2) == round(self._scale, 2):
            self.__updatingImage = True
            viewBox.scaleBy(x=self._scale, y=self._scale)  # restore to 100 %
            viewBox.scaleBy(x=1 / scale, y=1 / scale)  # to current scale
            self.__updatingImage = False
            self.updateImageScale()
            self._spinBoxScale.setValue(scale * 100)

    def setXLink(self, imageView):
        """
        Link the X axis to another ImageView.
        :param imageView: (ImageView) The ImageView widget to be linked
        """
        if isinstance(imageView, ImageView):
            local = self.getView()
            view = imageView.getView()
            local.setXLink(view)

    def setYLink(self, imageView):
        """
        Link the Y axis to another ImageView.
        :param imageView: (ImageView) The ImageView widget to be linked
        """
        if isinstance(imageView, ImageView):
            local = self.getView()
            view = imageView.getView()
            local.setYLink(view)

    def export(self, path=None, background=None, antialias=True,
               exportView=True):
        """
        Export the scene to the given path. Image - PNG is the default format.
        The exact set of image formats supported will depend on qtc.Qt libraries.
        However, common formats such as PNG, JPG, and TIFF are almost always
        available.

        :param path:       (str) The image path. If no path is specified,
                           then a save dialog will be displayed
        :param background: (str or qtg.QColor) The background color
        :param antialias:  (boolean) Use antialiasing for render the image
        :param exportView: (boolean) If true, all the view area will be exported
                                     else export the image
        """
        v = self.getView()
        if not exportView:
            rect = self.__groupVisibleItems()
            width = rect.width()/self._scale
            height = rect.height()/self._scale
            self._exporter = ImageExporter(v.scene(), rect)
            w = self._exporter.params.param('width')
            w.setValue(int(width), blockSignal=self._exporter.widthChanged)
            h = self._exporter.params.param('height')
            h.setValue(int(height), blockSignal=self._exporter.heightChanged)

        else:
            width, height = v.width(), v.height()
            self._exporter = pgImageExporter(v)
            # jump pyqtgraph bug, reported here:
            # https://github.com/pyqtgraph/pyqtgraph/issues/538
            w = self._exporter.params.param('width')
            w.setValue(width + 1, blockSignal=self._exporter.widthChanged)
            h = self._exporter.params.param('height')
            h.setValue(height + 1, blockSignal=self._exporter.heightChanged)

            w.setValue(int(width), blockSignal=self._exporter.widthChanged)
            h.setValue(int(height), blockSignal=self._exporter.heightChanged)

        if background is not None:
            self._exporter.parameters()['background'] = background

        self._exporter.parameters()['antialias'] = antialias
        self._exporter.export(path)


class ImageExporter(pgImageExporter):
    """
    The ImageExporter class provides functionality for export an scene rect to
    image file. The exact set of image formats supported will depend on qtc.Qt
    libraries. However, common formats such as PNG, JPG, and TIFF are almost
    always available.
    """
    def __init__(self, item, sourceRect):
        self._sourceRect = sourceRect
        pgImageExporter.__init__(self, item)

    def setSourceRect(self, rect):
        """
        Set the source rect
        :param rect: (qtc.QRect)
        """
        self._sourceRect = rect

    def getTargetRect(self):
        return self._sourceRect

    def getSourceRect(self):
        return self._sourceRect

    def export(self, fileName=None, toBytes=False, copy=False):
        """
        Export the scene to image file.
        :param fileName: (str)     The file path. If fileName is None,
                                   pop-up a file dialog.
        :param toBytes:  (boolean) If toBytes is True, return a bytes object
                                   rather than writing to file.
        :param copy:     (boolean) If copy is True, export to the copy buffer
                                   rather than writing to file.
        """
        if fileName is None and not toBytes and not copy:
            if USE_PYSIDE:
                filter = ["*." + str(f) for f in
                          qtg.QImageWriter.supportedImageFormats()]
            else:
                filter = ["*." + bytes(f).decode('utf-8') for f in
                          qtg.QImageWriter.supportedImageFormats()]

            preferred = ['*.png', '*.tif', '*.jpg']
            for p in preferred[::-1]:
                if p in filter:
                    filter.remove(p)
                    filter.insert(0, p)
            self.fileSaveDialog(filter=filter)
            return

        w, h = int(self.params['width']), int(self.params['height'])
        if w == 0 or h == 0:
            raise Exception(
                "Cannot export image with size=0 "
                "(requested export size is %dx%d)" % (w, h))
        targetRect = qtc.QRect(0, 0, w, h)
        sourceRect = self.getSourceRect()

        bg = np.empty((w, h, 4), dtype=np.ubyte)
        color = self.params['background']
        bg[:, :, 0] = color.blue()
        bg[:, :, 1] = color.green()
        bg[:, :, 2] = color.red()
        bg[:, :, 3] = color.alpha()
        self.png = fn.makeQImage(bg, alpha=True)

        ## set resolution of image:
        resolutionScale = targetRect.width() / sourceRect.width()
        painter = qtg.QPainter(self.png)
        try:
            self.setExportMode(True, {'antialias': self.params['antialias'],
                                      'background': self.params['background'],
                                      'painter': painter,
                                      'resolutionScale': resolutionScale})
            painter.setRenderHint(qtg.QPainter.Antialiasing,
                                  self.params['antialias'])
            self.getScene().render(painter, qtc.QRectF(targetRect),
                                   qtc.QRectF(sourceRect))
        finally:
            self.setExportMode(False)
        painter.end()

        if copy:
            qtg.QGuiApplication.clipboard().setImage(self.png)
        elif toBytes:
            return self.png
        else:
            self.png.save(fileName)


class _MaskItem(qtw.QAbstractGraphicsShapeItem):

    def __init__(self, parent, imageItem, roiType=CIRCLE_ROI, size=100,
                 showHandles=True):
        if imageItem is None:
            raise Exception("Invalid ImageItem: None value")

        qtw.QAbstractGraphicsShapeItem.__init__(self, parent=parent)
        self._imageItem = imageItem
        self._roiRegion = None
        self._maskColor = None
        self._mask = roiType

        if roiType == CIRCLE_ROI:
            size *= 2
            self._roi = pg.CircleROI((0, 0), (size, size), movable=False)
            self._regionType = qtg.QRegion.Ellipse
        else:
            size *= 2
            self._roi = pg.RectROI(0, 0, (size, size), movable=False)
            self._roi.aspectLocked = True
            self._regionType = qtg.QRegion.Rectangle

        if not showHandles:
            for h in self._roi.getHandles():
                h.hide()

        self.__updateRoiRegion(self._roi)

        self._roi.sigRegionChanged.connect(self.__updateRoiRegion)

    def __updateRoiRegion(self, o):
        """ Updates the qtc.Qt object(qtg.QRegion) used in paint method """
        pos = self._roi.pos()
        rect = self._roi.boundingRect()
        self._roiRegion = qtg.QRegion(pos.x(), pos.y(), rect.width(), rect.height(),
                                  self._regionType)

    def setMaskColor(self, maskColor):
        """
        Set the mask color
        :param maskColor: (str) The mask color in ARGB format.
                                Example: '#22FF00AA'
                          or (qtg.QColor)
        """
        self._maskColor = maskColor
        self.setBrush(qtg.QColor(maskColor))

    def getMaskColor(self):
        """ Return the mask color """
        return self._maskColor

    def paint(self, painter, option, widget):
        painter.save()

        imageRect = self._imageItem.boundingRect()
        imageRegion = qtg.QRegion(0, 0, imageRect.width(), imageRect.height())
        painter.setClipRegion(imageRegion.xored(self._roiRegion))
        painter.fillRect(imageRect, self.brush())

        painter.restore()

    def boundingRect(self):
        """ Return the bounding rect. Reimplemented from
        qtw.QAbstractGraphicsShapeItem """
        if self._imageItem:
            return self._imageItem.boundingRect()
        return qtc.QRectF(0, 0, 0, 0)

    def getRoi(self):
        """ Return the roi used for this mask item """
        return self._roi

    def getMask(self):
        """ Return the mask type. Possible values: CIRCLE_ROI, RECT_ROI """
        return self._mask

    def getMaskSize(self):
        """ Return the mask size """
        return int(self._roi.boundingRect().width())

    def setMaxBounds(self, bounds):
        """
        :param bounds:(qtc.QRect, qtc.QRectF, or None) Specifies boundaries that the ROI
                      cannot be dragged outside of by the user. Default is None.
        """
        self._roi.maxBounds = bounds


class _CustomMaskItem(pg.ImageItem):

    def __init__(self, imageItem, maskColor, maskData):
        """
        :param imageItem: (pg.ImageItem) The image item
        :param maskColor: (str) The mask color in ARGB format.
                                Example: '#22FF00AA'
                          or (qtg.QColor)
        :param maskData:  (numpy array) The mask data
        """
        if imageItem is None:
            raise Exception("Invalid ImageItem: None value")

        pg.ImageItem.__init__(self, image=maskData)
        self.setMaskColor(maskColor)
        self._imageItem = imageItem
        self.maskData = maskData
        self._maskColor = maskColor

    def setMaskColor(self, maskColor):
        """
        Set the mask color
        :param maskColor: (str) The mask color in ARGB format.
                                Example: '#22FF00AA'
                          or (qtg.QColor)
        """
        self._maskColor = maskColor
        c = qtg.QColor(maskColor)
        lut = [(c.red(), c.green(), c.blue(), c.alpha()), (255, 255, 255, 0)]
        self.setLookupTable(lut)

    def getMaskColor(self):
        """ Return the mask color """
        return self._maskColor

    def setMask(self, mask):
        """ Set the image mask """
        self.maskData = mask
        self._imageItem.setImage(mask)

    def getMask(self):
        """ Return the mask data """
        return self.maskData

    def setMaxBounds(self, bounds):
        """
        :param bounds: (qtc.QRect, qtc.QRectF, or None) Specifies mask boundaries.
                       Default is None.
        """
        pass


class EMImageItemDelegate(qtw.QStyledItemDelegate):
    """
    ImageItemDelegate class provides display and editing facilities for
    em image data items from a model.
    """
    def __init__(self, parent=None):
        """
        Constructs a EMImageItemDelegate.
        :param parent:  (QObject) The parent object
        """
        qtw.QStyledItemDelegate.__init__(self, parent)
        self._imageView = ImageView(None, toolBar=False, axis=False)
        self._pixmapItem = None
        self._noImageItem = pg.TextItem("NO IMAGE")
        self._imageView.getView().addItem(self._noImageItem)
        self._noImageItem.setVisible(False)
        self._sBorder = 3  # selected state border (px)
        self._textHeight = 16
        self._focusPen = qtg.QPen(qtc.Qt.DotLine)
        self._thumbSize = 64

    def paint(self, painter, option, index):
        """
        Reimplemented from qtw.QStyledItemDelegate
        """
        if not index.isValid():
            return

        x = option.rect.x()
        y = option.rect.y()
        w = option.rect.width()
        h = option.rect.height()
        rect = qtc.QRectF()
        selected = option.state & qtw.QStyle.State_Selected
        hasFocus = option.state & qtw.QStyle.State_HasFocus
        active = option.state & qtw.QStyle.State_Active

        colorGroup = qtg.QPalette.Active
        palette = qtg.QPalette.HighlightedText

        if selected:
            if not (hasFocus or active):
                colorGroup = qtg.QPalette.Inactive
            palette = qtg.QPalette.Highlight

        painter.fillRect(option.rect, option.palette.color(colorGroup, palette))
        labels = index.data(widgets.LABEL_ROLE)
        labelsCount = len(labels)
        if labels:
            h -= self._textHeight * labelsCount

        self._setupView(index, w, h, labelsCount)
        rect.setRect(self._sBorder, self._sBorder, w - 2 * self._sBorder,
                     h - 2 * self._sBorder)
        pgImageView = self._imageView.getImageView()
        pgImageView.ui.graphicsView.scene().setSceneRect(rect)
        rect.setRect(x + self._sBorder, y + self._sBorder,
                     w - 2 * self._sBorder, h - 2 * self._sBorder)

        pgImageView.ui.graphicsView.scene().render(painter, rect)

        if hasFocus:
            painter.save()
            self._focusPen.setColor(
                option.palette.color(qtg.QPalette.Active,
                                     qtg.QPalette.Highlight))
            painter.setPen(self._focusPen)
            rect.setRect(x, y, w - 1, h - 1)
            if labels:
                rect.setHeight(h + self._textHeight * labelsCount - 1)
            painter.drawRect(rect)
            painter.restore()

        for i, text in enumerate(labels):
            rect.setRect(x + self._sBorder, y + h + i * self._textHeight,
                         w - 2 * self._sBorder, self._textHeight)
            painter.drawText(rect, qtc.Qt.AlignLeft, text)

    def _setupView(self, index, width, height, labelsCount):
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
        size = index.data(qtc.Qt.SizeHintRole)
        if size is not None:
            (w, h) = (size.width(), size.height())
            h -= labelsCount

            v = self._imageView.getView()
            (cw, ch) = (v.width(), v.height())
            if not (w, h) == (cw, ch):
                v.setGeometry(0, 0, width, height)
                v.resizeEvent(None)

            if not isinstance(imgData, qtg.QPixmap):  # qtg.QPixmap or np.array
                if self._pixmapItem:
                    self._pixmapItem.setVisible(False)
                self._imageView.setModel(models.ImageModel(imgData))
            else:
                if not self._pixmapItem:
                    self._pixmapItem = qtw.QGraphicsPixmapItem(imgData)
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
        imgData = index.data(widgets.DATA_ROLE)

        return imgData

    def getImageView(self):
        """ Return the ImageView used to render de icons """
        return self._imageView

    def setLevels(self, levels):
        """
        Set levels for the image configuration.
        :param levels: (tupple) Minimum an maximum pixel values
        """
        self._imageView.setLevels(levels)

    def getTextHeight(self):
        """ The height of text """
        return self._textHeight