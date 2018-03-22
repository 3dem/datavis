#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from PyQt5.QtWidgets import QApplication
from gallery_view import GalleryView

if __name__ == '__main__':
    app = QApplication(sys.argv)
    kwargs = {}
    paramCount = 0
    if len(sys.argv) > 1:
        for argv in sys.argv:
            kwargs[sys.argv[paramCount]] = True
            paramCount += 1

    galleryView = GalleryView('em-image Path', **kwargs)
    galleryView.show()
    sys.exit(app.exec_())
