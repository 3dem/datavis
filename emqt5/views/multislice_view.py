

from PyQt5.QtWidgets import (QWidget, QGridLayout)
from PyQt5.QtCore import QSize, pyqtSlot
from PyQt5.QtGui import QPalette, QPainter, QPainterPath, QPen, QColor

from emqt5.utils import ImageManager
from .slices_view import SlicesView
from .model import VolumeDataModel, X_AXIS, Y_AXIS, Z_AXIS


class MultiSliceView(QWidget):
    """
    This view is currently used for displaying 3D volumes and it is composed
    by 3 SlicerViews and a custom 2D plot showing the axis and the slider
    position. This view is the default for Volumes.
    """
    def __init__(self, parent, path=None, model=None, **kwargs):
        """
        path: the volume path
        model: the model
        imageManager: the ImageManager
        """
        QWidget.__init__(self, parent=parent)
        self._imageManager = kwargs.get('imageManager') or ImageManager(50)
        self._dx = 0
        self._dy = 0
        self._dz = 0
        self._axis = X_AXIS
        self._slice = 0
        self._model = model or VolumeDataModel(path, parent=self) \
            if path is not None else None
        if self._model is not None:
            self.__loadImageDim(self._model.getDataSource())
        else:
            self.__loadImageDim(None)

        if kwargs.get('imageManager') is None:
            kwargs['imageManager'] = self._imageManager
        self.__setupUi(**kwargs)
        if self._model is not None:
            self._onFrontViewIndexChanged(self._frontView.getSliceIndex())
            self._onTopViewIndexChanged(self._topView.getSliceIndex())
            self._onRightViewIndexChanged(self._rightView.getSliceIndex())

    def __setupUi(self, **kwargs):
        self._mainLayout = QGridLayout(self)
        self._mainLayout.setSpacing(0)
        self._mainLayout.setContentsMargins(0, 0, 0, 0)
        kwargs['auto_fill'] = 'on'
        kwargs['volume_axis'] = 'y'
        self._topView = SlicesView(self, **kwargs)
        self._topView.setImageManager(self._imageManager)
        self._topView.setViewName('Top View')
        self._topView.sigCurrentIndexChanged.connect(
            self._onTopViewIndexChanged)
        kwargs['volume_axis'] = 'z'
        self._frontView = SlicesView(self, **kwargs)
        self._frontView.setImageManager(self._imageManager)
        self._frontView.setViewName('Front View')
        self._frontView.sigCurrentIndexChanged.connect(
            self._onFrontViewIndexChanged)
        kwargs['volume_axis'] = 'x'
        self._rightView = SlicesView(self, **kwargs)
        self._rightView.setImageManager(self._imageManager)
        self._rightView.setViewName('Right View')
        self._rightView.sigCurrentIndexChanged.connect(
            self._onRightViewIndexChanged)
        self._renderArea = RenderArea(self)

        self._mainLayout.addWidget(self._topView, 0, 0)
        self._mainLayout.addWidget(self._renderArea, 0, 1)
        self._mainLayout.addWidget(self._frontView, 1, 0)
        self._mainLayout.addWidget(self._rightView, 1, 1)

    def __connectModelSignals(self):
        """ Connect all model signals with the current slots """
        if self._model is not None:
            self._model.sigVolumeIndexChanged.\
                connect(self._onVolumeIndexChanged)

    def __setupAllWidgets(self):
        """ Configures the widgets """
        path = None if self._model is None else self._model.getDataSource()

        self._frontView.setPath(path)
        self._topView.setPath(path)
        self._rightView.setPath(path)

        if path is not None:
            index = self._model.getVolumeIndex()
            self._frontView.setVolumeIndex(index)
            self._topView.setVolumeIndex(index)
            self._rightView.setVolumeIndex(index)
            self._frontView.setIndex(index)
            self._frontView.setSliceIndex(int(self._dz / 2))
            self._topView.setIndex(index)
            self._topView.setSliceIndex(int(self._dy / 2))
            self._rightView.setIndex(index)
            self._rightView.setSliceIndex(int(self._dx / 2))

            self._onFrontViewIndexChanged(self._frontView.getSliceIndex())
            self._onTopViewIndexChanged(self._topView.getSliceIndex())
            self._onRightViewIndexChanged(self._rightView.getSliceIndex())

    def __loadImageDim(self, path):
        """ Load the em-image dim (x,y,z) """
        if path is None:
            self._dx = self._dy = self._dz = 0
        else:
            dim = ImageManager.getDim(path)
            if dim is None:
                self._dx = self._dy = self._dz = 0
            else:
                self._dx = dim.x
                self._dy = dim.y
                self._dz = dim.z

    @pyqtSlot(int)
    def _onVolumeIndexChanged(self, index):
        """ This slot is invoked when the volume index change """
        self.__setupAllWidgets()
        self._frontView.setVolumeIndex(index)
        self._topView.setVolumeIndex(index)
        self._rightView.setVolumeIndex(index)

    @pyqtSlot(int)
    def _onTopViewIndexChanged(self, value):
        """ This slot is invoked when the index of top view change """
        self._renderArea.setShiftY(40 * value / self._dy - 1)
        self._axis = Y_AXIS
        self._slice = self._topView.getSliceIndex()

    @pyqtSlot(int)
    def _onFrontViewIndexChanged(self, value):
        """ This slot is invoked when the index of front view change """
        self._renderArea.setShiftZ(40 * value / self._dz - 1)
        self._axis = Z_AXIS
        self._slice = self._frontView.getSliceIndex()

    @pyqtSlot(int)
    def _onRightViewIndexChanged(self, value):
        """ This slot is invoked when the index of right view change """
        self._renderArea.setShiftX(40 * value / self._dx - 1)
        self._axis = X_AXIS
        self._slice = self._rightView.getSliceIndex()

    def loadPath(self, path):
        """ Set the image path. None value for clear the Views """
        self.__loadImageDim(path)
        if path is None:
            self._model = None
        else:
            self._model = VolumeDataModel(path, parent=self)

        self.__setupAllWidgets()

    def setImageManager(self, imageManager):
        """
        Setter for imageManager
        :param imageManager: The ImageManager
        """
        self._imageManager = imageManager
        self._rightView.setImageManager(imageManager)
        self._frontView.setImageManager(imageManager)
        self._topView.setImageManager(imageManager)

    def clear(self):
        """
        This is an overloaded function. Sets the image path to None value
        """
        self.loadPath(None)

    def setModel(self, model):
        """ Sets the model for this view """
        if model is None:
            self.clear()
        else:
            self._model = model
            self.__loadImageDim(model.getDataSource())
            self.__setupAllWidgets()

    def getAxis(self):
        """ Return the current axis """
        return self._axis

    def setAxis(self, axis):
        """ Sets the current axis """
        self._axis = axis

    def getSlice(self):
        """ Return the current slice index for the current axis """
        return self._slice

    def getPreferredSliceIndex(self, axis):
        """ Return the preferred slice for the given axis """
        if axis == X_AXIS:
            r = self._rightView.getSliceRange()
        elif axis == Y_AXIS:
            r = self._topView.getSliceRange()
        elif axis == Z_AXIS:
            r = self._frontView.getSliceRange()

        return r[0] + int((r[1] - r[0]) / 2)

    def setSlice(self, sliceIndex):
        """ Sets the current slice index """
        if self._axis == X_AXIS:
            self._rightView.setSliceIndex(sliceIndex)
        elif self._axis == Y_AXIS:
            self._topView.setSliceIndex(sliceIndex)
        elif self._axis == Z_AXIS:
            self._frontView.setSliceIndex(sliceIndex)


