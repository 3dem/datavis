#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
import argparse

from PyQt5.QtWidgets import QApplication

from emqt5.widgets.table import ColumnProperties, PERCENT_UNITS, PIXEL_UNITS

from table_view_window import TableViewWindow


if __name__ == '__main__':

    kwargs = {}

    argParser = argparse.ArgumentParser(usage='TableView example',
                                        description='Show the table view '
                                                    'example',
                                        prefix_chars='--')
    argParser.add_argument('files', type=str, nargs='+',
                           help=' list of image files')
    argParser.add_argument('--cell-size', type=int, default=100,
                           required=False,
                           help=' an integer for default cell size')
    argParser.add_argument('--max-cell-size', type=int, default=300,
                           required=False,
                           help=' an integer for max cell size')
    argParser.add_argument('--min-cell-size', type=int, default=10,
                           required=False,
                           help=' an integer for min cell size')
    argParser.add_argument('--zoom-units', type=str, default='px',
                           required=False,
                           choices=['%', 'px'],
                           help=' units in which the rescaling  will be done: '
                                ' percent or pixels ')
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

    data = []
    i = 1
    lastPath = args.files[0]
    for index in range(0, 250):
        for path in args.files:
            _, ext = os.path.splitext(path)
            data.append([os.path.basename(path), path, lastPath, ext,
                         True if i % 2 else False, i])
            i = i+1
            lastPath = path

    properties = [ColumnProperties('FileName', 'File Name', 'Str',
                                   **{'renderable': False,
                                      'editable': True}),
                  ColumnProperties('Path', 'Icon', 'Image',
                                   **{'renderable':True,
                                      'editable': False,
                                      'allowSetVisible': True}),
                  ColumnProperties('Path', 'Real Image', 'Image',
                                   **{'renderable': True,
                                      'editable': False,
                                      'allowSetVisible': True,
                                      'visible': True}),
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
    kwargs['minRowHeight'] = args.min_cell_size
    kwargs['zoomUnits'] = PERCENT_UNITS if args.zoom_units == '%' \
        else PIXEL_UNITS
    kwargs['defaultView'] = args.default_view
    kwargs['views'] = args.views

    app = QApplication(sys.argv)
    tableWin = TableViewWindow(**kwargs)
    tableWin.show()
    sys.exit(app.exec_())
