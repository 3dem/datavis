#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys

import numpy as np
import pyqtgraph as pg

import datavis as dv


class TestRoiMaskVolumeListView(dv.tests.TestView):
    __title = "RoiMaskVolumeListView example"

    def __init__(self, singleAxis):
        self._mode = dv.models.AXIS_Z if singleAxis else dv.models.AXIS_XYZ

    def getDataPaths(self):
        return ['']

    def createView(self):
        maskColor = '#154BBC23'
        slicesKwargs = {
            dv.models.AXIS_X: {
                'imageViewKwargs': {'mask': dv.views.CIRCLE_ROI,
                                    'maskColor': maskColor,
                                    'maskSize': 20}
                                },
            dv.models.AXIS_Y: {
                'imageViewKwargs': {'mask': dv.views.CIRCLE_ROI,
                                    'maskColor': maskColor,
                                    'maskSize': 20}
                                 },
            dv.models.AXIS_Z: {
                'imageViewKwargs': {'mask': dv.views.CIRCLE_ROI,
                                    'maskColor': maskColor,
                                    'maskSize': 20}
                                 }
        }
        return dv.views.VolumeListView(
            None, SimpleVolumeListModel(['volume %d' % i for i in range(8)],
                                        'Volume', (64, 64, 64)),
            slicesKwargs=slicesKwargs, slicesMode=self._mode)


class SimpleVolumeListModel(dv.models.ListModel):
    """ The SimpleVolumeListModel class is an example implementation of
    ListModel
    """
    def __init__(self, names, columnName, imgSize):
        """
        Create an SimpleListModel
        :param names: (list) A list of names
        """
        self._names = list(names)
        self._columnName = columnName or 'Volume'
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
                                     [5 for i in range(len(self._imgSize))])
            self._imgData[row] = data

        return data

    def getModel(self, row):
        """ Return the model for the given row """
        return dv.models.VolumeModel(self.getData(row))


if __name__ == '__main__':
    if 'single' in sys.argv:
        singleAxis = True
    else:
        print("TIP: Use 'single' argument to show a single axis. ")
        singleAxis = False

    TestRoiMaskVolumeListView(singleAxis).runApp()
