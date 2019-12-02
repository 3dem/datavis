#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse

import datavis as dv
from datavis.models import ColumnConfig, TYPE_INT, TYPE_STRING


class MyPickerModel(dv.models.PickerCmpModel):
    def __init__(self, *args, **kwargs):
        dv.models.PickerCmpModel.__init__(self, *args, **kwargs)
        self._scoreThreshold = 0.5
        # Modify 'Auto' label to set red color
        self._labels['B'] = self.Label(name='B', color='#FF0000')
        self._showBelow = True

    def __coordsBelow(self, micId):
        return len([c for c in self._getCoordsList(micId)
                    if c.score < self._scoreThreshold])

    def getParams(self):
        Param = dv.models.Param
        scoreThreshold = Param('scoreThreshold', 'float', value=0.5,
                               display='slider', range=(0, 1.0),
                               label='Score threshold',
                               help='Display coordinates with score above '
                                    'this value.')

        proximityRadius = Param('proximityRadius', 'int', value=40,
                                display='slider', range=(0, 100),
                                label='Proximity radius',
                                help='Proximity radius.')

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
            [proximityRadius, nParam],
            pick,
            clear
        ])

    def changeParam(self, micId, paramName, paramValue, getValuesFunc):
        # Most cases here will modify the current coordinates
        r = self.Result(currentCoordsChanged=True, tableModelChanged=True)

        if paramName in ['pick', 'n']:
            values = getValuesFunc()
            self._models[0].pickRandomly(micId, n=values['n'])
            self._models[1].pickRandomly(micId, n=values['n'])
            self.markAll()
        elif paramName == 'scoreThreshold':
            self._scoreThreshold = getValuesFunc()['scoreThreshold']
        elif paramName == 'clear':
            self.clearMicrograph(micId)
        elif paramName == 'showBelow':
            self._showBelow = getValuesFunc()['showBelow']
        else:
            r = dv.models.PickerCmpModel.changeParam(self, micId, paramName,
                                                     paramValue, getValuesFunc)
        return r

    def iterCoordinates(self, micId):
        # Re-implement this to show only these above the threshold
        # or with a different color (label)
        for coord in self._getCoordsList(micId):
            good = coord.score > self._scoreThreshold
            if good or self._showBelow:
                yield coord

    def getRowsCount(self):
        return self._models[0].getRowsCount()

    def getData(self, micId):
        return self._models[0].getData(micId)

    def getImageInfo(self, micId):
        return self._models[0].getImageInfo(micId)

    def getValue(self, row, col):
        mic = self.getMicrographByIndex(row)
        micId = mic.getId()

        if col == 0:  # Name
            return mic.getPath()
        elif col == 1:  # 'A' coordinates
            return len(self._models[0].getMicrograph(micId))
        elif col == 2:  # 'B' coordinates
            return len(self._models[1].getMicrograph(micId))
        elif col == 3:  # 'AnB' coordinates
            return dv.models.PickerCmpModel.getValue(self, row, col)
        elif col == 4:  # Coordinates
            mic2 = self._models[1].getMicrographByIndex(row)
            return len(mic2) + len(mic) - self.__coordsBelow(micId)
        else:
            raise Exception("Invalid column value '%s'" % col)

    def getColumns(self):
        return [
            ColumnConfig('Micrograph', dataType=TYPE_STRING, editable=False),
            ColumnConfig('A', dataType=TYPE_INT, editable=False),
            ColumnConfig('B', dataType=TYPE_INT, editable=False),
            ColumnConfig('AnB', dataType=TYPE_INT, editable=False),
            ColumnConfig('Coords < Threshold', dataType=TYPE_INT,
                         editable=False)
        ]


class TestPickerCmpView(dv.tests.TestView):
    __title = "PickerView Comparator Example"

    def __init__(self, dim=(1512, 512), size=5, box=64, picks=80, radius=64):
        self._w, self._h = dim
        self._box = box
        self._radius = radius
        self._picks = picks
        self._size = size

    def getDataPaths(self):
        return ['']

    def createView(self):
        kwargs = dict()
        kwargs['selectionMode'] = dv.views.PagingView.SINGLE_SELECTION
        kwargs['boxSize'] = self._box
        kwargs['pickerMode'] = dv.views.DEFAULT_MODE
        kwargs['shape'] = dv.views.SHAPE_CIRCLE
        kwargs['removeRois'] = True
        kwargs['roiAspectLocked'] = True
        kwargs['roiCentered'] = True
        kwargs['readOnly'] = True

        w, h = self._w, self._h
        boxSize = kwargs.get('boxSize', 40)
        model1 = dv.tests.createSimplePickerModel((w, h), self._size,
                                                      boxSize, self._picks)
        model2 = dv.tests.createSimplePickerModel((w, h), self._size,
                                                      boxSize, self._picks)

        model = MyPickerModel(model1, model2, boxSize=self._box,
                                  radius=self._radius)

        return dv.views.PickerView(model, **kwargs)


if __name__ == '__main__':

    argParser = argparse.ArgumentParser(usage='PickerView Comparator',
                                        prefix_chars='--',
                                        argument_default=None)
    argParser.add_argument('radius', type=int, help='Comparator radius.')
    argParser.add_argument('--width', type=int, help='Image width.',
                           default=512)
    argParser.add_argument('--height', type=int, default=512,
                           help='Image width.')
    argParser.add_argument('--images', type=int, default=5,
                           help='Number of images.')
    argParser.add_argument('--box', type=int, default=64,
                           help='Box size.')
    argParser.add_argument('--picks', type=int, default=80,
                           help='Number of picks.')

    print("TIP: Use --help for more options.")

    args = argParser.parse_args()

    TestPickerCmpView((args.width, args.height), args.images, args.box,
                      args.picks, args.radius).runApp()

TestPickerCmpView((512, 512), 1, 64, 80, 64).runApp()