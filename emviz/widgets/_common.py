

from PyQt5.QtGui import QIcon

import qtawesome as qta


# TODO[phv] Consider move this function to other module

def createQPixmap(iconName, size):
    """
    Creates a QPixmap for the given qtawesome icon, scaling to size
    :param iconName:  (str) The qtawesome icon name
    :param size:      (int) The icon width
    :return:   The QPixmap object
    """
    return qta.icon(iconName).pixmap(size, QIcon.Normal, QIcon.On)
