#!/usr/bin/python
# -*- coding: utf-8 -*-

import PyQt5.QtCore as qtc
import PyQt5.QtWidgets as qtw

from datavis.widgets import (PageBar, TriggerAction, ZoomSpinBox, PagingInfo,
                           AxisSelector)
from datavis.models import (AXIS_X, AXIS_Y, AXIS_Z, AXIS_XYZ, EmptyTableModel,
                          EmptyVolumeModel, SlicesTableModel)
from ._multislice_view import MultiSliceView
from ._gallery import GalleryView
from ._constants import PIXEL_UNITS, GALLERY, SLICES, CIRCLE_ROI, RECT_ROI


class VolumeView(qtw.QWidget):
    """ View to display a volume and allows to switch between
    :class:`~datavis.views.MultiSliceView` and
    :class:`~datavis.views.GalleryView`.

    In case of multiple volumes, this view could be extended with a way
    to select which volume to display.
    """
    def __init__(self, model, **kwargs):
        """ Create a new VolumeView instance.

        Args:
            model: Input :class:`~datavis.models.VolumeModel` instance.

        Keyword Args:
            parent: (QWidget) Parent widget.
            cellSize: (int) The default cell size
            maxCellSize: (int) The maximum value for cell size
            minCellSize: (int) The minimum value for cell size
            zoomUnits: (int) The zoom type for GalleryView cells:
                PIXEL_UNITS or PERCENT_UNITS
            galleryKwargs: Configuration params for the internal
                :class:`~datavis.views.GalleryView`.
            slicesKwargs: Configuration params for the internal
                :class:`~datavis.views.MultiSliceView`.
            slicesMode: (int) Specifies which axis will be visible.
                Possible values: AXIS_X, AXIS_Y, AXIS_Z, AXIS_XYZ
        """
        qtw.QWidget.__init__(self, parent=kwargs.get('parent'))
        self._defaultCellSize = kwargs.get("cellSize", 120)
        self._maxCellSize = kwargs.get("maxCellSize", 300)
        self._minCellSize = kwargs.get("minCellSize", 20)
        self._zoomUnits = kwargs.get("zoomUnits", PIXEL_UNITS)
        self._view = kwargs.get('view', GALLERY)
        self.__setupGUI(model,
                        kwargs.get('slicesKwargs', dict()),
                        kwargs.get('slicesMode', AXIS_XYZ),
                        kwargs.get('galleryKwargs', dict()))
        self.setModel(model)
        self.setView(self._view)
        self._onChangeCellSize(self._defaultCellSize)

        w, h = self.getPreferredSize()
        self.setGeometry(0, 0, w, h)

    def __setupGUI(self, model, slicesKwargs, slicesMode, galleryKwargs):
        """ Setups the GUI """
        self._mainLayout = qtw.QVBoxLayout(self)
        self._mainLayout.setSpacing(0)
        self._mainLayout.setContentsMargins(1, 1, 1, 1)
        self._toolBar = qtw.QToolBar(self)
        self._mainLayout.addWidget(self._toolBar)
        self._stackedLayoud = qtw.QStackedLayout(self._mainLayout)
        self._stackedLayoud.setSpacing(0)
        self._mainLayout.addLayout(self._stackedLayoud)
        # actions
        self._actionGroupViews = qtw.QActionGroup(self._toolBar)
        self._actionGroupViews.setExclusive(True)

        self._aSlices = TriggerAction(parent=self._toolBar,
                                      actionName='Multi Slices View',
                                      text='Multi Slices View',
                                      faIconName='fa.sliders',
                                      checkable=True,
                                      slot=self._onMultiSlicesViewTriggered)
        self._actionGroupViews.addAction(self._aSlices)
        self._toolBar.addAction(self._aSlices)
        self._aSlices.setChecked(True)
        self._aGallery = TriggerAction(parent=self._toolBar,
                                       actionName='Gallery View',
                                       text='Gallery View', faIconName='fa.th',
                                       checkable=True,
                                       slot=self._onGalleryViewTriggered)
        self._actionGroupViews.addAction(self._aGallery)
        self._toolBar.addAction(self._aGallery)
        self._toolBar.addSeparator()
        # cell size
        zoomSpin = ZoomSpinBox(self._toolBar, valueType=int,
                               minValue=self._minCellSize,
                               maxValue=self._maxCellSize,
                               currentValue=self._defaultCellSize,
                               zoomUnits=ZoomSpinBox.PERCENT)
        zoomSpin.sigValueChanged[int].connect(self._onChangeCellSize)

        self._actZoomSpinGallery = self._toolBar.addWidget(zoomSpin)
        self._zoomSpinGallery = zoomSpin
        # ImageViews zoom
        zoomSpin = ZoomSpinBox(self._toolBar, valueType=float,
                               minValue=1, maxValue=10000,
                               zoomUnits=ZoomSpinBox.PERCENT)
        zoomSpin.sigValueChanged[float].connect(self._onChangeImgZoom)
        zoomSpin.sigIconClicked.connect(self.fitToSize)
        self._actZoomSpinImg = self._toolBar.addWidget(zoomSpin)
        self._zoomSpinImg = zoomSpin

        # for multiple volumes
        self._pagingInfo = PagingInfo(1, 1)
        self._pageBar = PageBar(parent=self._toolBar,
                                pagingInfo=self._pagingInfo)
        self._pageBar.setMaximumWidth(150)
        self._actPageBar = self._toolBar.addWidget(self._pageBar)
        self._pageBar.sigPageChanged.connect(self._onVolumeChanged)
        # FIXME [phv] Hide until review the volume stacks
        self._actPageBar.setVisible(False)

        # views
        d = {'model': model.getSlicesModel(AXIS_X)}
        d.update(slicesKwargs.get(AXIS_X, dict()))
        slicesKwargs[AXIS_X] = d
        d = {'model': model.getSlicesModel(AXIS_Y)}
        d.update(slicesKwargs.get(AXIS_Y, dict()))
        slicesKwargs[AXIS_Y] = d
        d = {'model': model.getSlicesModel(AXIS_Z)}
        d.update(slicesKwargs.get(AXIS_Z, dict()))
        slicesKwargs[AXIS_Z] = d

        self._multiSlicesView = MultiSliceView(self, slicesKwargs, slicesMode)
        self._multiSlicesView.sigScaleChanged.connect(self.__updateImageScale)
        # for axis selection
        selector = AxisSelector(parent=self)
        a = AXIS_Z if slicesMode == AXIS_XYZ else slicesMode
        self._actAxisSelect = self._toolBar.addWidget(selector)
        selector.sigAxisChanged.connect(self._onAxisChanged)
        selector.setCurrentAxis(a)
        selector.setViewMode(AxisSelector.SHOW_ALL)

        self._axisSelector = selector
        self._stackedLayoud.addWidget(self._multiSlicesView)

        self._galleryView = GalleryView(parent=self,
                                        model=EmptyTableModel(),
                                        **galleryKwargs)

        self._stackedLayoud.addWidget(self._galleryView)
        imgView = self._multiSlicesView.getSliceView(a).getImageView()
        imgView.sigMaskSizeChanged.connect(self.__maskSizeChanged)

    def __setupToolBar(self):
        """ Configure the toolbar according to the current view """
        v = self._view == GALLERY
        # Gallery
        self._actAxisSelect.setVisible(
            v or not self._multiSlicesView.getMode() == AXIS_XYZ)
        self._actZoomSpinGallery.setVisible(v)
        # MultiSliceView
        self._actZoomSpinImg.blockSignals(True)
        self._actZoomSpinImg.setVisible(not v)
        self._actZoomSpinImg.blockSignals(False)

    def __maskSizeChanged(self, size):
        """ Invoked when the mask size is changed in any one of the axis """
        d = self._galleryView.getImageItemDelegate()
        imgView = d.getImageView()
        imgView.setRoiMaskSize(size)

    @qtc.pyqtSlot(float, int)
    def __updateImageScale(self, scale, axis):
        """
        Update the image scale in
        :class:`ZoomSpinBox <datavis.widgets.ZoomSpinBox>`.

        Args:
            scale: (float) The image scale
            axis:  (int) The axis
        """
        self._zoomSpinImg.setValue(scale * 100)
        self._multiSlicesView.setScale(scale)

    @qtc.pyqtSlot(int)
    def _onChangeCellSize(self, size):
        """
        This slot is invoked when the cell size need to be rearranged
        """
        self._galleryView.setIconSize(size)

    @qtc.pyqtSlot(float)
    def _onChangeImgZoom(self, zoom):
        """
        This slot is invoked when the image zoom need to be rearranged
        """
        self._multiSlicesView.setScale(zoom * 0.01)

    @qtc.pyqtSlot(bool)
    def _onMultiSlicesViewTriggered(self, checked):
        """ Triggered function for multi-slices view action """
        if checked:
            self._stackedLayoud.setCurrentWidget(self._multiSlicesView)
            self._view = SLICES

        self._aGallery.setChecked(not checked)
        self.__setupToolBar()

    @qtc.pyqtSlot(int)
    def _onGalleryRowChanged(self, row):
        """ Invoked when change the current gallery row """
        axis = self._axisSelector.getCurrentAxis()
        self._multiSlicesView.setValue(row + 1, axis)

    @qtc.pyqtSlot(bool)
    def _onGalleryViewTriggered(self, checked):
        """ Triggered function for gallery view action """
        if checked:
            self._view = GALLERY
            axis = self._multiSlicesView.getAxis()
            self._axisSelector.setCurrentAxis(axis)
            model = self._slicesTableModels[axis]
            row = self._multiSlicesView.getValue() - 1
            self._stackedLayoud.setCurrentWidget(self._galleryView)
            if not model == self._galleryView.getModel():
                self._galleryView.setModel(model,
                                           minMax=self._model.getMinMax())
            self._galleryView.selectRow(row)
        self._aSlices.setChecked(not checked)
        self.__setupToolBar()

    @qtc.pyqtSlot(int)
    def _onAxisChanged(self, axis):
        """
        Invoked when the current value for
        :class:`AxisSelector <datavis.widgets.AxisSelector>` has been changed

        Args:
            axis: (int) The current axis
        """
        self._multiSlicesView.setAxis(axis)
        sv = self._multiSlicesView.getSliceView(axis)
        m = self._multiSlicesView.getMode()
        if not m == AXIS_XYZ and not self._view == GALLERY:
            zoom = self._zoomSpinImg.getValue()
            sv.getImageView().updateImageScale()
            self._multiSlicesView.setScale(zoom * 0.01)

        imgView = sv.getImageView()
        maskType = imgView.getMaskType()
        if maskType is not None:
            delegate = self._galleryView.getImageItemDelegate()
            maskParams = {
                'type': maskType,
                'color': imgView.getMaskColor(),
                'operation': None,
                'showHandles': True
            }
            if maskType == CIRCLE_ROI or maskType == RECT_ROI:
                maskParams['data'] = int(imgView.getMaskSize() / 2)
                maskParams['showHandles'] = False
            else:  # TODO[hv] if mask has been edited?
                maskParams['data'] = imgView.getMaskData()
            imgView = delegate.getImageView()
            imgView.setImageMask(**maskParams)

        self._galleryView.setModel(self._slicesTableModels[axis],
                                   minMax=self._model.getMinMax())
        self._galleryView.selectRow(self._multiSlicesView.getValue() - 1)

    @qtc.pyqtSlot(int)
    def _onVolumeChanged(self, index):
        # FIXME [phv] Review the volume stacks
        pass

    def getPreferredSize(self):
        w, h = self._multiSlicesView.getPreferredSize()
        return w, h + self._toolBar.height()

    def setModel(self, model):
        """
        Sets the :class:`VolumeModel <datavis.models.VolumeModel>`

        Raises:
            Exception if model is None.
        """

        if model is None:
            raise Exception("Invalid value for model: None")

        self._model = model
        xModel, yModel, zModel = (model.getSlicesModel(AXIS_X),
                                  model.getSlicesModel(AXIS_Y),
                                  model.getSlicesModel(AXIS_Z))
        self._slicesTableModels = {
            AXIS_X: SlicesTableModel(xModel, 'Axis-X'),
            AXIS_Y: SlicesTableModel(yModel, 'Axis-Y'),
            AXIS_Z: SlicesTableModel(zModel, 'Axis-Z')
        }
        self._multiSlicesView.setModel((xModel, yModel, zModel), normalize=True,
                                       slice=int(model.getDim()[0]/2))
        if self._view == GALLERY:
            self._onAxisChanged(self._axisSelector.getCurrentAxis())
        else:
            sv = self._multiSlicesView.getSliceView()
            self._zoomSpinImg.setValue(sv.getScale() * 100)

    def clear(self):
        """ Clear the volume view """
        self.setModel(EmptyVolumeModel())

    def setView(self, view):
        """ Sets the current view: GALLERY or SLICES """
        if view == GALLERY:
            self._view = GALLERY
            self._aGallery.setChecked(True)
            self._onGalleryViewTriggered(True)
        elif view == SLICES:
            self._view = SLICES
            self._aSlices.setChecked(True)
            self._onMultiSlicesViewTriggered(True)

        self.__setupToolBar()

    def fitToSize(self):
        """ Fit the images to the widget size in MultiSliceView"""
        self._multiSlicesView.fitToSize()
        self._zoomSpinImg.setValue(
            self._multiSlicesView.getSliceView().getScale() * 100)

    def getModel(self):
        """ Return the current model """
        return self._model
