#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from PyQt5.QtWidgets import QApplication
from picker_window import PickerWindow
from model import PickerDataModel


if __name__ == '__main__':
    app = QApplication(sys.argv)

    kwargs = {}
    if len(sys.argv) < 1:
        raise Exception("You should provide at least one input micrograph to pick")

    kwargs = {
        '--disable-zoom': False,
        '--disable-histogram': False,
        '--disable-roi': False,
        '--disable-menu': False,
        '--pick-files': False,
        '--disable-remove-rois': False,
        '--disable-roi-aspect-locked': False,
        '--disable-roi-centered': False,
        '--disable-x-axis': False,
        '--disable-y-axis': False
    }

    model = PickerDataModel()

    for a in sys.argv[1:]:
        if a in kwargs:
            kwargs[a] = True
        elif not a.startswith('--'):
            model.addMicrograph(a)

    model.setBoxSize(int(kwargs.get('--boxsize', 100)))

    pickerWin = PickerWindow(model, **kwargs)
    pickerWin.show()
    sys.exit(app.exec_())
