#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
from random import randrange
import numpy as np
import pyqtgraph as pg

import datavis as dv


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
        model1 = dv.tests.createSimplePickerDataModel((w, h), boxSize)
        model2 = dv.tests.createSimplePickerDataModel((w, h), boxSize)

        for i in range(self._size):
            micId = i + 1
            name = 'Image #%d' % micId
            coordsA = [
                dv.models.Coordinate(x, y, threshold=randrange(0, 100)*0.01)
                for x, y in {(randrange(0, w), randrange(0, h))
                             for i in range(randrange(1, self._picks))}
            ]
            coordsB = [
                dv.models.Coordinate(x, y, threshold=randrange(0, 100) * 0.01)
                for x, y in {(randrange(0, w), randrange(0, h))
                             for i in range(randrange(1, self._picks))}
            ]

            model1.addMicrograph(dv.models.Micrograph(micId, name, coordsA))
            model2.addMicrograph(dv.models.Micrograph(micId, name, coordsB))

        model = ThresholdPickerModel(model1, model2, boxSize=self._box,
                                     radius=self._radius,
                                     imageSize=(self._w, self._h))
        pickerParams = [
            {
                'name': 'threshold',
                'type': 'enum',
                'value': 0,
                'choices': (0, 100),
                'label': 'Quality threshold',
                'help': 'Quality threshold',
                'display': 'slider',
                'onChange': 'onParamChanged'
            },
            {
                'name': 'radius',
                'type': 'enum',
                'value': self._radius,
                'choices': (1, 200),
                'label': 'Radius',
                'help': 'Radius',
                'display': 'slider',
                'onChange': 'onParamChanged'
            }
        ]
        kwargs['pickerParams'] = pickerParams

        return dv.views.PickerView(None, model, **kwargs)


class ThresholdPickerModel(dv.models.PickerCmpModel):
    """ """
    def __init__(self, model1, model2, boxSize=64, radius=64, threshold=0,
                 imageSize=(512, 512)):
        dv.models.PickerCmpModel.__init__(self, model1, model2, boxSize=boxSize,
                                          radius=radius)
        self._threshold = threshold
        self._images = dict()
        self._cache = {}
        self._imageSize = imageSize

    def __getitem__(self, micId):
        mic = dv.models.PickerCmpModel.__getitem__(self, micId)
        self.__applyThreshold(mic)

        return mic

    def __applyThreshold(self, mic):
        """
        Apply the current threshold to the given micrograph
        :param mic: (Micrograph) The micrograph
        """
        coords = list(mic)
        mic.clear()
        for c in coords:
            if c.threshold >= self._threshold:
                mic.addCoordinate(c)

    def onParamChanged(self, paramName, value):
        dv.models.PickerCmpModel.onParamChanged(self, paramName, value)
        if paramName == 'threshold':
            self._threshold = value * 0.01

    def getData(self, micId):
        """
        Return the micrograph image data
        :param micId: (int) The micrograph id
        :return: The micrograph image data
        """
        if micId in self._cache:
            data = self._cache[micId]
        else:
            #  simulating image data
            data = pg.gaussianFilter(np.random.normal(size=self._imageSize),
                                     (5, 5))
            self._cache[micId] = data

        return data

    def getImageInfo(self, micId):
        """
        Return some specified info from the given image path.
        dim : Image dimensions
        ext : File extension
        data_type: Image data type

        :param micId:  (int) The micrograph Id
        :return: dict
        """
        return {'dim': self._imageSize}


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