#!/usr/bin/python
# -*- coding: utf-8 -*-

import datavis as dv


class TestVolumeListView(dv.tests.TestView):
    __title = "VolumeListView example"

    def __init__(self, methodName='runTest'):
        dv.tests.TestView.__init__(self, methodName=methodName)

    def getDataPaths(self):
        return ['']

    def createView(self):
        model = dv.tests.createListImageModel(
            ['volume %d' % i for i in range(8)], 'Volume', (64, 64, 64))
        return dv.views.VolumeListView(model)

    def test_VolumeListView(self):
        print('test_VolumeListView')


if __name__ == '__main__':
    TestVolumeListView().runApp()
