#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys

import PyQt5.QtWidgets as qtw
import PyQt5.QtCore as qtc


class ViewWindow(qtw.QMainWindow):
    """ Extension of QMainWindow that receive a View as input
    and set as its central widget. This window will also resize
    to a given percent of the screen size, if necessary given
    the View preferred dimensions.
    """
    def __init__(self, view, title='', maxScreenPercent=0.8):
        """
        Construct the ViewMainWindow instance.
        :param view: Input view that will be set as the central widget
        :param maxScreenPercent: Maximum screen percent that will be used
            if necessary
        """
        qtw.QMainWindow.__init__(self)
        self.setCentralWidget(view)
        self.setWindowTitle(title)
        self._view = view

    def setGeometryFromCentralView(self, maxScreenPercent=0.8):
        view = self.centralWidget()

        if hasattr(view, 'getPreferredSize'):
            width, height = view.getPreferredSize()
        else:
            width, height = None, None

        size = qtw.QApplication.desktop().size()
        p = maxScreenPercent
        w, h = int(p * size.width()), int(p * size.height())
        width = width or w
        height = height or h

        if width > w or height > h:
            s = qtc.QSize(width, height).scaled(w, h, qtc.Qt.KeepAspectRatio)
            w, h = s.width(), s.height()
        else:
            w, h = width, height

        x, y = (size.width() - w)/2, (size.height() - h)/2
        self.setGeometry(x, y, w, h)


def showView(createViewFunc, title='', argv=None, app=None,
             maxScreenPercent=0.8):
    """ Shortcut function to quickly create a QApplication
    to show the given view, using a ViewWindow.

    Args:
        createViewFunc: function to create the view to show.
            We don't use directly the view because application needs to be
            created first.
        title: Optional title for the window.
        argv: arguments to the application, by default sys.argv
        app: Optional application, if None, a new one will be created
        maxScreenPercent: Maximum percent of the screen that will be used
            if the view needs more space.
    """
    argv = argv or sys.argv
    app = app or qtw.QApplication(argv)
    win = ViewWindow(createViewFunc(), title=title,
                     maxScreenPercent=maxScreenPercent)
    win.show()
    win.setGeometryFromCentralView()
    sys.exit(app.exec_())