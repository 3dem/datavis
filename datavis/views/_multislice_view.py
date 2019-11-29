
import PyQt5.QtCore as qtc
import PyQt5.QtWidgets as qtw
import PyQt5.QtGui as qtg

import datavis as dv

from ._slices_view import SlicesView
from ._constants import AXIS_BOTTOM_LEFT, AXIS_BOTTOM_RIGHT, AXIS_TOP_LEFT


class MultiSliceView(qtw.QWidget):
    """
    This view is currently used for displaying 3D volumes and it is composed
    by 3 :class:`SlicesView <datavis.views.SlicesView>` and a custom 2D plot
    showing the axis and the slider position.
    This view is the default for Volumes.
    """
    # Signal for current slice changed(axis, slice)
    sigSliceChanged = qtc.pyqtSignal(int, int)

    # Signal for current axis changed(axis)
    sigAxisChanged = qtc.pyqtSignal(int)

    # Signal for scale changed (scale, axis)
    sigScaleChanged = qtc.pyqtSignal(float, int)

    def __init__(self, parent, slicesKwargs, mode=dv.models.AXIS_XYZ):
        """
        Create a new MultiSliceView instance

        Args:
            parent:       (QWidget) Parent widget
            slicesKwargs: (dict) A dict with keys of axis(AXIS_X, AXIS_Y,
                          AXIS_Z) and values for the model for each axis.
                          See :class:`SlicesView <datavis.views.SlicesView>`
            mode:         (int) Specifies which axis will be visible.
                          Possible values: AXIS_X, AXIS_Y, AXIS_Z, AXIS_XYZ
        """
        qtw.QWidget.__init__(self, parent=parent)
        self._slicesKwargs = slicesKwargs
        self._slicesDict = {}
        self._axis = dv.models.AXIS_X
        self._slice = -1
        self._mode = mode
        self.__setupGUI()
        w, h = self.getPreferredSize()
        self.setGeometry(0, 0, w, h)

    def __setupGUI(self):
        """ This is the standard method for the GUI creation """
        mainLayout = qtw.QGridLayout(self)
        mainLayout.setSpacing(0)
        mainLayout.setContentsMargins(0, 0, 0, 0)

        axisPos = {
            dv.models.AXIS_X: [1, 2],
            dv.models.AXIS_Y: [0, 1],
            dv.models.AXIS_Z: [1, 1],
            dv.models.AXIS_XYZ: [0, 1]
        }

        slicesInfo = {
            dv.models.AXIS_X: ('X Axis (side)', [1, 1], self._onSliceXChanged),
            dv.models.AXIS_Y: ('Y Axis (top)', [0, 0], self._onSliceYChanged),
            dv.models.AXIS_Z: ('Z Axis (front)', [1, 0], self._onAxisZChanged)
        }

        # Build one SlicesView for each axis, taking into account the
        # input parameters and some reasonable default values
        defaultImgViewKargs = {'histogram': False,
                               'toolBar': False,
                               'autoFill': True,
                               'axis': True,
                               'axisColor': '#000000'
                               }
        xArgs = {
            'labelText': 'X',
            'labelStyle': {'color': '#0000FF',
                           'font-weight': 'bold'}
        }
        yArgs = {
            'labelText': 'Y',
            'labelStyle': {'color': '#FF0000',
                           'font-weight': 'bold'}
        }
        zArgs = {
            'labelText': 'Z',
            'labelStyle': {'color': '#009900',
                           'font-weight': 'bold'}
        }
        axisImgViewKargs = {
            dv.models.AXIS_X: {'labelX': zArgs, 'labelY': yArgs,
                     'axisPos': AXIS_BOTTOM_RIGHT},
            dv.models.AXIS_Y: {'labelX': xArgs, 'labelY': zArgs,
                     'axisPos': AXIS_TOP_LEFT},
            dv.models.AXIS_Z: {'labelX': xArgs, 'labelY': yArgs,
                     'axisPos': AXIS_BOTTOM_LEFT}
        }

        if not self._mode == dv.models.AXIS_XYZ:
            layout = qtw.QStackedLayout()
        else:
            layout = mainLayout

        for axis, args in self._slicesKwargs.items():
            text, pos, slot = slicesInfo[axis]
            model = args['model']
            _, _, n = model.getDim()
            imgViewKargs = dict(defaultImgViewKargs)
            imgViewKargs.update(axisImgViewKargs[axis])
            imgViewKargs.update(args.get('imageViewKwargs', dict()))
            sv = SlicesView(model, parent=self, text=args.get('text', text),
                            currentValue=args.get('currentValue',
                                                  int((n + 1)/2)),
                            imageViewKwargs=imgViewKargs)
            sv.sigSliceChanged.connect(slot)
            imgView = sv.getImageView()
            # FIXME[phv] Determine how to pass the AXIS
            imgView.sigScaleChanged.connect(self.__onScaleChanged)
            imgView.sigMaskSizeChanged.connect(self.__onMaskSizeChanged)
            if self._mode == dv.models.AXIS_XYZ:
                layout.addWidget(sv, *pos)
            else:
                layout.addWidget(sv)

            self._slicesDict[axis] = sv

        self._axisWidget = AxisWidget(self)
        if not self._mode == dv.models.AXIS_XYZ:
            mainLayout.addWidget(self._axisWidget, 0, 1, 
                                 alignment=qtc.Qt.AlignTop)
            mainLayout.addLayout(layout, 0, 0)
        else:
            mainLayout.addWidget(self._axisWidget, 0, 1)

        self._mainLayout = mainLayout

    @qtc.pyqtSlot(float)
    def __onScaleChanged(self, scale):
        """ Called when the image scale is changed in any one of the
        :class:`SlicesView <datavis.views.SlicesView>`. Updates the scale in all
        :class:`SlicesView <datavis.views.SlicesView>`."""
        self.setScale(scale)
        self.sigScaleChanged.emit(scale, dv.models.AXIS_X)

    def __onMaskSizeChanged(self, size):
        """ Called when the roi size is changed """
        for axis in [dv.models.AXIS_X, dv.models.AXIS_Y, dv.models.AXIS_Z]:
            imgView = self._slicesDict[axis].getImageView()
            imgView.setRoiMaskSize(size)

    def _onSliceChanged(self, axis, value):
        """ Called when the slice index is changed in any one of the axis. """
        e = not self._axis == axis
        self._axis = axis
        self._slice = value
        nMax = float(self._slicesDict[axis].getRange()[1] - 1)
        if nMax == 0:
            nMax = 1
        value = nMax - value
        # Convert to 40 scale index that is required by the RenderArea
        renderAreaShift = int(40 * (1 - value / nMax))
        self._axisWidget.setShift(axis, renderAreaShift)
        if e:
            self.sigAxisChanged.emit(self._axis)
        self.sigSliceChanged.emit(axis, value)

    @qtc.pyqtSlot(int)
    def _onSliceYChanged(self, value):
        """ Called when the slice index is changed in Y axis """
        self._onSliceChanged(dv.models.AXIS_Y, value)

    @qtc.pyqtSlot(int)
    def _onAxisZChanged(self, value):
        """ Called when the slice index is changed in Z axis """
        self._onSliceChanged(dv.models.AXIS_Z, value)

    @qtc.pyqtSlot(int)
    def _onSliceXChanged(self, value):
        """ Called when the slice index is changed in Z axis """
        self._onSliceChanged(dv.models.AXIS_X, value)

    def getValue(self, axis=None):
        """ Return the current slice index for the given axis.
         (If axis=None, the last changed axis is used)

        Args:
            axis: AXIS_X or AXIS_Y or AXIS_Z
        """
        return self._slicesDict[axis or self._axis].getValue()

    def setValue(self, value, axis=None):
        """ Sets the slice value for the given axis.
        (If axis is None the last modified axis is used) """
        self._slicesDict[axis or self._axis].setValue(value)

    def getSliceView(self, axis=None):
        """ Return the :class:`SlicesView <datavis.views.SlicesView>` widget
        for the given axis """
        return self._slicesDict[self._axis if axis is None else axis]

    def getAxis(self):
        """ Returns the current axis """
        return self._axis

    def setAxis(self, axis):
        """
        Sets the current axis. Updates the axis graphic.

        Args:
            axis: (int) The axis (AXIS_X or AXIS_Y or AXIS_Z)
        """
        if axis in [dv.models.AXIS_X, dv.models.AXIS_Y, dv.models.AXIS_Z]:
            e = not self._axis == axis
            self._axis = axis
            if not self._mode == dv.models.AXIS_XYZ:
                s = self._mainLayout.itemAtPosition(0, 0).layout()
                s.setCurrentWidget(self._slicesDict[axis])
            self._onSliceChanged(axis, self._slicesDict[axis].getValue())
            if e:
                self.sigAxisChanged.emit(self._axis)
        else:
            raise Exception("Invalid axis value: %d" % axis)

    def getText(self, axis):
        """
        Returns the label text for the given axis

        Args:
            axis: (int) The axis. (AXIS_X or AXIS_Y or AXIS_Z)

        Returns:  (str) The label text

        Raises:
            Exception If the axis is not anyone of the following:
                datavis.models.AXIS_X, datavis.models.AXIS_Y,
                datavis.models.AXIS_Z
        """
        if axis in [dv.models.AXIS_X, dv.models.AXIS_Y, dv.models.AXIS_Z]:
            return self._slicesDict[axis].getText()

        raise Exception("Invalid axis: %d" % axis)

    def setModel(self, models, **kwargs):
        """
        Set the data models for display.

        Args:
            models: (tuple) The models (AXIS_X, AXIS_Y, AXIS_Z) for views
                    or None for clear the view.
        Keyword Args:
            normalize: (bool) If True, each of the
                       :class:`SlicesView <datavis.views.SlicesView>` will be
                       normalized, levels of the image will be set all range
            slice:    (int) Default slice
        """
        if models:
            for axis, model in zip([dv.models.AXIS_X, dv.models.AXIS_Y,
                                    dv.models.AXIS_Z], models):
                self._slicesDict[axis].setModel(model, **kwargs)
        else:
            self.clear()

    def setScale(self, scale):
        """ Set the image scale for all axis
        Args:
            scale: (float) The new image scale.
        """
        for v in self._slicesDict.values():
            v.setScale(scale)

    def getMode(self):
        """ Return the current mode. Possible values:
        AXIS_X, AXIS_Y, AXIS_Z, AXIS_XYZ """
        return self._mode

    def clear(self):
        """ Clear the view """
        for sliceWidget in self._slicesDict.values():
            sliceWidget.clear()

    def fitToSize(self):
        """ Fit images to the widget size """
        for sliceWidget in self._slicesDict.values():
            sliceWidget.getImageView().fitToSize()

    def getPreferredSize(self):
        """
        Returns a tuple (width, height), which represents the preferred
        dimensions to contain all the data
        """
        w, h = 1, 1

        for sv in self._slicesDict.values():
            sw, sh = sv.getPreferredSize()
            w, h = max(w, sw), max(h, sh)

        return 2 * w, 2 * h


