#!/usr/bin/python
# -*- coding: utf-8 -*-

import numpy as np
import pyqtgraph as pg

import datavis as dv


class TestSlicesView(dv.tests.TestView):
    __title = "Slices View example"

    def getDataPaths(self):
        return ['']

    def createView(self):
        return dv.views.SlicesView(None,
                                   model=SimpleSlicesModel((512, 512), 50),
                                   text='Slice, image number: ',
                                   currentValue=1)


class SimpleSlicesModel(dv.models.SlicesModel):
    """ Example class implementing a simple slices model """

    def __init__(self, imgSize, size):
        """
        Creates an StackModel.
        :param imgSize: (tupple) The image size
        :param size: (int) The number of images
        """
        dv.models.SlicesModel.__init__(self)
        self._imgData = []
        self._dim = imgSize[0], imgSize[1], size
        self._imgData = [
            pg.gaussianFilter(np.random.normal(size=imgSize),
                              (5, 5)) for i in range(size)]

    def getData(self, i=-1):
        return None if i == -1 else self._imgData[i]


if __name__ == '__main__':
    TestSlicesView().runApp()
