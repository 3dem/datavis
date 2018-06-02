#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from PyQt5.QtWidgets import QApplication, QMessageBox

from PyQt5.QtCore import QDir

import em
from emqt5.widgets.image.browser_window import BrowserWindow
from emqt5.widgets.image.volume_slicer import VolumeSlice
from emqt5.views import (TableView, PERCENT_UNITS, PIXEL_UNITS,
                         createVolumeModel, createStackModel, createTableModel)
import emqt5.utils.functions as em_utils


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
    argParser.add_argument('files', type=str, nargs='?', default=[],
                            help='3D image path or a list of image files or'
                                 ' specific directory')
    argParser.add_argument('--slices', type=str, default=['gallery', 'axis'],
                           nargs='+', required=False, choices=['gallery',
                                                               'axis'],
                           help=' list of accessible')

    # EM-BROWSER PARAMETERS
    argParser.add_argument('--disable-zoom', default=False,
                           required=False, action='store_true',
                           help=' do not scale the image')
    argParser.add_argument('--enable-axis', default=False,
                           required=False, action='store_true',
                           help='disable the image axis')

    # TABLE-VIEW PARAMETERS
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

    # GENERAL ARGS
    kwargs['files'] = QDir.toNativeSeparators(args.files) if len(args.files) \
        else QDir.currentPath()
    kwargs['--slices'] = args.slices

    # EM-BROWSER ARGS
    kwargs['--disable-zoom'] = args.disable_zoom
    kwargs['--disable-histogram'] = args.disable_histogram
    kwargs['--disable-roi'] = args.disable_roi
    kwargs['--disable-menu'] = args.disable_menu

    # TABLE-VIEW ARGS
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

    if not args.files:  # Display the EM-BROWSER component

        kwargs['--files'] = QDir.currentPath()
        browserWin = BrowserWindow(**kwargs)
        browserWin.show()
    else:  # We parse the path

        isDir = QDir(args.files)

        if isDir:  # The path constitute an directory. In this case we display
                   # the EM-BROWSER component
            kwargs['--files'] = args.files
            browserWin = BrowserWindow(**kwargs)
            browserWin.show()

        else:  # The path constitute a file. In this case we parse this file

            directory = QDir(args.files)
            isFileExist = directory.exists(args.files)

            if isFileExist:  # The file exist

                if em_utils.isEmImage(args.files) or \
                        em_utils.isEMImageVolume(args.files):
                    # The file constitute an em-image.
                    # In this case we determined if the
                    # image has a volume or not

                    # Create an image from imagePath using em-bindings
                    image = em.Image()
                    loc2 = em.ImageLocation(args.files)
                    image.read(loc2)

                    # Determinate the image dimension
                    z = image.getDim().z

                    if z == 1:  # Display the EM-BROWSER component
                        kwargs['--files'] = args.files
                        browserWin = BrowserWindow(**kwargs)
                        browserWin.show()

                    else:  # The image has a Volume
                        if len(args.slices) == 1:
                            if args.slices[0] == 'axis':  # Display the Volume
                                                          # Slicer app
                                kwargs['imagePath'] = args.files
                                volumeSlice = VolumeSlice(**kwargs)
                                volumeSlice.show()
                            elif args.slices[0] == 'gallery':  # Display the
                                                               # Gallery app
                                models, delegates = createVolumeModel(args.files)
                                kwargs['defaultRowHeight'] = 120
                                kwargs['defaultView'] = 'GALLERY'
                                kwargs['views'] = ['GALLERY', 'TABLE']
                                tableWin = TableView(parent=None,
                                                     **kwargs)
                                tableWin.setModel(models, delegates)
                                tableWin.show()

                            else:
                                QMessageBox.critical(app.parent(), 'ERROR',
                                                     'A valid way to display '
                                                     'the image are required')
                        else:  # Display the image by the default component:
                               # Volume-Slicer
                            kwargs['imagePath'] = args.files
                            volumeSlice = VolumeSlice(**kwargs)
                            volumeSlice.show()

                elif em_utils.isEMImageStack(args.files):  # Display the file as
                                                          # a Image Stack
                    models, delegates = createStackModel(args.files)
                    kwargs['defaultRowHeight'] = 120
                    kwargs['defaultView'] = 'GALLERY'
                    kwargs['views'] = ['GALLERY', 'TABLE']
                    tableWin = TableView(parent=None,
                                         **kwargs)
                    tableWin.setModel(models, delegates)
                    tableWin.show()

                elif em_utils.isEMTable(args.files):   # Display the file as
                                                      # a Table
                        models = [createTableModel(args.files)]
                        kwargs['defaultRowHeight'] = 120
                        kwargs['defaultView'] = 'TABLE'
                        kwargs['views'] = ['TABLE']

                        tableWin = TableView(parent=None,
                                             **kwargs)
                        tableWin.setModel(models)
                        tableWin.show()

                else:  # Display the EM-BROWSER component
                    kwargs['--files'] = args.files
                    browserWin = BrowserWindow(**kwargs)
                    browserWin.show()

            else:  # The file don't exist
                QMessageBox.critical(app.parent(), 'ERROR',
                                     'A file do not exist')
    sys.exit(app.exec_())
