

from PyQt5.QtWidgets import QAction
from PyQt5.QtGui import QIcon

import qtawesome as qta


def createQAction(parent, actionName, text="", faIconName=None, icon=None,
                  checkable=False, slot=None):
    """
    Creates a QAction with the given name, text and icon. If slot is not None
    then the signal QAction.triggered is connected to it
    :param actionName:   (str)The action name
    :param text:         (str)Action text
    :param faIconName:   (str)qtawesome icon name
    :param icon:         (QIcon) used if faIconName=None
    :param checkable: if this action is checkable
    :param slot: the slot to connect QAction.triggered signal
    :return: The QAction
    """
    a = QAction(parent)
    a.setObjectName(str(actionName))
    if faIconName:
        icon = qta.icon(faIconName)
    a.setIcon(icon)
    a.setCheckable(checkable)
    a.setText(str(text))

    if slot:
        a.triggered.connect(slot)
    return a


def createQPixmap(iconName, size):
    """
    Creates a QPixmap for the given qtawesome icon, scaling to size
    :param iconName:  (str) The qtawesome icon name
    :param size:      (int) The icon width
    :return:   The QPixmap object
    """
    return qta.icon(iconName).pixmap(size, QIcon.Normal, QIcon.On)
