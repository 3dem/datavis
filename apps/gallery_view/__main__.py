#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from PyQt5.QtWidgets import QApplication
from emqt5.widgets.image.gallery_view import GalleryView
import argparse

if __name__ == '__main__':

    app = QApplication(sys.argv)

    kwargs = {}

    argParser = argparse.ArgumentParser(usage='Tool for Gallery View',
                                        description='Display all the slices in '
                                                    'the given plane ')
    argParser.add_argument('imagePath', type=str, default='',
                           help=' Path of the 3D image')
    argParser.add_argument('--iconWidth', type=int, default=150,
                           required=False,
                           help=' an integer for image width')
    argParser.add_argument('--iconHeight', type=int, default=150,
                           required=False,
                           help=' an integer for image height')

    args = argParser.parse_args()

    kwargs['imagePath'] = args.imagePath
    kwargs['--iconWidth'] = args.iconWidth
    kwargs['--iconHeight'] = args.iconHeight

    galleryView = GalleryView(**kwargs)
    galleryView.show()
    sys.exit(app.exec_())