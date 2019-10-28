
import PyQt5.QtCore as qtc
import PyQt5.QtWidgets as qtw

from datavis.models import AXIS_X, AXIS_Y, AXIS_Z


class AxisSelector(qtw.QWidget):
    """
    Custom widget for axis selection. Show a label text in the left side, and
    the axis for selection.
    """
    """ Signal for axis changed """
    sigAxisChanged = qtc.pyqtSignal(int)

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
        Create a new AxisSelector instance.
        Args:
            parent:    The parent widget
            label:     (str) A label text for the widget
            xlabel:    (str) The label text for X-axis
            ylabel:    (str) The label text for Y-axis
            zlabel:    (str) The label text for Y-axis
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
        """ Called when the current axis is changed """
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
        """ Sets the current axis. Possible values: AXIS_X, AXIS_Y, AXIS_Z """
        btn = self.__group.button(axis)

        if btn is not None:
            btn.setChecked(True)

    def getCurrentAxis(self):
        """ Return the current axis: AXIS_X, AXIS_Y or AXIS_Z """
        return self.__group.checkedId()

    def setViewMode(self, mode):
        """
        Set the view mode.
        Args:
            mode: (int) Specify the view mode: SHOW_CURRENT or SHOW_ALL
        """
        self._viewMode = mode
        self.__setupViewMode()
