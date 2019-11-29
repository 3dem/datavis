#!/usr/bin/python
# -*- coding: utf-8 -*-

import PyQt5.QtWidgets as qtw
import PyQt5.QtCore as qtc

from datavis.models import EmptySlicesModel
from datavis.widgets import SpinSlider
from ._image_view import ImageView


class SlicesView(qtw.QWidget):
    """
    This view can be used when displaying 3D data:
    (a) a single volume (x, y, z, 1)
    (b) stacks of particles (x, y, 1, n).
    In the case (b) for particles, usually the gallery view will be preferred,
    but for movies (stacks of frames), this view is very useful since these are
    big images and will take much memory loading all of them at once.
    """
    sigSliceChanged = qtc.pyqtSignal(int)  # Signal for current slice changed

    def __init__(self, model, **kwargs):
        """ Construct an SlicesView instance.
        SlicesView use an :class:`ImageView <datavis.views.ImageView>`
        to display the slices, see ImageView class for initialization params.

        Args:
            model:      The :class:`SlicesModel <datavis.models.SlicesModel>`

        Keyword Args:
            parent :    (QWidget) Specifies the parent widget to which
                        this ImageView will belong.
                        If None, then the SlicesView is created with no parent.
            text:       (str) Text to be display in the slider.
            currentValue:  (int) The index (starting at 1) of the initial slice.

            imageViewKwargs: The :class:`ImageView <datavis.views.ImageView>`
                             arguments
        """
        qtw.QWidget.__init__(self, parent=kwargs.get('parent'))
        self._model = model
        self._text = kwargs.get('text', '')
        self._currentValue = kwargs.get('currentValue', 1)
        self._imageViewKwargs = kwargs.get('imageViewKwargs', {})
        self._imageModel = None
        self.__setupGUI()
        self.setModel(model, **kwargs)

    def __setupGUI(self):
        """ This is the standard method for the GUI creation """
        # Create ImageView widget
        self._imageView = ImageView(parent=self,
                                    model=self._model.getImageModel(0),
                                    **self._imageViewKwargs)
        self._imageView.setSizePolicy(
            qtw.QSizePolicy(qtw.QSizePolicy.MinimumExpanding,
                            qtw.QSizePolicy.MinimumExpanding))
        self._imageView.installEventFilter(self)

        # Create SpinSlider widget
        _, _, n = self._model.getDim()
        self._spinSlider = SpinSlider(self, text=self._text,
                                      minValue=1, maxValue=n,
                                      currentValue=self._currentValue)
        # Arrange widgets in a vertical layout
        layout = qtw.QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._imageView)
        self._spinSlider.setMaximumWidth(400)
        l = qtw.QHBoxLayout()
        l.addWidget(self._spinSlider, qtc.Qt.AlignCenter)
        layout.addLayout(l)

        self._spinSlider.sigValueChanged.connect(self._onSliceChanged)

    def _onSliceChanged(self, value):
        """ Load the slice indexed by the given index value """
        value -= 1
        if self._imageModel is None:
            self._imageModel = self._model.getImageModel(value)
            self._imageView.setModel(self._imageModel, True)
        else:
            imgData = self._model.getData(value)
            if imgData is not None:
                self._imageModel.setData(imgData)
                self._imageView.imageModelChanged()
            else:
                self._imageView.clear()

        self.sigSliceChanged.emit(value)

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
        """ Set the label text for the internal slider """
        self._spinSlider.setText(text)

    def getText(self):
        """ Returns the label text for the internal slider """
        return self._spinSlider.getText()

    def setScale(self, scale):
        """
        Set the image scale

        Args:
            scale: (float) The scale
        """
        self._imageView.setScale(scale)

    def getScale(self):
        """ Return the current scale """
        return self._imageView.getScale()

    def setModel(self, model, **kwargs):
        """
        Set the :class:`SlicesModel <datavis.models.SlicesModel>`

        Args:
            model: The model or None for clear the view

        Keyword Args:
            normalize: (bool) If true, set the ImageView levels
            slice: (int) If not None, set this as the initial slice
        """
        self._model = model
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

    def getImageView(self):
        """
        Return the :class:`ImageView <datavis.views.ImageView>` widget,
        used to visualize the slices.
        """
        return self._imageView

    def clear(self):
        """ Clear the view """
        self.setModel(EmptySlicesModel())

    def getPreferredSize(self):
        """
        Returns a tuple (width, height), which represents the preferred
        dimensions to contain all the data.
        """
        w, h = self._imageView.getPreferredSize()
        return w, h + self._spinSlider.height()
