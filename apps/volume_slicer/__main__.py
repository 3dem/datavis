#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from PyQt5.QtWidgets import QApplication
from emqt5.widgets.image.volume_slicer import VolumeSlice

if __name__ == '__main__':

    kwargs = {}
    paramCount = 0

    if len(sys.argv) < 2:
        raise Exception("Specify input volume path.")

        # for argv in sys.argv:
        #     kwargs[sys.argv[paramCount]] = True
        #     paramCount += 1

    fn = sys.argv[1]
    app = QApplication(sys.argv)
    volumeSlice = VolumeSlice(fn, **kwargs)
    volumeSlice.show()
    sys.exit(app.exec_())

