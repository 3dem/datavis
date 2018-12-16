#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from PyQt5.QtWidgets import QApplication
from emqt5.views.picker_view import PickerWindow
from emqt5.views.picker_model import PickerDataModel
import argparse


if __name__ == '__main__':


    kwargs = {}

    argParser = argparse.ArgumentParser(usage='Tool for particle picking',
                                        description='Organize micrograph images'
                                                    ' in a tree for particle '
                                                    'picking operations',
                                        prefix_chars='--')
    argParser.add_argument('files', type=str, nargs='+',
                           help=' list of micrographs files')

    argParser.add_argument('--boxsize', type=int, default=100,
                           required=False,
                           help=' an integer for pick size')
    argParser.add_argument('--shape', default='RECT',
                           required=False, choices=['RECT', 'CIRCLE'],
                           help=' the shape type [CIRCLE or RECT]')
    argParser.add_argument('--disable-remove-rois', default=False,
                           required=False, action='store_true',
                           help=' the user will not be able to eliminate rois')
    argParser.add_argument('--disable-roi-aspect-locked', default=False,
                           required=False, action='store_true',
                           help=' the rois will retain the aspect ratio')
    argParser.add_argument('--disable-roi-centered', default=False,
                           required=False, action='store_true',
                           help=' the rois will work accordance with its '
                                'center')

    args = argParser.parse_args()

    model = PickerDataModel()

    for file in args.files:
        model.addMicrograph(file)

    model.setBoxSize(args.boxsize)

    kwargs['--disable-histogram'] = args.disable_histogram
    kwargs['--disable-zoom'] = args.disable_zoom
    kwargs['--disable-roi'] = args.disable_roi
    kwargs['--disable-menu'] = args.disable_menu
    kwargs['--disable-remove-rois'] = args.disable_remove_rois
    kwargs['--disable-roi-aspect-locked'] = args.disable_roi_aspect_locked
    kwargs['--disable-zoom'] = args.disable_zoom
    kwargs['--disable-roi-centered'] = args.disable_roi_centered
    kwargs['--disable-x-axis'] = args.disable_x_axis
    kwargs['--disable-y-axis'] = args.disable_y_axis
    kwargs['--shape'] = 0 if args.shape == 'RECT' else 1

    app = QApplication(sys.argv)
    pickerWin = PickerWindow(model, **kwargs)
    pickerWin.show()
    sys.exit(app.exec_())
