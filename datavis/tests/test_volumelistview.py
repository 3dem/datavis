#!/usr/bin/python
# -*- coding: utf-8 -*-

import datavis as dv


class TestVolumeListView(dv.tests.TestView):
    __title = "VolumeListView example"

    def getDataPaths(self):
        return ['']

    def createView(self):
        model = dv.tests.createListImageModel(
            ['volume %d' % i for i in range(8)], 'Volume', (64, 64, 64))
        return dv.views.VolumeListView(model)


if __name__ == '__main__':
    TestVolumeListView().runApp()
