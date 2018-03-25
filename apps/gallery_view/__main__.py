#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from PyQt5.QtWidgets import QApplication
from emqt5.widgets.image.gallery_view import GalleryView

if __name__ == '__main__':
    app = QApplication(sys.argv)
    kwargs = {}
    paramCount = 0
    if len(sys.argv) > 1:
        for argv in sys.argv:
            kwargs[sys.argv[paramCount]] = True
            paramCount += 1

    kwargs['iconWidth'] = 150
    kwargs['iconHeight'] = 150

    galleryView = GalleryView('/home/yunior/ScipionUserData/image-single.mrc',
                              **kwargs)
    galleryView.show()
    sys.exit(app.exec_())