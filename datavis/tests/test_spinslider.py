#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys

import PyQt5.QtCore as qtc
import PyQt5.QtWidgets as qtw

import datavis as dv


# Connect to the valueChanged signal and print value
@qtc.pyqtSlot(int)
def onValueChanged(value):
    print("value: %s" % value)


app = qtw.QApplication(sys.argv)

win = qtw.QMainWindow()
win.resize(400, 200)

# Create a SpinSlider
spinSlider = dv.widgets.SpinSlider(win, text='Testing SpinSlider',
                                   minValue=1, maxValue=100)

spinSlider.sigValueChanged.connect(onValueChanged)

win.setCentralWidget(spinSlider)
win.show()
win.setWindowTitle('SpinSlider Example')

sys.exit(app.exec_())
