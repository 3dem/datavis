#!/usr/bin/python
# -*- coding: utf-8 -*-

import numpy as np

import datavis as dv


class TestImageMaskListView(dv.tests.TestView):
    __title = "ImageMaskListView example"

    def getDataPaths(self):
        return ['']

    def createView(self):
        # creating the image mask
        mask = np.zeros(shape=(1024, 1024), dtype=np.int8)
        for i in range(300, 600):
            for j in range(300, 600):
                mask[i][j] = 1

        maskParams = {
            'type': dv.views.DATA,
            'color': '#334BBC23',
            'data': mask
        }
        model = dv.tests.createListImageModel(
            ['image %d' % i for i in range(10)], 'Image', (1024, 1024))
        return dv.views.ImageMaskListView(model, maskParams=maskParams)


if __name__ == '__main__':
    TestImageMaskListView().runApp()
