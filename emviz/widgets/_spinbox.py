
from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal
import PyQt5.QtWidgets as qtw

from ._common import createQPixmap


class IconSpinBox(qtw.QWidget):
    """ Custom widget that contains a Icon and a Spinbox. """

    # Signal for value changed
    sigValueChanged = pyqtSignal([int], [float])
    sigEditingFinished = pyqtSignal()

    # Signal emitted when the user clicks hover the image icon
    sigIconClicked = pyqtSignal()

    def __init__(self, parent=None, **kwargs):
        """
        Create a new IconSpinBox
        :param parent:
        :param kwargs:
            valueType:    (int) The type for the spinbox values: int or float
            minValue:     (int) The minimum value to be shown
            maxValue:     (int) The maximum value to be shown
            currentValue: (int) The currentValue
            iconName:     (str) The icon name
            iconSize:     (int) The icon size in pixels
            sufix:        (str) The suffix is appended to the end of the
                                displayed value
            prefix:       (str) The prefix is prepended to the start of the
                                displayed value
        """
        qtw.QWidget.__init__(self, parent=parent)

        t = kwargs.get('valueType', int)
        if t == int:
            sbClass = qtw.QSpinBox
        elif t == float:
            sbClass = qtw.QDoubleSpinBox
        else:
            raise Exception("Invalid valueType for SpinBox")

        minValue = kwargs['minValue']  # this is mandatory
        maxValue = kwargs['maxValue']  # this is mandatory
        currentValue = kwargs.get('currentValue', minValue)

        # Create the SpinBox
        spinBox = sbClass(self)
        spinBox.setSuffix(kwargs.get('sufix', ''))
        spinBox.setPrefix(kwargs.get('prefix', ''))
        spinBox.setRange(minValue, maxValue)
        spinBox.setValue(currentValue)
        spinBox.editingFinished.connect(self._onValueChanged)
        spinBox.setMinimumWidth(60)

        # Group them all in a horizontal box layout
        layout = qtw.QHBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(5, 5, 5, 5)
        iconName = kwargs.get('iconName')
        if iconName:
            label = qtw.QLabel(self)
            label.mousePressEvent = self.__labelClicked
            label.setPixmap(createQPixmap(iconName, kwargs.get('iconSize', 28)))
            layout.addWidget(label)

        layout.addWidget(spinBox)
        layout.setAlignment(Qt.AlignCenter)

        self.setMinimumWidth(layout.sizeHint().width())
        # Keep references to spinbox and type
        self._spinBox = spinBox
        self._spinBoxType = t

    def __labelClicked(self, evt):
        self.sigIconClicked.emit()

    @pyqtSlot()
    def _onValueChanged(self):
        """ Either the slider or the spinbox changed the
        value. Let's update the other one and emit the signal.
        """
        self.sigValueChanged[self._spinBoxType].emit(self.getValue())

    def getValue(self):
        """ Return the current value.
        (Same in both the slider and the spinbox).
        """
        return self._spinBox.value()

    def setValue(self, value):
        """ Set a new value. """
        if not self._spinBox.value() == value:
            self._spinBox.setValue(value)

    def setRange(self, minimum, maximum):
        """
        Set the minimum and maximum values
        :param minimum: (int) The minimum possible value
        :param maximum: (int) The maximum possible value
        """
        self._spinBox.setRange(minimum, maximum)

    def getRange(self):
        """ Return a tuple (minimum, maximum) values
        """
        return self._spinBox.minimum(), self._spinBox.maximum()

    def setFocusPolicy(self, policy):
        self._spinBox.setFocusPolicy(policy)


class ZoomSpinBox(IconSpinBox):
    """ Custom widget that contains a Loupe icon and a Spinbox.
    The SpinBox will handle the zooming of images in a given range.
    """
    PIXELS = 0
    PERCENT = 1

    def __init__(self, parent=None, **kwargs):
        """
        Create a new ZoomSpinBox
        :param parent:
        :param kwargs:
            valueType:    (int) The type for the spinbox values:
                                TYPE_REAL or TYPE_INT. Default type: TYPE_INT
            minValue:     (int) The minimum value to be shown
            maxValue:     (int) The maximum value to be shown
            currentValue: (int) The currentValue
            zoomUnits:    (int) The units
        """
        z = kwargs.get('zoomUnits', ZoomSpinBox.PIXELS)
        IconSpinBox.__init__(self, parent=parent,
                             sufix=' %' if z == ZoomSpinBox.PERCENT else ' px',
                             iconName='fa.search', **kwargs)
        self._units = z

    def getUnits(self):
        """ Return the zoom units. Possible values are: PIXELS and PERCENT """
        return self._units
