#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os

from PyQt5.QtWidgets import QApplication

from table_view_window import TableViewWindow
from emqt5.widgets.table import ColumnProperties
import argparse


if __name__ == '__main__':

    kwargs = {}

    argParser = argparse.ArgumentParser(usage='TableView example',
                                        description='Show the table view '
                                                    'example',
                                        prefix_chars='--')
    argParser.add_argument('files', type=str, nargs='+',
                           help=' list of image files')
    argParser.add_argument('--cell-size', type=int, default=32,
                           required=False,
                           help=' an integer for default cell size')
    argParser.add_argument('--max-cell-size', type=int, default=512,
                           required=False,
                           help=' an integer for max cell size')
    argParser.add_argument('--default-view', type=str, default='TABLE',
                           required=False,
                           choices=['GALLERY', 'TABLE', 'ELEMENT'],
                           help=' the default view. TABLE if not specified')
    argParser.add_argument('--views', type=str,
                           default=['GALLERY', 'TABLE', 'ELEMENT'],
                           nargs='+', required=False,
                           choices=['GALLERY', 'TABLE', 'ELEMENT'],
                           help=' list of accessible '
                                'views.[\'GALLERY\', \'TABLE\', \'ELEMENT\'] if'
                                ' not specified')

    args = argParser.parse_args()
    print("Arguments: ")
    print(args)

    data = []
    i = 1

    for index in range(0, 250):
        for path in args.files:
            _, ext = os.path.splitext(path)
            data.append([os.path.basename(path), path, ext,
                         True if i % 2 else False, i])
            i = i+1

    properties = [ColumnProperties('FileName', 'File Name', 'Str',
                                   **{'renderable': False,
                                      'editable': False}),
                  ColumnProperties('Path', 'Icon', 'Image',
                                   **{'renderable':True,
                                      'editable': False}),
                  ColumnProperties('Ext', 'Ext', 'Str',
                                   **{'renderable': False,
                                      'editable': False}),
                  ColumnProperties('Checked', 'Checked', 'Bool',
                                   **{'renderable': False,
                                      'editable': True}),
                  ColumnProperties('Count', 'Count', 'Int',
                                   **{'renderable': False,
                                      'editable': True})]

    kwargs['tableData'] = data
    kwargs['colProperties'] = properties
    kwargs['defaultRowHeight'] = args.cell_size
    kwargs['maxRowHeight'] = args.max_cell_size
    kwargs['defaultView'] = args.default_view
    kwargs['views'] = args.views

    app = QApplication(sys.argv)
    tableWin = TableViewWindow(**kwargs)
    tableWin.show()
    sys.exit(app.exec_())
