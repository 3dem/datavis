
import os

from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QFrame, QSizePolicy, QLabel,
                             QGridLayout, QSlider, QPushButton, QSpacerItem)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QPalette, QPainter, QPainterPath, QPen, QColor
from emqt5.widgets.image import GalleryView

import qtawesome as qta
import numpy as np
import pyqtgraph as pg
import em


class VolumeSlice(QWidget):
    """
    Declaration of Volume Slice class
    """
    def __init__(self, imagePath, parent=None, **kwargs):

        super(VolumeSlice, self).__init__(parent)

        self._imagePath = imagePath
        self._image = None
        self.enableSlicesLine = kwargs.get('--enable-slicesLines', False)
        self.enableAxis = kwargs.get('--enable-axis', False)
        if self.isEmImage(self._imagePath):
            self.setMinimumWidth(300)
            self.setMinimumHeight(400)

            self._initComponents()
            self.volumeSlice()

    def _onTopSliderChange(self, value):
        """
        Display a Top View Slice in a specific value
        :param value: value of Slide
        """
        self.sliceY = value
        self.topLabelValue.setText(str(value))
        self.topView.setImage(self.array3D[:, self.sliceY, :])
        self.renderArea.setShiftY(40*value/self.dy)

    def _onFrontSliderChange(self, value):
        """
         Display a Front View Slice in a specific value
        :param value: value of Slide
        """
        self.sliceZ = value
        self.frontLabelValue.setText(str(value))
        self.frontView.setImage(self.array3D[self.sliceZ, :, :])
        self.renderArea.setShiftZ(40*value/self.dz)

    def _onRightSliderChange(self, value):
        """
        Display a Front View Slice in a specific value
        :param value: value of Slide
        """
        self.sliceX = value
        self.rightLabelValue.setText(str(value))
        self.rightView.setImage(self.array3D[:, :, self.sliceX])
        self.renderArea.setShiftX(40*value/self.dx)

    def _onTopLineVChange(self, pos):
        """
        This Slot is executed when the Horizontal Line in the Top View is moved.
        Display a slices in the right plane
        :param pos: new pos of the horizontal line
        """
        pos1 = pos.x()
        self.rightSlider.setValue(pos1)
        self._onRightSliderChange(int(pos1))

    def _onTopLineHChange(self, pos):
        """
        This Slot is executed when the Horizontal Line in the Top View is moved.
        Display a slices in the front plane
        :param pos: new pos of the horizontal line
        """
        pos1 = pos.y()
        self.frontSlider.setValue(pos1)
        self._onFrontSliderChange(int(pos1))

    def _onFrontLineHChange(self, pos):
        """
        This Slot is executed when the Horizontal Line in the Front View is moved.
        Display a slices in the top plane
        :param pos: new pos of the horizontal line
        """
        pos1 = pos.y()
        self.topSlider.setValue(pos1)
        self._onTopSliderChange(int(pos1))

    def _onFrontLineVChange(self, pos):
        """
        This Slot is executed when the Vertical Line in the Front View is moved.
        Display a slices in the right plane
        :param pos: new pos of the vertical line
        """
        pos1 = pos.x()
        self.rightSlider.setValue(pos1)
        self._onRightSliderChange(int(pos1))

    def _onRightLineHChange(self, pos):
        """
        This Slot is executed when the Horizontal Line in the Right View is moved.
        Display a slices in the top plane
        :param pos: new pos of the horizontal line
        """
        pos1 = pos.y()
        self.topSlider.setValue(pos1)
        self._onTopSliderChange(int(pos1))

    def _onRightLineVChange(self, pos):
        """
        This Slot is executed when the Vertical Line in the Right View is moved.
        Display a slices in the front plane
        :param pos: new pos of the vertical line
        """
        pos1 = pos.x()
        self.frontSlider.setValue(pos1)
        self._onFrontSliderChange(int(pos1))

    def _initComponents(self):
        """
        Init all Volume Slice Components
        :return:
        """
        self._image = None
        self.topView = pg.ImageView(self, view=pg.PlotItem())
        self.frontView = pg.ImageView(self, view=pg.PlotItem())
        self.rightView = pg.ImageView(self, view=pg.PlotItem())
        self.renderArea = RenderArea()

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
            self.topView.close()
            self.frontView.close()
            self.rightView.close()
            self.topWidget.close()
            self.rightWidget.close()
            self.frontWidget.close()
            self.renderArea.close()
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

            self.dx = dim.x
            self.dy = dim.y
            self.dz = dim.z

            """x1 = np.linspace(-30, 10, 128)[:, np.newaxis, np.newaxis]
            x2 = np.linspace(-20, 20, 128)[:, np.newaxis, np.newaxis]
            y = np.linspace(-30, 10, 128)[np.newaxis, :, np.newaxis]
            z = np.linspace(-20, 20, 128)[np.newaxis, np.newaxis, :]
            d1 = np.sqrt(x1 ** 2 + y ** 2 + z ** 2)
            d2 = 2 * np.sqrt(x1[::-1] ** 2 + y ** 2 + z ** 2)
            d3 = 4 * np.sqrt(x2 ** 2 + y[:, ::-1] ** 2 + z ** 2)
            data = (np.sin(d1) / d1 ** 2) + (np.sin(d2) / d2 ** 2) + (
                    np.sin(d3) / d3 ** 2)

            self.dx = 128
            self.dy = 128
            self.dz = 128

            self.array3D = np.array(data, copy=False)"""

            if self.dz > 1:  # The image has a volumes

                # Create a numpy 3D array with the image values pixel
                self.array3D = np.array(self._image, copy=False)

                self.sliceZ = int(self.dz / 2)
                self.sliceY = int(self.dy / 2)
                self.sliceX = int(self.dx / 2)

                # Create a window with three ImageView widgets with
                # central slice on each axis
                self.createVolumeSliceDialog(self.dx, self.dy, self.dz)

                # Display the data on the Top View
                self.topView.setImage(self.array3D[:, self.sliceY, :])
                self.topView.getView().setAspectLocked(False)

                # Display the data on the Front View
                self.frontView.setImage(self.array3D[self.sliceZ, :, :])
                self.frontView.getView().setAspectLocked(False)

                # Display the data on the Right View
                self.rightView.setImage(self.array3D[:, :, self.sliceX])
                self.rightView.getView().setAspectLocked(False)

    def createVolumeSliceDialog(self, x, y, z):
        """
        Create a window with the Volume Slice Dialog

        :param x: number of slices in the right view
        :param y: number of slices in the top view
        :param z: number of slices in the front view
        """
        # Create a main widgets
        self.gridLayoutSlice = QGridLayout(self)
        self.setLayout(self.gridLayoutSlice.layout())

        # Create a Top View Slice (widgets)
        self.topWidget = QFrame(self)
        self.toplayout = QGridLayout()
        self.topWidget.setLayout(self.toplayout.layout())
        self.topSlider = QSlider(self)
        self.topSlider.setMinimum(0)
        self.topSlider.setMaximum(y-1)
        self.topSlider.setValue(int(y / 2))

        self.topLabelValue = QLabel(self)
        self.topLabelValue.setText(str(self.topSlider.value()))
        self.topLabelValue.setAlignment(Qt.AlignCenter)

        self.topSlider.valueChanged.connect(self._onTopSliderChange)
        sizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.topSlider.sizePolicy().hasHeightForWidth())
        self.topSlider.setSizePolicy(sizePolicy)
        self.topSlider.setOrientation(Qt.Horizontal)

        self.toplayout.addWidget(self.topLabelValue, 0, 2)
        self.toplayout.addWidget(QLabel('Top View'), 0, 0)
        self.toplayout.addWidget(self.topSlider, 0, 1)
        self.toplayout.setAlignment(Qt.AlignCenter)

        # Create a Front View Slice (widgets)
        self.frontWidget = QFrame(self)
        self.frontlayout = QGridLayout()
        self.frontWidget.setLayout(self.frontlayout.layout())
        self.frontSlider = QSlider(self)
        self.frontSlider.setMinimum(0)
        self.frontSlider.setMaximum(z-1)
        self.frontSlider.setValue(int(z/2))

        self.frontLabelValue = QLabel(self)
        self.frontLabelValue.setText(str(self.frontSlider.value()))
        self.frontLabelValue.setAlignment(Qt.AlignCenter)

        self.frontSlider.valueChanged.connect(self._onFrontSliderChange)
        sizePolicy = QSizePolicy(QSizePolicy.Minimum,
                                 QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.frontSlider.sizePolicy().hasHeightForWidth())
        self.frontSlider.setSizePolicy(sizePolicy)
        self.frontSlider.setOrientation(Qt.Horizontal)

        self.frontlayout.addWidget(self.frontLabelValue, 0, 2)
        self.frontlayout.addWidget(QLabel('Front View'), 0, 0)
        self.frontlayout.addWidget(self.frontSlider, 0, 1)
        self.frontlayout.setAlignment(Qt.AlignCenter)

        # Create a Right View Slice (widgets)
        self.rightWidget = QFrame(self)
        self.rightlayout = QGridLayout()
        self.rightWidget.setLayout(self.rightlayout.layout())
        self.rightSlider = QSlider(self)
        self.rightSlider.setMinimum(0)
        self.rightSlider.setMaximum(x-1)
        self.rightSlider.setValue(int(x / 2))

        self.rightLabelValue = QLabel(self)
        self.rightLabelValue.setText(str(self.rightSlider.value()))
        self.rightLabelValue.setAlignment(Qt.AlignCenter)

        self.rightSlider.valueChanged.connect(self._onRightSliderChange)
        sizePolicy = QSizePolicy(QSizePolicy.Minimum,
                                 QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.rightSlider.sizePolicy().hasHeightForWidth())
        self.rightSlider.setSizePolicy(sizePolicy)
        self.rightSlider.setOrientation(Qt.Horizontal)

        self.rightlayout.addWidget(self.rightLabelValue, 0, 2)
        self.rightlayout.addWidget(QLabel('Right View'), 0, 0)
        self.rightlayout.addWidget(self.rightSlider, 0, 1)
        self.rightlayout.setAlignment(Qt.AlignCenter)

        # Create three ImageView widgets with central slice on each axis.
        # We put inside a vertical and horizontal line to select the image slice
        # in each view

        if self.enableAxis:
            # Top View Axis
            self.topAxisV = pg.InfiniteLine(angle=90, pen='y', label='Z',
                                            pos=[-10, 0])
            self.topAxisH = pg.InfiniteLine(angle=0, pen='y', label='X',
                                            pos=[0, self.dx + 5])
            self.topView.getView().getViewBox().addItem(self.topAxisV)
            self.topView.getView().getViewBox().addItem(self.topAxisH)

            # Front View Axis
            self.frontAxisV = pg.InfiniteLine(angle=90, pen='y', label='Y',
                                              pos=[-10, 0])
            self.frontAxisH = pg.InfiniteLine(angle=0, pen='y', label='X',
                                              pos=[0, self.dx + 5])
            self.frontView.getView().getViewBox().addItem(self.frontAxisV)
            self.frontView.getView().getViewBox().addItem(self.frontAxisH)

            # Right View Axis
            self.rightAxisV = pg.InfiniteLine(angle=90, pen='y', label='Z',
                                              pos=[-10, 0])
            self.rightAxisH = pg.InfiniteLine(angle=0, pen='y', label='Y',
                                              pos=[0, self.dx + 5])
            self.rightView.getView().getViewBox().addItem(self.rightAxisV)
            self.rightView.getView().getViewBox().addItem(self.rightAxisH)

        if self.enableSlicesLine:  #  Put into the Slices an horizontal and
                                   #  vertical lines
            # Top View Lines
            self.topLineV = pg.InfiniteLine(angle=90, movable=True, pen='g',
                                    pos=[self.sliceX, self.sliceX])
            self.topLineV.setBounds([0, self.sliceX*2-1])
            self.topLineH = pg.InfiniteLine(angle=0, movable=True, pen='b',
                                    pos=[self.sliceX, self.sliceX])
            self.topLineH.setBounds([0, self.sliceX*2-1])

            self.topView.getView().getViewBox().addItem(self.topLineV)
            self.topView.getView().getViewBox().addItem(self.topLineH)

            self.topLineV.sigDragged.connect(self._onTopLineVChange)
            self.topLineH.sigDragged.connect(self._onTopLineHChange)

            # Front View Lines
            self.frontLineV = pg.InfiniteLine(angle=90, movable=True, pen='g',
                                            pos=[self.sliceX, self.sliceX])
            self.frontLineV.setBounds([0, self.sliceX * 2 - 1])
            self.frontLineH = pg.InfiniteLine(angle=0, movable=True, pen='r',
                                            pos=[self.sliceX, self.sliceX])
            self.frontLineH.setBounds([0, self.sliceX * 2 - 1])

            self.frontView.getView().getViewBox().addItem(self.frontLineV)
            self.frontView.getView().getViewBox().addItem(self.frontLineH)

            self.frontLineV.sigDragged.connect(self._onFrontLineVChange)
            self.frontLineH.sigDragged.connect(self._onFrontLineHChange)

            # Right View Lines
            self.rightLineV = pg.InfiniteLine(angle=90, movable=True, pen='b',
                                              pos=[self.sliceX, self.sliceX])
            self.rightLineV.setBounds([0, self.sliceX * 2 - 1])
            self.rightLineH = pg.InfiniteLine(angle=0, movable=True, pen='r',
                                              pos=[self.sliceX, self.sliceX])
            self.rightLineH.setBounds([0, self.sliceX * 2 - 1])

            self.rightView.getView().getViewBox().addItem(self.rightLineV)
            self.rightView.getView().getViewBox().addItem(self.rightLineH)

            self.rightLineV.sigDragged.connect(self._onRightLineVChange)
            self.rightLineH.sigDragged.connect(self._onRightLineHChange)


        # Put in the Grid all components
        self.gridLayoutSlice.addWidget(self.topView, 0, 0)
        self.gridLayoutSlice.addWidget(self.renderArea, 0, 1)
        self.gridLayoutSlice.addWidget(self.topWidget, 1, 0)

        self.gridLayoutSlice.addWidget(self.frontView, 2, 0)
        self.gridLayoutSlice.addWidget(self.frontWidget, 3, 0)

        self.gridLayoutSlice.addWidget(self.rightView, 2, 1)
        self.gridLayoutSlice.addWidget(self.rightWidget, 3, 1)

        # Disable all image operations
        self.topView.ui.menuBtn.hide()
        self.topView.ui.roiBtn.hide()
        self.topView.ui.histogram.hide()


        self.frontView.ui.menuBtn.hide()
        self.frontView.ui.roiBtn.hide()
        self.frontView.ui.histogram.hide()


        self.rightView.ui.menuBtn.hide()
        self.rightView.ui.roiBtn.hide()
        self.rightView.ui.histogram.hide()

        plotTopView = self.topView.getView()
        plotTopView.showAxis('bottom', False)
        plotTopView.showAxis('left', False)

        plotFrontView = self.frontView.getView()
        plotFrontView.showAxis('bottom', False)
        plotFrontView.showAxis('left', False)

        plotRightView = self.rightView.getView()
        plotRightView.showAxis('bottom', False)
        plotRightView.showAxis('left', False)


    @staticmethod
    def isEmImage(imagePath):
        """ Return True if imagePath has an extension recognized as supported
            EM-image """
        _, ext = os.path.splitext(imagePath)
        return ext in ['.mrc', '.mrcs', '.spi', '.stk', '.map']


