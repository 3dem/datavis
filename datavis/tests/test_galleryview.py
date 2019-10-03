#!/usr/bin/python
# -*- coding: utf-8 -*-

import numpy as np
import pyqtgraph as pg

import datavis as dv


class TestGalleryView(dv.tests.TestView):
    __title = "GalleryView example"

    def getDataPaths(self):
        return [""]

    def createView(self):
        return dv.views.GalleryView(model=StackModel((60, 60), 100))


class StackModel(dv.models.SimpleTableModel):
    """ Example class implementing a simple stack model """
    def __init__(self, imgSize, size):
        """
        Creates an StackModel.
        :param imgSize: (tupple) The image size
        :param size: (int) The number of images
        """
        dv.models.SimpleTableModel.__init__(
            self, [dv.models.ColumnInfo('index', dv.models.TYPE_STRING)])
        for i in range(size):
            self.addRow([pg.gaussianFilter(np.random.normal(size=imgSize),
                                           (5, 5)) * 20 + 100])

    def getData(self, row, col):
        return self.getValue(row, col)
    
    def createDefaultConfig(self):
        c = self._columnsInfo[0]
        cols = [dv.models.ColumnConfig(c.getName(), c.getType(),
                                       renderable=True)]
        return dv.models.TableConfig(*cols)


if __name__ == '__main__':
    TestGalleryView().runApp()
