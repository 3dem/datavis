#!/usr/bin/python
# -*- coding: utf-8 -*-

import numpy as np
import pyqtgraph as pg

import datavis as dv


class TestVolumeView(dv.tests.TestView):
    __title = "Volume View example"

    def getDataPaths(self):
        return ['']

    def createView(self):
        data = pg.gaussianFilter(np.random.normal(size=(64, 64, 64)), (5, 5, 5))
        return dv.views.VolumeView(dv.models.VolumeModel(data), toolBar=True,
                                   slicesMode=dv.models.AXIS_XYZ)


if __name__ == '__main__':
    TestVolumeView().runApp()

