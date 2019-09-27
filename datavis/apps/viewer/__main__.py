#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import traceback
import argparse
from glob import glob

from PyQt5.QtCore import QDir, QSize, Qt
from PyQt5.QtWidgets import (QApplication, QMessageBox)

from datavis.core import (EmPath, ViewsFactory, MOVIE_SIZE,
                        ImageManager)
from datavis.views import (DataView, PIXEL_UNITS, GALLERY, COLUMNS, ITEMS, SLICES,
                         ImageView, SlicesView, SHAPE_CIRCLE, SHAPE_RECT,
                         SHAPE_SEGMENT,
                         SHAPE_CENTER, DEFAULT_MODE, FILAMENT_MODE, PickerView,
                         PagingView)

from datavis.windows import BrowserWindow


class ValidateValues(argparse.Action):
    """ Class that allows the validation of mapped arguments values to the user
    valuesDict. The valuesDict keys most be specified in lower case.
    Example of use with argparse:
    on_off = {'on': True, 'off': False}
    argParser.add_argument('--zoom', type=str, default='on', required=False,
                           choices=on_off.keys(), action=ValidateValues,
                           valuesDict=on_off,
                           help=' Enable/disable the option to zoom in/out in '
                                'the image(s)')
    """
    def __init__(self, option_strings, dest, valuesDict, **kwargs):
        """ Creates a ValidateValues object
         - kwargs: The argparse.Action arguments and
            - valuesDict:  (dict) a dictionary for maps the values
        """
        argparse.Action.__init__(self, option_strings, dest, **kwargs)
        self._valuesDict = valuesDict or dict()

    def __call__(self, parser, namespace, values, option_string=None):
        values = str(values).lower()
        value = self._valuesDict.get(values, self._valuesDict.get(
            values.upper()))
        if value is None:
            raise ValueError("Invalid argument for %s" % option_string)
        setattr(namespace, self.dest, value)


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


