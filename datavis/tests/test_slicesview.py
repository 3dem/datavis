#!/usr/bin/python
# -*- coding: utf-8 -*-

import datavis as dv


class TestSlicesView(dv.tests.TestView):
    __title = "Slices View example"

    def __init__(self, methodName='runTest'):
        dv.tests.TestView.__init__(self, methodName=methodName)

    def getDataPaths(self):
        return ['']

    def createView(self):
        model = dv.tests.createSlicesModel((512, 512), 50)
        return dv.views.SlicesView(model=model, text='Slice, image number: ',
                                   currentValue=1)

    def test_SlicesView(self):
        print('test_SlicesView')


if __name__ == '__main__':
    TestSlicesView().runApp()
