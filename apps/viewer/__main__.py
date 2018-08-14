#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import argparse


from PyQt5.QtCore import QDir
from PyQt5.QtWidgets import QApplication, QMessageBox

import em
from emqt5.utils import EmPath, EmTable, EmImage
from emqt5.views import (DataView, PERCENT_UNITS, PIXEL_UNITS,
                         createVolumeModel, TableDataModel, MultiSliceView,
                         TableViewConfig)
from emqt5.widgets.image import ImageView
from emqt5.windows import BrowserWindow

import numpy as np

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
    argParser.add_argument('--view', type=str, default='',
                           required=False,
                           choices=['gallery', 'columns', 'items', 'slices'],
                           help=' the default view. COLUMNS if not specified')
    argParser.add_argument('--views', type=str, nargs='+',
                           choices=['gallery', 'columns', 'items'],
                           default=['gallery', 'columns', 'items'],
                           required=False,
                           help=' list of views. [COLUMNS, ITEMS, GALLERY] '
                                'if not specified')
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
    #  ImageView Params
    argParser.add_argument('--tool-bar', type=str, default='On',
                           required=False,
                           choices=['On', 'Off'],
                           help=' show or hide the toolbar for ImageView')
    argParser.add_argument('--roi-btn', type=str, default='On',
                           required=False,
                           choices=['On', 'Off'],
                           help=' show or hide the ROI button for ImageView')
    argParser.add_argument('--menu-btn', type=str, default='On',
                           required=False,
                           choices=['On', 'Off'],
                           help=' show or hide the menu button for ImageView')
    argParser.add_argument('--histogram', type=str, default='On',
                           required=False,
                           choices=['On', 'Off'],
                           help=' show or hide the histogram for ImageView')
    argParser.add_argument('--rotation-step', type=int, default=90,
                           required=False,
                           help=' set the rotation step for ImageView')
    argParser.add_argument('--img-desc', type=str, default='On',
                           required=False,
                           choices=['On', 'Off'],
                           help=' show or hide the image description '
                                'for ImageView')
    argParser.add_argument('--fit-to-size', type=str, default='On',
                           required=False,
                           choices=['On', 'Off'],
                           help=' enables fit to size for ImageView')
    argParser.add_argument('--popup-menu', type=str, default='On',
                           required=False,
                           choices=['On', 'Off'],
                           help=' enables the Popup Menu for ImageView')
    args = argParser.parse_args()

    models = None
    delegates = None

    # GENERAL ARGS
    kwargs['files'] = QDir.toNativeSeparators(args.files) if len(args.files) \
        else QDir.currentPath()

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

    view = args.view
    views = {'gallery': DataView.GALLERY,
             'columns': DataView.COLUMNS,
             'items': DataView.ITEMS}

    vs = []
    for v in args.views:
        vs.append(views[v])
    kwargs['views'] = vs
    kwargs['histogram'] = args.histogram
    kwargs['menu-btn'] = args.menu_btn
    kwargs['roi-btn'] = args.roi_btn
    kwargs['popup-menu'] = args.popup_menu
    kwargs['fit-to-size'] = args.fit_to_size

    # IMAGE VIEW ARGS
    kwargs['tool-bar'] = args.tool_bar
    kwargs['roi-btn'] = args.roi_btn
    kwargs['menu-btn'] = args.menu_btn
    kwargs['histogram'] = args.histogram
    kwargs['rotation-step'] = args.rotation_step
    kwargs['img-desc'] = args.tool_bar
    kwargs['fit-to-size'] = args.fit_to_size

    def createDataView(table, tableViewConfig, title, defaultView):
        kwargs['view'] = defaultView
        dataView = DataView(None, **kwargs)
        dataView.setModel(TableDataModel(table, title=title,
                                         tableViewConfig=tableViewConfig))
        return dataView

    def createBrowserView(path):
        return BrowserWindow(None, path, **kwargs)

    def createImageView(image):
        dim = image.getDim()
        imgView = ImageView(None, **kwargs)
        desc = "<html><head/><body><p><span style=\" color:#0055ff;\">" \
               "Dimension:  </span><span style=\" color:#000000;\">" \
               "(%d,%d,%d,%d)</span></p></body></html>"
        data = np.array(image, copy=False)
        imgView.setImage(data)
        imgView.setImageDescription(desc % (dim.x, dim.y, dim.z, dim.n))
        return imgView

    files = args.files or os.getcwd()  # if not files use the current dir

    if not os.path.exists(files):
        raise Exception("Input file '%s' does not exists. " % files)

    # If the input is a directory, display the BrowserWindow
    if os.path.isdir(files):
        view = createBrowserView(files)
    elif EmPath.isTable(files):  # Display the file as a Table:
        view = createDataView(EmTable.load(files), None, 'Table',
                              views.get(args.view, DataView.COLUMNS))
    elif EmPath.isImage(files) or EmPath.isVolume(files) \
            or EmPath.isStack(files):
        # *.mrc may be image, stack or volume. Ask for dim.n
        d = EmImage.getDim(files)
        if d.n == 1:  # Single image or volume
            if d.z == 1:  # Single image
                image = em.Image()
                loc2 = em.ImageLocation(files)
                image.read(loc2)
                view = createImageView(image)
            else:  # Volume
                mode = args.view or 'slices'
                if mode == 'slices':
                    view = MultiSliceView(path=files)
                elif mode == 'gallery' or mode == 'columns' or mode == 'items':
                    model = createVolumeModel(files)
                    kwargs['view'] = views[mode]
                    view = DataView(None, **kwargs)
                    view.setModel(model)
                else:
                    raise Exception("Invalid display mode for volume: '%s'"
                                    % mode)
        else:  # Stack
            view = createDataView(EmTable.fromStack(files),
                                  TableViewConfig.createStackConfig(),
                                  'Stack',
                                  views.get(args.view, DataView.GALLERY))
    elif EmPath.isTable(files):  # Display the file as a Table:
        view = createDataView(EmTable.load(files), None, 'Table',
                               views.get(args.view, DataView.COLUMNS))
    else:
        view = None
        raise Exception("Can't perform a view for this file.")

    if view:
        view.show()

    sys.exit(app.exec_())
