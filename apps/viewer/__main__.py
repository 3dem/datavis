#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
from glob import glob
import argparse
import traceback


from PyQt5.QtCore import QDir
from PyQt5.QtWidgets import QApplication, QMessageBox

from emqt5.utils import EmPath, EmTable, EmImage
from emqt5.views import (DataView, PERCENT_UNITS, PIXEL_UNITS, TableViewConfig,
                         ImageView, SlicesView, createDataView,
                         createVolumeView, createImageView, createSlicesView,
                         MOVIE_SIZE, SHAPE_CIRCLE, SHAPE_RECT, PickerView,
                         createPickerModel)
from emqt5.windows import BrowserWindow


if __name__ == '__main__':
    app = QApplication(sys.argv)
    paramCount = 0

    kwargs = {}

    class ValidateMics(argparse.Action):
        """
        Class that allows the validation of the values corresponding to
        the "picker" parameter
        """
        def __init__(self, option_strings, dest, **kwargs):
            argparse.Action.__init__(self, option_strings, dest, **kwargs)

        def __call__(self, parser, namespace, values, option_string=None):
            """
            Validate the maximum number of values corresponding to the
            picker parameter. Try to matching a path pattern for micrographs
            and another for coordinates.

            Return a list of tuples [mic_path, pick_path].
            """
            length = len(values)
            result = dict()
            if length > 2:
                raise ValueError("Invalid number of arguments for %s. Only 2 "
                                 "arguments are supported." % option_string)

            if length > 0:
                mics = self.__ls(values[0])
                for i in mics:
                    basename = os.path.splitext(os.path.basename(i))[0]
                    result[basename] = (i, None)

            if length > 1:
                coords = self.__ls(values[1])
                for i in coords:
                    basename = os.path.splitext(os.path.basename(i))[0]
                    t = result.get(basename)
                    if t:
                        result[basename] = (t[0], i)

            setattr(namespace, self.dest, result)

        def __ls(self, pattern):
            return glob(pattern)

    argParser = argparse.ArgumentParser(usage='Tool for Viewer Apps',
                                        description='Display the selected '
                                                    'viewer app',
                                        prefix_chars='--',
                                        argument_default=None)

    # GLOBAL PARAMETERS
    argParser.add_argument('files', type=str, nargs='*', default=[],
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

    # Picker arguments
    argParser.add_argument('--picker', type=str, nargs='*', default=[],
                           required=False, action=ValidateMics,
                           help='Show the Picker tool. '
                                '2 path pattern for micrograph and coordinates '
                                'files.')
    argParser.add_argument('--boxsize', type=int, default=100,
                           required=False,
                           help=' an integer for pick size(Default=100).')
    argParser.add_argument('--shape', default='RECT',
                           required=False, choices=['RECT', 'CIRCLE'],
                           help=' the shape type [CIRCLE or RECT]')
    argParser.add_argument('--remove-rois', type=str, default='on',
                           required=False, choices=on_off,
                           help=' Enable/disable the option. '
                                'The user will be able to eliminate rois')
    argParser.add_argument('--roi-aspect-locked', type=str, default='on',
                           required=False, choices=on_off,
                           help=' Enable/disable the option. '
                                'The rois will retain the aspect ratio')
    argParser.add_argument('--roi-centered', type=str, default='on',
                           required=False, choices=on_off,
                           help=' Enable/disable the option. '
                                'The rois will work accordance with its center')

    args = argParser.parse_args()

    models = None
    delegates = None

    # ARGS
    files = []
    for f in args.files:
        files.append(QDir.toNativeSeparators(f))

    if not files and not args.picker:
        files = [str(os.getcwd())]  # if not files use the current dir

    kwargs['files'] = files
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

    # Picker params
    kwargs['boxsize'] = args.boxsize
    kwargs['shape'] = SHAPE_RECT if args.shape == 'RECT' else SHAPE_CIRCLE
    kwargs['remove_rois'] = args.remove_rois
    kwargs['roi_aspect_locked'] = args.roi_aspect_locked
    kwargs['roi_centered'] = args.roi_centered

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
            size = viewWidget.getPreferedSize()
            x, y, w, h = getPreferedBounds(size[0], size[1])
        elif (isinstance(viewWidget, ImageView) or
                isinstance(viewWidget, SlicesView)) and \
                imageDim is not None:
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

        msgBox.exec_()

    try:
        d = None
        if args.picker == 'on' or isinstance(args.picker, dict):
            if files and files[0] == str(os.getcwd()):
                files = None
            view = PickerView(None, createPickerModel(files, args.boxsize),
                              sources=args.picker, **kwargs)
            view.setWindowTitle("EM-PICKER")
        else:
            # If the input is a directory, display the BrowserWindow
            if len(files) > 1:
                raise Exception("Multiple files are not supported")
            else:
                files = files[0]

            if not os.path.exists(files):
                raise Exception("Input file '%s' does not exists. " % files)

            if os.path.isdir(files):
                view = BrowserWindow(None, files, **kwargs)
            elif EmPath.isTable(files):  # Display the file as a Table:
                if not args.view == 'slices':
                    t = EmTable.load(files)  # name, table
                    view = createDataView(t[1], None, t[0],
                                          views.get(args.view,
                                                    DataView.COLUMNS),
                                          dataSource=files)
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
                            raise Exception("Invalid display mode for volume: "
                                            "'%s'" % mode)
                else:  # Stack
                    if d.z > 1:  # volume stack
                        mode = args.view or 'slices'
                        if mode == 'slices':
                            kwargs['tool_bar'] = 'off'
                            view = createVolumeView(files, **kwargs)
                        else:
                            view = createDataView(
                                EmTable.fromStack(files),
                                TableViewConfig.createStackConfig(),
                                ['Stack'], views.get(args.view,
                                                     DataView.GALLERY),
                                **kwargs)
                    else:
                        mode = args.view or ('slices' if d.x > MOVIE_SIZE
                                             else 'gallery')
                        if mode == 'slices':
                            view = createSlicesView(files, **kwargs)
                        else:
                            view = createDataView(
                                EmTable.fromStack(files),
                                TableViewConfig.createStackConfig(),
                                ['Stack'], views.get(mode, DataView.GALLERY),
                                **kwargs)
            elif EmPath.isStandardImage(files):
                view = createImageView(files, **kwargs)
            else:
                view = None
                raise Exception("Can't perform a view for this file.")

        if view:
            fitViewSize(view, d)
            view.show()

    except Exception as ex:
        showMsgBox("Can't perform the action", QMessageBox.Critical, str(ex))
        print(traceback.format_exc())
        sys.exit(0)
    except RuntimeError as ex:
        showMsgBox("Can't perform the action", QMessageBox.Critical, str(ex))
        print(traceback.format_exc())
        sys.exit(0)
    except ValueError as ex:
        showMsgBox("Can't perform the action", QMessageBox.Critical, str(ex))
        print(traceback.format_exc())
        sys.exit(0)

    sys.exit(app.exec_())
