

from PyQt5.QtWidgets import QAction
from PyQt5.QtGui import QIcon

import qtawesome as qta


class TriggerAction(QAction):
    """
    The TriggerAction class offers an initialization of configuration params
    not provided by Qt.
    """
    def __init__(self, parent, actionName, text="", faIconName=None, icon=None,
                  checkable=False, slot=None, shortCut=None):
        """
        Creates a TriggerAction with the given name, text and icon. If slot is
        not None then the signal QAction.triggered is connected to it.
        :param actionName:   (str)The action name
        :param text:         (str)Action text
        :param faIconName:   (str)qtawesome icon name
        :param icon:         (QIcon) used if faIconName=None
        :param checkable:    (bool)if this action is checkable
        :param slot:         (slot) the slot to connect QAction.triggered signal
        :param shortCut:     (QKeySequence) the short cut key
        """
        QAction.__init__(self, parent)
        self.setObjectName(str(actionName))
        if faIconName:
            icon = qta.icon(faIconName)

        if icon is not None:
            self.setIcon(icon)

        self.setCheckable(checkable)
        self.setText(str(text))

        if slot:
            self.triggered.connect(slot)

        if shortCut is not None:
            self.setShortcut(shortCut)


def createQPixmap(iconName, size):
    """
    Creates a QPixmap for the given qtawesome icon, scaling to size
    :param iconName:  (str) The qtawesome icon name
    :param size:      (int) The icon width
    :return:   The QPixmap object
    """
    return qta.icon(iconName).pixmap(size, QIcon.Normal, QIcon.On)