class RenderArea:
    def __init__(self):
        self._shiftx = 0
        self._widthx = 40
        self._shifty = 0
        self._widthy = 40
        self._shiftz = 0
        self._widthz = 20
        self._boxaxis = dv.models.AXIS_Z
        self._oldPosX = 60
        self._width = 80
        self._height = 80

    def paint(self, painter):
        w = self._width
        h = self._height
        painter.setRenderHint(qtg.QPainter.Antialiasing)
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
        painter.setPen(qtg.QColor(200, 0, 0))
        painter.drawLine(ox, oy, ox, ty)
        painter.drawLine(ox, ty, ox - 1, ty + 1)
        painter.drawLine(ox, ty, ox + 1, ty + 1)
        painter.drawLine(ox + 1, ty + 1, ox - 1, ty + 1)

        # Draw X axis
        tx = ox + wx
        painter.setPen(qtg.QColor(0, 0, 200))
        painter.drawLine(ox, oy, tx, oy)
        painter.drawLine(tx - 1, oy + 1, tx, oy)
        painter.drawLine(tx - 1, oy - 1, tx, oy)
        painter.drawLine(tx - 1, oy + 1, tx - 1, oy - 1)

        # Draw Z axis
        painter.setPen(qtg.QColor(0, 200, 0))
        tzx = ox - wz
        tzy = oy + wz
        painter.drawLine(ox, oy, tzx, tzy)
        painter.drawLine(tzx, tzy - 1, tzx, tzy)
        painter.drawLine(tzx + 1, tzy, tzx, tzy)
        painter.drawLine(tzx + 1, tzy, tzx, tzy - 1)
        # painter.drawPath(self.path)

        # Draw labels
        painter.setPen(qtg.QColor(0, 0, 0))
        painter.drawText(tx - 5, oy + 15, "x")
        painter.drawText(ox - 15, ty + 15, "y")
        painter.drawText(tzx + 5, tzy + 10, "z")

        painter.setPen(qtg.QPen(qtg.QColor(50, 50, 50), 0.3))
        painter.setBrush(qtg.QColor(220, 220, 220, 100))
        rectPath = qtg.QPainterPath()

        self.size = float(self._widthx)
        bw = 30
        bwz = float(wz) / wx * bw

        if self._boxaxis == dv.models.AXIS_Z:
            shiftz = float(self._widthz) / self.size * self._shiftz
            box = ox - shiftz
            boy = oy + shiftz
            rectPath.moveTo(box, boy)
            rectPath.lineTo(box, boy - bw)
            rectPath.lineTo(box + bw, boy - bw)
            rectPath.lineTo(box + bw, boy)

        elif self._boxaxis == dv.models.AXIS_Y:
            shifty = float(self._widthy) / self.size * self._shifty
            box = ox
            boy = oy - shifty
            rectPath.moveTo(box, boy)
            rectPath.lineTo(box + bw, boy)
            rectPath.lineTo(box + bw - bwz, boy + bwz)
            rectPath.lineTo(box - bwz, boy + bwz)

        elif self._boxaxis == dv.models.AXIS_X:
            shiftx = float(self._widthx) / self.size * self._shiftx
            box = ox + shiftx
            boy = oy
            rectPath.moveTo(box, boy)
            rectPath.lineTo(box, boy - bw)
            rectPath.lineTo(box - bwz, boy - bw + bwz)
            rectPath.lineTo(box - bwz, boy + bwz)

        rectPath.closeSubpath()
        painter.drawPath(rectPath)

    def setWidth(self, width):
        """ Setter for RenderArea width """
        self._width = width

    def setHeight(self, height):
        """ Setter for RenderArea height """
        self._height = height

    def setBoxAxis(self, axis):
        self._boxaxis = axis

    def setShift(self, axis, value):
        if axis == dv.models.AXIS_X:
            self._shiftx = value
        elif axis == dv.models.AXIS_Y:
            self._shifty = value
        elif axis == dv.models.AXIS_Z:
            self._shiftz = value


