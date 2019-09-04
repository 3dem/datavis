
from PyQt5.QtCore import pyqtSignal
import PyQt5.QtWidgets as qtw

from emviz.models import AXIS_X, AXIS_Y, AXIS_Z


class AxisSelector(qtw.QWidget):
    """
    Custom widget for axis selection
    """
    """ Signal for axis changed """
    sigAxisChanged = pyqtSignal(int)

    """ This value is used to signify an horizontal orientation """
    HORIZONTAL = 0

    """ This value is used to signify an vertical orientation """
    VERTICAL = 1

    def __init__(self, parent=None, orientation=HORIZONTAL,
                 xlabel='X', ylabel='Y', zlabel='Z'):
        """
        Create a new AxisSelector object.
        :param parent:   (QWidget) The parent widget
        :param xlabel:       (str) The label text for X-axis
        :param ylabel:       (str) The label text for Y-axis
        :param zlabel:       (str) The label text for Y-axis
        """
        qtw.QWidget.__init__(self, parent=parent)
        if orientation == AxisSelector.HORIZONTAL:
            layout = qtw.QHBoxLayout(self)
        else:
            layout = qtw.QVBoxLayout(self)

        axisInfo = [(AXIS_X, xlabel),
                    (AXIS_Y, ylabel),
                    (AXIS_Z, zlabel)]

        group = qtw.QButtonGroup(self)
        group.setExclusive(True)

        for axis, label in axisInfo:
            btn = qtw.QRadioButton(label, self)
            layout.addWidget(btn)
            group.addButton(btn, axis)

        group.buttonClicked[int].connect(self.__onAxisChanged)
        self.__group = group

    def __onAxisChanged(self, id):
        """ Called when the current button change """
        self.sigAxisChanged.emit(id)

    def setCurrentAxis(self, axis):
        """ Sets the current axis """
        btn = self.__group.button(axis)

        if btn is not None:
            btn.setChecked(True)

    def getCurrentAxis(self):
        """ Return the current axis """
        return self.__group.checkedId()