class RenderArea(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self._shiftx = 0
        self._widthx = 40
        self._shifty = 0
        self._widthy = 40
        self._shiftz = 0
        self._widthz = 20
        self._boxaxis = 'z'
        self._oldPosX = 60

        self.setBackgroundRole(QPalette.Base)

    def paintEvent(self, event):
        painter = QPainter(self)
        w = self.width()
        h = self.height()
        painter.setRenderHint(QPainter.Antialiasing)
        painter.translate(w / 3 + 20, h / 2)
        scale = w if w < h else h
        painter.scale(scale / 100.0, scale / 100.0)
        ox = 0
        oy = 0
        wx = self._widthx
        wy = self._widthy
        wz = self._widthz

        # Draw Y axis
        ty = oy - wy
        painter.setPen(QColor(200, 0, 0))
        painter.drawLine(ox, oy, ox, ty)
        painter.drawLine(ox, ty, ox - 1, ty + 1)
        painter.drawLine(ox, ty, ox + 1, ty + 1)
        painter.drawLine(ox + 1, ty + 1, ox - 1, ty + 1)

        # Draw X axis
        tx = ox + wx
        painter.setPen(QColor(0, 0, 200))
        painter.drawLine(ox, oy, tx, oy)
        painter.drawLine(tx - 1, oy + 1, tx, oy)
        painter.drawLine(tx - 1, oy - 1, tx, oy)
        painter.drawLine(tx - 1, oy + 1, tx - 1, oy - 1)

        # Draw Z axis
        painter.setPen(QColor(0, 200, 0))
        tzx = ox - wz
        tzy = oy + wz
        painter.drawLine(ox, oy, tzx, tzy)
        painter.drawLine(tzx, tzy - 1, tzx, tzy)
        painter.drawLine(tzx + 1, tzy, tzx, tzy)
        painter.drawLine(tzx + 1, tzy, tzx, tzy - 1)
        # painter.drawPath(self.path)

        # Draw labels
        painter.setPen(QColor(0, 0, 0))
        painter.drawText(tx - 5, oy + 15, "x")
        painter.drawText(ox - 15, ty + 15, "y")
        painter.drawText(tzx + 5, tzy + 10, "z")

        painter.setPen(QPen(QColor(50, 50, 50), 0.3))
        painter.setBrush(QColor(220, 220, 220, 100))
        rectPath = QPainterPath()

        self.size = float(self._widthx)
        bw = 30
        bwz = float(wz) / wx * bw

        if self._boxaxis == 'z':
            shiftz = float(self._widthz) / self.size * self._shiftz
            box = ox - shiftz
            boy = oy + shiftz
            rectPath.moveTo(box, boy)
            rectPath.lineTo(box, boy - bw)
            rectPath.lineTo(box + bw, boy - bw)
            rectPath.lineTo(box + bw, boy)

        elif self._boxaxis == 'y':
            shifty = float(self._widthy) / self.size * self._shifty
            box = ox
            boy = oy - shifty
            rectPath.moveTo(box, boy)
            rectPath.lineTo(box + bw, boy)
            rectPath.lineTo(box + bw - bwz, boy + bwz)
            rectPath.lineTo(box - bwz, boy + bwz)

        elif self._boxaxis == 'x':
            shiftx = float(self._widthx) / self.size * self._shiftx
            box = ox + shiftx
            boy = oy
            rectPath.moveTo(box, boy)
            rectPath.lineTo(box, boy - bw)
            rectPath.lineTo(box - bwz, boy - bw + bwz)
            rectPath.lineTo(box - bwz, boy + bwz)

        rectPath.closeSubpath()
        painter.drawPath(rectPath)

    def setShiftZ(self, value):
        self._boxaxis = 'z'
        self._shiftz = value
        self.update()

    def setShiftY(self, value):
        self._boxaxis = 'y'
        self._shifty = value
        self.update()

    def setShiftX(self, value):
        self._boxaxis = 'x'
        self._shiftx = value
        self.update()

    def minimumSizeHint(self):
        return QSize(30, 30)

    def sizeHint(self):
        return QSize(80, 80)

