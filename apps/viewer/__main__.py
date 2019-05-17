#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
from glob import glob
import argparse
import traceback
import qtawesome as qta

from PyQt5.QtCore import QDir, QSize, Qt, pyqtSlot
from PyQt5.QtWidgets import (QApplication, QMessageBox, QWidget, QHBoxLayout,
                             QSplitter, QSizePolicy, QVBoxLayout, QAction,
                             QPushButton, QAbstractItemView)

from emqt5.utils import EmPath, EmTable, ImageManager, VolImageManager
from emqt5.views import (DataView, PIXEL_UNITS, TableViewConfig,
                         ImageView, SlicesView, createDataView,
                         createVolumeView, createImageView, createSlicesView,
                         MOVIE_SIZE, SHAPE_CIRCLE, SHAPE_RECT, SHAPE_SEGMENT,
                         SHAPE_CENTER, DEFAULT_MODE, FILAMENT_MODE, PickerView,
                         createPickerModel)
from emqt5.views.base import AbstractView, DynamicWidgetsFactory
from emqt5.widgets import ToolBar
from emqt5.views.columns import ColumnsView
from emqt5.views.volume_view import VolumeView
from emqt5.windows import BrowserWindow
from emqt5.views.model import TableDataModel


import em

tool_params1 = [
    [
        {
            'name': 'threshold',
            'type': 'float',
            'value': 0.55,
            'label': 'Quality threshold',
            'help': 'If this is ... bla bla bla',
            'display': 'default'
        },
        {
            'name': 'thresholdBool',
            'type': 'bool',
            'value': True,
            'label': 'Quality checked',
            'help': 'If this is a boolean param'
        }
    ],
    [
        {
            'name': 'threshold543',
            'type': 'float',
            'value': 0.67,
            'label': 'Quality',
            'help': 'If this is ... bla bla bla',
            'display': 'default'
        },
        {
            'name': 'threshold',
            'type': 'float',
            'value': 14.55,
            'label': 'Quality threshold2',
            'help': 'If this is ... bla bla bla',
            'display': 'default'
        }
    ],
    {
        'name': 'threshold2',
        'type': 'string',
        'value': 'Explanation text',
        'label': 'Threshold ex',
        'help': 'If this is ... bla bla bla 2',
        'display': 'default'
    },
    {
        'name': 'text',
        'type': 'string',
        'value': 'Text example',
        'label': 'Text',
        'help': 'If this is ... bla bla bla for text'
    },
    {
        'name': 'threshold4',
        'type': 'float',
        'value': 1.5,
        'label': 'Quality',
        'help': 'If this is ... bla bla bla for quality'
    },
    {
      'name': 'picking-method',
      'type': 'enum',  # or 'int' or 'string' or 'enum',
      'choices': ['LoG', 'Swarm', 'SVM'],
      'value': 1,  # values in enum are int, in this case it is 'LoG'
      'label': 'Picking method',
      'help': 'Select the picking strategy that you want to use. ',
      # display should be optional, for most params, a textbox is the default
      # for enum, a combobox is the default, other options could be sliders
      'display': 'combo'  # or 'combo' or 'vlist' or 'hlist'
    },
    {
        'name': 'threshold3',
        'type': 'bool',
        'value': True,
        'label': 'Checked',
        'help': 'If this is a boolean param'
    }
]

