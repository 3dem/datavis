#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from PyQt5.QtWidgets import QApplication
from picker_window import PPWindow
from model import PPSystem


if __name__ == '__main__':
    app = QApplication(sys.argv)

    if len(sys.argv) > 1:
        files = sys.argv[1:]
        pps = PPSystem()
        for f in files:
            pps.addMicrograph(f)
    else:
        pps = None
    pickerWin = PPWindow(system=pps)
    pickerWin.show()
    sys.exit(app.exec_())
