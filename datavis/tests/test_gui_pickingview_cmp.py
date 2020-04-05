#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
from itertools import chain

import datavis as dv
from datavis.models import ColumnConfig, TYPE_INT, TYPE_STRING


class MyPickerCmpModel(dv.models.PickerModel):
    def __init__(self, model1, model2, **kwargs):
        dv.models.PickerModel.__init__(self, boxSize=kwargs.get('boxSize', 64))
        # format RRGGBBAA
        self._labels['a'] = self.Label(name="a", color="#00ff0055")
        self._labels['b'] = self.Label(name="b", color="#00ff00")
        self._labels['c'] = self.Label(name="c", color="#0000ff55")
        self._labels['d'] = self.Label(name="d", color="#0000ff")

        self._models = (model1, model2)
        self._radius = kwargs.get('radius', 40)
        self._union = dict()
        self.markAll()
        self._scoreThreshold = 0.5
        # Modify 'Auto' label to set red color
        self._labels['B'] = self.Label(name='B', color='#FF0000')
        self._showBelow = True

    def __getitem__(self, micId):
        return self._models[0].getMicrograph(micId)

    def __coordsBelow(self, micId):
        return len([c for c in self._getCoordsList(micId)
                    if c.score < self._scoreThreshold])

    def _getCoordsList(self, micId):
        """ Return the coordinates list of a given micrograph. """
        c1 = self._models[0].getMicrograph(micId)._coordinates
        c2 = self._models[1].getMicrograph(micId)._coordinates
        return chain(c1, c2)

    def _markCoordinates(self, listA, listB, radius):
        """
        Set the labels for the given list of Coordinates according to the
        following:
         - a) The coordinates of A and are not close to any of B
         - b) The coordinates of A and that are close to ones of B.
              (color similar to a))
         - c) Those of B that do not have close ones in A
         - d) Those of B that are close in A (color similar to c))
        :param listA: (list of Coordinate)
        :param listB: (list of Coordinate)
        :param radius: (int) Radius
        :return : (int) Number of coordinates having a) and b) conditions
        """
        c = set()
        radius *= radius

        for b in listB:
            b.set(label='c')  # case c)

        for a in listA:
            a.set(label='a')  # case a)

            for b in listB:

                d = (b.x - a.x) ** 2 + (b.y - a.y) ** 2
                if d <= radius:
                    a.set(label='b')  # case b)
                    b.set(label='d')  # case d)
                    c.add(a)
                    c.add(b)

        return len(c)

    def getMicrographByIndex(self, micIndex):
        return self._models[0].getMicrographByIndex(micIndex)

    def getMicrograph(self, micId):
        return self._models[0].getMicrograph(micId)

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

    def onParamChanged(self, micId, paramName, paramValues):
        # Most cases here will modify the current coordinates
        d = {'micId': micId,
             'currentCoordsChanged': True,
             'tableModelChanged': True}
        n = True

        if paramName in ['pick', 'n']:
            self._models[0].pickRandomly(micId, n=paramValues['n'])
            self._models[1].pickRandomly(micId, n=paramValues['n'])
            self.markAll()
        elif paramName == 'scoreThreshold':
            self._scoreThreshold = paramValues['scoreThreshold']
        elif paramName == 'clear':
            self.clearMicrograph(micId)
        elif paramName == 'showBelow':
            self._showBelow = paramValues['showBelow']
        elif paramName == 'proximityRadius':
            self._radius = paramValues['proximityRadius']
            self.markAll()
        else:
            n= False

        if n:
            self.notifyEvent(type=dv.models.PICK_EVT_DATA_CHANGED, info=d)

    def clearMicrograph(self, micId):
        for m in self._models:
            m.clearMicrograph(micId)

        self._union[micId] = 0
        self.notifyEvent(type=dv.models.PICK_EVT_DATA_CHANGED,
                         info={'currentCoordsChanged': True,
                               'tableModelChanged': True})

    def markAll(self):
        """
        Set label colors to all micrograph in the models
        """
        a, b = self._models
        for mic in a:
            micId = mic.getId()
            c = self._markCoordinates(mic._coordinates,
                                      b.getMicrograph(micId)._coordinates,
                                      self._radius)
            self._union[micId] = c

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
            return self._union.get(micId, 0)
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

    def addCoordinates(self, micId, coords):
        #  Disable the addCoordinates because we have two models.
        pass

class TestPickerCmpView(dv.tests.TestView):
    __title = "PickerView Comparator Example"

    def __init__(self, methodName='runTest', dim=(1512, 512), size=5, box=64,
                 picks=80, radius=64):
        self._w, self._h = dim
        self._box = box
        self._radius = radius
        self._picks = picks
        self._size = size
        dv.tests.TestView.__init__(self, methodName=methodName)

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

        model = MyPickerCmpModel(model1, model2, boxSize=self._box,
                                 radius=self._radius)

        return dv.views.PickerView(model, **kwargs)

    def testPickingViewCmp(self):
        print('testPickingViewCmp')


if __name__ == '__main__':

    argParser = argparse.ArgumentParser(usage='PickerView Comparator',
                                        prefix_chars='--',
                                        argument_default=None)
    argParser.add_argument('radius', type=int, help='Comparator radius.')
    argParser.add_argument('--width', type=int, help='Image width.',
                           default=512)
    argParser.add_argument('--height', type=int, default=512,
                           help='Image width.')
    argParser.add_argument('--images', type=int, default=15,
                           help='Number of images.')
    argParser.add_argument('--box', type=int, default=64,
                           help='Box size.')
    argParser.add_argument('--picks', type=int, default=80,
                           help='Number of picks.')

    print("TIP: Use --help for more options.")

    args = argParser.parse_args()

    TestPickerCmpView(dim=(args.width, args.height), size=args.images,
                      box=args.box, picks=args.picks,
                      radius=args.radius).runApp()
