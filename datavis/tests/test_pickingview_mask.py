#!/usr/bin/python
# -*- coding: utf-8 -*-

import numpy as np

import datavis as dv
from datavis.models import ColumnConfig, TYPE_STRING, TYPE_INT


class MyPickerModel(dv.tests.SimplePickerModel):
    def __init__(self, *args, **kwargs):
        dv.tests.SimplePickerModel.__init__(self, *args, **kwargs)
        self._scoreThreshold = 0.5
        # Modify 'Auto' label to set red color
        self._labels['A'] = self._labels['A']._replace(color='#FF0000')
        self._showBelow = True

        self._maskCache = {}

    def __coordsBelow(self, micId):
        return len([c for c in self._getCoordsList(micId)
                    if c.score < self._scoreThreshold])

    def __createMask(self, micId):
        w, h = self._imageSize
        mask = np.zeros(shape=(h, w), dtype=np.int8)
        for c in self._getCoordsList(micId):
            for i in range(c.y - int(self._boxsize/2),
                           c.y + int(self._boxsize/2)):
                for j in range(c.x - int(self._boxsize/2),
                               c.x + int(self._boxsize/2)):
                    if 0 <= i < h and 0 <= j < w:
                        mask[i][j] = 1

        return mask

    def getParams(self):
        Param = dv.models.Param
        scoreThreshold = Param('scoreThreshold', 'float', value=0.5,
                               display='slider', range=(0, 1.0),
                               label='Score threshold',
                               help='Display coordinates with score above '
                                    'this value.')

        showBelow = Param('showBelow', 'bool', value=self._showBelow,
                          label='Show coordinates below?')

        nParam = Param('n', 'int', value=100,
                       label='Particles:',
                       help='Number of particles that you will pick randomly'
                            ' from the current micrograph.')

        clear = Param('clear', 'button', label='Clear coordinates')
        pick = Param('pick', 'button', label='Pick Again')

        return dv.models.Form([
            [scoreThreshold, showBelow],
            [pick, nParam],
            clear
        ])

    def changeParam(self, micId, paramName, paramValue, getValuesFunc):
        # Most cases here will modify the current coordinates
        r = self.Result(currentCoordsChanged=True, tableModelChanged=True)

        if paramName in ['pick', 'n']:
            values = getValuesFunc()
            self.pickRandomly(micId, n=values['n'])
        elif paramName == 'scoreThreshold':
            self._scoreThreshold = getValuesFunc()['scoreThreshold']
        elif paramName == 'clear':
            self.clearMicrograph(micId)
        elif paramName == 'showBelow':
            self._showBelow = getValuesFunc()['showBelow']
        else:
            r = self.Result()  # No modification

        return r

    def iterCoordinates(self, micId):
        # Re-implement this to show only these above the threshold
        # or with a different color (label)
        for coord in self._getCoordsList(micId):
            good = coord.score > self._scoreThreshold
            coord.label = 'M' if good else 'A'
            if good or self._showBelow:
                yield coord

    def getColumns(self):
        """ Return a Column list that will be used to display micrographs. """
        return [
            ColumnConfig('Micrograph', dataType=TYPE_STRING, editable=False),
            ColumnConfig('Coords', dataType=TYPE_INT, editable=False),
            ColumnConfig('Coords < Threshold', dataType=TYPE_INT,
                         editable=False),
            ColumnConfig('Id', dataType=TYPE_INT, editable=False, visible=False)
        ]

    def getValue(self, row, col):
        # Re-implement this to show only these above the threshold
        mic = self.getMicrographByIndex(row)
        micId = mic.getId()

        if col == 0:  # Name
            return 'Micrograph %02d' % micId
        elif col == 1:  # Coordinates
            return len(mic) - self.__coordsBelow(micId)
        elif col == 2:  # Coordinates below threshold
            return self.__coordsBelow(micId)
        elif col == 3:  # Id
            return mic.getId()
        else:
            raise Exception("Invalid column value '%s'" % col)

    def getMicrographMask(self, micId):
        if micId not in self._maskCache:
            self._maskCache[micId] = self.__createMask(micId)

        return self._maskCache[micId]


class TestPickerViewMask(dv.tests.TestView):
    __title = "PickerViewMask Example"

    def __init__(self, methodName='runTest'):
        dv.tests.TestView.__init__(self, methodName=methodName)

    def getDataPaths(self):
        return ['']

    def createView(self):
        kwargs = dict()
        kwargs['selectionMode'] = dv.views.PagingView.SINGLE_SELECTION
        kwargs['boxSize'] = 64
        kwargs['pickerMode'] = dv.views.DEFAULT_MODE
        kwargs['shape'] = dv.views.SHAPE_CIRCLE
        kwargs['removeRois'] = True
        kwargs['roiAspectLocked'] = True
        kwargs['roiCentered'] = True

        model = MyPickerModel((512, 1024), 10, 64, 150, False)
        return dv.views.PickerView(model, **kwargs)

    def test_PickingViewMask(self):
        print('test_PickingViewMask')


if __name__ == '__main__':
    TestPickerViewMask().runApp()
