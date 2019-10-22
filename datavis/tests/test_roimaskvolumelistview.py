#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys

import datavis as dv


class TestRoiMaskVolumeListView(dv.tests.TestView):
    __title = "RoiMaskVolumeListView example"

    def __init__(self, singleAxis):
        self._mode = dv.models.AXIS_Z if singleAxis else dv.models.AXIS_XYZ

    def getDataPaths(self):
        return ['']

    def createView(self):
        maskParams = {
            'type': dv.views.CIRCLE_ROI,
            'color': '#154BBC23',
            'data': 20,
            'operation': None,
            'showHandles': True
        }
        slicesKwargs = {
            dv.models.AXIS_X: {
                'imageViewKwargs': {'maskParams': maskParams}},
            dv.models.AXIS_Y: {
                'imageViewKwargs': {'maskParams': maskParams}},
            dv.models.AXIS_Z: {
                'imageViewKwargs': {'maskParams': maskParams}}
        }
        model = dv.tests.createListImageModel(
            ['volume %d' % i for i in range(8)], 'Volume', (64, 64, 64))
        return dv.views.VolumeListView(model,
                                       slicesKwargs=slicesKwargs,
                                       slicesMode=self._mode)


if __name__ == '__main__':
    if 'single' in sys.argv:
        singleAxis = True
    else:
        print("TIP: Use 'single' argument to show a single axis. ")
        singleAxis = False

    TestRoiMaskVolumeListView(singleAxis).runApp()
