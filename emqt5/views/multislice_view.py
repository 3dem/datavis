

from PyQt5.QtWidgets import (QWidget, QGridLayout)
from PyQt5.QtCore import QSize, pyqtSlot
from PyQt5.QtGui import QPalette, QPainter, QPainterPath, QPen, QColor

from emqt5.utils import EmImage
from .slices_view import SlicesView
from .model import ImageCache


class MultiSliceView(QWidget):
    """
    This view is currently used for displaying 3D volumes and it is composed
    by 3 SlicerViews and a custom 2D plot showing the axis and the slider
    position. This view is the default for Volumes.
    """
    def __init__(self, parent, **kwargs):
        """
        Constructor.

        """
        QWidget.__init__(self, parent=parent)
        self._imageCache = kwargs.get('cache', None) or ImageCache(50)
        self._dx = 0
        self._dy = 0
        self._dz = 0
        self._path = kwargs.get('path', None)
        self.__loadImageDim(self._path)

        self.__setupUi(**kwargs)
        if self._path is not None:
            self._onFrontViewIndexChanged(self._frontView.getSliceIndex())
            self._onTopViewIndexChanged(self._topView.getSliceIndex())
            self._onRightViewIndexChanged(self._rightView.getSliceIndex())

    def __setupUi(self, **kwargs):
        self._mainLayout = QGridLayout(self)
        self._mainLayout.setSpacing(0)
        self._mainLayout.setContentsMargins(1, 1, 1, 1)
        kwargs['back_color'] = kwargs.get('back_color',
                                          None) or self.palette().\
            color(QPalette.Window)
        kwargs['border_color'] = kwargs.get('border_color',
                                            None) or self.palette().\
            color(QPalette.Window)
        kwargs['volume_axis'] = 'y'
        self._topView = SlicesView(self, **kwargs)
        self._topView.setImageCache(self._imageCache)
        self._topView.setViewName('Top View')
        self._topView.sigCurrentIndexChanged.connect(
            self._onTopViewIndexChanged)
        kwargs['volume_axis'] = 'z'
        self._frontView = SlicesView(self, **kwargs)
        self._frontView.setImageCache(self._imageCache)
        self._frontView.setViewName('Front View')
        self._frontView.sigCurrentIndexChanged.connect(
            self._onFrontViewIndexChanged)
        kwargs['volume_axis'] = 'x'
        self._rightView = SlicesView(self, **kwargs)
        self._rightView.setImageCache(self._imageCache)
        self._rightView.setViewName('Right View')
        self._rightView.sigCurrentIndexChanged.connect(
            self._onRightViewIndexChanged)
        self._renderArea = RenderArea(self)

        self._mainLayout.addWidget(self._topView, 0, 0)
        self._mainLayout.addWidget(self._renderArea, 0, 1)
        self._mainLayout.addWidget(self._frontView, 1, 0)
        self._mainLayout.addWidget(self._rightView, 1, 1)

    def __loadImageDim(self, path):
        """ Load the em-image dim (x,y,z) """
        if path is not None:
            dim = EmImage.getDim(path)
            if dim is not None:
                self._dx = dim.x
                self._dy = dim.y
                self._dz = dim.z

    @pyqtSlot(int)
    def _onTopViewIndexChanged(self, value):
        """ This slot is invoked when the index of top view change """
        self._renderArea.setShiftY(40 * value / self._dy - 1)

    @pyqtSlot(int)
    def _onFrontViewIndexChanged(self, value):
        """ This slot is invoked when the index of front view change """
        self._renderArea.setShiftZ(40 * value / self._dz - 1)

    @pyqtSlot(int)
    def _onRightViewIndexChanged(self, value):
        """ This slot is invoked when the index of right view change """
        self._renderArea.setShiftX(40 * value / self._dx - 1)

    def loadPath(self, path):
        """ Set the image Path """
        self._path = path
        self.__loadImageDim(path)
        if path is not None:
            self._frontView.setPath(path)
            self._frontView.setSliceIndex(self._dz / 2)
            self._topView.setPath(path)
            self._topView.setSliceIndex(self._dy / 2)
            self._rightView.setPath(path)
            self._rightView.setSliceIndex(self._dx / 2)

            self._onFrontViewIndexChanged(self._frontView.getSliceIndex())
            self._onTopViewIndexChanged(self._topView.getSliceIndex())
            self._onRightViewIndexChanged(self._rightView.getSliceIndex())


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

