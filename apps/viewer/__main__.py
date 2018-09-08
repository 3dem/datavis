#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import argparse


from PyQt5.QtCore import QDir
from PyQt5.QtWidgets import QApplication

import em
from emqt5.utils import EmPath, EmTable, EmImage
from emqt5.views import (DataView, PERCENT_UNITS, PIXEL_UNITS,
                         createVolumeModel, TableDataModel, TableViewConfig,
                         ImageView, VolumeView, SlicesView)
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
    on_off = ['on', 'off']
    argParser.add_argument('--zoom', type=str, default='on', required=False,
                           choices=on_off,
                           help=' Enable/disable the option to zoom in/out in '
                                'the image(s)')
    argParser.add_argument('--axis', type=str, default='on', required=False,
                           choices=on_off,
                           help=' Show/hide the image axis (ImageView)')
    argParser.add_argument('--tool-bar', type=str, default='on', required=False,
                           choices=on_off,
                           help=' Show or hide the toolbar for ImageView')
    argParser.add_argument('--histogram', type=str, default='off',
                           required=False, choices=on_off,
                           help=' Show or hide the histogram for ImageView')
    argParser.add_argument('--fit', type=str, default='on',
                           required=False, choices=on_off,
                           help=' Enables fit to size for ImageView')
    argParser.add_argument('--view', type=str, default='', required=False,
                           choices=['gallery', 'columns', 'items', 'slices'],
                           help=' The default view. Default will depend on the '
                                'input')
    argParser.add_argument('--size', type=int, default=100,
                           required=False,
                           help=' The default size of the displayed image, '
                                'either in pixels or in percentage')

    args = argParser.parse_args()

    models = None
    delegates = None

    # ARGS
    kwargs['files'] = QDir.toNativeSeparators(args.files) if len(args.files) \
        else QDir.currentPath()

    kwargs['zoom'] = args.zoom
    kwargs['histogram'] = args.histogram
    kwargs['roi'] = on_off[1]
    kwargs['menu'] = on_off[1]
    kwargs['popup'] = on_off[1]
    kwargs['tool_bar'] = args.tool_bar
    kwargs['img_desc'] = on_off[1]
    kwargs['fit'] = args.fit
    kwargs['axis'] = args.axis
    kwargs['size'] = args.size
    kwargs['max_cell_size'] = 300
    kwargs['min_cell_size'] = 20
    kwargs['zoom_units'] = PIXEL_UNITS
    kwargs['views'] = [DataView.GALLERY, DataView.COLUMNS, DataView.ITEMS]

    views = {'gallery': DataView.GALLERY,
             'columns': DataView.COLUMNS,
             'items': DataView.ITEMS,
             'slices': DataView.SLICES}
    kwargs['view'] = views.get(args.view, DataView.COLUMNS)

    def getPreferedBounds():
        size = QApplication.desktop().size()
        p = 0.8
        (w, h) = (int(p * size.width()), int(p * size.height()))
        return (size.width() - w) / 2, (size.height() - h) / 2, w, h


    def createDataView(table, tableViewConfig, title, defaultView):
        kwargs['view'] = defaultView
        dataView = DataView(None, **kwargs)
        dataView.setModel(TableDataModel(table, title=title,
                                         tableViewConfig=tableViewConfig))
        return dataView

    def createBrowserView(path):
        bounds = getPreferedBounds()
        browser = BrowserWindow(None, path, **kwargs)
        browser.setGeometry(bounds[0], bounds[1], bounds[2], bounds[3])
        return browser

    def createVolumeView():
        kwargs['tool_bar'] = 'off'
        bounds = getPreferedBounds()
        volumeView = VolumeView(None, **kwargs)
        volumeView.setGeometry(bounds[0], bounds[1], bounds[2], bounds[3])
        return volumeView

    def createSlicesView():
        bounds = getPreferedBounds()
        slicesView = SlicesView(None, **kwargs)
        slicesView.setGeometry(bounds[0], bounds[1], bounds[2], bounds[3])
        return slicesView

    def createImageView(image):
        dim = image.getDim()
        imgView = ImageView(None, **kwargs)
        desc = "<html><head/><body><p><span style=\" color:#0055ff;\">" \
               "Dimension:  </span><span style=\" color:#000000;\">" \
               "(%d,%d,%d,%d)</span></p></body></html>"
        data = np.array(image, copy=False)
        imgView.setImage(data)
        imgView.setImageDescription(desc % (dim.x, dim.y, dim.z, dim.n))
        bounds = getPreferedBounds()
        imgView.setGeometry(bounds[0], bounds[1], bounds[2], bounds[3])
        return imgView

    files = args.files or os.getcwd()  # if not files use the current dir

    if not os.path.exists(files):
        raise Exception("Input file '%s' does not exists. " % files)

    # If the input is a directory, display the BrowserWindow
    if os.path.isdir(files):
        view = createBrowserView(files)
    elif EmPath.isTable(files):  # Display the file as a Table:
        if not args.view == 'slices':
            view = createDataView(EmTable.load(files), None, 'Table',
                                  views.get(args.view, DataView.COLUMNS))
        else:
            raise Exception("Invalid display mode for table: '%s'"
                            % args.view)
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
                if mode == 'slices' or mode == 'gallery':
                    kwargs['path'] = files
                    kwargs['view'] = views[mode]
                    view = createVolumeView()
                else:
                    raise Exception("Invalid display mode for volume: '%s'"
                                    % mode)
        else:  # Stack
            mode = args.view or 'slices'
            if d.z > 1:  # volume stack
                if mode == 'slices':
                    kwargs['path'] = files
                    view = createVolumeView()
                else:
                    view = createDataView(EmTable.fromStack(files),
                                          TableViewConfig.createStackConfig(),
                                          'Stack',
                                          views.get(args.view,
                                                    DataView.GALLERY))
            else:
                if mode == 'slices':
                    kwargs['path'] = files
                    view = createSlicesView()
                else:
                    view = createDataView(EmTable.fromStack(files),
                                          TableViewConfig.createStackConfig(),
                                          'Stack',
                                          views.get(args.view,
                                                    DataView.GALLERY))
    else:
        view = None
        raise Exception("Can't perform a view for this file.")

    if view:
        view.show()

    sys.exit(app.exec_())
