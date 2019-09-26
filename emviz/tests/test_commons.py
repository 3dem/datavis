#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import unittest

import PyQt5.QtWidgets as qtw


class TestData:
    """ Simple base class to define basic parameters and functions
    related to testing view examples.
    """
    __title = ''

    def _loadPaths(self):
        if not hasattr(self, '_argv'):
            return

        argv = self._argv
        self._path = None

        i = 0

        if len(argv) > 1:
            a = argv[1]
            if len(a) == 1 and a.isdigit():  # consider it as index
                i = int(a)
            else:
                self._path = argv[1]

        if not self._path:
            self._path = self.getDataPaths()[i]

    def getPath(self, *paths):
        if not hasattr(self, '_path'):
            self._loadPaths()

        testDataPath = os.environ.get("EM_TEST_DATA", None)
        joinedPath = os.path.join(*paths)

        if testDataPath is None:
            raise Exception("Define EM_TEST_DATA to run this tests."
                            "Needed for path: $EM_TEST_DATA/%s" % joinedPath)

        return os.path.join(testDataPath, joinedPath)

    def getTitle(self):
        return self.__title

    def getArgs(self):
        return self._argv

    def getDataPaths(self):
        return []


class TestBase(unittest.TestCase, TestData):
    """ Simple base class to define basic parameters and functions
    related to testing view examples.
    """
    __title = ''


# TODO: Check if this simple window with central widget and resize
# can be re-used in other contexts and not only here in the tests
class ViewMainWindow(qtw.QMainWindow):
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
        w = min(width, w)
        h = min(height, h)
        x, y = (size.width() - w) / 2, (size.height() - h) / 2
        self.setGeometry(x, y, w, h)


class TestView(TestData):
    """ Class that will test existing Views. """

    def createView(self):
        return None

    def runApp(self, argv=None, app=None):
        self._argv = argv or sys.argv
        self._loadPaths()
        app = app or qtw.QApplication(self.getArgs())
        win = ViewMainWindow(self.createView(), title=self.getTitle())
        win.show()
        win.setGeometryFromCentralView()
        sys.exit(app.exec_())
