#!/usr/bin/python
# -*- coding: utf-8 -*-

from PyQt5.QtCore import pyqtSlot, pyqtSignal, QEvent, Qt
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QSizePolicy, QHBoxLayout)

from emviz.models import EmptySlicesModel
from emviz.widgets import SpinSlider
from ._image_view import ImageView


class SlicesView(QWidget):
    """
    This view can be used when displaying 3D data:
    (a) a single volume (x, y, z, 1)
    (b) stacks of particles (x, y, 1, n).
    In the case (b) for particles, usually the gallery view will be preferred,
    but for movies (stacks of frames), this view is very useful since these are
    big images and will take much memory loading all of them at once.
    """
    sigSliceChanged = pyqtSignal(int)  # Signal for current slice changed

    def __init__(self, parent, sliceModel, **kwargs):
        """ Constructor. SlicesView use an ImageView for display the slices,
        see ImageView class for initialization params.

        parent :        (QWidget) Specifies the parent widget to which
                        this ImageView will belong.
                        If None, then the SlicesView is created with no parent.
        text:           (str) Text to be display in the slider.
        currentValue:   (int) The index (starting at 1) of the initial slice.
        """
        QWidget.__init__(self, parent=parent)
        self._sliceModel = sliceModel
        self._viewRect = None
        self._text = kwargs.get('text', '')
        self._currentValue = kwargs.get('currentValue', 1)
        self._imageViewKwargs = kwargs.get('imageViewKwargs', {})
        self._imageModel = None
        self.__setupGUI()

    def __setupGUI(self):
        """ This is the standard method for the GUI creation """
        # Create ImageView widget
        self._imageView = ImageView(self, **self._imageViewKwargs)
        self._imageView.setSizePolicy(QSizePolicy(QSizePolicy.MinimumExpanding,
                                                  QSizePolicy.MinimumExpanding))
        self._imageView.installEventFilter(self)

        # Create SpinSlider widget
        _, _, n = self._sliceModel.getDim()
        self._spinSlider = SpinSlider(self, text=self._text,
                                      minValue=1, maxValue=n,
                                      currentValue=self._currentValue)
        self._onSliceChanged(self._currentValue)

        # Arrange widgets in a vertical layout
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._imageView)
        self._spinSlider.setMaximumWidth(400)
        l = QHBoxLayout()
        l.addWidget(self._spinSlider, Qt.AlignCenter)
        layout.addLayout(l)

        self._spinSlider.sigValueChanged.connect(self._onSliceChanged)

    @pyqtSlot(int)
    def _onSliceChanged(self, value):
        """ Load the slice """
        value -= 1
        if self._imageModel is None:
            self._imageModel = self._sliceModel.getImageModel(value)
            self._imageView.setModel(self._imageModel)
        else:
            imgData = self._sliceModel.getData(value)
            if imgData is not None:
                self._imageModel.setData(imgData)
                self._imageView.imageModelChanged()
                if self._viewRect is not None:
                    self._imageView.getView().setRange(rect=self._viewRect,
                                                       padding=0.0)
            else:
                self._imageView.clear()

        self.sigSliceChanged.emit(value)

    def eventFilter(self, obj, event):
        """
        Filters events if this object has been installed as an event filter for
        the obj object.
        In our reimplementation of this function, we always filter the event.
        In this case, the function return true. We install self as even filter
        for ImageView.
        :param obj: object
        :param event: event
        :return: True
        """
        t = event.type()
        if obj == self._imageView:  # Calculate the View scale
            c = t in [QEvent.Wheel, QEvent.MouseMove, QEvent.MouseButtonRelease]
            if c:
                self._viewRect = self._imageView.getViewRect()

        return True

    def getValue(self):
        """ Returns the value of the current slice. """
        return self._spinSlider.getValue()

    def setValue(self, value):
        """ Set the current value to a different one. """
        self._spinSlider.setValue(value)

    def getRange(self):
        """ Returns a tuple (min, max) with the slices range. """
        return self._spinSlider.getRange()

    def setText(self, text):
        """
        Set the label text for the internal slider
        :param text: (str) The text
        """
        self._spinSlider.setText(text)

    def getText(self):
        """
        Returns the label text for the internal slider
        """
        return self._spinSlider.getText()

    def setModel(self, model, **kwargs):
        """
        Set the data model
        :param model: The model or None for clear the view
        :param kwargs: Extra params
            * normalize (bool) If true, set the ImageView levels
            * slice (int) If not None, set this as the initial slice
        """
        self._sliceModel = model
        self._imageModel = None

        minSlice, maxSlice = 1, 1 if model is None else model.getDim()[2]
        self._currentValue = kwargs.get('slice', 1)

        self._spinSlider.setRange(minSlice, maxSlice)
        if model is not None and kwargs.get('normalize', False):
            self._imageView.setLevels(model.getMinMax())

        if self._spinSlider.getValue() == self._currentValue:
            self._onSliceChanged(self._currentValue)
        else:
            self._spinSlider.setValue(self._currentValue)

    def clear(self):
        """ Clear the view """
        self.setModel(EmptySlicesModel())

