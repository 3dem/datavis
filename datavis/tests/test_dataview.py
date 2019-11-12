#!/usr/bin/python
# -*- coding: utf-8 -*-

import datavis as dv


class TestDataView(dv.tests.TestView):
    __title = "DataView example"

    def getDataPaths(self):
        return ['']

    def createView(self):
        model = dv.tests.createTableModel((60, 60))
        return dv.views.DataView(model)


if __name__ == '__main__':
    TestDataView().runApp()