class ValidateStrList(argparse.Action):
    """
    Class that allows the validation of the values corresponding to
    the "picker" parameter
    """

    def __init__(self, option_strings, dest, **kwargs):
        argparse.Action.__init__(self, option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        """
        Build a list with parameters separated by spaces.
        """
        setattr(namespace, self.dest, values.split())


def capitalizeStrList(strIterable):
    """
    Returns a capitalized str list from the given strIterable object
    :param strIterable: Iterable object
    """
    ret = []

    for v in strIterable:
        ret.append(v)
        ret.append(v.capitalize())
    return ret


if __name__ == '__main__':
    app = QApplication(sys.argv)
    paramCount = 0

    kwargs = {}

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
    on_off_dict = {'on': True, 'off': False}
    on_off = capitalizeStrList(on_off_dict.keys())
    argParser.add_argument('--zoom', type=str, default=True, required=False,
                           choices=on_off, action=ValidateValues,
                           valuesDict=on_off_dict,
                           help=' Enable/disable the option to zoom in/out in '
                                'the image(s)')
    argParser.add_argument('--axis', type=str, default=True, required=False,
                           choices=on_off, action=ValidateValues,
                           valuesDict=on_off_dict,
                           help=' Show/hide the image axis (ImageView)')
    argParser.add_argument('--tool-bar', type=str, default=True, required=False,
                           choices=on_off, action=ValidateValues,
                           valuesDict=on_off_dict,
                           help=' Show or hide the toolbar for ImageView')
    argParser.add_argument('--histogram', type=str, default=False,
                           required=False, choices=on_off,
                           action=ValidateValues,
                           valuesDict=on_off_dict,
                           help=' Show or hide the histogram for ImageView')
    argParser.add_argument('--fit', type=str, default=True,
                           required=False, choices=on_off,
                           action=ValidateValues,
                           valuesDict=on_off_dict,
                           help=' Enables fit to size for ImageView')
    viewsDict = {
        'gallery': GALLERY,
        'columns': COLUMNS,
        'items': ITEMS,
        'slices': SLICES
    }
    views_params = capitalizeStrList(viewsDict.keys())

    argParser.add_argument('--view', type=str, default='', required=False,
                           choices=views_params, action=ValidateValues,
                           valuesDict=viewsDict,
                           help=' The default view. Default will depend on the '
                                'input')
    argParser.add_argument('--size', type=int, default=64,
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
    shapeDict = {
        'RECT': SHAPE_RECT,
        'CIRCLE': SHAPE_CIRCLE,
        'CENTER': SHAPE_CENTER,
        'SEGMENT': SHAPE_SEGMENT
    }
    shape_params = capitalizeStrList(shapeDict.keys())
    argParser.add_argument('--shape', default=SHAPE_RECT,
                           required=False, choices=shape_params,
                           valuesDict=shapeDict,
                           action=ValidateValues,
                           help=' the shape type '
                                '[CIRCLE, RECT, CENTER or SEGMENT]')
    pickerDict = {
        'default': DEFAULT_MODE,
        'filament': FILAMENT_MODE
    }
    picker_params = capitalizeStrList(pickerDict.keys())
    argParser.add_argument('--picker-mode', type=str, default=DEFAULT_MODE,
                           required=False,
                           choices=picker_params, valuesDict=pickerDict,
                           action=ValidateValues,
                           help=' the picker type [default or filament]')
    argParser.add_argument('--remove-rois', type=str, default=True,
                           required=False, choices=on_off,
                           action=ValidateValues,
                           valuesDict=on_off_dict,
                           help=' Enable/disable the option. '
                                'The user will be able to eliminate rois')
    argParser.add_argument('--roi-aspect-locked', type=str, default=True,
                           required=False, choices=on_off,
                           action=ValidateValues,
                           valuesDict=on_off_dict,
                           help=' Enable/disable the option. '
                                'The rois will retain the aspect ratio')
    argParser.add_argument('--roi-centered', type=str, default=True,
                           required=False, choices=on_off,
                           action=ValidateValues,
                           valuesDict=on_off_dict,
                           help=' Enable/disable the option. '
                                'The rois will work accordance with its center')
    # COLUMNS PARAMS
    argParser.add_argument('--visible', type=str, nargs='?', default='',
                           required=False, action=ValidateStrList,
                           help=' Columns to be shown (and their order).')
    argParser.add_argument('--render', type=str, nargs='?', default='',
                           required=False, action=ValidateStrList,
                           help=' Columns to be rendered.')
    argParser.add_argument('--sort', type=str, nargs='?', default='',
                           required=False, action=ValidateStrList,
                           help=' Sort command.')

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
    kwargs['roi'] = False
    kwargs['menu'] = False
    kwargs['popup'] = False
    kwargs['toolBar'] = args.tool_bar
    kwargs['img_desc'] = False
    kwargs['fit'] = args.fit
    kwargs['axis'] = args.axis
    kwargs['size'] = args.size
    kwargs['maxCellSize'] = 300
    kwargs['minCellSize'] = 25
    kwargs['zoom_units'] = PIXEL_UNITS
    kwargs['views'] = {GALLERY: {}, COLUMNS: {}, ITEMS: {}}

    kwargs['view'] = args.view
    kwargs['selectionMode'] = PagingView.MULTI_SELECTION

    # Picker params
    kwargs['boxSize'] = args.boxsize
    kwargs['pickerMode'] = args.picker_mode
    kwargs['shape'] = args.shape
    kwargs['removeRois'] = args.remove_rois
    kwargs['roiAspectLocked'] = args.roi_aspect_locked
    kwargs['roiCentered'] = args.roi_centered

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
            size = viewWidget.getPreferredSize()
            x, y, w, h = getPreferedBounds(size[0], size[1])
        elif (isinstance(viewWidget, ImageView) or
                isinstance(viewWidget, SlicesView) or
                isinstance(viewWidget, PickerView)) and \
                imageDim is not None:
            dx, dy = imageDim[0], imageDim[1]
            x, y, w, h = getPreferedBounds(max(viewWidget.width(), dx),
                                           max(viewWidget.height(), dy))
            size = QSize(dx, dy).scaled(w, h, Qt.KeepAspectRatio)
            dw, dh = w - size.width(), h - size.height()
            x, y, w, h = x + dw/2, y + dh/2, size.width(), size.height()
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
        if args.picker in ['on', 'On'] or isinstance(args.picker, dict):
            if files and files[0] == str(os.getcwd()):
                files = None
            kwargs['selectionMode'] = PagingView.SINGLE_SELECTION
            view = ViewsFactory.createPickerView(files, sources=args.picker,
                                                 **kwargs)
            view.setWindowTitle("EM-PICKER")
            d = view.getPreferredSize()
        else:
            # If the input is a directory, display the BrowserWindow
            if len(files) > 1:
                raise Exception("Multiple files are not supported")
            else:
                files = files[0]

            if not os.path.exists(files):
                raise Exception("Input file '%s' does not exists. " % files)

            if os.path.isdir(files):
                kwargs['selectionMode'] = PagingView.SINGLE_SELECTION
                kwargs['view'] = args.view or COLUMNS
                view = BrowserWindow(None, files, **kwargs)
            elif EmPath.isTable(files):  # Display the file as a Table:
                if not args.view == SLICES:
                    if args.visible or args.render:
                        # FIXME[phv] create the TableConfig
                        pass
                    else:
                        tableViewConfig = None
                    if args.sort:
                        # FIXME[phv] sort by the given column
                        pass
                    kwargs['view'] = args.view or COLUMNS
                    view = ViewsFactory.createDataView(files, **kwargs)
                    fitViewSize(view, d)
                else:
                    raise Exception("Invalid display mode for table: '%s'"
                                    % args.view)
            elif EmPath.isData(files):
                # *.mrc may be image, stack or volume. Ask for dim.n
                x, y, z, n = ImageManager().getDim(files)
                if n == 1:  # Single image or volume
                    if z == 1:  # Single image
                        view = ViewsFactory.createImageView(files, **kwargs)
                    else:  # Volume
                        mode = args.view or SLICES
                        if mode == SLICES or mode == GALLERY:
                            kwargs['toolBar'] = False
                            kwargs['axis'] = False
                            sm = PagingView.SINGLE_SELECTION
                            kwargs['selectionMode'] = sm
                            view = ViewsFactory.createVolumeView(files,
                                                                 **kwargs)
                        else:
                            raise Exception("Invalid display mode for volume")
                else:  # Stack
                    kwargs['selectionMode'] = PagingView.SINGLE_SELECTION
                    if z > 1:  # volume stack
                        mode = args.view or SLICES
                        if mode == SLICES:
                            kwargs['toolBar'] = False
                            kwargs['axis'] = False
                            view = ViewsFactory.createVolumeView(files,
                                                                 **kwargs)
                        else:
                            kwargs['view'] = GALLERY
                            view = ViewsFactory.createDataView(files, **kwargs)
                    else:
                        mode = args.view or (SLICES if x > MOVIE_SIZE
                                             else GALLERY)
                        if mode == SLICES:
                            view = ViewsFactory.createSlicesView(files,
                                                                 **kwargs)
                        else:
                            kwargs['view'] = mode
                            view = ViewsFactory.createDataView(files, **kwargs)
            elif EmPath.isStandardImage(files):
                view = ViewsFactory.createImageView(files, **kwargs)
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
