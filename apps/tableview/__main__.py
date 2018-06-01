#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
import argparse
import numpy as np

import em

from PyQt5.QtWidgets import QApplication

from emqt5.views import (TableViewConfig, EMImageItemDelegate, PERCENT_UNITS,
                         PIXEL_UNITS, X_AXIS, Y_AXIS, Z_AXIS, N_DIM)
from emqt5.views import TableDataModel
import emqt5.utils.functions as em_utils

from table_view_window import TableViewWindow

Column = em.Table.Column
Row = em.Table.Row


def loadEMTable(imagePath):
    """ Return the TableDataModel for the given EM table file"""
    table = em.Table()
    tableIO = em.TableIO()
    tableIO.open(imagePath)
    tableIO.read('', table)
    tableIO.close()
    tableViewConfig = TableViewConfig.fromTable(table)

    return TableDataModel(parent=None, title="TABLE", emTable=table,
                          tableViewConfig=tableViewConfig)


def loadEMStack(imagePath):
    """ Return a tuple"""
    xTable = em.Table([em.Table.Column(0, "index",
                                       em.typeInt32,
                                       "Image index"),
                       em.Table.Column(1, "Stack",
                                       em.typeString,
                                       "Image stack")])
    imageIO = em.ImageIO()
    loc2 = em.ImageLocation(emFile)
    imageIO.open(loc2.path, em.File.Mode.READ_ONLY)
    _dim = imageIO.getDim()
    _dx = _dim.x
    _dy = _dim.y
    _dn = _dim.n

    for i in range(0, _dn):
        row = xTable.createRow()
        row['Stack'] = str(i) + '@' + imagePath
        row['index'] = i
        xTable.addRow(row)

    tableViewConfig = TableViewConfig()
    tableViewConfig.addColumnConfig(name='index',
                                    dataType=TableViewConfig.TYPE_INT,
                                    **{'label': 'Index',
                                       'editable': False,
                                       'visible': True})
    tableViewConfig.addColumnConfig(name='Image',
                                    dataType=TableViewConfig.TYPE_STRING,
                                    **{'label': 'Image',
                                       'renderable': True,
                                       'editable': False,
                                       'visible': True})
    models = list()
    models.append(TableDataModel(parent=None, title='Stack',
                                 emTable=xTable,
                                 tableViewConfig=tableViewConfig))
    delegates = dict()
    stackDelegates = dict()
    stackDelegates[1] = EMImageItemDelegate(parent=None,
                                            selectedStatePen=None,
                                            borderPen=None,
                                            iconWidth=150,
                                            iconHeight=150,
                                            axis=N_DIM)
    delegates['Stack'] = stackDelegates

    return models, delegates


