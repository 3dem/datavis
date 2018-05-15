#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
import argparse

import em

from PyQt5.QtWidgets import QApplication

from emqt5.widgets.table import ColumnProperties, PERCENT_UNITS, PIXEL_UNITS

from table_view_window import TableViewWindow

Column = em.Table.Column
Row = em.Table.Row

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
    argParser.add_argument('--disable-histogram', default=False,
                           required=False, action='store_true',
                           help=' hide the histogram widget in the view image '
                                'widget for ELEMENT view mode')
    argParser.add_argument('--disable-menu', default=False,
                           required=False, action='store_true',
                           help=' hide the menu button in the view image widget'
                                ' for ELEMENT view ')
    argParser.add_argument('--disable-roi', default=False,
                           required=False, action='store_true',
                           help=' hide the roi button in the view image widget'
                                ' for ELEMENT view ')
    argParser.add_argument('--disable-popup-menu', default=False,
                           required=False, action='store_true',
                           help=' disable the popup menu in the view image '
                                'widget for ELEMENT view ')
    argParser.add_argument('--disable-fit-to-size', default=False,
                           required=False, action='store_true',
                           help=' the image is not rescaled to the size of view'
                                ' image widget for ELEMENT view ')

    args = argParser.parse_args()

    table = em.Table([Column(1, "FileName", em.typeString, "File Name"),
                      Column(2, "Path", em.typeString, "Icon"),
                      Column(3, "RealImage", em.typeString, "Image"),
                      Column(4, "Ext", em.typeString, "Ext"),
                      Column(5, "Check", em.typeBool, "Checked"),
                      Column(6, "Count", em.typeInt32, "Count")])
    i = 1
    lastPath = args.files[0]
    for index in range(0, 250):
        for path in args.files:
            _, ext = os.path.splitext(path)
            row = table.createRow()
            row["FileName"] = os.path.basename(path)
            row["Path"] = path
            row["RealImage"] = lastPath
            row["Ext"] = ext
            row["Check"] = True if i % 2 else False
            row["Count"] = i
            table.addRow(row)

            i = i+1
            lastPath = path

    properties = [ColumnProperties('FileName', 'File Name', 'Str',
                                   **{'renderable': False,
                                      'editable': True}),
                  ColumnProperties('Path', 'Icon', 'Image',
                                   **{'renderable': True,
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

    kwargs['tableData'] = table
    kwargs['colProperties'] = properties
    kwargs['defaultRowHeight'] = args.cell_size
    kwargs['maxRowHeight'] = args.max_cell_size
    kwargs['minRowHeight'] = args.min_cell_size
    kwargs['zoomUnits'] = PERCENT_UNITS if args.zoom_units == '%' \
        else PIXEL_UNITS
    kwargs['defaultView'] = args.default_view
    kwargs['views'] = args.views
    kwargs['disableHistogram'] = args.disable_histogram
    kwargs['disableMenu'] = args.disable_menu
    kwargs['disableROI'] = args.disable_roi
    kwargs['disablePopupMenu'] = args.disable_popup_menu
    kwargs['disableFitToSize'] = args.disable_fit_to_size

    app = QApplication(sys.argv)
    tableWin = TableViewWindow(**kwargs)
    tableWin.show()
    sys.exit(app.exec_())
