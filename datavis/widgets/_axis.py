
from PyQt5.QtCore import pyqtSignal
import PyQt5.QtWidgets as qtw

from datavis.models import AXIS_X, AXIS_Y, AXIS_Z


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

    """ This value is used to show only the current axis """
    SHOW_CURRENT = 2

    """ This value is used to show all axis """
    SHOW_ALL = 3

    def __init__(self, parent=None, orientation=HORIZONTAL, label='Axis: ',
                 xlabel='X', ylabel='Y', zlabel='Z'):
        """
        Create a new AxisSelector object.
        :param parent:   (QWidget) The parent widget
        :param label:        (str) A label text at for the widget
        :param xlabel:       (str) The label text for X-axis
        :param ylabel:       (str) The label text for Y-axis
        :param zlabel:       (str) The label text for Y-axis
        """
        qtw.QWidget.__init__(self, parent=parent)

        self._viewMode = AxisSelector.SHOW_ALL

        if orientation == AxisSelector.HORIZONTAL:
            layout = qtw.QHBoxLayout(self)
        else:
            layout = qtw.QVBoxLayout(self)

        layout.addWidget(qtw.QLabel(text=label, parent=self))

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
        self.__setupViewMode()
        self.sigAxisChanged.emit(id)

    def __setupViewMode(self):
        """ Configure the current view mode """
        bg = self.__group
        sa = AxisSelector.SHOW_ALL
        for btn in self.__group.buttons():
            v = self._viewMode == sa or bg.id(btn) == bg.checkedId()
            btn.setVisible(v)

    def setCurrentAxis(self, axis):
        """ Sets the current axis """
        btn = self.__group.button(axis)

        if btn is not None:
            btn.setChecked(True)

    def getCurrentAxis(self):
        """ Return the current axis """
        return self.__group.checkedId()

    def setViewMode(self, mode):
        """
        Set the view mode.
        :param mode: (int) Specify the view mode (SHOW_CURRENT, SHOW_ALL)
        """
        self._viewMode = mode
        self.__setupViewMode()
