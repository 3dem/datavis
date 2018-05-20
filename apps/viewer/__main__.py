#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
from PyQt5.QtWidgets import QApplication, QFileSystemModel, QDialog, QLabel, \
    QMessageBox

from PyQt5.QtCore import QDir
import numpy as np

import em
from emqt5.widgets.image.browser_window import BrowserWindow
from emqt5.widgets.image.volume_slicer import VolumeSlice
from emqt5.widgets.table import TableView, ColumnProperties
from emqt5.widgets.table.table_view import (EMImageItemDelegate,
                                            X_AXIS, Y_AXIS, Z_AXIS)
from emqt5.widgets.table.model import TableDataModel

import emqt5.utils.functions as utils


import argparse

if __name__ == '__main__':
    app = QApplication(sys.argv)
    kwargs = {}
    paramCount = 0

    kwargs = {}

    argParser = argparse.ArgumentParser(usage='Tool for Viewer Apps',
                                        description='Display the selected '
                                                    'viewer app',
                                        prefix_chars='--',
                                        argument_default=None)

    # GLOBAL PARAMETERS
    argParser.add_argument('path', type=str, nargs='?', default=[],
                            help='3D image path or a specific '
                                                'directory')
    argParser.add_argument('--slices', type=str, default=['gallery', 'axis'],
                           nargs='+', required=False, choices=['gallery',
                                                               'axis'],
                           help=' list of accessible')

    # EM-BROWSER PARAMETERS
    argParser.add_argument('--disable-zoom', default=False,
                           required=False, action='store_true',
                           help=' do not scale the image')
    argParser.add_argument('--disable-histogram', default=False,
                           required=False, action='store_true',
                           help='disable the histogram')
    argParser.add_argument('--disable-roi', default=False,
                           required=False, action='store_true',
                           help='disable the ROI button')
    argParser.add_argument('--disable-menu', default=False,
                           required=False, action='store_true',
                           help='disable the MENU button')
    argParser.add_argument('--enable-axis', default=False,
                           required=False, action='store_true',
                           help='disable the image axis')

    # VOLUME-SLICER PARAMETERS
    argParser.add_argument('--enable-slicesLines', default=False,
                           required=False, action='store_true',
                           help=' hide the slices lines')
    argParser.add_argument('--enable-slicesAxis', default=False,
                           required=False, action='store_true',
                           help='hide the axis')

    # GALLERY-VIEW PARAMETERS
    argParser.add_argument('--iconWidth', type=int, default=150,
                           required=False,
                           help=' an integer for image width')
    argParser.add_argument('--iconHeight', type=int, default=150,
                           required=False,
                           help=' an integer for image height')

    args = argParser.parse_args()

    # GENERAL ARGS
    kwargs['path'] = QDir.toNativeSeparators(args.path) if len(args.path) else \
        QDir.currentPath()
    kwargs['--slices'] = args.slices

    # EM-BROWSER ARGS
    kwargs['--disable-zoom'] = args.disable_zoom
    kwargs['--disable-histogram'] = args.disable_histogram
    kwargs['--disable-roi'] = args.disable_roi
    kwargs['--disable-menu'] = args.disable_menu
    kwargs['--enable-slicesAxis'] = args.enable_slicesAxis

    # VOLUME SLICER ARGS
    kwargs['--enable-slicesLines'] = args.enable_slicesLines
    kwargs['--enable-axis'] = args.enable_axis

    # GALLERY-VIEW ARGS
    kwargs['--iconWidth'] = args.iconWidth
    kwargs['--iconHeight'] = args.iconHeight

    if not args.path:  # Display the EM-BROWSER component

        kwargs['--path'] = QDir.currentPath()
        browserWin = BrowserWindow(**kwargs)
        browserWin.show()
    else:  # We parse the path

        isDir = QDir(args.path)

        if isDir:  # The path constitute an directory. In this case we display
                   # the EM-BROWSER component
            kwargs['--path'] = args.path
            browserWin = BrowserWindow(**kwargs)
            browserWin.show()

        else:  # The path constitute a file. In this case we parse this file

            directory = QDir(args.path)
            isFileExist = directory.exists(args.path)

            if isFileExist:  # The file exist

                if utils.isEmImage(args.path):  # The file constitute an
                                                # em-image.
                                          # In this case we determined if the
                                          # image has a volume or not

                    # Create an image from imagePath using em-bindings
                    image = em.Image()
                    loc2 = em.ImageLocation(args.path)
                    image.read(loc2)

                    # Determinate the image dimension
                    z = image.getDim().z

                    if z == 1:  # Display the EM-BROWSER component
                        kwargs['--path'] = args.path
                        browserWin = BrowserWindow(**kwargs)
                        browserWin.show()

                    else:  # The image has a Volume
                        if len(args.slices) == 1:
                            if args.slices[0] == 'axis':  # Display the Volume
                                                          # Slicer app
                                kwargs['imagePath'] = args.path
                                volumeSlice = VolumeSlice(**kwargs)
                                volumeSlice.show()
                            elif args.slices[0] == 'gallery':

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

                                xProperties = [
                                    ColumnProperties('X', 'X',
                                                     'Int',
                                                     **{'renderable': True,
                                                        'editable': False})]
                                yProperties = [
                                    ColumnProperties('Y', 'Y',
                                                     'Int',
                                                     **{'renderable': True,
                                                        'editable': False})]
                                zProperties = [
                                    ColumnProperties('Z', 'Z',
                                                     'Int',
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

                                tableWin = TableView(parent=None,
                                                      **xTableKwargs)
                                models = []

                                models.append(TableDataModel(
                                    parent=tableWin,
                                    title='X Axis (Right View)',
                                    emTable=xTable,
                                    columnProperties=xProperties))

                                models.append(TableDataModel(
                                    parent=tableWin,
                                    title='Y Axis (Left View)',
                                    emTable=yTable,
                                    columnProperties=yProperties))

                                models.append(TableDataModel(
                                    parent=tableWin,
                                    title='Z Axis (Front View)',
                                    emTable=zTable,
                                    columnProperties=zProperties))

                                tableWin.setModel(models)
                                tableWin.setItemDelegateForColumn(
                                    0, EMImageItemDelegate(
                                        parent=tableWin,
                                        selectedStatePen=None,
                                        borderPen=None,
                                        iconWidth=150,
                                        iconHeight=150,
                                        volData=_array3D,
                                        axis=X_AXIS),
                                    X_AXIS)
                                tableWin.setItemDelegateForColumn(
                                    0, EMImageItemDelegate(
                                        parent=tableWin,
                                        selectedStatePen=None,
                                        borderPen=None,
                                        iconWidth=150,
                                        iconHeight=150,
                                        volData=_array3D,
                                        axis=Y_AXIS),
                                    Y_AXIS)
                                tableWin.setItemDelegateForColumn(
                                    0, EMImageItemDelegate(
                                        parent=tableWin,
                                        selectedStatePen=None,
                                        borderPen=None,
                                        iconWidth=150,
                                        iconHeight=150,
                                        volData=_array3D,
                                        axis=Z_AXIS),
                                    Z_AXIS)

                                tableWin.show()

                            else:
                                QMessageBox.critical(app.parent(), 'ERROR',
                                                     'A valid way to display '
                                                     'the image are required')
                        else:  # Display the image by the default component:
                               # Volume-Slicer
                            kwargs['imagePath'] = args.path
                            volumeSlice = VolumeSlice(**kwargs)
                            volumeSlice.show()

                else:  # Display the EM-BROWSER component
                    kwargs['--path'] = args.path
                    browserWin = BrowserWindow(**kwargs)
                    browserWin.show()

            else:  # The file don't exist
                QMessageBox.critical(app.parent(), 'ERROR',
                                     'A file do not exist')
    sys.exit(app.exec_())
