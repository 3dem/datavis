#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys

import PyQt5.QtCore as qtc
import PyQt5.QtWidgets as qtw

import datavis as dv


def onValueChanged(value):
    print("value: %s" % value)


app = qtw.QApplication(sys.argv)

win = qtw.QMainWindow()
win.resize(400, 200)

frame = qtw.QWidget()
layout = qtw.QVBoxLayout(frame)

# Create a SpinSlider
spinSlider = dv.widgets.SpinSlider(win, text='Testing SpinSlider',
                                   minValue=1, maxValue=100)
spinSlider.sigValueChanged.connect(onValueChanged)
layout.addWidget(spinSlider)


# Create a SpinSlider
spinSliderFloat = dv.widgets.SpinSlider(win, text='Float SpinSlider',
                                        minValue=0, maxValue=1.0,
                                        currentValue=0.5, step=0.01)
spinSliderFloat.sigValueChanged.connect(onValueChanged)
layout.addWidget(spinSliderFloat)

win.setCentralWidget(frame)
win.show()
win.setWindowTitle('SpinSlider Example')

sys.exit(app.exec_())
