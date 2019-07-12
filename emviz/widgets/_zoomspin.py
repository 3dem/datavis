
from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal
import PyQt5.QtWidgets as qtw

from ._common import createQPixmap


class ZoomSpinBox(qtw.QWidget):
    """ Custom widget that contains a Loupe icon and a Spinbox.
    The SpinBox will handle the zooming of images in a given range.
    """
    sigValueChanged = pyqtSignal(int)

    def __init__(self, parent=None, **kwargs):
        """
        Create a new SliderSpin
        :param parent:
        :param kwargs:
            minValue:     (int) The minimum value to be shown
            maxValue:     (int) The maxium value to be shown
            currentValue: (int) The currentValue
            zoomUnits     (value) REVIEW
        """
        qtw.QWidget.__init__(self, parent=parent)

        text = kwargs.get('text', '')
        minValue = kwargs['minValue']  # this is mandatory
        maxValue = kwargs['maxValue']  # this is mandatory
        currentValue = kwargs.get('currentValue', minValue)
        self._zoomUnits = kwargs.get('zoomUnits', 1)

        # First the label
        label = qtw.QLabel(self)
        label.setPixmap(createQPixmap('fa.search', 28))

        # Create the SpinBox
        spinBox = qtw.QSpinBox(self)
        # TODO: Check how to handle the suffix
        spinBox.setSuffix(' px' if self._zoomUnits == 1 else ' %')
        spinBox.setRange(minValue, maxValue)
        spinBox.setValue(currentValue)
        spinBox.editingFinished.connect(self._onValueChanged)

        # Group them all in a horizontal box layout
        layout = qtw.QHBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.addWidget(label)
        layout.addWidget(spinBox)
        layout.addWidget(spinBox)
        layout.setAlignment(Qt.AlignCenter)

        # Keep references to label, slider and spinbox
        self._spinBox = spinBox

    @pyqtSlot()
    def _onValueChanged(self):
        """ Either the slider or the spinbox changed the
        value. Let's update the other one and emit the signal.
        """
        self.sigValueChanged.emit(self.getValue())

    def getValue(self):
        """ Return the current value.
        (Same in both the slider and the spinbox).
        """
        return self._spinBox.value()

    def setValue(self, value):
        """ Set a new value. """
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