if __name__ == '__main__':
    app = QApplication(sys.argv)
    paramCount = 0

    kwargs = {}


    class CmpView(QWidget):

        def __init__(self, parent, files, **kwargs):
            """
            Constructor
            :param parent: the parent widget
            :param files: the file list
            :param kwargs:
            """
            QWidget.__init__(self, parent)
            self._tvModel = None
            self._imageData = None
            self._processedImageData = None
            self._leftView = None
            self._rightView = None
            self._path = None
            self.__setupUi(**kwargs)
            self.__createColumsViewModel(files)
            self._columnsViewFiles.setSelectionBehavior(
                QAbstractItemView.SelectRows)
            self._columnsViewFiles.sigCurrentRowChanged.connect(
                self.__onCurrentRowChanged)

        def __setupUi(self, **kwargs):
            self.resize(1097, 741)
            self._mainLayout = QHBoxLayout(self)
            self._mainLayout.setContentsMargins(1, 1, 1, 1)
            self._mainSplitter = QSplitter(self)

            self._splitter = QSplitter(self)
            self._toolBar = ToolBar(self, orientation=Qt.Vertical)
            self._toolBar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            self._splitter.addWidget(self._toolBar)
            self._splitter.setCollapsible(0, False)
            self._splitter.addWidget(self._mainSplitter)

            self._filesPanel = self._toolBar.createSidePanel()
            self._filesPanel.setObjectName('filesPanel')
            self._filesPanel.setStyleSheet(
                'QWidget#filesPanel{border-left: 1px solid lightgray;}')
            self._filesPanel.setSizePolicy(QSizePolicy.Ignored,
                                           QSizePolicy.Ignored)

            vLayout = QVBoxLayout(self._filesPanel)
            vLayout.setContentsMargins(0, 0, 0, 0)
            self._columnsViewFiles = ColumnsView(self._filesPanel)
            vLayout.addWidget(self._columnsViewFiles)
            self._actFiles = QAction(None)
            self._actFiles.setIcon(qta.icon('fa5s.file'))
            self._actFiles.setText('Files')
            #  setting a reasonable width for display panel
            self._filesPanel.setGeometry(0, 0, vLayout.sizeHint().width(),
                                         self._filesPanel.height())
            self._toolBar.addAction(self._actFiles, self._filesPanel,
                                    exclusive=False, checked=True)

            self._paramsPanel = self._toolBar.createSidePanel()
            self._paramsPanel.setObjectName('paramsPanel')
            self._paramsPanel.setStyleSheet(
                'QWidget#paramsPanel{border-left: 1px solid lightgray;}')
            self._paramsPanel.setSizePolicy(QSizePolicy.Ignored,
                                            QSizePolicy.Ignored)
            dFactory = DynamicWidgetsFactory()
            self._dynamicWidget = dFactory.createWidget(tool_params1)
            vLayout = QVBoxLayout(self._paramsPanel)
            vLayout.setContentsMargins(0, 0, 0, 0)
            vLayout.addWidget(self._dynamicWidget)
            button = QPushButton(self)
            button.setText("Collect")
            button.clicked.connect(self.__collectParams)
            button.setStyleSheet("font-weight:bold;")
            vLayout.addWidget(button)
            self._paramsPanel.setFixedHeight(vLayout.totalSizeHint().height())
            self._paramsPanel.setMinimumWidth(vLayout.totalSizeHint().width())

            self._actParams = QAction(None)
            self._actParams.setIcon(qta.icon('fa5s.id-card'))
            self._actParams.setText('Params')
            self._toolBar.addAction(self._actParams, self._paramsPanel,
                                    exclusive=False, checked=True)

            self._mainLayout.addWidget(self._splitter)

        def __createViews(self, dim, **kwargs):
            """
            Creates the left and right views according
            to the given image dimensions
            """
            if dim.z == 1:
                # kwargs['tool_bar'] = 'off'
                self._leftView = ImageView(self, **kwargs)
                self._rightView = ImageView(self, **kwargs)
            else:
                kwargs['tool_bar'] = 'off'
                kwargs['imageManager'] = VolImageManager(self._imageData)
                self._leftView = VolumeView(self, **kwargs)
                kwargs['imageManager'] = \
                    VolImageManager(self._processedImageData)
                self._rightView = VolumeView(self, **kwargs)

            self._splitter.addWidget(self._leftView)
            self._splitter.addWidget(self._rightView)

        def __createColumsViewModel(self, files=None):
            """ Setup the em table """
            Column = em.Table.Column
            emTable = em.Table([Column(1, "File Name", em.typeString),
                                Column(2, "Path", em.typeString)])
            tableViewConfig = TableViewConfig()
            tableViewConfig.addColumnConfig(name='File Name',
                                            dataType=TableViewConfig.TYPE_STRING,
                                            label='File Name',
                                            editable=False,
                                            visible=True)
            tableViewConfig.addColumnConfig(name='Path',
                                            dataType=TableViewConfig.TYPE_STRING,
                                            label='Path',
                                            editable=False,
                                            visible=False)
            if isinstance(files, list):
                for file in files:
                    r = emTable.createRow()
                    tableColumn = emTable.getColumnByIndex(0)
                    r[tableColumn.getName()] = os.path.basename(file)
                    tableColumn = emTable.getColumnByIndex(1)
                    r[tableColumn.getName()] = file
                    emTable.addRow(r)

            self._tvModel = TableDataModel(emTable,
                                           tableViewConfig=tableViewConfig)
            self._columnsViewFiles.setModel(self._tvModel)

        @pyqtSlot()
        def __collectParams(self):
            """ Collect params """
            data = self._dynamicWidget.getParams()
            print(data)

        @pyqtSlot(int)
        def __onCurrentRowChanged(self, row):
            """ Invoked when current row change in micrographs list """
            path = self._tvModel.getTableData(row, 1)
            try:
                if self._leftView is None:
                    dim = ImageManager.getDim(path)
                    self.__createViews(dim, **kwargs)
                self._showPath(path)
            except RuntimeError as ex:
                self._showError(ex.message)

        def _showPath(self, path):
            """
            Show the given image
            :param path: the image path
            """
            if not self._path == path:
                try:
                    self._path = path
                    image = ImageManager.readImage(path)
                    self._imageData = ImageManager.getNumPyArray(image)
                    self._processedImageData = \
                        ImageManager.getNumPyArray(image, copy=True)
                    if isinstance(self._leftView, ImageView):
                        self._leftView.setImage(self._imageData)
                        ext = EmPath.getExt(path)
                        data_type = str(image.getType())
                        self._leftView.setImageInfo(path=path, format=ext,
                                                    data_type=data_type)
                        self._rightView.setImage(self._processedImageData)
                        self._rightView.setImageInfo(path=path, format=ext,
                                                     data_type=data_type)
                    elif isinstance(self._leftView, VolumeView):
                        imgManager = VolImageManager(self._imageData)
                        self._leftView.setup(path, imageManager=imgManager)
                        imgManager = VolImageManager(self._processedImageData)
                        self._rightView.setup(path, imageManager=imgManager)

                except RuntimeError as ex:
                    print(ex)
                    raise ex
                except Exception as ex:
                    print(ex)
                    raise ex

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

    class ValidateCmpList(argparse.Action):
        """
        Class that allows the validation of the values corresponding to
        the "cmp" parameter
        """
        def __init__(self, option_strings, dest, **kwargs):
            argparse.Action.__init__(self, option_strings, dest, **kwargs)

        def __call__(self, parser, namespace, values, option_string=None):
            """
            Validate the maximum number of values corresponding to the
            cmp parameter. Try to matching a path pattern for micrographs
            and another for coordinates.

            Return a list of paths.
            """
            result = list()
            if not values:
                raise ValueError("Invalid number of arguments for %s."
                                 % option_string)

            for pattern in values:
                mics = self.__ls(pattern)
                result.extend(mics)

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
                           required=False, choices=['RECT', 'CIRCLE', 'CENTER'
                                                    'SEGMENT'],
                           help=' the shape type '
                                '[CIRCLE, RECT, CENTER or SEGMENT]')
    argParser.add_argument('--picker-mode', default='default', required=False,
                           choices=['default', 'filament'],
                           help=' the picker type [default or filament]')
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

    argParser.add_argument('--cmp', type=str, nargs='*', default=[],
                           required=False, action=ValidateCmpList,
                           help='Show the Comparator tool. '
                                'You can specify a list of path patterns.')
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
    kwargs['selection_mode'] = AbstractView.MULTI_SELECTION

    # Picker params
    kwargs['boxsize'] = args.boxsize
    kwargs['picker_mode'] = DEFAULT_MODE \
        if args.picker_mode == 'default' else FILAMENT_MODE
    if kwargs['picker_mode'] == DEFAULT_MODE:
        if args.shape == 'RECT':
            kwargs['shape'] = SHAPE_RECT
        elif args.shape == 'CIRCLE':
            kwargs['shape'] = SHAPE_CIRCLE
        else:
            kwargs['shape'] = SHAPE_CENTER
    else:
        kwargs['shape'] = \
            SHAPE_CENTER if args.shape == 'CENTER' else SHAPE_SEGMENT
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
                isinstance(viewWidget, SlicesView) or
                isinstance(viewWidget, PickerView)) and \
                imageDim is not None:
            if isinstance(viewWidget, SlicesView):
                toolWith = 0
            else:
                toolBar = viewWidget.getToolBar()
                toolWith = toolBar.getSidePanelMinimumWidth() + toolBar.width()

            x, y, w, h = getPreferedBounds(max(viewWidget.width(), imageDim.x),
                                           max(viewWidget.height(),
                                               imageDim.y))
            size = QSize(imageDim.x, imageDim.y).scaled(w, h,
                                                        Qt.KeepAspectRatio)
            dw, dh = w - size.width(), h - size.height()
            x, y, w, h = x + dw/2 - toolWith, y + dh/2, \
                         size.width() + 2 * toolWith, size.height()
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
            kwargs["selection_mode"] = AbstractView.SINGLE_SELECTION
            view = PickerView(None, createPickerModel(files, args.boxsize),
                              sources=args.picker, **kwargs)
            view.setWindowTitle("EM-PICKER")
            d = view.getImageDim()
        elif args.cmp == 'on' or isinstance(args.cmp, list):
            view = CmpView(None,
                           args.cmp if isinstance(args.cmp, list) else files)
            view.setWindowTitle('EM-COMPARATOR')

        else:
            # If the input is a directory, display the BrowserWindow
            if len(files) > 1:
                raise Exception("Multiple files are not supported")
            else:
                files = files[0]

            if not os.path.exists(files):
                raise Exception("Input file '%s' does not exists. " % files)

            if os.path.isdir(files):
                kwargs["selection_mode"] = AbstractView.SINGLE_SELECTION
                view = BrowserWindow(None, files, **kwargs)
            elif EmPath.isTable(files):  # Display the file as a Table:
                if not args.view == 'slices':
                    t = EmTable.load(files)  # name, table
                    if args.visible or args.render:
                        tableViewConfig = \
                            TableViewConfig.fromTable(t[1], args.visible)
                        renderCount = 0
                        for colConfig in tableViewConfig:
                            colName = colConfig.getName()
                            if args.visible:
                                colConfig['visible'] = colName in args.visible
                            if args.render:
                                ren = colName in args.render
                                colConfig['renderable'] = ren
                                renderCount += 1 if ren else 0
                        if not renderCount == len(args.render):
                            raise Exception('Invalid renderable column')
                    else:
                        tableViewConfig = None
                    if args.sort:
                        colName = t[1].getColumn(args.sort[0]).getName()
                        order = " " + args.sort[1] if len(args.sort) > 1 else ""
                        t[1].sort([colName + order])
                    view = createDataView(t[1], tableViewConfig, t[0],
                                          views.get(args.view,
                                                    DataView.COLUMNS),
                                          dataSource=files,
                                          **kwargs)
                    fitViewSize(view, d)
                else:
                    raise Exception("Invalid display mode for table: '%s'"
                                    % args.view)
            elif EmPath.isImage(files) or EmPath.isVolume(files) \
                    or EmPath.isStack(files):
                # *.mrc may be image, stack or volume. Ask for dim.n
                d = ImageManager.getDim(files)
                if d.n == 1:  # Single image or volume
                    if d.z == 1:  # Single image
                        view = createImageView(files, **kwargs)
                    else:  # Volume
                        mode = args.view or 'slices'
                        if mode == 'slices' or mode == 'gallery':
                            kwargs['view'] = views[mode]
                            kwargs['tool_bar'] = 'off'
                            kwargs['axis'] = 'off'
                            kwargs["selection_mode"] = \
                                AbstractView.SINGLE_SELECTION
                            view = createVolumeView(files, **kwargs)
                        else:
                            raise Exception("Invalid display mode for volume: "
                                            "'%s'" % mode)
                else:  # Stack
                    kwargs["selection_mode"] = AbstractView.SINGLE_SELECTION
                    if d.z > 1:  # volume stack
                        mode = args.view or 'slices'
                        if mode == 'slices':
                            kwargs['tool_bar'] = 'off'
                            kwargs['axis'] = 'off'
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
