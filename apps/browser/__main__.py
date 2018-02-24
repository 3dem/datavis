#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from PyQt5.QtWidgets import QApplication
from browser_actions import MainWindow

if __name__ == '__main__':
    app = QApplication(sys.argv)
    kwargs = {}
    if len(sys.argv) > 1:
        kwargs['imageFile'] = sys.argv[1]

    mWindow = MainWindow(**kwargs)
    mWindow.show()
    sys.exit(app.exec_())
