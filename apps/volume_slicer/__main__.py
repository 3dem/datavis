#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from PyQt5.QtWidgets import QApplication
from volume_slicer import VolumeSlice


if __name__ == '__main__':
    app = QApplication(sys.argv)
    kwargs = {}
    paramCount = 0
    if len(sys.argv) > 1:
        for argv in sys.argv:
            kwargs[sys.argv[paramCount]] = True
            paramCount += 1

    volumeSlice = VolumeSlice('em-image Path', **kwargs)
    volumeSlice.show()
    sys.exit(app.exec_())
