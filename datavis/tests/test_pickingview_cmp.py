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
        model1 = dv.tests.createSimplePickerDataModel((w, h),
                                                      kwargs.get('boxSize', 40))
        model2 = dv.tests.createSimplePickerDataModel((w, h),
                                                      kwargs.get('boxSize', 40))

        for i in range(self._size):
            micId = i + 1
            name = 'Image #%d' % micId
            coordsA = [ThresholdCoord(x, y, None, randrange(0, 100) * 0.01)
                       for x, y in {(randrange(0, w), randrange(0, h))
                                    for i in range(randrange(1, self._picks))}]
            coordsB = [ThresholdCoord(x, y, None, randrange(0, 100) * 0.01)
                       for x, y in {(randrange(0, w), randrange(0, h))
                                    for i in range(randrange(1, self._picks))}]
            c = ThresholdCoord(0, 0, None, randrange(0, 100) * 0.01)
            coordsA.append(c)
            c = ThresholdCoord(0, 0, None, randrange(0, 100) * 0.01)
            coordsB.append(c)
            model1.addMicrograph(dv.models.Micrograph(micId, name, coordsA))
            model2.addMicrograph(dv.models.Micrograph(micId, name, coordsB))

        model = PickerCmpModelImpl(model1, model2)
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
                'choices': (10, 200),
                'label': 'Radius',
                'help': 'Radius',
                'display': 'slider',
                'onChange': 'onParamChanged'
            }
        ]
        kwargs['pickerParams'] = pickerParams

        return dv.views.PickerView(None, model, **kwargs)


class PickerCmpModelImpl(dv.models.PickerCmpModel):
    """ """
    def __init__(self, model1, model2, boxSize=64, imageSize=(512, 512)):
        dv.models.PickerCmpModel.__init__(self, model1, model2, boxSize=boxSize)
        self._images = dict()
        self._cache = {}
        self._imageSize = imageSize

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


class ThresholdCoord(dv.models.Coordinate):
    """ Coordinate with threshold quality value """
    def __init__(self, x, y, label="Manual", threshold=1.0):
        dv.models.Coordinate.__init__(self, x, y, label)
        self.threshold = threshold


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