#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse

from PyQt5.QtCore import QDir, QFileInfo
import PyQt5.QtWidgets as qtw
from emviz.views import *
from emviz.widgets import FileBrowser, FileNavigatorPanel
from test_commons import TestView


class TestBowser(TestView):
    __title = "Browser example"

    def __init__(self, **kwargs):
        self._kwargs = kwargs

    def createView(self):
        mainWidget = qtw.QWidget(None)
        layout = qtw.QHBoxLayout(mainWidget)
        fileNav = FileNavigatorPanel(None, **self._kwargs)
        self._info = qtw.QTextEdit(mainWidget)
        self._info.setReadOnly(True)
        layout.addWidget(fileNav)
        layout.addWidget(self._info)
        fileNav.sigIndexSelected.connect(self.__onIndexChanged)
        return mainWidget

    def __onIndexChanged(self, index):
        info = QFileInfo(index.model().filePath(index))
        if info.isDir():
            self._info.clear()
        else:
            text = 'File name: %s\nExt: %s\nAbsolute path:%s\nSize: %d bytes\n'
            self._info.setText(text % (info.fileName(), info.suffix(),
                                       info.absolutePath(), info.size()))


if __name__ == '__main__':
    kwargs = {}

    argParser = argparse.ArgumentParser(usage='Test Browser',
                                        prefix_chars='--',
                                        argument_default=None)
    argParser.add_argument('--mode', default='dir',
                           required=False, choices=['dir', 'default'],
                           help=' the view mode: dir, or default')
    argParser.add_argument('--navigate', default='on',
                           required=False, choices=['on', 'off'],
                           help=' if the user can navigate')
    argParser.add_argument('--read-only', default='off',
                           required=False, choices=['on', 'off'],
                           help=' the read only mode')
    argParser.add_argument('--path', nargs='?', default=QDir.homePath(),
                           required=False, type=str,
                           help=' the initial path')

    print("TIP: Use --help for a more specific explanation.")
    args = argParser.parse_args()
    kwargs['path'] = args.path
    if args.mode == 'dir':
        kwargs['mode'] = FileBrowser.DIR_MODE
    else:
        kwargs['mode'] = FileBrowser.DEFAULT_MODE

    kwargs['navigate'] = args.navigate == 'on'
    kwargs['readOnly'] = args.read_only == 'on'

    TestBowser(**kwargs).runApp()
