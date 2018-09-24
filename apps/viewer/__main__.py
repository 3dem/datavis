#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import argparse
import traceback


from PyQt5.QtCore import QDir
from PyQt5.QtWidgets import QApplication, QMessageBox

from emqt5.utils import EmPath, EmTable, EmImage
from emqt5.views import (DataView, PERCENT_UNITS, PIXEL_UNITS,
                         ColumnsView, TableDataModel, TableViewConfig,
                         ImageView, VolumeView, SlicesView, createDataView,
                         createVolumeView, createImageView, createSlicesView)
from emqt5.windows import BrowserWindow


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

    def getPreferedBounds(width=None, height=None):
        size = QApplication.desktop().size()
        p = 0.8
        (w, h) = (int(p * size.width()), int(p * size.height()))
        width = width or w
        height = height or h
        w = min(width, w)
        h = min(height, h)
        return (size.width() - w) / 2, (size.height() - h) / 2, w, h

    def fitViewSize(viewWidget, imageDim=None):
        """
        Fit the view size according to the desktop size.
        imageDim is the image dimensions if viewWidget is ImageView
         """
        if view is None:
            return

        if isinstance(viewWidget, DataView):
            currentView = view.getViewWidget()

            if isinstance(currentView, ColumnsView):
                width = currentView.getHeaderSize()
                x, y, w, h = getPreferedBounds(width, viewWidget.height())
        elif isinstance(viewWidget, ImageView) and imageDim is not None:
            x, y, w, h = getPreferedBounds(max(viewWidget.width(),
                                               imageDim.x),
                                           max(viewWidget.height(),
                                               imageDim.y))
        else:
            x, y, w, h = getPreferedBounds(100000,
                                           100000)
        viewWidget.setGeometry(x, y, w, h)

    def showMsgBox(text, icon=None, details=None):
        """
        Show a message box with the given text, icon and details.
        The icon of the message box can be specified with one of the Qt values:
            QMessageBox.NoIcon
            QMessageBox.Question
            QMessageBox.Information
            QMessageBox.Warning
            QMessageBox.Critical
        """
        msgBox = QMessageBox()
        msgBox.setText(text)
        msgBox.setStandardButtons(QMessageBox.Ok)
        msgBox.setDefaultButton(QMessageBox.Ok)
        if icon is not None:
            msgBox.setIcon(icon)
        if details is not None:
            msgBox.setDetailedText(details)

        msgBox.exec()

    files = args.files or os.getcwd()  # if not files use the current dir

    try:
        if not os.path.exists(files):
            raise Exception("Input file '%s' does not exists. " % files)

        d = None
        # If the input is a directory, display the BrowserWindow
        if os.path.isdir(files):
            view = BrowserWindow(None, files, **kwargs)
        elif EmPath.isTable(files):  # Display the file as a Table:
            if not args.view == 'slices':
                view = createDataView(EmTable.load(files), None, 'Table',
                                      views.get(args.view, DataView.COLUMNS))
                fitViewSize(view, d)
            else:
                raise Exception("Invalid display mode for table: '%s'"
                                % args.view)
        elif EmPath.isImage(files) or EmPath.isVolume(files) \
                or EmPath.isStack(files):
            # *.mrc may be image, stack or volume. Ask for dim.n
            d = EmImage.getDim(files)
            if d.n == 1:  # Single image or volume
                if d.z == 1:  # Single image
                    view = createImageView(files, **kwargs)
                else:  # Volume
                    mode = args.view or 'slices'
                    if mode == 'slices' or mode == 'gallery':
                        kwargs['view'] = views[mode]
                        kwargs['tool_bar'] = 'off'
                        view = createVolumeView(files, **kwargs)
                    else:
                        raise Exception("Invalid display mode for volume: '%s'"
                                        % mode)
            else:  # Stack
                mode = args.view or 'slices'
                if d.z > 1:  # volume stack
                    if mode == 'slices':
                        kwargs['tool_bar'] = 'off'
                        view = createVolumeView(files, **kwargs)
                    else:
                        view = createDataView(EmTable.fromStack(files),
                                              TableViewConfig.createStackConfig(),
                                              'Stack',
                                              views.get(args.view,
                                                        DataView.GALLERY))
                else:
                    if mode == 'slices':
                        view = createSlicesView(files, **kwargs)
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
            fitViewSize(view, d)
            view.show()

    except Exception as ex:
        showMsgBox("Can't perform the action", QMessageBox.Critical, str(ex))
        print(traceback.format_exc())
    except RuntimeError as ex:
        showMsgBox("Can't perform the action", QMessageBox.Critical, str(ex))
        print(traceback.format_exc())
    except ValueError as ex:
        showMsgBox("Can't perform the action", QMessageBox.Critical, str(ex))
        print(traceback.format_exc())

    sys.exit(app.exec_())