class RenderArea(QWidget):
    def __init__(self, parent=None):
        super(RenderArea, self).__init__(parent)
        self.shiftx = 0
        self.widthx = 40
        self.shifty = 0
        self.widthy = 40
        self.shiftz = 0
        self.widthz = 20
        self.boxaxis = 'z'

        self.setBackgroundRole(QPalette.Base)

    def minimumSizeHint(self):
        return QSize(30, 30)

    def sizeHint(self):
        return QSize(80, 80)

    def setShiftZ(self, value):
        self.boxaxis = 'z'
        self.shiftz = value
        self.update()

    def setShiftY(self, value):
        self.boxaxis = 'y'
        self.shifty = value
        self.update()

    def setShiftX(self, value):
        self.boxaxis = 'x'
        self.shiftx = value
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.scale(self.width() / 110.0, self.height() / 110.0)

        ox = 50
        oy = 50
        wx = self.widthx
        wy = self.widthy
        wz = self.widthz

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

        self.size = float(self.widthx)
        bw = 30
        bwz = float(wz) / wx * bw

        if self.boxaxis == 'z':
            shiftz = float(self.widthz) / self.size * self.shiftz
            box = ox - shiftz
            boy = oy + shiftz
            rectPath.moveTo(box, boy)
            rectPath.lineTo(box, boy - bw)
            rectPath.lineTo(box + bw, boy - bw)
            rectPath.lineTo(box + bw, boy)

        elif self.boxaxis == 'y':
            shifty = float(self.widthy) / self.size * self.shifty
            box = ox
            boy = oy - shifty
            rectPath.moveTo(box, boy)
            rectPath.lineTo(box + bw, boy)
            rectPath.lineTo(box + bw - bwz, boy + bwz)
            rectPath.lineTo(box - bwz, boy + bwz)

        elif self.boxaxis == 'x':
            shiftx = float(self.widthx) / self.size * self.shiftx
            box = ox + shiftx
            boy = oy
            rectPath.moveTo(box, boy)
            rectPath.lineTo(box, boy - bw)
            rectPath.lineTo(box - bwz, boy - bw + bwz)
            rectPath.lineTo(box - bwz, boy + bwz)

        rectPath.closeSubpath()
        painter.drawPath(rectPath)
