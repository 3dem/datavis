#!/usr/bin/python
# -*- coding: utf-8 -*-

import numpy as np
import pyqtgraph as pg

import datavis as dv


class TestVolumeView(dv.tests.TestView):
    __title = "Volume View example"

    def __init__(self, methodName='runTest'):
        dv.tests.TestView.__init__(self, methodName=methodName)

    def getDataPaths(self):
        return ['']

    def createView(self):
        z, y, x = 300, 200, 100
        data = np.random.normal(size=(z, y, x))
        data = pg.gaussianFilter(data, (5, 5, 5))

        return dv.views.VolumeView(dv.models.VolumeModel(data), toolBar=True,
                                   slicesMode=dv.models.AXIS_XYZ)

    def test_VolumeView(self):
        print('test_VolumeView')


if __name__ == '__main__':
    TestVolumeView().runApp()

