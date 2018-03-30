#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from PyQt5.QtWidgets import QApplication
from browser_window import BrowserWindow

if __name__ == '__main__':
    app = QApplication(sys.argv)
    kwargs = {}
    paramCount = 0

    if len(sys.argv) < 2:
        raise Exception("Specify input volume path.")

    browserWin = BrowserWindow(**kwargs)
    browserWin.show()
    sys.exit(app.exec_())
