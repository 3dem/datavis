#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
from PyQt5.QtWidgets import QApplication
from table_view_window import TableViewWindow
import argparse


if __name__ == '__main__':

    kwargs = {}

    argParser = argparse.ArgumentParser(usage='TableView example',
                                        description='Show the table view '
                                                    'example',
                                        prefix_chars='--')
    argParser.add_argument('files', type=str, nargs='+',
                           help=' list of image files')

    args = argParser.parse_args()

    data = []
    i = 1
    for path in args.files:
        _, ext = os.path.splitext(path)
        data.append({"name": os.path.basename(path),
                     "image": path,
                     "ext": ext})

    kwargs['tableData'] = data

    app = QApplication(sys.argv)
    tableWin = TableViewWindow(model=None, **kwargs)
    tableWin.show()
    sys.exit(app.exec_())
