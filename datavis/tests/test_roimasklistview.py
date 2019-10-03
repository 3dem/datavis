#!/usr/bin/python
# -*- coding: utf-8 -*-

import numpy as np
import pyqtgraph as pg

import datavis as dv


class TestRoiMaskListView(dv.tests.TestView):
    __title = "RoiMaskListView example"

    def getDataPaths(self):
        return ['']

    def createView(self):
        return dv.views.ImageMaskListView(
            None, SimpleListModel(['image %d' % i for i in range(10)],
                                  'Image', (1024, 1024)),
            maskColor='#154BBC23', mask=dv.views.CIRCLE_ROI, maskSize=500)


class SimpleListModel(dv.models.ListModel):
    """ The SimpleListModel class is an example implementation of ListModel
    """
    def __init__(self, names, columnName, imgSize):
        """
        Create an SimpleListModel
        :param names: (list) A list of names
        """
        self._names = list(names)
        self._columnName = columnName or 'Image'
        self._imgSize = imgSize
        self._imgData = dict()

        self._tableName = ''
        self._tableNames = [self._tableName]

    def iterColumns(self):
        yield dv.models.ColumnInfo(self._columnName, dv.models.TYPE_STRING)

    def getRowsCount(self):
        """ Return the number of rows. """
        return len(self._names)

    def getValue(self, row, col):
        """ Return the value of the item in this row, column. """
        return self._names[row]

    def getData(self, row, col=0):
        """ Return the data (array like) for the item in this row, column.
         Used by rendering of images in a given cell of the table.
        """
        data = self._imgData.get(row)
        if data is None:
            data = pg.gaussianFilter(np.random.normal(size=self._imgSize),
                                     (5, 5))
            self._imgData[row] = data

        return data

    def getModel(self, row):
        """ Return the model for the given row """
        return dv.models.ImageModel(self.getData(row))

    def createDefaultConfig(self):
        c = dv.models.ListModel.createDefaultConfig(self)
        cc = c[0]
        cc[dv.models.RENDERABLE] = True
        return c


if __name__ == '__main__':
    TestRoiMaskListView().runApp()
