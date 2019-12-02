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
from ..utils import py23
from ._constants import (AXIS_BOTTOM_LEFT, AXIS_TOP_LEFT, AXIS_TOP_RIGHT,
                         CIRCLE_ROI, RECT_ROI, ADD, REMOVE)


class ImageView(qtw.QWidget):
    """ This widget provides functionality for displaying images provided by a
    :class:`ImageModel <datavis.models.ImageModel>`.

    This class also allows to perform basic display operations over the
    data that is being displayed such as: rotations, zoom, drag and flips,
    among others.

    Example of use:
        imageView = datavis.views.ImageView(parent=None, border_color='#FFAA33')
        d = pyqtgraph.gaussianFilter(np.random.normal(size=(512, 512)), (5, 5))
        imgModel = dv.models.ImageModel(data)
        imageView.setModel(imgModel)

    """

    """ Signal emitted when the image scale changed """
    sigScaleChanged = qtc.pyqtSignal(float)

    """ Signal emitted when the mask ROI size changed"""
    sigMaskSizeChanged = qtc.pyqtSignal(int)

    def __init__(self, model=None, **kwargs):
        """ Create a new ImageView instance.

        Args:
            model:     :class:`ImageModel <datavis.models.ImageModel>` instance
                       that will be used to fetch the image data.

        Keyword Args:
            parent:    (QWidget) Is the parent widget to which this
                       ImageView will belong. If None, then the ImageView is
                       created with no parent.
            toolBar:   Bool value to specify if showing or hiding the toolbar.
                       By default, the toolbar is visible.

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
                       the qtg.QPalette::Window color role from the widget's
                       palette. False by default.
            hideButtons: (Bool) Hide/show the internal pg buttons. For example,
                         the button used to center an image. False by default.
            axisPos:   (Bool) The axis position.
                       Possible values:  AXIS_TOP_LEFT, AXIS_TOP_RIGHT,
                       AXIS_BOTTOM_RIGHT, AXIS_BOTTOM_LEFT
            axisColor  (str) The axis color. Example: '#00FFAF'
            axis:      (Bool) Show/hide de view's axes
            labelX:    (dict) Dictionary with label properties, like CSS style:

                        * labelStyle: (dict) CSS style. Example::

                            {'color': '#FFF', 'font-size': '14pt'}
                        * labelText:  (str) The label text
            labelY:    Same as labelX.
            levels:    (min, max) Pass the min and max range that will be used
                       for image display. By default is None, so the data from
                       the pixel values will be used. Passing a different range
                       is useful for normalization of the slices in volumes.
            preferredSize: (tuple). Minimum and maximum preferred image size.

            maskParams: Dictionary with mask-related params. Following are
                some possible values in this dict:

                * type:

                  * ROI_CIRCLE (display a circular mask from center) or
                  * ROI_RECT (display rectangular mask from center) or
                  * CONSTANT (generate data mask with given constant value) or
                  * DATA (just provide data mask as numpy array)
                * data: If the type is ROI_CIRCLE or ROI_RECT, it is the value
                  of the radius of the mask. If type is CONSTANT it is the
                  value of entire mask. Finally, if the type is DATA, this
                  should be a numpy array with values of the mask.
                * color: (QColor or str) The color for the mask.
                  Example: '#66212a55' in ARGB format.
                * operation: What operation will be performed in the mask
                  * NONE (the mask editor is not shown) or
                  * ADD  (add 1 values to the mask with the pen) or
                  * REMOVE (add 0 values to the mask with the pen)
                * penSize: Size of the pen to be used, only relevant when not
                  operation is not NONE (default 50px).
                * showHandles: (boolean) Enable/Disable the ROI handles
        """
        qtw.QWidget.__init__(self, parent=kwargs.get('parent'))
        self._model = None
        self._oddFlips = False
        self._oddRotations = False
        self._isVerticalFlip = False
        self._isHorizontalFlip = False
        self._rotationStep = 90
        self._scale = 1
        self._rowMajor = kwargs.get('rowMajor', True)

        # Handle scale input, it can be string or numeric
        # if it is string, it can also have % character for percent
        scale = kwargs.get('scale')
        # Convert from string, considering % possibility
        if isinstance(scale, py23.str):
            if '%' in scale:
                scale = float(scale.replace('%', '')) / 100.
            else:
                scale = float(scale)

        # Set the scale depending on the value
        if scale and not 0 < scale <= 1.0:
            # FIXME: Compute the scale based on input dimension
            raise Exception('Still not implemented')

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
        # ARGB format
        maskParams = kwargs.get('maskParams') or dict()
        self._maskColor = qtg.QColor(maskParams.get('color',
                                                    qtg.QColor('#66212a55')))
        self._maskItem = None
        self._removeMaskPen = pg.mkPen({'color': "FFF", 'width': 1})
        self._addMaskPen = pg.mkPen({'color': "00FF00", 'width': 1})
        d = {'pen': self._removeMaskPen}
        self._maskPen = PenROI((0, 0), 20, **d)
        self._maskData = maskParams.get('data')
        self._maskType = maskParams.get('type')
        self._maskOperation = maskParams.get('operation')
        self._maskPenSize = maskParams.get('penSize', 50)
        self._showMaskHandles = maskParams.get('showHandles', True)
        self.__setupGUI()
        self.__setupImageView()
        self._roi = None
        self.setModel(model)
        #if scale:
        #    self.setScale(scale)
        w, h = self.getPreferredSize()
        self.setGeometry(0, 0, w, h)

    def __setupGUI(self):
        """ This is the internal method for the GUI creation """
        self._mainLayout = qtw.QHBoxLayout(self)
        self._mainLayout.setSpacing(0)
        self._mainLayout.setContentsMargins(1, 1, 1, 1)
        self._imageView = pg.ImageView(parent=self, view=pg.PlotItem())
        v = self.getViewBox()
        v.addItem(self._maskPen)
        self._maskPen.setAcceptedMouseButtons(qtc.Qt.NoButton)
        self._maskPen.setAcceptHoverEvents(False)
        self._maskPen.setZValue(0)
        self._maskPen.setVisible(False)

        scene = v.scene()
        if scene is not None:
            scene.sigMouseMoved.connect(self.__viewBoxMouseMoved)

        self.__viewRect = None
        self._imageView.installEventFilter(self)
        self._splitter = qtw.QSplitter(self)
        self._toolBar = widgets.ActionsToolBar(self,
                                               orientation=qtc.Qt.Vertical)
        self._splitter.addWidget(self._toolBar)
        self._splitter.setCollapsible(0, False)
        self._splitter.addWidget(self._imageView)

        displayPanel = self._toolBar.createPanel('displayPanel')
        vLayout = qtw.QVBoxLayout(displayPanel)
        self._labelScale = qtw.QLabel('Scale: ', displayPanel)
        hLayout = qtw.QHBoxLayout()
        hLayout.addWidget(self._labelScale)
        self._spinBoxScale = widgets.ZoomSpinBox(
            displayPanel, valueType=float, minValue=0, maxValue=10000,
            zoomUnits=widgets.ZoomSpinBox.PERCENT, iconSize=25)
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
        self._actAxisOnOff = actAxisOnOff
        vLayout.addWidget(toolbar)

        # -- Flip --
        toolbar = qtw.QToolBar(displayPanel)
        toolbar.addWidget(qtw.QLabel('Flip ', toolbar))
        self._actHorFlip = widgets.TriggerAction(
            parent=toolbar, actionName="HFlip", text="Horizontal Flip",
            icon=qta.icon('fa.long-arrow-right',
                          'fa.long-arrow-left',
                          options=[
                              {'offset': (0, 0.2)},
                              {'offset': (0, -0.2)}
                          ]),
            checkable=True, slot=self.horizontalFlip)
        toolbar.addAction(self._actHorFlip)
        self._actVerFlip = widgets.TriggerAction(
            parent=toolbar, actionName="VFlip", text="Vertical Flip",
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
                                    text="Rotate Right",
                                    faIconName="fa.rotate-right",
                                    checkable=False,
                                    slot=self.__rotateRight)
        toolbar.addAction(act)
        act = widgets.TriggerAction(parent=toolbar, actionName="RLeft",
                                    text="Rotate Left",
                                    faIconName="fa.rotate-left",
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
        actDisplay = widgets.TriggerAction(parent=self._toolBar,
                                           actionName="ADisplay",
                                           text='Display',
                                           faIconName='fa.adjust')
        self._toolBar.addAction(actDisplay, displayPanel, exclusive=False)
        # --Mask Creator--
        self.__addMaskCreatorTools(self._toolBar)
        # --End-Mask Creator--
        # --File-Info--
        fileInfoPanel = self._toolBar.createPanel('fileInfoPanel')
        fileInfoPanel.setSizePolicy(qtw.QSizePolicy.Ignored,
                                    qtw.QSizePolicy.Minimum)
        vLayout = qtw.QVBoxLayout(fileInfoPanel)
        self._textEditPath = qtw.QTextEdit(fileInfoPanel)
        self._textEditPath.viewport().setAutoFillBackground(False)

        vLayout.addWidget(self._textEditPath)
        fileInfoPanel.setMinimumHeight(30)

        actFileInfo = widgets.TriggerAction(parent=self._toolBar,
                                            actionName='FInfo',
                                            text='File Info',
                                            faIconName='fa.info-circle')
        self._toolBar.addAction(actFileInfo, fileInfoPanel, exclusive=False)
        # --End-File-Info--

        self._mainLayout.addWidget(self._splitter)
        self.setGeometry(0, 0, 640, 480)

    def __viewBoxMouseMoved(self, pos):
        """
        This slot is invoked when the mouse is moved hover the pyqtgraph.ViewBox
        Args:
            pos: The mouse pos
        """
        if (self._maskItem is not None and
                self._maskItem.isVisible() and
                pos is not None):
            vb = self.getViewBox()
            pos = vb.mapSceneToView(pos)
            size = self._maskPen.size()
            self._maskPen.setPos(pos - size / 2)

    def __addMaskCreatorTools(self, toolbar):
        """ Creates the mask creator panel """
        maskPanel = toolbar.createPanel('maskCreatorPanel')
        layout = qtw.QVBoxLayout(maskPanel)
        maskPanel.setSizePolicy(qtw.QSizePolicy.MinimumExpanding,
                                qtw.QSizePolicy.Minimum)
        tb = qtw.QToolBar(maskPanel)
        layout.addWidget(tb)
        tb.addWidget(qtw.QLabel("<strong>Mask:</strong>", tb))

        self._actColor = widgets.TriggerAction(parent=tb, actionName='ASColor',
                                               faIconName='fa5s.palette',
                                               faIconColor=self._maskColor,
                                               tooltip='Select mask color',
                                               slot=self.__onSelectColor)
        tb.addAction(self._actColor)

        self._actMaskCreatorShowHide = widgets.OnOffAction(
            tb, toolTipOn='Hide mask', toolTipOff='Show mask')
        showMaskCreator = self._maskOperation is not None
        self._actMaskCreatorShowHide.set(showMaskCreator)
        self._actMaskCreatorShowHide.sigStateChanged.connect(
            self.__onMaskCreatorShowHideTriggered)
        tb.addAction(self._actMaskCreatorShowHide)
        self._actMaskCreator = widgets.TriggerAction(
            parent=toolbar, actionName='AMask', text='Mask\nCreator',
            faIconName='fa5s.stroopwafel')
        # pen
        tb = qtw.QToolBar(maskPanel)
        layout.addWidget(tb)
        tb.addWidget(qtw.QLabel("<strong>Pen:</strong>", tb))
        self._spinBoxMaskPen = widgets.IconSpinBox(
            maskPanel, valueType=int, minValue=5, maxValue=10000,
            currentValue=self._maskPenSize, iconName='fa5s.pen', iconSize=16,
            suffix=' px')
        self._spinBoxMaskPen.sigValueChanged[int].connect(
            self.__onSpinBoxMaskPenValueChanged)
        self._spinBoxMaskPen.setMinimumHeight(30)
        tb.addWidget(self._spinBoxMaskPen)
        # mask actions
        tb = qtw.QToolBar(maskPanel)
        tb.addWidget(qtw.QLabel("<strong>Action: </strong>", tb))
        self._radioButtonAddMask = qtw.QRadioButton(text='Add', parent=tb)
        tb.addWidget(self._radioButtonAddMask)
        self._radioButtonRemoveMask = qtw.QRadioButton(text='Remove', parent=tb)
        tb.addWidget(self._radioButtonRemoveMask)
        maskPanel.setFixedHeight(190)
        self._maskButtonGroup = qtw.QButtonGroup(tb)
        self._maskButtonGroup.setExclusive(True)
        self._maskButtonGroup.addButton(self._radioButtonRemoveMask)
        self._maskButtonGroup.addButton(self._radioButtonAddMask)
        if self._maskOperation == ADD:
            self._radioButtonAddMask.setChecked(True)
        elif self._maskOperation == REMOVE:
            self._radioButtonRemoveMask.setChecked(True)

        self._maskButtonGroup.buttonToggled[qtw.QAbstractButton, bool].connect(
            self.__onActionMaskToggled)
        layout.addWidget(tb)

        btn = qtw.QPushButton(parent=maskPanel, text='Invert',
                              icon=qta.icon('fa5s.exchange-alt'))
        btn.clicked.connect(self.__invertMask)
        btn.setToolTip('Invert image mask')
        layout.addWidget(btn)
        btn = qtw.QPushButton(parent=maskPanel, text='Reset',
                              icon=qta.icon('fa.mail-reply-all'))
        btn.clicked.connect(self.__resetMask)
        btn.setToolTip('Reset image mask to initial state')
        layout.addWidget(btn)
        toolbar.addAction(self._actMaskCreator, maskPanel, exclusive=False,
                          checked=showMaskCreator)

        self._actMaskCreator.setVisible(showMaskCreator)
        self._maskPen.setVisible(showMaskCreator)
        self.__onSpinBoxMaskPenValueChanged(self._spinBoxMaskPen.getValue())

    def __resetMask(self):
        """ Reset the image mask according to the mask operation """
        if isinstance(self._maskItem, _CustomMaskItem):
            data = self._maskItem.image
            v = 2 if self._maskOperation == REMOVE else 0
            data[...] = v
            self._maskItem.updateImage()

    def __invertMask(self):
        """ Invert the image mask data"""
        if isinstance(self._maskItem, _CustomMaskItem):
            data = self._maskItem.image
            data[...] = 3 - data
            self._maskItem.updateImage()

    def __onSelectColor(self):
        """ Invoked when select color action is triggered. Show a QColorDialog
        for color selection """
        color = qtw.QColorDialog.getColor(
            initial=self._maskColor, parent=self, title='Mask Color Selector',
            options=qtw.QColorDialog.ShowAlphaChannel)

        if color.isValid():
            self._maskColor = color
            self._actColor.setIcon(qta.icon('fa5s.palette',
                                            color=self._maskColor))
            if self._maskItem is None:
                self.__createMaskItem(self._maskData)
            else:
                self._maskItem.setMaskColor(self._maskColor)

            self._actMaskCreatorShowHide.set(True)

    def __onSpinBoxMaskPenValueChanged(self, size):
        """ Invoked when the spinbox pen size is changed. Resize the pen and
        creates a new mask brush """
        self.__createMaskCreatorBrush(size)
        pos = self._maskPen.pos()
        oldSize = self._maskPen.size()
        newsize = pg.Point(size, size)

        self._maskPen.setSize((size, size))
        self._maskPen.setPos(pos - (newsize-oldSize) / 2)

    def __onMaskCreatorShowHideTriggered(self, state):
        """ Invoked when action mask-creator-show-hide is triggered.
        Show or hide the image mask """
        cursor = qtc.Qt.ArrowCursor
        self._maskPen.setVisible(False)
        if self._actMaskCreatorShowHide.get():
            self._maskPen.setVisible(True)
            if self._maskItem is None:
                self.__createMaskItem(self._maskData)
            else:
                self.getViewBox().addItem(self._maskItem)
            cursor = qtc.Qt.CrossCursor
        elif self._maskItem is not None:
            self.getViewBox().removeItem(self._maskItem)

        self._imageView.setCursor(cursor)
        # make circle pen
        self.__onSpinBoxMaskPenValueChanged(self._spinBoxMaskPen.getValue())

    def __onActionMaskToggled(self, button, checked):
        """ Invoked when the action mask button is toggled. Creates a new mask
        brush according to the current mask operation (ADD or REMOVE) """
        if checked:
            if button == self._radioButtonRemoveMask:
                pen = self._removeMaskPen
            else:
                pen = self._addMaskPen
            self.__createMaskCreatorBrush(self._spinBoxMaskPen.getValue())
            self._maskPen.setPen(pen)

    def __createMaskCreatorBrush(self, size):
        """ Create the mask creator brush """
        if isinstance(self._maskItem, _CustomMaskItem):
            roi = pg.CircleROI((0, 0), size)
            path = roi.shape()
            k = []
            pos = pg.Point()
            for i in range(size):
                r = []
                for j in range(size):
                    pos.setX(i)
                    pos.setY(j)
                    v = 1 if path.contains(pos) else 0
                    r.append(v)
                k.append(r)
            kern = np.array(k)
            self._maskItem.setDrawKernel(kern, mask=kern,
                                         center=(int(size/2), int(size/2)),
                                         mode=self.__drawMask)

    def __drawMask(self, dk, image, mask, ss, ts, ev):
        """ Function passed to pyqtgraph.ImageItem for draw mode.
        For more information, you can see pyqtgraph.ImageItem.setDrawKernel """
        mask = mask[ss]
        if self._radioButtonAddMask.isChecked():
            image[ts] |= 1 + mask
        else:
            image[ts] = image[ts] * (1 - mask)

        self._maskItem.updateImage()

    def __createMaskItem(self, data=0):
        """ Create the mask item, initializing the mask with the given value.

        Args:
            data: int or numpy array
        """
        imageItem = self.getImageItem()
        w, h = (imageItem.width(), imageItem.height())
        viewBox = self.getViewBox()
        if w is not None and h is not None:
            if isinstance(data, int):
                value = 1 if data == 0 else 2
                data = np.full(shape=(w, h), fill_value=value, dtype=np.int8)

            if self._rowMajor:
                data = data.T

            if (self._maskItem is None or
                    not self._maskItem.width() == w or
                    not self._maskItem.height() == h):
                self._maskItem = _CustomMaskItem(imageItem,
                                                 self._maskColor,
                                                 data)
                viewBox.addItem(self._maskItem)
            else:
                self._maskItem.setMaskColor(self._maskColor)
                self._maskItem.setImage(data)

            if self._maskOperation is not None:
                self.__createMaskCreatorBrush(self._spinBoxMaskPen.getValue())
        elif self._maskItem is not None:
            viewBox.removeItem(self._maskItem)
            self._maskItem = None

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

        Args:
            width: (int)
            height: (int)

        Returns:
            A tupple, representing the preferred size
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
            self._actHistOnOff.next()

        if ev.key() == qtc.Qt.Key_A:
            self._actAxisOnOff.next()

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

    def __getVisibleItemsBoundingRect(self):
        """
        Return the bounding rectangle of all visible items.
        Returns: (QRectF)
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
        """ Calculate the image scale

        Returns: (float) the image scale
        """
        viewBox = self.getViewBox()
        bounds = viewBox.rect()
        vr = viewBox.viewRect()
        if vr.width() == 0:
            return 0
        scale = bounds.width() / float(vr.width())

        return scale

    def __onRoiRegionChanged(self, roi):
        """ Slot for roi mask region changed """
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
        """
        Slot for roi mask region changed started. """
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

    def __normalizeMask(self):
        """
        Normalize the mask by setting the pixel values to 0 and 1

        Returns: (u8bit numpy array) the mask
        """
        if self._maskItem is not None:
            data = self._maskItem.image
            w, h = (data.shape[1],
                    data.shape[0])
            maskData = np.zeros(shape=(w, h), dtype=np.uint8)
            for i in range(w):
                for j in range(h):
                    if data[i][j] <= 1:
                        maskData[i][j] = 0
                    else:
                        maskData[i][j] = 1
            return maskData
        return None

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
        """ This slot is invoked when the action histogram is triggered.
        Sets the axis orientation """
        self.setAxisOrientation(state)

    @qtc.pyqtSlot(int)
    def __actHistOnOffChanged(self, state):
        """ This slot is invoked when the action histogram is triggered.
        Show or hide the  histogram widget """
        self._imageView.ui.histogram.setVisible(bool(state))

    @qtc.pyqtSlot(int)
    def __actAxisOnOffTriggered(self, state):
        """ This slot is invoked when the action axis-on-off is triggered.
        Show or hide the axis """
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
        This slot is invoked when the spinbox value for image scale is changed.
        Set the given scale to this ImageView
        """
        self.setScale(value * 0.01)

    @qtc.pyqtSlot(object)
    def __onImageScaleChanged(self, view):
        """ Invoked when the image scale has changed. This slot is connected to
        the sigTransformChanged pyqtgraph.ViewBox used for the internal
        pyqtgraph.ImageView. Update the spinbox image scale and emits
        sigScaleChanged
        """
        if not self.__updatingImage:
            self.__viewRect = self.getViewRect()
            scale = self.__calcImageScale()
            if not round(scale, 2) == round(self._scale, 2):
                self._scale = scale
                self._spinBoxScale.setValue(self._scale * 100)
                self.sigScaleChanged.emit(self._scale)

    def setRoiMaskSize(self, size):
        """
        Sets the size to the roi mask. If the ROI mask has been configured,
        then sets a new size to the roi mask.
        Args:
            size: (int) The roi size
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
        """ Show or hide the TextItem used to display the roi mask size """
        self._textItem.setVisible(visible)

    def getMask(self):
        """ Return the current image mask data """
        return self._maskItem.getMask() if self._maskItem else self._maskData

    def getMaskSize(self):
        """ Return the image mask size. This function si valid only if a roi
        mask has been configured and return None in other case """
        if self._roi:
            return int(self._roi.boundingRect().width())
        return None

    def getMaskColor(self):
        """ Return the mask color """
        return self._maskColor

    def getMaskData(self):
        """ Return the mask data. If mask-type is CONSTANT it is the value of
        entire mask. If the mask-type is DATA, this is a numpy array with values
        of the mask. If no mask has been configured, return None """
        return self._maskData

    def setMaskColor(self, color):
        """
        Set the mask color.

        Args:
            color: (str) The color in #ARGB format. Example: #22AAFF00
                         or (qtg.QColor)
        """
        if self._maskItem:
            self._maskItem.setMaskColor(qtg.QColor(color))

    def setImageMask(self, **kwargs):
        """ Set the mask to use in this ImageView.

        If mask=None, the current mask will be removed.

        Keyword Args:
            type:   ROI_CIRCLE (display a circular mask from center) or
                    ROI_RECT (display rectangular mask from center) or
                    CONSTANT (generate a data mask with given constant value) or
                    DATA (just provide a data mask as numpy array)
            color:  (str or QColor) The color in #ARGB format.
                    Example: #22AAFF00. Default value: '#2200FF55'
            data:   If the type is ROI_CIRCLE or ROI_RECT, it is the value of
                    the radius of the mask. If type is CONSTANT it is the value
                    of entire mask. Finally, if the type is DATA, this should be
                    a numpy array with values of the mask.
            showHandles: (boolean) Enable/Disable the ROI handles
        """
        self.__removeMask()  # remove previous mask
        self._maskColor = qtg.QColor(kwargs.get('color', '#2200FF55'))
        self._maskData = kwargs.get('data')
        self._maskType = kwargs.get('type')
        self._showMaskHandles = kwargs.get('showHandles', False)
        if self._model is not None:
            isROI = self._maskType == CIRCLE_ROI or self._maskType == RECT_ROI
            self._maskPenSize = self._maskData if isROI else 1
            self._showMaskHandles = kwargs.get('showHandles', True)
            vb = self.getViewBox()
            imgItem = self._imageView.getImageItem()

            if isROI:
                maskItem = _MaskItem(imgItem, imgItem, self._maskType,
                                     self._maskPenSize, self._showMaskHandles)
                maskItem.setMaskColor(self._maskColor)
                self._roi = maskItem.getRoi()

                b = imgItem.boundingRect()
                r = self._roi.boundingRect()
                maskItem.setMaxBounds(b)
                self._roi.setPos(imgItem.pos() +
                                 pg.Point((b.width() - r.width()) / 2,
                                          (b.height() - r.height()) / 2))
                self._textItem = pg.TextItem(
                    text="", color=(220, 220, 0),
                    fill=pg.mkBrush(color=(0, 0, 0, 128)))
                vb.addItem(self._roi)
                vb.addItem(self._textItem)
                self._roi.sigRegionChanged.connect(self.__onRoiRegionChanged)
                self._roi.sigRegionChangeStarted.connect(
                    self.__onRoiRegionChangedStarted)
                self._roi.sigRegionChangeFinished.connect(
                    self.__onRoiRegionChangedFinished)
                vb.addItem(maskItem)
                self._maskItem = maskItem
            elif self._maskData is not None:
                self.__createMaskItem(self._maskData)

    def setAxisOrientation(self, orientation):
        """ Sets the axis orientation for this ImageView.

        Args:
            orientation: Orientation of the axis. Possible values are:

                * AXIS_TOP_LEFT: axis in top-left
                * AXIS_TOP_RIGHT: axis in top-right
                * AXIS_BOTTOM_RIGHT: axis in bottom-right
                * AXIS_BOTTOM_LEFT: axis in bottom-left
         """
        self._axisPos = orientation
        self.__setupAxis()

    def getViewBox(self):
        """ Return the pyqtgraph.ViewBox used for the internal
        pyqtgraph.ImageView. See pyqtgraph.ImageView"""
        view = self._imageView.getView()
        if isinstance(view, pg.PlotItem):
            view = view.getViewBox()
        return view

    def getImageView(self):
        """ Return the internal pyqtgraph.ImageView """
        return self._imageView

    def setModel(self, imageModel, fitToSize=True):
        """ Set the image model to be used for this ImageView.

        Args:
            imageModel: Input :class:`ImageModel <datavis.models.ImageModel>`
        """
        dim = (0, 0) if self._model is None else self._model.getDim()
        self.clear()

        if imageModel:
            self.__updatingImage = True
            rect = self.getViewRect() if self._model else None
            if self._rowMajor:
                data = imageModel.getData().T
            else:
                data = imageModel.getData()

            self._imageView.setImage(data,
                                     autoRange=True,
                                     levels=self._levels)

            if not fitToSize and dim == imageModel.getDim():
                self.setViewRect(rect or self.getViewRect())
            else:
                self.fitToSize()
            self.__updatingImage = False

            self.updateImageScale()
        else:
            self.__removeMask()

        self._model = imageModel
        if self._maskOperation is not None:
            self.__onMaskCreatorShowHideTriggered(
                self._actMaskCreatorShowHide.get())
        elif self._maskItem is None:
            self.setImageMask(type=self._maskType, color=self._maskColor,
                              data=self._maskData,
                              showHandles=self._showMaskHandles)
        elif self._maskType == CIRCLE_ROI or self._maskType == RECT_ROI:
            imgItem = self._imageView.getImageItem()
            b = imgItem.boundingRect()
            r = self._roi.boundingRect()
            self._maskItem.setMaxBounds(b)
            self._roi.setPos(imgItem.pos() +
                             pg.Point((b.width() - r.width()) / 2,
                                      (b.height() - r.height()) / 2))
        self.sigScaleChanged.emit(self._scale)

    def updateImageScale(self):
        """ Update the image scale, calculating the current scale. """
        self.__viewRect = self.getViewRect()
        self._scale = self.__calcImageScale()

    def setLevels(self, levels):
        """ Set levels for the display. """
        self._levels = levels
        if self._model is not None:
            #  reload the image data with the new levels
            self.imageModelChanged()

    @qtc.pyqtSlot()
    def imageModelChanged(self):
        """ Call this function when the image model has been modified externally

        In this case, the ImageView will need to be notified so that the view
        can be updated.
        """
        data = None if self._model is None else self._model.getData()
        # conserve image QTransform
        t = self._imageView.getImageItem().transform()
        # For image change, not emit sigScaleChanged
        self.__updatingImage = True
        if self._rowMajor:
            data = data.T
        self._imageView.setImage(data, transform=t, levels=self._levels)
        self._imageView.getView().setRange(rect=self.__viewRect, padding=0.0)
        self.__updatingImage = False

    def setViewRect(self, rect):
        """ Set the current view rect.
        The view rect is the rect region that will be visible in the view.

        Args:
            rect: (QRect) The view rect
        """
        self._imageView.getView().setRange(rect=rect, padding=0.0)

    @qtc.pyqtSlot(int)
    def rotate(self, angle):
        """
        Make a rotation according to the given angle.
        Does not modify the image.
        Args:
            angle: (int) The angle(in degrees)
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
        """ Flip the image horizontally (Image data is not modified). """
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
        """ Flips the image vertically. (Image data is not modified). """
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
        """ Show or hide the tool bar. """
        self._toolBar.setVisible(visible)

    def showMenuButton(self, visible=True):
        """ Show or hide the menu button used by the internal
        pyqtgraph.ImageView """
        self._imageView.ui.menuBtn.setVisible(visible)

    def showRoiButton(self, visible=True):
        """ Show or hide the ROI button. used by the internal
        pyqtgraph.ImageView """
        self._imageView.ui.menuBtn.setVisible(visible)

    def showHistogram(self, visible=True):
        """ Show or hide the histogram widget used by the internal
        pyqtgraph.ImageView. """
        self._imageView.ui.histogram.setVisible(visible)

    def setImageInfo(self, **kwargs):
        """ Set the image info that will be displayed.

        Keyword Args:
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
        """ Returns the view rect area. See pyqtgraph.ViewBox.viewRect() """
        view = self.getViewBox()

        return view.viewRect()

    def getView(self):
        """ Returns the widget used for the internal pyqtgraph.ImageView
        to display image data.

        Returns: pyqtgraph.ViewBox (or other compatible object)
                 used by pyqtgraph.ImageView to display the image data """
        return self._imageView.getView()

    def getViewSize(self):
        """ Returns the image view size.

        Returns: A tupple (width, height) representing the view size
        """
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
        """ Return the ImageItem object used for in pyqtgraph.ImageView.
         See pyqtgraph.ImageView.getImageItem

         Returns:
             pyqtgraph.ImageItem
         """
        return self._imageView.getImageItem()

    def getToolBar(self):
        """ Get the left side toolbar. """
        return self._toolBar

    def getPreferredSize(self):
        """ Returns a tuple (width, height), which represents the preferred
        dimensions to contain all the image """
        if self._model is None:
            return 800, 600
        w = self._imageView.ui.histogram.item.width()
        hw = w if self._showHistogram else 0

        plot = self._imageView.getView()
        dim = self._model.getDim()
        width, height = self.__getPreferredImageSize(dim[0], dim[1])
        padding = 105
        width += hw + padding

        if self._toolBar.hasVisiblePanel():
            width += self._toolBar.getPanelMaxWidth()

        if isinstance(plot, pg.PlotItem):
            bottomAxis = plot.getAxis("bottom")
            topAxis = plot.getAxis("top")
            leftAxis = plot.getAxis("left")
            rightAxis = plot.getAxis("right")
            axisPadding = 65
            if bottomAxis is not None and bottomAxis.isVisible():
                height += bottomAxis.boundingRect().height()
                if len(bottomAxis.label.toPlainText()):
                    height += axisPadding
            if topAxis is not None and topAxis.isVisible():
                height += topAxis.boundingRect().height()
                if len(topAxis.label.toPlainText()):
                    height += axisPadding
            if leftAxis is not None and leftAxis.isVisible():
                width += leftAxis.boundingRect().width()
                if len(leftAxis.label.toPlainText()):
                    width += axisPadding
            if rightAxis is not None and rightAxis.isVisible():
                width += rightAxis.boundingRect().width()
                if len(rightAxis.label.toPlainText()):
                    width += axisPadding

        return width, height

    def eventFilter(self, obj, event):
        """ Filters events if this object has been installed as an event filter
        for the watched object.

        Args:
            obj: watched object
            event: event

        Returns:
            True if this object has been installed, False otherwise.
        """
        t = event.type()
        if t == qtc.QEvent.KeyPress:
            self.__imageViewKeyPressEvent(event)
            return True

        return qtw.QWidget.eventFilter(self, obj, event)

    def getScale(self):
        """ Return the image scale. """
        return self.__calcImageScale()

    def setScale(self, scale):
        """ Set de image scale.

        Args:
            scale: (float) The new image scale.
        """
        viewBox = self.getViewBox()
        if scale == 0:
            self._spinBoxScale.setValue(self._scale * 100)
        elif not round(scale, 2) == round(self._scale, 2):
            self.__updatingImage = True
            s = self.getScale()
            viewBox.scaleBy(x=s, y=s)  # restore to 100 %
            viewBox.scaleBy(x=1/scale, y=1/scale)  # to current scale
            self.__updatingImage = False
            self.updateImageScale()
            self._spinBoxScale.setValue(scale * 100)

    def setXLink(self, imageView):
        """
        Link the X axis to another ImageView.

        Args:
            imageView: (ImageView) The ImageView widget to be linked
        """
        if isinstance(imageView, ImageView):
            local = self.getView()
            view = imageView.getView()
            local.setXLink(view)

    def setYLink(self, imageView):
        """
        Link the Y axis to another ImageView.
        Args:
            imageView: (ImageView) The ImageView widget to be linked
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

        Args:
            path:       (str) The image path. If no path is specified,
                        then a save dialog will be displayed
            background: (str or qtg.QColor) The background color
            antialias:  (boolean) Use antialiasing for render the image
            exportView: (boolean) If true, all the view area will be exported
                        else export the image
        """
        v = self.getView()
        if not exportView:
            rect = self.__getVisibleItemsBoundingRect()
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

    def getMaskImage(self):
        """ Return the mask created by the user using the Mask Creator Tools.

        Returns: (u8bit numpy array) or None
        """
        m = self.__normalizeMask()
        if m is not None and self._rowMajor:
            m = m.T
        return m

    def getMaskType(self):
        """ Return the mask-type. Possible values are:
        ROI_CIRCLE, ROI_RECT, CONSTANT, DATA or None if no mask has been
        configured. """
        return self._maskType


class ImageExporter(pgImageExporter):
    """
    The ImageExporter class provides functionality to export an scene rect to
    image file. The exact set of image formats supported will depend on qtc.Qt
    libraries. However, common formats such as PNG, JPG, and TIFF are almost
    always available.
    """
    def __init__(self, item, sourceRect):
        """
        Creates an ImageExporter object.

        Args:
            item: the item to be exported. Can be an individual graphics item
            or a scene.
            sourceRect: (QRect) The source rect
        """
        self._sourceRect = sourceRect
        pgImageExporter.__init__(self, item)

    def setSourceRect(self, rect):
        """ Set the source rect.
        Args:
            rect: (qtc.QRect)
        """
        self._sourceRect = rect

    def getTargetRect(self):
        """ Return the target rect. """
        return self._sourceRect

    def getSourceRect(self):
        """ Return the source rect. """
        return self._sourceRect

    def export(self, fileName=None, toBytes=False, copy=False):
        """
        Export the scene to image file.

        Args:
            fileName: (str)  The file path. If fileName is None,
                            pop-up a file dialog.
            toBytes:  (boolean) If toBytes is True, return a bytes object
                                rather than writing to file.
            copy:     (boolean) If copy is True, export to the copy buffer
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
    """
    Represents a graphics mask item that can add to a QGraphicsScene. It can be
    configured for circle-roi or rect-roi types.
    """
    def __init__(self, parent, imageItem, roiType=CIRCLE_ROI, size=100,
                 showHandles=True):
        """
        Construct a _MaskItem object

        Args:
            parent: The parent object
            imageItem: The image item hover the mask will be shown
            roiType: The roi type. Possible values are: CIRCLE_ROI, RECT_ROI
            size: (int) The roi size
            showHandles: If True, the roi handles will be shown
        """
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
        """ Updates the Qt object(QRegion) used in paint method """
        pos = self._roi.pos()
        rect = self._roi.boundingRect()
        self._roiRegion = qtg.QRegion(pos.x(), pos.y(), rect.width(), rect.height(),
                                  self._regionType)

    def setMaskColor(self, maskColor):
        """
        Set the mask color

        Args:
            maskColor: (str) The mask color in ARGB format. Example: '#22FF00AA'
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
        QAbstractGraphicsShapeItem """
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
        Set the max bounds

        Arg:
            bounds:(QRect, QRectF, or None) Specifies boundaries that the ROI
                      cannot be dragged outside of by the user. Default is None.
        """
        self._roi.maxBounds = bounds


class _CustomMaskItem(pg.ImageItem):
    """ Represents a graphics image mask item that can add to a QGraphicsScene.
    It can be configured with specific mask data and color """
    def __init__(self, imageItem, maskColor, maskData):
        """
        Construct an _CustomMaskItem object

        Args:
            imageItem: (pyqtgraph.ImageItem) The image item
            maskColor: (str) The mask color in ARGB format. Example: '#22FF00AA'
                        or (QColor)
            maskData:  (numpy array) The mask data
        """
        if imageItem is None:
            raise Exception("Invalid ImageItem: None value")

        pg.ImageItem.__init__(self, image=maskData)
        self.setMaskColor(maskColor)
        self._imageItem = imageItem
        self.maskData = maskData

    def setMaskColor(self, maskColor):
        """
        Set the mask color.

        Args:
            maskColor: (str) The mask color in ARGB format. Example: '#22FF00AA'
                        or (QColor)
        """
        self._maskColor = maskColor
        if maskColor is not None:
            c = qtg.QColor(maskColor)
            lut = [(c.red(), c.green(), c.blue(), c.alpha())]
            for i in range(254):
                lut.append((0, 0, 0, 0))
            self.setLookupTable(lut)

    def getMaskColor(self):
        """ Return the mask color """
        return self._maskColor

    def getMask(self):
        """ Return the mask data """
        return self.maskData

    def setMaxBounds(self, bounds):
        """
        Set the maz bounds
        :param bounds: (QRect, QRectF, or None) Specifies mask boundaries.
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

        Args:
            parent:  (QObject) The parent object
        """
        qtw.QStyledItemDelegate.__init__(self, parent)
        self._imageView = ImageView(parent=None, toolBar=False, axis=False)
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
        Reimplemented from QStyledItemDelegate
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
        scene = pgImageView.ui.graphicsView.scene()
        scene.setSceneRect(rect)
        rect.setRect(x + self._sBorder, y + self._sBorder,
                     w - 2 * self._sBorder, h - 2 * self._sBorder)

        scene.render(painter, rect)
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
        Return the image data provided by the given index

        Arg:
            index: QModelIndex
            height: height to scale the image
        """
        imgData = index.data(widgets.DATA_ROLE)

        return imgData

    def getImageView(self):
        """ Return the ImageView used to render de thumbnails """
        return self._imageView

    def setLevels(self, levels):
        """
        Set levels for the image configuration.

        Args:
            levels: (tupple) Minimum an maximum pixel values
        """
        self._imageView.setLevels(levels)

    def getTextHeight(self):
        """ The height of text """
        return self._textHeight


class PenROI(pg.CircleROI):
    """ Circular ROI subclass without handles. """
    def __init__(self, pos, size, **args):
        pg.ROI.__init__(self, pos, size, **args)

    def _updateHoverColor(self):
        """ Reimplemented. Don't set yellow color """
        pass
