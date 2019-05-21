#!/usr/bin/python
# -*- coding: utf-8 -*-

from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal, QEvent
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QSlider, QSizePolicy,
                             QGridLayout, QSpinBox, QLabel)

from emqt5.widgets import SpinSlider
from .image_view import ImageView


class SlicesView(QWidget):
    """
    This view can be used when displaying 3D data:
    (a) a single volume (x, y, z, 1)
    (b) stacks of particles (x, y, 1, n).
    In the case (b) for particles, usually the gallery view will be preferred,
    but for movies (stacks of frames), this view is very useful since these are
    big images and will take much memory loading all of them at once.
    """
    sigCurrentIndexChanged = pyqtSignal(int)  # Signal for current index changed

    def __init__(self, parent, sliceModel, **kwargs):
        """
        Constructor. SlicesView use an ImageView for display the slices,
        see ImageView class for initialization params.

        parent : (QWidget) Specifies the parent widget to which this ImageView
                 will belong. If None, then the SlicesView is created with
                 no parent.
        text: Text to be display in the slider
        currentValue: The index (starting at 1) of the initial slice to display

        """
        QWidget.__init__(self, parent=parent)
        self._sliceModel = sliceModel
        self._viewRect = None
        self._text = kwargs.get('text', '')
        self._currentValue = kwargs.get('currentValue', 1)
        self.__setupUI()

    def __setupUI(self):
        # Create ImageView widget
        self._imageView = ImageView(self)
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
        layout.addWidget(self._spinSlider)

        self._spinSlider.valueChanged.connect(self._onSliceChanged)

    @pyqtSlot(int)
    def _onSliceChanged(self, value):
        """ Load the slice """
        data = self._sliceModel.getData(value)
        if data is not None:
            self._imageView.setImage(data)
            if self._viewRect is not None:
                self._imageView.getView().setRange(rect=self._viewRect,
                                                   padding=0.0)
        else:
            self._imageView.clear()

    # FIXME: Check if this method is needed
    def eventFilter(self, obj, event):
        """
        Filters events if this object has been installed as an event filter for
        the obj object.
        In our reimplementation of this function, we always filter the event.
        In this case, the function return true.
        :param obj: object
        :param event: event
        :return: True
        """
        t = event.type()
        # FIXME: If the image is moved, it should be kept there
        # when changing the slice, tried with MouseMove, but not working
        if t == QEvent.Wheel or t == QEvent.MouseMove:
            if obj == self._imageView:  # Calculate the View scale
                self._viewRect = self._imageView.getViewRect()

        return True

    def getValue(self):
        """ Returns the value of the current slice. """
        return self._index

    def setValue(self, newValue):
        """ Set the current value to a different one. """
        self._spinSlider.setValue(newValue)

    def getRange(self):
        """ Returns a tuple (min, max) with the slices range. """
        return self._slider.minimum(), self._slider.maximum()

