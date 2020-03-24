#!/usr/bin/python
# -*- coding: utf-8 -*-

import datavis as dv


class TestImageListView(dv.tests.TestView):
    __title = "ImageListView example"

    def __init__(self, methodName='runTest'):
        dv.tests.TestView.__init__(self, methodName=methodName)

    def getDataPaths(self):
        return ['']

    def createView(self):
        model = dv.tests.createListImageModel(
            ['image %d' % i for i in range(10)], 'Image', (512, 512))
        return dv.views.ImageListView(model)

    def test_ImageListView(self):
        print('test_ImageListView')


if __name__ == '__main__':
    TestImageListView().runApp()
