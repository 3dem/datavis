#!/usr/bin/python
# -*- coding: utf-8 -*-

import numpy as np

import datavis as dv


class TestImageMaskVolumeListView(dv.tests.TestView):
    __title = "ImageMaskVolumeListView example"

    def __init__(self, methodName='runTest'):
        dv.tests.TestView.__init__(self, methodName=methodName)

    def getDataPaths(self):
        return ['']

    def createView(self):
        # creating the image mask
        mask = np.zeros(shape=(64, 64), dtype=np.int8)
        for i in range(20, 44):
            for j in range(20, 44):
                mask[i][j] = 1

        maskParams = {
            'type': dv.views.DATA,
            'color': '#334BBC23',
            'data': mask,
        }
        slicesKwargs = {
            dv.models.AXIS_X: {
                'imageViewKwargs': {'maskParams': maskParams}},
            dv.models.AXIS_Y: {
                'imageViewKwargs': {'maskParams': maskParams}},
            dv.models.AXIS_Z: {'imageViewKwargs': {'maskParams': maskParams}
                               }
        }
        model = dv.tests.createListImageModel(
            ['volume %d' % i for i in range(8)], 'Volume', (64, 64, 64))
        return dv.views.VolumeListView(model,
                                       slicesKwargs=slicesKwargs,
                                       slicesMode=dv.models.AXIS_XYZ)

    def test_ImageMaskVolumeListView(self):
        print('test_ImageMaskVolumeListView')


if __name__ == '__main__':
    TestImageMaskVolumeListView().runApp()
