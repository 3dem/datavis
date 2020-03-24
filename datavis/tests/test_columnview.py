#!/usr/bin/python
# -*- coding: utf-8 -*-

import datavis as dv


class TestColumnsView(dv.tests.TestView):
    __title = "ColumnsView example"

    def __init__(self, methodName='runTest'):
        dv.tests.TestView.__init__(self, methodName=methodName)

    def getDataPaths(self):
        return ['']

    def createView(self):
        model = dv.tests.createTableModel((60, 60))
        return dv.views.ColumnsView(model=model)

    def test_ColumnsView(self):
        print('test_ColumnsView')


if __name__ == '__main__':
    TestColumnsView().runApp()