class AxisWidget(qtw.QWidget):
    """ """
    def __init__(self, parent=None, renderArea=RenderArea()):
        qtw.QWidget.__init__(self, parent=parent)
        self._renderArea = renderArea
        self.setBackgroundRole(qtg.QPalette.Base)

    def resizeEvent(self, evt):
        qtw.QWidget.resizeEvent(self, evt)
        size = evt.size()
        self._renderArea.setWidth(size.width())
        self._renderArea.setHeight(size.height())

    def paintEvent(self, event):
        painter = qtg.QPainter(self)
        self._renderArea.paint(painter)

    def setShift(self, axis, value):
        self._renderArea.setShift(axis, value)
        self._renderArea.setBoxAxis(axis)
        self.update()

    def minimumSizeHint(self):
        return qtc.QSize(30, 30)

    def sizeHint(self):
        return qtc.QSize(80, 80)


class AxisItem(qtw.QGraphicsWidget):
    """ """
    def __init__(self, parent=None, renderArea=RenderArea()):
        qtw.QGraphicsWidget.__init__(self, parent=parent)
        self._renderArea = renderArea

    def setShift(self, axis, value):
        self._renderArea.setShift(axis, value)
        self._renderArea.setBoxAxis(axis)

    def paint(self, painter, option, widget):
        self._renderArea.paint(painter)
