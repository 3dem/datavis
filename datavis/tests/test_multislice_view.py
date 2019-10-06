#!/usr/bin/python
# -*- coding: utf-8 -*-

import numpy as np
import pyqtgraph as pg

import datavis as dv


class TestMultiSliceView(dv.tests.TestView):
    __title = "MultiSliceView example"

    def getDataPaths(self):
        return ['']

    def createView(self):
        data = pg.gaussianFilter(np.random.normal(size=(64, 64, 64)), (5, 5, 5))
        volModel = dv.models.VolumeModel(data)
        msv = dv.views.MultiSliceView(
            None, {axis: {'model': volModel.getSlicesModel(axis),
                          'normalize': True}
                   for axis in [dv.models.AXIS_X, dv.models.AXIS_Y,
                                dv.models.AXIS_Z]})
        return msv


if __name__ == '__main__':
    TestMultiSliceView().runApp()

