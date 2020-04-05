#!/usr/bin/python
# -*- coding: utf-8 -*-

import datavis as dv


class TestGalleryView(dv.tests.TestView):
    __title = "GalleryView example"

    def __init__(self, methodName='runTest'):
        dv.tests.TestView.__init__(self, methodName=methodName)

    def getDataPaths(self):
        return [""]

    def createView(self):
        model = dv.tests.createTableModel((60, 60))
        return dv.views.GalleryView(model=model)

    def test_GalleryView(self):
        print('test_GalleryView')


if __name__ == '__main__':
    TestGalleryView().runApp()
