#!/usr/bin/python
# -*- coding: utf-8 -*-

import datavis as dv


class TestRoiMaskListView(dv.tests.TestView):
    __title = "RoiMaskListView example"

    def __init__(self, methodName='runTest'):
        dv.tests.TestView.__init__(self, methodName=methodName)

    def getDataPaths(self):
        return ['']

    def createView(self):
        maskParams = {
            'type': dv.views.CIRCLE_ROI,
            'color': '#154BBC23',
            'data': 500,
            'showHandles': True
        }
        model = dv.tests.createListImageModel(
            ['image %d' % i for i in range(10)], 'Image', (1024, 1024))
        return dv.views.ImageMaskListView(model, maskParams=maskParams)

    def test_RoiMaskListView(self):
        print('test_RoiMaskListView')


if __name__ == '__main__':
    TestRoiMaskListView().runApp()
