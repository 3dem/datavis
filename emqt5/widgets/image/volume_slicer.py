
import os

from PyQt5.QtWidgets import (QWidget, QFrame, QSizePolicy, QLabel,
                             QGridLayout, QSlider, QVBoxLayout, QHBoxLayout,
                             QSpacerItem, QPushButton)
from PyQt5.QtCore import Qt, QSize, QEvent, QPointF, QRectF
from PyQt5.QtGui import QPalette, QPainter, QPainterPath, QPen, QColor, QIcon
import numpy as np
import pyqtgraph as pg
import qtawesome as qta

import em


class VolumeSlice(QWidget):
    """
    Declaration of Volume Slice class
    """
    def __init__(self, parent=None, **kwargs):

        super(VolumeSlice, self).__init__(parent)

        self._imagePath = kwargs.get('imagePath')
        self._image = None
        self._enableSlicesLine = kwargs.get('--enable-slicesLines', False)
        self._enableAxis = kwargs.get('--enable-axis', False)
        if self._imagePath:
            if self.isEmImage(self._imagePath):
                self.setMinimumWidth(500)
                self.setMinimumHeight(500)
                self.__initComponents__()
                self.volumeSlice()

    def _onTopSliderChange(self, value):
        """
        Display a Top View Slice in a specific value
        :param value: value of Slide
        """
        self._sliceY = value
        self._topLabelValue.setText(str(value))

        self._topView.setImage(self._array3D[:, self._sliceY, :])

        if self._topViewScale:
            self._topView.getView().setRange(rect=self._topViewScale,
                                             padding=0.0)

        self._renderArea.setShiftY(40 * value / self._dy-1)

        if value > 0 and value < self._dy:
            self._topBackwardButton.setEnabled(True)
            self._topForwardButton.setEnabled(True)
        if value == 0:
            self._topBackwardButton.setEnabled(False)
        if value == self._dy-1:
            self._topForwardButton.setEnabled(False)

    def _onFrontSliderChange(self, value):
        """
         Display a Front View Slice in a specific value
        :param value: value of Slide
        """
        self._sliceZ = value
        self._frontLabelValue.setText(str(value))
        self._frontView.setImage(self._array3D[self._sliceZ, :, :])

        if self._frontViewScale:
            self._frontView.getView().setRange(rect=self._frontViewScale,
                                             padding=0.0)

        self._renderArea.setShiftZ(40 * value / self._dz-1)

        if value > 0 and value < self._dy:
            self._frontBackwardButton.setEnabled(True)
            self._frontForwardButton.setEnabled(True)
        if value == 0:
            self._frontBackwardButton.setEnabled(False)
        if value == self._dy-1:
            self._frontForwardButton.setEnabled(False)

    def _onRightSliderChange(self, value):
        """
        Display a Front View Slice in a specific value
        :param value: value of Slide
        """
        self._sliceX = value
        self._rightLabelValue.setText(str(value))
        self._rightView.setImage(self._array3D[:, :, self._sliceX])

        if self._rightViewScale:
            self._rightView.getView().setRange(rect=self._rightViewScale,
                                             padding=0.0)

        self._renderArea.setShiftX(40 * value / self._dx-1)

        if value > 0 and value < self._dy:
            self._rightBackwardButton.setEnabled(True)
            self._rightForwardButton.setEnabled(True)
        if value == 0:
            self._rightBackwardButton.setEnabled(False)
        if value == self._dy-1:
            self._rightForwardButton.setEnabled(False)

    def _onTopLineVChange(self, pos):
        """
        This Slot is executed when the Horizontal Line in the Top View is moved.
        Display a slices in the right plane
        :param pos: new pos of the horizontal line
        """
        posX = pos.x()
        self._rightSlider.setValue(posX)
        self._onRightSliderChange(int(posX))

    def _onTopLineHChange(self, pos):
        """
        This Slot is executed when the Horizontal Line in the Top View is moved.
        Display a slices in the front plane
        :param pos: new pos of the horizontal line
        """
        posY = pos.y()
        self._frontSlider.setValue(posY)
        self._onFrontSliderChange(int(posY))

    def _onFrontLineHChange(self, pos):
        """
        This Slot is executed when the Horizontal Line in the Front View is
        moved.
        Display a slices in the top plane
        :param pos: new pos of the horizontal line
        """
        posZ = pos.y()
        self._topSlider.setValue(posZ)
        self._onTopSliderChange(int(posZ))

    def _onFrontLineVChange(self, pos):
        """
        This Slot is executed when the Vertical Line in the Front View is moved.
        Display a slices in the right plane
        :param pos: new pos of the vertical line
        """
        pos1 = pos.x()
        self._rightSlider.setValue(pos1)
        self._onRightSliderChange(int(pos1))

    def _onRightLineHChange(self, pos):
        """
        This Slot is executed when the Horizontal Line in the Right View is
        moved.
        Display a slices in the top plane
        :param pos: new pos of the horizontal line
        """
        pos1 = pos.y()
        self._topSlider.setValue(pos1)
        self._onTopSliderChange(int(pos1))

    def _onRightLineVChange(self, pos):
        """
        This Slot is executed when the Vertical Line in the Right View is moved.
        Display a slices in the front plane
        :param pos: new pos of the vertical line
        """
        pos1 = pos.x()
        self._frontSlider.setValue(pos1)
        self._onFrontSliderChange(int(pos1))

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

            if obj.name == 'TopView':  # Calculate a Top View scale
                self._topViewScale = self._topView.getView().viewRect()

            elif obj.name == 'FrontView':  # Calculate a Front View scale
                self._frontViewScale = self._frontView.getView().viewRect()

            else:  # Calculate a Right View scale
                self._rightViewScale = self._rightView.getView().viewRect()

        return True

    def _onTopBackwardButtonClicked(self):
        """
        Decrease the Top Slider value in one
        Display a Top View Slice in a specific value
        :return:
        """
        self._topSlider.setValue(self._topSlider.value()-1)
        self._onTopSliderChange(self._topSlider.value())
        if self._topSlider.value() == 0:
            self._topBackwardButton.setEnabled(False)

    def _onTopForwardButtonClicked(self):
        """
        Increment the Top Slider value in one
        Display a Top View Slice in a specific value
        :return:
        """
        self._topSlider.setValue(self._topSlider.value()+1)
        self._onTopSliderChange(self._topSlider.value())
        if self._topSlider.value() == self._dy:
            self._topForwardButton.setEnabled(False)

    def _onFrontBackwardButtonClicked(self):
        """
        Decrease the Front Slider value in one
        Display a Front View Slice in a specific value
        :return:
        """
        self._frontSlider.setValue(self._frontSlider.value()-1)
        self._onFrontSliderChange(self._frontSlider.value())
        if self._frontSlider.value() == 0:
            self._frontBackwardButton.setEnabled(False)

    def _onFrontForwardButtonClicked(self):
        """
        Increment the Front Slider value in one
        Display a Front View Slice in a specific value
        :return:
        """
        self._frontSlider.setValue(self._frontSlider.value()+1)
        self._onFrontSliderChange(self._frontSlider.value())
        if self._frontSlider.value() == self._dy:
            self._frontForwardButton.setEnabled(False)

    def _onRightBackwardButtonClicked(self):
        """
        Decrease the Right Slider value in one
        Display a Right View Slice in a specific value
        :return:
        """
        self._rightSlider.setValue(self._rightSlider.value()-1)
        self._onRightSliderChange(self._rightSlider.value())
        if self._rightSlider.value() == 0:
            self._rightBackwardButton.setEnabled(False)

    def _onRightForwardButtonClicked(self):
        """
        Increment the Right Slider value in one
        Display a Right View Slice in a specific value
        :return:
        """
        self._rightSlider.setValue(self._rightSlider.value()+1)
        self._onRightSliderChange(self._rightSlider.value())
        if self._rightSlider.value() == self._dy:
            self._rightForwardButton.setEnabled(False)

    def __initComponents__(self):
        """
        Init all Volume Slice Components
        :return:
        """
        self._image = None

        self._topView = pg.ImageView(self, view=pg.ViewBox(), name='TopView')
        self._topViewScale = None
        self._topView.installEventFilter(self)
        self._topView.getView().setBackgroundColor(self.palette().color(
            QPalette.Window))
        self._topWidget = QFrame(self)

        self._frontView = pg.ImageView(self, view=pg.ViewBox(), name='FrontView')
        self._frontViewScale = None
        self._frontView.installEventFilter(self)
        self._frontView.getView().setBackgroundColor(self.palette().color(
            QPalette.Window))
        self._frontWidget = QFrame(self)

        self._rightView = pg.ImageView(self, view=pg.ViewBox(), name='RightView')
        self._rightViewScale = None
        self._rightView.installEventFilter(self)
        self._rightView.getView().setBackgroundColor(self.palette().color(
            QPalette.Window))
        self._rightWidget = QFrame(self)

        self._renderArea = RenderArea()

    def getImage(self):
        """
        Get the image
        :return: an em-image
        """
        return self._image

    def setImagePath(self, imagePath):
        """
        Set the image Path
        :param imagePath: new image path
        """
        self._imagePath = imagePath

    def setupProperties(self):
        """
        Setup all properties
        """
        if self._image:
            self._image = None
            self._topView.close()
            self._frontView.close()
            self._rightView.close()
            self._topWidget.close()
            self._rightWidget.close()
            self._frontWidget.close()
            self._renderArea.close()
            self.close()

    def volumeSlice(self):
        """
        Given 3D data, select a 2D plane and interpolate data along that plane
        to generate a slice image.
        """
        if self.isEmImage(self._imagePath):

            # Create an image from imagePath using em-bindings
            self._image = em.Image()
            loc2 = em.ImageLocation(self._imagePath)
            self._image.read(loc2)
            # Read the dimensions of the image
            dim = self._image.getDim()

            self._dx = dim.x
            self._dy = dim.y
            self._dz = dim.z

            if self._dz > 1:  # The image has a volumes

                # Create a numpy 3D array with the image values pixel
                self._array3D = np.array(self._image, copy=False)

                self._sliceZ = int(self._dz / 2)
                self._sliceY = int(self._dy / 2)
                self._sliceX = int(self._dx / 2)

                # Create a window with three ImageView widgets with
                # central slice on each axis
                self.createVolumeSliceDialog(self._dx, self._dy, self._dz)

                # Display the data on the Top View
                self._topView.setImage(self._array3D[:, self._sliceY, :])
                self._topView.getView().setAspectLocked(True)

                # Display the data on the Front View
                self._frontView.setImage(self._array3D[self._sliceZ, :, :])
                self._frontView.getView().setAspectLocked(True)

                # Display the data on the Right View
                self._rightView.setImage(self._array3D[:, :, self._sliceX])
                self._rightView.getView().setAspectLocked(True)
            else:
                self.createErrorTextLoadingImage()
                self.setupProperties()

    def createErrorTextLoadingImage(self):
        """
        Create an Error Text because the image do not has a volume
        """
        self.setGeometry(500, 150, 430, 400)
        label = QLabel(self)
        label.setText(' ERROR: A valid 3D image format are required. See the '
                      'image path.')

    def createVolumeSliceDialog(self, x, y, z):
        """
        Create a window with the Volume Slice Dialog

        :param x: number of slices in the right view
        :param y: number of slices in the top view
        :param z: number of slices in the front view
        """
        self.setWindowTitle('Volume-Slicer')
        # Create a main widgets
        self._gridLayoutSlice = QGridLayout(self)
        self.setLayout(self._gridLayoutSlice.layout())

        # Create a Top View Slice (widgets)
        self._toplayout = QGridLayout()
        self._topWidget.setLayout(self._toplayout.layout())
        self._topSlider = QSlider()
        self._topSlider.setMinimum(0)
        self._topSlider.setMaximum(y - 1)
        self._topSlider.setValue(int(y / 2))

        self._topLabelValue = QLabel()
        self._topLabelValue.setText(str(self._topSlider.value()))
        self._topLabelValue.setAlignment(Qt.AlignCenter)

        self._topSlider.valueChanged.connect(self._onTopSliderChange)
        sizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self._topSlider.sizePolicy().hasHeightForWidth())
        self._topSlider.setSizePolicy(sizePolicy)
        self._topSlider.setOrientation(Qt.Horizontal)

        self._topBackwardButton = QPushButton()
        self._topBackwardButton.setIcon(qta.icon('fa.fast-backward'))
        self._topBackwardButton.setMaximumSize(30,15)
        self._topBackwardButton.clicked.connect(
            self._onTopBackwardButtonClicked)

        self._topForwardButton = QPushButton()
        self._topForwardButton.setIcon(qta.icon('fa.fast-forward'))
        self._topForwardButton.setMaximumSize(30, 15)
        self._topForwardButton.clicked.connect(
            self._onTopForwardButtonClicked)

        self._toplayout.addWidget(QLabel('Top View'), 0, 0)
        self._toplayout.addWidget(self._topBackwardButton, 0, 1)
        self._toplayout.addWidget(self._topSlider, 0, 2)
        self._toplayout.addWidget(self._topForwardButton, 0, 3)
        self._toplayout.addWidget(self._topLabelValue, 0, 4)

        self._toplayout.setAlignment(Qt.AlignCenter)

        # Create a Front View Slice (widgets)
        self._frontlayout = QGridLayout()
        self._frontWidget.setLayout(self._frontlayout.layout())
        self._frontSlider = QSlider()
        self._frontSlider.setMinimum(0)
        self._frontSlider.setMaximum(z - 1)
        self._frontSlider.setValue(int(z / 2))

        self._frontLabelValue = QLabel()
        self._frontLabelValue.setText(str(self._frontSlider.value()))
        self._frontLabelValue.setAlignment(Qt.AlignCenter)

        self._frontSlider.valueChanged.connect(self._onFrontSliderChange)
        sizePolicy = QSizePolicy(QSizePolicy.Minimum,
                                 QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self._frontSlider.sizePolicy().hasHeightForWidth())
        self._frontSlider.setSizePolicy(sizePolicy)
        self._frontSlider.setOrientation(Qt.Horizontal)

        self._frontBackwardButton = QPushButton()
        self._frontBackwardButton.setIcon(qta.icon('fa.fast-backward'))
        self._frontBackwardButton.setMaximumSize(30, 15)
        self._frontBackwardButton.clicked.connect(
            self._onFrontBackwardButtonClicked)

        self._frontForwardButton = QPushButton()
        self._frontForwardButton.setIcon(qta.icon('fa.fast-forward'))
        self._frontForwardButton.setMaximumSize(30, 15)
        self._frontForwardButton.clicked.connect(
            self._onFrontForwardButtonClicked)

        self._frontlayout.addWidget(QLabel('Front View'), 0, 0)
        self._frontlayout.addWidget(self._frontBackwardButton, 0, 1)
        self._frontlayout.addWidget(self._frontSlider, 0, 2)
        self._frontlayout.addWidget(self._frontForwardButton, 0, 3)
        self._frontlayout.addWidget(self._frontLabelValue, 0, 4)
        self._frontlayout.setAlignment(Qt.AlignCenter)

        # Create a Right View Slice (widgets)
        self._rightlayout = QGridLayout()
        self._rightWidget.setLayout(self._rightlayout.layout())
        self._rightSlider = QSlider()
        self._rightSlider.setMinimum(0)
        self._rightSlider.setMaximum(x - 1)
        self._rightSlider.setValue(int(x / 2))

        self._rightLabelValue = QLabel()
        self._rightLabelValue.setText(str(self._rightSlider.value()))
        self._rightLabelValue.setAlignment(Qt.AlignCenter)

        self._rightSlider.valueChanged.connect(self._onRightSliderChange)
        sizePolicy = QSizePolicy(QSizePolicy.Minimum,
                                 QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self._rightSlider.sizePolicy().hasHeightForWidth())
        self._rightSlider.setSizePolicy(sizePolicy)
        self._rightSlider.setOrientation(Qt.Horizontal)

        self._rightBackwardButton = QPushButton()
        self._rightBackwardButton.setIcon(qta.icon('fa.fast-backward'))
        self._rightBackwardButton.setMaximumSize(30, 15)
        self._rightBackwardButton.clicked.connect(
            self._onRightBackwardButtonClicked)

        self._rightForwardButton = QPushButton()
        self._rightForwardButton.setIcon(qta.icon('fa.fast-forward'))
        self._rightForwardButton.setMaximumSize(30, 15)
        self._rightForwardButton.clicked.connect(
            self._onRightForwardButtonClicked)

        self._rightlayout.addWidget(QLabel('Right View'), 0, 0)
        self._rightlayout.addWidget(self._rightBackwardButton, 0, 1)
        self._rightlayout.addWidget(self._rightSlider, 0, 2)
        self._rightlayout.addWidget(self._rightForwardButton, 0, 3)
        self._rightlayout.addWidget(self._rightLabelValue, 0, 4)
        self._rightlayout.setAlignment(Qt.AlignCenter)

        # Put into the Grid all components

        self._gridLayoutSlice.addWidget(self._topView, 0, 0)
        self._gridLayoutSlice.addWidget(self._renderArea, 0, 1)
        self._gridLayoutSlice.addWidget(self._topWidget, 1, 0)

        self._gridLayoutSlice.addWidget(self._frontView, 2, 0)
        self._gridLayoutSlice.addWidget(self._frontWidget, 3, 0)

        self._gridLayoutSlice.addWidget(self._rightView, 2, 1)
        self._gridLayoutSlice.addWidget(self._rightWidget, 3, 1)

        # Set the focus to the Top View
        self._topSlider.setFocus()
        self._onTopSliderChange(self._topSlider.value())

        # Disable all image operations
        self._topView.ui.menuBtn.hide()
        self._topView.ui.roiBtn.hide()
        self._topView.ui.histogram.hide()

        self._frontView.ui.menuBtn.hide()
        self._frontView.ui.roiBtn.hide()
        self._frontView.ui.histogram.hide()

        self._rightView.ui.menuBtn.hide()
        self._rightView.ui.roiBtn.hide()
        self._rightView.ui.histogram.hide()

        """ plotTopView = self.topView.getView()
        plotTopView.showAxis('bottom', False)
        plotTopView.showAxis('left', False)

        plotFrontView = self.frontView.getView()
        plotFrontView.showAxis('bottom', False)
        plotFrontView.showAxis('left', False)

        plotRightView = self.rightView.getView()
        plotRightView.showAxis('bottom', False)
        plotRightView.showAxis('left', False)"""

    @staticmethod
    def isEmImage(imagePath):
        """ Return True if imagePath has an extension recognized as supported
            EM-image """
        _, ext = os.path.splitext(imagePath)
        return ext in ['.mrc', '.mrcs', '.spi', '.stk', '.map', '.vol']


class RenderArea(QWidget):
    def __init__(self, parent=None):
        super(RenderArea, self).__init__(parent)
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
        painter.setRenderHint(QPainter.Antialiasing)
        painter.scale(self.height()/100.0, self.height()/100.0)

        ox = 20 + self.width()/8
        oy = 60
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

