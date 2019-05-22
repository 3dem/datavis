
from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal
from PyQt5.QtWidgets import (QWidget, QSlider, QHBoxLayout, QLabel, QSpinBox,
                             QSizePolicy)


class SpinSlider(QWidget):
    """ Custom widget that contains a Slider and also a Spinbox.
    Both components will have the same range and the values will
    be synchronized.
    """
    valueChanged = pyqtSignal(int)

    def __init__(self, parent=None, **kwargs):
        """
        Create a new SliderSpin
        :param parent:
        :param kwargs:
            text: Optional text to be used as label of the Widget
            minValue: the minimum value to be shown
            maxValue: the maxium value to be shown
            currentValue: the currentValue
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
        sp = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        sp.setHorizontalStretch(0)
        sp.setVerticalStretch(0)
        sp.setHeightForWidth(slider.sizePolicy().hasHeightForWidth())
        slider.setSizePolicy(sp)
        slider.setOrientation(Qt.Horizontal)
        slider.setRange(minValue, maxValue)
        slider.setValue(currentValue)

        # SpinBox
        spinBox = QSpinBox(self)
        spinBox.setRange(minValue, maxValue)
        spinBox.setValue(currentValue)

        # Group them all in a horizontal box layout
        layout = QHBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.addWidget(label)
        layout.addWidget(slider)
        layout.addWidget(spinBox)

        # Connect signals when value change to synchronize
        slider.valueChanged.connect(self._onSliderChange)
        spinBox.valueChanged.connect(self._onSpinBoxChanged)

        # Keep references to slider and spinbox
        self._slider = slider
        self._spinBox = spinBox

    def _onValueChanged(self, newIndex, widgetToUpdate):
        """ Either the slider or the spinbox changed the
        value. Let's update the other one and emit the signal.
        """
        widgetToUpdate.blockSignals(True)
        widgetToUpdate.setValue(newIndex)
        widgetToUpdate.blockSignals(False)

        self.valueChanged.emit(newIndex)

    @pyqtSlot(int)
    def _onSpinBoxChanged(self, value):
        """ Invoked when change the spinbox value """
        self._onValueChanged(value, self._slider)

    @pyqtSlot(int)
    def _onSliderChange(self, value):
        """ Invoked when change the spinbox value """
        self._onValueChanged(value, self._spinBox)

    def getValue(self):
        """ Return the current value.
        (Same in both the slider and the spinbox).
        """
        return self._slider.value

    def setValue(self, value):
        """ Set a new value. """
        self._slider.setValue(value)

    def getRange(self):
        return self._slider.minimum(), self._slider.maximum()




