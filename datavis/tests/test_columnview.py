#!/usr/bin/python
# -*- coding: utf-8 -*-

import datavis as dv


class TestColumnsView(dv.tests.TestView):
    __title = "ColumnsView example"

    def getDataPaths(self):
        return ['']

    def createView(self):
        model = dv.tests.createTableModel((60, 60))
        return dv.views.ColumnsView(model=model)


if __name__ == '__main__':
    TestColumnsView().runApp()
