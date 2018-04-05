#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
from PyQt5.QtWidgets import QApplication, QFileSystemModel, QDialog, QLabel
from PyQt5.QtCore import QDir
import em
from emqt5.widgets.image.browser_window import BrowserWindow
from emqt5.widgets.image.volume_slicer import VolumeSlice
from emqt5.widgets.image.gallery_view import GalleryView

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
    argParser.add_argument('--path', type=str, default=None, required=False,
                           help='3D image path or a specific directory')
    argParser.add_argument('--slices', type=str, default=['GALLERY', 'AXIS'],
                           nargs='+', required=False, choices=['GALLERY', 'AXIS'],
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
    kwargs['--path'] = args.path
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

    errorDialog = QDialog()
    errorDialog.setModal(True)
    errorLabel = QLabel(errorDialog)

    if not args.path:  # Display the EM-BROWSER component

        kwargs['--path'] = QDir.currentPath()
        browserWin = BrowserWindow(**kwargs)
        browserWin.show()
    else: # We parse the path

        isDir = QDir(args.path)

        if isDir:  # The path constitute an directory. In this case we display
                   # the EM-BROWSER component
            kwargs['--path'] = args.path
            browserWin = BrowserWindow(**kwargs)
            browserWin.show()

        else:  # The path constitute a file. In this case we parse this file

            directory = QDir(args.path)
            isExistFile = directory.exists(args.path)

            if isExistFile:  # The file exist

                def isEmImage(imagePath):
                    """ Return True if imagePath has an extension recognized as
                        supported EM-image """
                    _, ext = os.path.splitext(imagePath)
                    return ext in ['.mrc', '.mrcs', '.spi', '.stk', '.map',
                                   '.vol']

                if isEmImage(args.path):  # The file constitute an em-image.
                                          # In this case we determined if the
                                          # image has a volume or not

                    # Create an image from imagePath using em-bindings
                    image = em.Image()
                    loc2 = em.ImageLocation(args.path)
                    image.read(loc2)

                    # Determinate the image dimension
                    z = image.getDim().z

                    if z == 1: # Display the EM-BROWSER component
                        kwargs['--path'] = args.path
                        browserWin = BrowserWindow(**kwargs)
                        browserWin.show()

                    else:  # The image has a Volume
                        if len(args.slices) == 1:
                            if args.slices[0] == 'AXIS':  # Display the Volume Slicer app
                                kwargs['imagePath'] = args.path
                                volumeSlice = VolumeSlice(**kwargs)
                                volumeSlice.show()
                            elif args.slices[0] == 'GALLERY':
                                    kwargs['imagePath'] = args.path
                                    galleryView = GalleryView(**kwargs)
                                    galleryView.show()
                            else:
                                errorDialog.setGeometry(450, 200, 340, 100)
                                errorLabel.setText(
                                    '   ERROR: A way to display the image are '
                                    'required')
                                errorDialog.show()
                        else:
                            errorDialog.setGeometry(450, 200, 340, 100)
                            errorLabel.setText(
                                '   ERROR: A way to display the image are '
                                'required')
                            errorDialog.show()
                else: # Display the EM-BROWSER component
                    kwargs['--path'] = args.path
                    browserWin = BrowserWindow(**kwargs)
                    browserWin.show()

            else:  # The file don't exist
                errorDialog.setGeometry(450, 200, 240, 100)
                errorLabel.setText(
                    '   ERROR: A file do not exist.')
                errorDialog.show()

    sys.exit(app.exec_())
