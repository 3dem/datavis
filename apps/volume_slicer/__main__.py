#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from PyQt5.QtWidgets import QApplication
from emqt5.widgets.image.volume_slicer import VolumeSlice
import argparse

if __name__ == '__main__':
    app = QApplication(sys.argv)

    kwargs = {}

    argParser = argparse.ArgumentParser(usage='Tool for Volume Slicer',
                                        description='Display the slices in the'
                                                    'given plane ')
    argParser.add_argument('imagePath', type=str, default='',
                           help='Path of the 3D image')
    argParser.add_argument('--enable-slicesLines', default=False,
                           required=False, action='store_true',
                           help=' hide the slices lines')
    argParser.add_argument('--enable-axis', default=False,
                           required=False, action='store_true',
                           help='hide the axis')

    args = argParser.parse_args()

    kwargs['imagePath'] = args.imagePath
    kwargs['--enable-slicesLines'] = args.enable_slicesLines
    kwargs['--enable-axis'] = args.enable_axis

    volumeSlice = VolumeSlice(**kwargs)
    volumeSlice.show()
    sys.exit(app.exec_())

