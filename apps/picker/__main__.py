#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from PyQt5.QtWidgets import QApplication
from picker_window import PPWindow
from model import PPSystem


if __name__ == '__main__':
    app = QApplication(sys.argv)

    kwargs = {}
    if len(sys.argv) > 1:
        ppArg = sys.argv[1:]

        pFiles = []
        options = ['--disable-zoom',
                   '--disable-histogram',
                   '--disable-roi',
                   '--disable-menu',
                   '--pick-files'
                   ]

        kwargs['--disable-zoom'] = False
        kwargs['--disable-histogram'] = False
        kwargs['--disable-roi'] = True
        kwargs['--disable-menu'] = True

        for a in ppArg:
            if a not in options:
                pFiles.append(a)
        kwargs['--pick-files'] = pFiles

    pickerWin = PPWindow(**kwargs)
    pickerWin.show()
    sys.exit(app.exec_())
