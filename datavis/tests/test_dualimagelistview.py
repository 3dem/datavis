#!/usr/bin/python
# -*- coding: utf-8 -*-

import numpy as np
import pyqtgraph as pg

import datavis as dv


class TestDualImageListView(dv.tests.TestView):
    __title = "DualImageListView example"

    def getDataPaths(self):
        return ['']

    def createView(self):
        tool_params1 = [
            [
                {
                    'name': 'threshold',
                    'type': 'float',
                    'value': 0.55,
                    'label': 'Quality threshold',
                    'help': 'If this is ... bla bla bla',
                    'display': 'default'
                },
                {
                    'name': 'thresholdBool',
                    'type': 'bool',
                    'value': True,
                    'label': 'Quality checked',
                    'help': 'If this is a boolean param'
                }
            ],
            [
                {
                    'name': 'threshold543',
                    'type': 'float',
                    'value': 0.67,
                    'label': 'Quality',
                    'help': 'If this is ... bla bla bla',
                    'display': 'default'
                },
                {
                    'name': 'threshold',
                    'type': 'float',
                    'value': 14.55,
                    'label': 'Quality threshold2',
                    'help': 'If this is ... bla bla bla',
                    'display': 'default'
                }
            ],
            {
                'name': 'threshold2',
                'type': 'string',
                'value': 'Explanation text',
                'label': 'Threshold ex',
                'help': 'If this is ... bla bla bla 2',
                'display': 'default'
            },
            {
                'name': 'text',
                'type': 'string',
                'value': 'Text example',
                'label': 'Text',
                'help': 'If this is ... bla bla bla for text'
            },
            {
                'name': 'threshold4',
                'type': 'float',
                'value': 1.5,
                'label': 'Quality',
                'help': 'If this is ... bla bla bla for quality'
            },
            {
                'name': 'picking-method',
                'type': 'enum',  # or 'int' or 'string' or 'enum',
                'choices': ['LoG', 'Swarm', 'SVM'],
                'value': 1,  # values in enum are int, in this case it is 'LoG'
                'label': 'Picking method',
                'help': 'Select the picking strategy that you want to use. ',
                # display should be optional, for most params, a textbox is the
                # default
                # for enum, a combobox is the default, other options could be
                # sliders
                'display': 'combo'  # or 'combo' or 'vlist' or 'hlist' or
                # 'slider'
            },
            {
                'name': 'threshold3',
                'type': 'bool',
                'value': True,
                'label': 'Checked',
                'help': 'If this is a boolean param'
            }
        ]
        return dv.views.DualImageListView(
            None, SimpleListModel(['image %d' % i for i in range(10)],
                                  'Image', (512, 512)),
            options=tool_params1, method=printFunc)


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


def printFunc(*args):
    print(args)


if __name__ == '__main__':
    TestDualImageListView().runApp()