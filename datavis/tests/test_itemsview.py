#!/usr/bin/python
# -*- coding: utf-8 -*-

import datavis as dv


class TestItemsView(dv.tests.TestView):
    __title = "ItemsView Example"

    def getDataPaths(self):
        return [""]

    def createView(self):
        model = dv.tests.createTableModel((60, 60))
        view = dv.views.ItemsView(model=model)
        return view


if __name__ == '__main__':
    TestItemsView().runApp()
