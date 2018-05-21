#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
import argparse
import numpy as np

import em

from PyQt5.QtWidgets import QApplication

from emqt5.widgets.table import ColumnProperties
from emqt5.widgets.table.table_view import (EMImageItemDelegate, PERCENT_UNITS,
                                            PIXEL_UNITS, X_AXIS, Y_AXIS, Z_AXIS,
                                            N_DIM)
from emqt5.widgets.table.model import TableDataModel
import emqt5.utils.functions as em_utils

from table_view_window import TableViewWindow

Column = em.Table.Column
Row = em.Table.Row

if __name__ == '__main__':

    app = QApplication(sys.argv)
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

    models = None
    delegates = None
    table = None
    emFile = args.files[0]
    if len(args.files) == 1:
        _, ext = os.path.splitext(emFile)
        if em_utils.isEMTable(emFile):
            if True:  # em.TableIO.hasImpl(ext):
                table = em.Table()
                tableIO = em.TableIO()
                tableIO.open(emFile)
                tableIO.read('', table)
                tableIO.close()
                properties = []
                colTypes = {}
                colTypes[em.typeBool.getName()] = 'Bool'
                colTypes[em.typeCDouble.getName()] = 'Real'
                colTypes[em.typeCFloat.getName()] = 'Real'
                colTypes[em.typeFloat.getName()] = 'Real'
                colTypes[em.typeInt16.getName()] = 'Int'
                colTypes[em.typeInt32.getName()] = 'Int'
                colTypes[em.typeInt64.getName()] = 'Int'
                colTypes[em.typeInt8.getName()] = 'Int'
                colTypes[em.typeSizeT.getName()] = 'Int'
                colTypes[em.typeString.getName()] = 'Str'
                colTypes[em.typeUInt16.getName()] = 'Int'
                colTypes[em.typeUInt32.getName()] = 'Int'
                colTypes[em.typeUInt64.getName()] = 'Int'
                colTypes[em.typeUInt8.getName()] = 'Int'

                for i in range(0, table.getColumnsSize()):
                    column = table.getColumnByIndex(i)
                    colProp = ColumnProperties(column.getName(),
                                               column.getName(),
                                               colTypes[column.getType().\
                                               getName()],
                                               **{'renderable': False,
                                                  'editable': True}
                                               )
                    properties.append(colProp)
            else:
                print("Can not read input file:", emFile)
                sys.exit(0)
        elif em_utils.isEMImageStack(emFile):
            xTable = em.Table([em.Table.Column(0, "Stack",
                                               em.typeInt32,
                                               "Image stack")])
            imageIO = em.ImageIO()
            loc2 = em.ImageLocation(emFile)
            imageIO.open(loc2.path, 0)
            _dim = imageIO.getDim()
            _dx = _dim.x
            _dy = _dim.y
            _dn = _dim.n

            _stack = list()

            for i in range(0, _dn):
                loc2.index = i + 1
                img = em.Image()
                img.read(loc2)
                a = np.array(img, copy=False)
                _stack.append(a)
                row = xTable.createRow()
                row['Stack'] = i
                xTable.addRow(row)

            xProperties = [ColumnProperties('Stack', 'Stack', 'Int',
                                            **{'renderable': True,
                                               'editable': False})]
            xTableKwargs = {}
            xTableKwargs['colProperties'] = xProperties
            xTableKwargs['views'] = ['GALLERY']
            xTableKwargs['defaultView'] = 'GALLERY'
            xTableKwargs['defaultRowHeight'] = 100
            xTableKwargs['maxRowHeight'] = 300
            xTableKwargs['minRowHeight'] = 50
            xTableKwargs['zoomUnits'] = 1

            models = list()
            models.append(TableDataModel(
                parent=None,
                title='Stack',
                emTable=xTable,
                columnProperties=xProperties))
            delegates = list()
            delegates.append(EMImageItemDelegate(parent=None,
                                                 selectedStatePen=None,
                                                 borderPen=None,
                                                 iconWidth=150,
                                                 iconHeight=150,
                                                 volData=_stack,
                                                 axis=N_DIM))
            kwargs["models"] = models
            kwargs["delegates"] = delegates

        elif em_utils.isEMImageVolume(emFile):
            image = em.Image()
            loc2 = em.ImageLocation(emFile)
            image.read(loc2)

            # Create three Tables with the volume slices
            xTable = em.Table([em.Table.Column(0, "X",
                                               em.typeInt32,
                                               "X Dimension")])
            yTable = em.Table([em.Table.Column(0, "Y",
                                               em.typeInt32,
                                               "Y Dimension")])
            zTable = em.Table([em.Table.Column(0, "Z",
                                               em.typeInt32,
                                               "Z Dimension")])

            # Get the volume dimension
            _dim = image.getDim()
            _dx = _dim.x
            _dy = _dim.y
            _dz = _dim.z

            # Create a 3D array with the volume slices
            _array3D = np.array(image, copy=False)

            for i in range(0, _dx):
                row = xTable.createRow()
                row['X'] = i
                xTable.addRow(row)

            for i in range(0, _dy):
                row = yTable.createRow()
                row['Y'] = i
                yTable.addRow(row)

            for i in range(0, _dz):
                row = zTable.createRow()
                row['Z'] = i
                zTable.addRow(row)

            xProperties = [ColumnProperties('X', 'X', 'Int',
                                            **{'renderable': True,
                                               'editable': False})]
            yProperties = [ColumnProperties('Y', 'Y', 'Int',
                                            **{'renderable': True,
                                            'editable': False})]
            zProperties = [ColumnProperties('Z', 'Z', 'Int',
                                            **{'renderable': True,
                                            'editable': False})]
            xTableKwargs = {}
            xTableKwargs['colProperties'] = xProperties
            xTableKwargs['views'] = ['GALLERY']
            xTableKwargs['defaultView'] = 'GALLERY'
            xTableKwargs['defaultRowHeight'] = 100
            xTableKwargs['maxRowHeight'] = 300
            xTableKwargs['minRowHeight'] = 50
            xTableKwargs['zoomUnits'] = 1

            yTableKwargs = {}
            yTableKwargs['colProperties'] = yProperties
            yTableKwargs['views'] = ['GALLERY']
            yTableKwargs['defaultView'] = 'GALLERY'
            yTableKwargs['defaultRowHeight'] = 100
            yTableKwargs['maxRowHeight'] = 300
            yTableKwargs['minRowHeight'] = 50
            yTableKwargs['zoomUnits'] = 1

            zTableKwargs = {}
            zTableKwargs['colProperties'] = zProperties
            zTableKwargs['views'] = ['GALLERY']
            zTableKwargs['defaultView'] = 'GALLERY'
            zTableKwargs['defaultRowHeight'] = 100
            zTableKwargs['maxRowHeight'] = 300
            zTableKwargs['minRowHeight'] = 50
            zTableKwargs['zoomUnits'] = 1

            models = list()
            models.append(TableDataModel(
                parent=None,
                title='X Axis (Right View)',
                emTable=xTable,
                columnProperties=xProperties))

            models.append(TableDataModel(
                parent=None,
                title='Y Axis (Left View)',
                emTable=yTable,
                columnProperties=yProperties))

            models.append(TableDataModel(
                parent=None,
                title='Z Axis (Front View)',
                emTable=zTable,
                columnProperties=zProperties))

            delegates = list()
            delegates.append(EMImageItemDelegate(parent=None,
                                                 selectedStatePen=None,
                                                 borderPen=None,
                                                 iconWidth=150,
                                                 iconHeight=150,
                                                 volData=_array3D,
                                                 axis=X_AXIS))
            delegates.append(EMImageItemDelegate(parent=None,
                                                 selectedStatePen=None,
                                                 borderPen=None,
                                                 iconWidth=150,
                                                 iconHeight=150,
                                                 volData=_array3D,
                                                 axis=Y_AXIS))
            delegates.append(EMImageItemDelegate(parent=None,
                                                 selectedStatePen=None,
                                                 borderPen=None,
                                                 iconWidth=150,
                                                 iconHeight=150,
                                                 volData=_array3D,
                                                 axis=Z_AXIS))
            kwargs["models"] = models
            kwargs["delegates"] = delegates
    else:
        print("Only one file is supported")
        sys.exit(0)

    if models:
        kwargs['models'] = models
        kwargs['delegates'] = delegates
    else:
        kwargs['tableData'] = table
        kwargs['colProperties'] = properties
        kwargs['models'] = None
        kwargs['delegates'] = None

    kwargs['defaultRowHeight'] = args.cell_size
    kwargs['maxRowHeight'] = args.max_cell_size
    kwargs['minRowHeight'] = args.min_cell_size
    kwargs['zoomUnits'] = PERCENT_UNITS if args.zoom_units == '%' \
        else PIXEL_UNITS
    if models:
        kwargs['defaultView'] = 'GALLERY'
        kwargs['views'] = ['GALLERY']
    else:
        kwargs['defaultView'] = args.default_view
        kwargs['views'] = args.views
    kwargs['disableHistogram'] = args.disable_histogram
    kwargs['disableMenu'] = args.disable_menu
    kwargs['disableROI'] = args.disable_roi
    kwargs['disablePopupMenu'] = args.disable_popup_menu
    kwargs['disableFitToSize'] = args.disable_fit_to_size

    tableWin = TableViewWindow(**kwargs)
    tableWin.show()
    sys.exit(app.exec_())