def loadEMVolume(imagePath):
    image = em_utils.loadEMImage(imagePath)

    # Create three Tables with the volume slices
    xTable = em.Table([em.Table.Column(0, "index",
                                       em.typeInt32,
                                       "Image index"),
                       em.Table.Column(1, "X",
                                       em.typeString,
                                       "X Dimension")])
    xtableViewConfig = TableViewConfig()
    xtableViewConfig.addColumnConfig(name='index',
                                     dataType=TableViewConfig.TYPE_INT,
                                     **{'label': 'Index',
                                        'editable': False,
                                        'visible': True})
    xtableViewConfig.addColumnConfig(name='X',
                                     dataType=TableViewConfig.TYPE_STRING,
                                     **{'label': 'X',
                                        'renderable': True,
                                        'editable': False,
                                        'visible': True})

    yTable = em.Table([em.Table.Column(0, "index",
                                       em.typeInt32,
                                       "Image index"),
                       em.Table.Column(1, "Y",
                                       em.typeString,
                                       "Y Dimension")])
    ytableViewConfig = TableViewConfig()
    ytableViewConfig.addColumnConfig(name='index',
                                     dataType=TableViewConfig.TYPE_INT,
                                     **{'label': 'Index',
                                        'editable': False,
                                        'visible': True})
    ytableViewConfig.addColumnConfig(name='Y',
                                     dataType=TableViewConfig.TYPE_STRING,
                                     **{'label': 'Y',
                                        'renderable': True,
                                        'editable': False,
                                        'visible': True})
    zTable = em.Table([em.Table.Column(0, "index",
                                       em.typeInt32,
                                       "Image index"),
                       em.Table.Column(1, "Z",
                                       em.typeString,
                                       "Z Dimension")])
    ztableViewConfig = TableViewConfig()
    ztableViewConfig.addColumnConfig(name='index',
                                     dataType=TableViewConfig.TYPE_INT,
                                     **{'label': 'Index',
                                        'editable': False,
                                        'visible': True})
    ztableViewConfig.addColumnConfig(name='Z',
                                     dataType=TableViewConfig.TYPE_STRING,
                                     **{'label': 'Z',
                                        'renderable': True,
                                        'editable': False,
                                        'visible': True})

    # Get the volume dimension
    _dim = image.getDim()
    _dx = _dim.x
    _dy = _dim.y
    _dz = _dim.z

    for i in range(0, _dx):
        row = xTable.createRow()
        row['X'] = str(i) + '@' + str(X_AXIS) + '@' + imagePath
        row['index'] = i
        xTable.addRow(row)

    for i in range(0, _dy):
        row = yTable.createRow()
        row['Y'] = str(i) + '@' + str(Y_AXIS) + '@' + imagePath
        row['index'] = i
        yTable.addRow(row)

    for i in range(0, _dz):
        row = zTable.createRow()
        row['Z'] = str(i) + '@' + str(Z_AXIS) + '@' + imagePath
        row['index'] = i
        zTable.addRow(row)

    models = list()
    models.append(TableDataModel(parent=None, title='X Axis (Right View)',
                                 emTable=xTable,
                                 tableViewConfig=xtableViewConfig))

    models.append(TableDataModel(parent=None, title='Y Axis (Left View)',
                                 emTable=yTable,
                                 tableViewConfig=ytableViewConfig))

    models.append(TableDataModel(parent=None, title='Z Axis (Front View)',
                                 emTable=zTable,
                                 tableViewConfig=ztableViewConfig))

    delegates = dict()
    dx = dict()
    dx[1] = EMImageItemDelegate(parent=None,
                                selectedStatePen=None,
                                borderPen=None,
                                iconWidth=150,
                                iconHeight=150,
                                axis=X_AXIS)
    delegates['Y Axis (Left View)'] = dx
    dy = dict()
    dy[1] = EMImageItemDelegate(parent=None,
                                selectedStatePen=None,
                                borderPen=None,
                                iconWidth=150,
                                iconHeight=150,
                                axis=Y_AXIS)
    delegates['X Axis (Right View)'] = dy
    dz = dict()
    dz[1] = EMImageItemDelegate(parent=None,
                                selectedStatePen=None,
                                borderPen=None,
                                iconWidth=150,
                                iconHeight=150,
                                axis=Z_AXIS)
    delegates['Z Axis (Front View)'] = dz

    return models, delegates


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
            models = [loadEMTable(emFile)]
        elif em_utils.isEMImageStack(emFile):
            models, delegates = loadEMStack(emFile)
        elif em_utils.isEMImageVolume(emFile):
            models, delegates = loadEMVolume(emFile)
    else:
        print("Only one file is supported")
        sys.exit(0)

    if models:
        kwargs['models'] = models
        kwargs['delegates'] = delegates
    else:
        kwargs['tableData'] = table
        kwargs['colProperties'] = None
        kwargs['models'] = None
        kwargs['delegates'] = None

    kwargs['defaultRowHeight'] = args.cell_size
    kwargs['maxRowHeight'] = args.max_cell_size
    kwargs['minRowHeight'] = args.min_cell_size
    kwargs['zoomUnits'] = PERCENT_UNITS if args.zoom_units == '%' \
        else PIXEL_UNITS
    if models:
        kwargs['defaultView'] = 'GALLERY'
        kwargs['views'] = ['GALLERY', 'TABLE']
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
