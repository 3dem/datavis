#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse

from PyQt5.QtCore import QDir
from emviz.views import *
from emviz.widgets import FileTreeView, FileNavigator
from test_commons import TestView


class TestBowser(TestView):
    __title = "Browser example"

    def __init__(self, **kwargs):
        self._kwargs = kwargs

    def createView(self):
        return FileNavigator(None, **self._kwargs)


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
    kwargs['mode'] = FileTreeView.DIR_MODE \
        if args.mode == 'dir' else FileTreeView.DEFAULT_MODE
    kwargs['navigate'] = True if args.navigate == 'on' else False
    kwargs['readOnly'] = True if args.read_only == 'on' else False

    TestBowser(**kwargs).runApp()
