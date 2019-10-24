#!/usr/bin/python
# -*- coding: utf-8 -*-

import numpy as np
import pyqtgraph as pg

import datavis as dv


class TestImageListView(dv.tests.TestView):
    __title = "ImageListView example"

    def getDataPaths(self):
        return ['']

    def createView(self):
        model = dv.tests.createListImageModel(
            ['image %d' % i for i in range(10)], 'Image', (512, 512))
        return dv.views.ImageListView(model)


if __name__ == '__main__':
    TestImageListView().runApp()
