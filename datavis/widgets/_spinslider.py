
from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal
from PyQt5.QtWidgets import (QWidget, QSlider, QHBoxLayout, QLabel, QSpinBox,
                             QSizePolicy, QGridLayout)


class SpinSlider(QWidget):
    """ Custom widget that contains a Slider and also a Spinbox.
    Both components will have the same range and the values will
    be synchronized.
    """
    """ Emitted when the spin value is changed. """
    sigValueChanged = pyqtSignal(int)
    """ Emitted when the user releases the slider."""
    sigSliderReleased = pyqtSignal()

    def __init__(self, parent=None, **kwargs):
        """
        Create a new SliderSpin
        :param parent:
        :param kwargs:
            text:         (str) Optional text to be used as label of the Widget
            minValue:     (int) The minimum value to be shown
            maxValue:     (int) The maxium value to be shown
            currentValue: (int) The currentValue
        """
        QWidget.__init__(self, parent=parent)

        text = kwargs.get('text', '')
        minValue = kwargs['minValue']  # this is mandatory
        maxValue = kwargs['maxValue']  # this is mandatory
        currentValue = kwargs.get('currentValue', minValue)

        # First the label
        label = QLabel(self)
        label.setText(text)

        # Slider
        slider = QSlider(self)
        sp = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        #sp.setHorizontalStretch(0)
        #sp.setVerticalStretch(0)
        #sp.setHeightForWidth(slider.sizePolicy().hasHeightForWidth())
        slider.setSizePolicy(sp)
        slider.setOrientation(Qt.Horizontal)
        slider.setRange(minValue, maxValue)
        slider.setValue(currentValue)

        # SpinBox
        spinBox = QSpinBox(self)
        spinBox.setRange(minValue, maxValue)
        spinBox.setValue(currentValue)

        # Group them all in a grid layout
        layout = QGridLayout(self,)
        layout.setSpacing(5)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.addWidget(label, 0, 0, 1, 1, Qt.AlignRight)
        boxLayout = QHBoxLayout()
        boxLayout.addWidget(slider)
        layout.addLayout(boxLayout, 0, 1, 1, 3, Qt.AlignCenter)
        layout.addWidget(spinBox, 0, 4, 1, 1, Qt.AlignLeft)

        # Connect signals when value change to synchronize
        slider.valueChanged.connect(self._onSliderChange)
        spinBox.valueChanged.connect(self._onSpinBoxChanged)
        # Connect signal when the slider is released
        slider.sliderReleased.connect(self._onSliderReleased)
        # Keep references to label, slider and spinbox
        self._slider = slider
        self._spinBox = spinBox
        self._label = label

    @pyqtSlot(int, object)
    def _onValueChanged(self, newIndex, widgetToUpdate):
        """ Either the slider or the spinbox changed the
        value. Let's update the other one and emit the signal.
        """
        widgetToUpdate.blockSignals(True)
        widgetToUpdate.setValue(newIndex)
        widgetToUpdate.blockSignals(False)

        self.sigValueChanged.emit(newIndex)

    @pyqtSlot(int)
    def _onSpinBoxChanged(self, value):
        """ Invoked when change the spinbox value """
        self._onValueChanged(value, self._slider)

    @pyqtSlot(int)
    def _onSliderChange(self, value):
        """ Invoked when change the spinbox value """
        self._onValueChanged(value, self._spinBox)

    def _onSliderReleased(self):
        """ Invoked when the slider is released """
        self.sigSliderReleased.emit()

    def getValue(self):
        """ Return the current value.
        (Same in both the slider and the spinbox).
        """
        return self._slider.value()

    def setValue(self, value):
        """ Set a new value. """
        self._slider.setValue(value)

    def setRange(self, minimum, maximum):
        """
        Set the minimum and maximum values
        :param minimum: (int) The minimum possible value
        :param maximum: (int) The maximum possible value
        """
        self._slider.blockSignals(True)
        self._spinBox.blockSignals(True)
        self._slider.setRange(minimum, maximum)
        self._spinBox.setRange(minimum, maximum)
        self._slider.blockSignals(False)
        self._spinBox.blockSignals(False)

    def getRange(self):
        """ Return a tuple (minimum, maximum) values
        """
        return self._slider.minimum(), self._slider.maximum()

    def setText(self, text):
        """
        Set the label text for the internal slider
        :param text: (str) The text
        """
        self._label.setText(text)

    def getText(self):
        """
        Returns the label text for the internal slider
        """
        return self._label.text()

    def setFocusPolicy(self, policy):
        self._spinBox.setFocusPolicy(policy)
