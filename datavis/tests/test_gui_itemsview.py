#!/usr/bin/python
# -*- coding: utf-8 -*-

import datavis as dv


class TestItemsView(dv.tests.TestView):
    __title = "ItemsView Example"

    def __init__(self, methodName='runTest'):
        dv.tests.TestView.__init__(self, methodName=methodName)

    def getDataPaths(self):
        return [""]

    def createView(self):
        model = dv.tests.createTableModel((60, 60))
        view = dv.views.ItemsView(model=model)
        return view

    def test_ItemsView(self):
        print('test_ItemsView')


if __name__ == '__main__':
    TestItemsView().runApp()
