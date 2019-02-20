#!/usr/bin/python
# -*- coding: utf-8 -*-

from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal, QEvent
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QSlider, QSizePolicy,
                             QGridLayout, QSpinBox, QLabel)

from .model import ImageCache, X_AXIS, Y_AXIS, Z_AXIS, N_DIM
from .image_view import ImageView

from emqt5.utils import EmImage, EmPath


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

    def __init__(self, parent, **kwargs):
        """
        Constructor. SlicesView use an ImageView for display the slices,
        see ImageView class for initialization params.

        parent : (QWidget) Specifies the parent widget to which this ImageView
                 will belong. If None, then the SlicesView is created with
                 no parent.
        cache : The image cache to use for load images
        volume_axis : 'x', 'y', 'z', None (for stacks)
        path : The image path
        index : The slice index. First index is 0

        """
        QWidget.__init__(self, parent=parent)
        self._imageCache = kwargs.get('cache', None) or ImageCache(10)
        self._sliceIndex = 0
        self._index = 0
        self._axis = N_DIM
        self._imagePath = None
        self._dim = None
        self._viewRect = None

        self.__setupUI(**kwargs)
        self.setup(**kwargs)

    def __setupUI(self, **kwargs):
        self._mainLayout = QVBoxLayout(self)
        self._mainLayout.setSpacing(0)
        self._mainLayout.setContentsMargins(0, 0, 0, 0)
        sizePolicy = QSizePolicy(QSizePolicy.MinimumExpanding,
                                 QSizePolicy.MinimumExpanding)
        self._imageView = ImageView(self, **kwargs)
        self._imageView.setSizePolicy(sizePolicy)
        self._imageView.installEventFilter(self)
        self._mainLayout.addWidget(self._imageView)
        self._slider = QSlider(self)
        sizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self._slider.sizePolicy().hasHeightForWidth())
        self._slider.setSizePolicy(sizePolicy)
        self._slider.setOrientation(Qt.Horizontal)
        self._slider.valueChanged.connect(self._onSliderChange)
        self._label = QLabel(self)
        grid = QGridLayout()
        grid.setSpacing(0)
        grid.setContentsMargins(1, 1, 1, 1)
        self._spinBox = QSpinBox(self)
        self._spinBox.valueChanged.connect(self._onSpinBoxChanged)
        grid.addWidget(self._label, 0, 0)
        grid.addWidget(self._slider, 0, 1)
        grid.addWidget(self._spinBox, 0, 2)
        grid.setAlignment(Qt.AlignCenter)
        self._mainLayout.addLayout(grid)

    def __showSlice(self):
        """ Load the slice """
        try:
            if self._imagePath is None:
                self._imageView.clear()
            else:
                imgId = '%i-%s' % (self._index, self._imagePath)
                data = self._imageCache.addImage(imgId, self._imagePath,
                                                 self._index)
                if data is not None:
                    if self._axis == X_AXIS:
                        data = data[:, :, self._sliceIndex]
                    elif self._axis == Y_AXIS:
                        data = data[:, self._sliceIndex, :]
                    elif self._axis == Z_AXIS:
                        data = data[self._sliceIndex, :, :]

                    self._imageView.setImage(data)
                    if self._viewRect is not None:
                        self._imageView.getView().setRange(rect=self._viewRect,
                                                           padding=0.0)
                else:
                    self._imageView.clear()
        except Exception as ex:
            raise ex
        except RuntimeError as ex:
            raise ex

    def __setupNavWidgets(self):
        """ Configure the navigation widgets (QSlider, QSpinBox) """
        if self._dim is not None:
            if self._axis == X_AXIS:
                size = self._dim.x
            elif self._axis == Y_AXIS:
                size = self._dim.y
            elif self._axis == Z_AXIS:
                size = self._dim.z
            else:
                size = self._dim.n

            index = self._index if self._axis == N_DIM else int(size / 2)

            blocked = self._spinBox.blockSignals(True)
            self._spinBox.setMinimum(0)
            self._spinBox.setMaximum(size - 1)
            self._spinBox.setValue(index)
            self._spinBox.blockSignals(blocked)

            blocked = self._slider.blockSignals(True)
            self._slider.setMinimum(0)
            self._slider.setMaximum(size - 1)
            self._slider.setValue(index)
            self._slider.blockSignals(blocked)

    @pyqtSlot(int)
    def _onSpinBoxChanged(self, value):
        """ Invoked when change the spinbox value """
        if self._axis == N_DIM:
            self._index = value
        else:
            self._sliceIndex = value

        try:
            self._slider.setValue(value)
        except Exception as ex:
            print(ex)
        except RuntimeError as ex:
            print(ex)

    @pyqtSlot(int)
    def _onSliderChange(self, value):
        """ Invoked when change the spinbox value """
        try:
            if self._axis == N_DIM:
                self._index = value
            else:
                self._sliceIndex = value

            self.__showSlice()
            if not self._spinBox.value() == value:
                self._spinBox.setValue(value)
        except Exception as ex:
            raise ex
        except RuntimeError as ex:
            raise ex

        self.sigCurrentIndexChanged.emit(value)

    def setImageCache(self, imageCache):
        """ Sets the image cache """
        self._imageCache = imageCache

    def setup(self, **kwargs):
        """ Setups this slice view. See constructor for init params. """
        self._imageView.setup(**kwargs)
        self._sliceIndex = kwargs.get('index', -1)
        self.setAxis(kwargs.get('volume_axis', None))
        self.setPath(kwargs.get('path', None))
        self.setViewName(kwargs.get('view_name', ''))
        if self._imagePath:
            info = EmImage.getInfo(self._imagePath)
            if info:
                dt = info.get("data_type")
                self._imageView.setImageInfo(path=self._imagePath,
                                             format=info.get("ext", ""),
                                             data_type=dt.toString())

    def setViewName(self, text):
        """ Sets the view name """
        self._label.setText(text)

    def setPath(self, path):
        """
        Sets the image path.(initialize slice index to 0)
        None value for clear.
        """
        try:
            self._imagePath = path
            self._dim = None if self._imagePath is None else \
                EmImage.getDim(self._imagePath)

            self.setSliceIndex(0)
            self.setIndex(0)
            self.__setupNavWidgets()
        except Exception as ex:
            raise ex
        except RuntimeError as ex:
            raise ex

    def setAxis(self, axis):
        """ Sets the axis for this view. ('x', 'y', 'z' or None for stacks) """
        if axis == 'x':
            self._axis = X_AXIS
        elif axis == 'y':
            self._axis = Y_AXIS
        elif axis == 'z':
            self._axis = Z_AXIS
        else:
            self._axis = N_DIM

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
        if event.type() == QEvent.Wheel:
            if obj == self._imageView:  # Calculate the View scale
                self._viewRect = self._imageView.getViewRect()

        return True

    def getIndex(self):
        """ Returns the current image index (for image stacks) """
        return self._index

    def getSliceRange(self):
        """ Returns a tuple (min, max) """
        return self._slider.minimum(), self._slider.maximum()

    def setIndex(self, index):
        """ Sets the current image index (for stacks) """
        if self._dim is not None and index in range(0, self._dim.n):
            self._index = index

    def getSliceIndex(self):
        """ Return the current slice index """
        return self._sliceIndex

    def setSliceIndex(self, index):
        """ Sets the slice index """
        if self._dim is None:
            self._sliceIndex = 0
        else:
            if self._axis == X_AXIS and index in range(0, self._dim.x):
                self._sliceIndex = index
            elif self._axis == Y_AXIS and index in range(0, self._dim.y):
                self._sliceIndex = index
            elif self._axis == Z_AXIS and index in range(0, self._dim.z):
                self._sliceIndex = index
            else:
                self._sliceIndex = 0

            try:
                self._onSliderChange(index)
            except Exception as ex:
                raise ex
            except RuntimeError as ex:
                raise ex
