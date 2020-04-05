#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys

import PyQt5.QtCore as qtc
import PyQt5.QtWidgets as qtw

import datavis as dv


class TestSpinSlider(dv.tests.TestView):
    __title = "SpinSlider example"

    def __init__(self, methodName='runTest'):
        dv.tests.TestView.__init__(self, methodName=methodName)

    def createView(self):
        frame = qtw.QWidget()
        layout = qtw.QVBoxLayout(frame)

        # Create a SpinSlider
        spinSlider = dv.widgets.SpinSlider(frame, text='Testing SpinSlider',
                                           minValue=1, maxValue=100)
        spinSlider.sigValueChanged.connect(self.onValueChanged)
        layout.addWidget(spinSlider)

        # Create a SpinSlider
        spinSliderFloat = dv.widgets.SpinSlider(frame, text='Float SpinSlider',
                                                minValue=0, maxValue=1.0,
                                                currentValue=0.5, step=0.01)
        spinSliderFloat.sigValueChanged.connect(self.onValueChanged)
        layout.addWidget(spinSliderFloat)
        return frame

    def onValueChanged(self, value):
        print("value: %s" % value)

    def test_SpinSlider(self):
        print('test_SpinSlider')


if __name__ == '__main__':
    TestSpinSlider().runApp()
