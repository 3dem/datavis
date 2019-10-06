#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse

import PyQt5.QtCore as qtc

import datavis as dv


class TestFileBrowser(dv.tests.TestView):
    __title = "File Browser Example"

    def __init__(self, **kwargs):
        self._kwargs = kwargs

    def getDataPaths(self):
        return [qtc.QDir.homePath()]

    def createView(self):
        return dv.widgets.FileBrowser(**self._kwargs)


if __name__ == '__main__':
    kwargs = {}

    argParser = argparse.ArgumentParser(usage='Test Browser',
                                        prefix_chars='--',
                                        argument_default=None)
    argParser.add_argument('--mode', default='dir',
                           required=False, choices=['dir', 'tree'],
                           help=' the view mode: dir, or default')
    argParser.add_argument('--navigate', default='on',
                           required=False, choices=['on', 'off'],
                           help=' if the user can navigate')
    argParser.add_argument('--read-only', default='off',
                           required=False, choices=['on', 'off'],
                           help=' the read only mode')
    argParser.add_argument('--root', nargs='?', default=qtc.QDir.homePath(),
                           required=False, type=str,
                           help=' the initial path')
    argParser.add_argument('--select', nargs='?', default=None,
                           required=False, type=str,
                           help=' the selected path')

    print("TIP: Use --help for a more specific explanation.")
    args = argParser.parse_args()
    kwargs['selectedPath'] = args.select
    kwargs['rootPath'] = args.root

    if args.mode == 'dir':
        kwargs['mode'] = dv.widgets.TreeModelView.DIR_MODE
    else:
        kwargs['mode'] = dv.widgets.TreeModelView.TREE_MODE

    kwargs['navigate'] = args.navigate == 'on'
    kwargs['readOnly'] = args.read_only == 'on'

    TestFileBrowser(**kwargs).runApp()
