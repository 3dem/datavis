
import numpy as np
import PyQt5.QtCore as qtc
import PyQt5.QtWidgets as qtw


class SpinSlider(qtw.QWidget):
    """ Custom widget that contains a Slider and also a Spinbox.
    Both components will have the same range and the values will
    be synchronized.
    """
    """ Emitted when the spin value is changed. """
    sigValueChanged = qtc.pyqtSignal(object)
    """ Emitted when the user releases the slider."""
    sigSliderReleased = qtc.pyqtSignal()

    def __init__(self, parent=None, **kwargs):
        """ Create a new SliderSpin instance.

        Args:
            parent: Parent QWidget.

        Keyword Args:
            text:         (str) Optional text to be used as label of the Widget
            minValue:     (int/float) The minimum value to be shown
            maxValue:     (int/float) The maximum value to be shown
            currentValue: (int/float) The currentValue
        """
        qtw.QWidget.__init__(self, parent=parent)

        text = kwargs.get('text', '')
        minValue = kwargs['minValue']  # this is mandatory
        maxValue = kwargs['maxValue']  # this is mandatory
        currentValue = kwargs.get('currentValue', minValue)

        if any(isinstance(v, float) for v in [minValue, maxValue, currentValue]):
            distance = float(maxValue) - float(minValue)
            step = kwargs.get('step', distance/100.)
            self.__float2int = lambda f: round((f - minValue) / step)
            self.__int2float = lambda i: minValue + float(i) * step
            spinBox = qtw.QDoubleSpinBox(self)
            spinBox.setSingleStep(step)
            spinBox.setDecimals(3)
            self._type = float
        else:
            # No conversion is needed
            self.__float2int = lambda f: f
            self.__int2float = lambda i: i
            spinBox = qtw.QSpinBox(self)
            self._type = int

        # First the label
        label = qtw.QLabel(self)
        label.setText(text)

        # Slider
        slider = qtw.QSlider(self)
        sp = qtw.QSizePolicy(qtw.QSizePolicy.Expanding, qtw.QSizePolicy.Minimum)
        #sp.setHorizontalStretch(0)
        #sp.setVerticalStretch(0)
        #sp.setHeightForWidth(slider.sizePolicy().hasHeightForWidth())
        slider.setSizePolicy(sp)
        slider.setOrientation(qtc.Qt.Horizontal)
        slider.setRange(self.__float2int(minValue),
                        self.__float2int(maxValue))
        slider.setValue(self.__float2int(currentValue))
        slider.setMinimumWidth(80)

        # SpinBox
        # spinBox = qtw.QSpinBox(self)
        spinBox.setRange(minValue, maxValue)
        spinBox.setValue(currentValue)

        # Group them all in a grid layout
        layout = qtw.QGridLayout(self,)
        layout.setSpacing(5)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.addWidget(label, 0, 0, 1, 1, qtc.Qt.AlignRight)
        boxLayout = qtw.QHBoxLayout()
        boxLayout.addWidget(slider)
        layout.addLayout(boxLayout, 0, 1, 1, 3, qtc.Qt.AlignCenter)
        layout.addWidget(spinBox, 0, 4, 1, 1, qtc.Qt.AlignLeft)

        # Connect signals when value change to synchronize
        slider.valueChanged.connect(self._onSliderChange)
        spinBox.valueChanged.connect(self._onSpinBoxChanged)
        # Connect signal when the slider is released
        slider.sliderReleased.connect(self._onSliderReleased)
        # Keep references to label, slider and spinbox
        self._slider = slider
        self._spinBox = spinBox
        self._label = label

    def _onValueChanged(self, widgetToUpdate, value, signalValue=None):
        """ Either the slider or the spinbox changed the
        value. Let's update the other one and emit the signal.
        """
        widgetToUpdate.blockSignals(True)
        widgetToUpdate.setValue(value)
        widgetToUpdate.blockSignals(False)
        self.sigValueChanged.emit(signalValue or value)

    def _onSpinBoxChanged(self, value):
        """ Invoked when change the spinbox value """
        self._onValueChanged(self._slider, self.__float2int(value), value)

    @qtc.pyqtSlot(int)
    def _onSliderChange(self, value):
        """ Invoked when change the spinbox value """
        self._onValueChanged(self._spinBox,
                             self.__int2float(value))

    def _onSliderReleased(self):
        """ Invoked when the slider is released """
        self.sigSliderReleased.emit()

    def getValue(self):
        """ Return the current value.
        (Same in both the slider and the spinbox).
        """
        return self._spinBox.value()

    def setValue(self, value):
        """ Set a new value. """
        self._spinBox.setValue(value)

    def setRange(self, minValue, maxValue):
        """
        Set the minimum and maximum values
        :param minimum: (int) The minimum possible value
        :param maximum: (int) The maximum possible value
        """
        self._slider.blockSignals(True)
        self._spinBox.blockSignals(True)
        self._slider.setRange(self.__float2int(minValue),
                              self.__float2int(maxValue))
        self._spinBox.setRange(minValue, maxValue)
        self._slider.blockSignals(False)
        self._spinBox.blockSignals(False)

    def getRange(self):
        """ Return a tuple (minimum, maximum) values
        """
        return self._spinBox.minimum(), self._spinBox.maximum()

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
