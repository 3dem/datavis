#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
from random import randrange
from math import sqrt

import PyQt5.QtCore as qtc

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
        w, h = self._w, self._h
        model = dv.tests.createSimplePickerDataModel((w, h),
                                                     kwargs.get('boxSize', 40))
        model.addPrivateLabel('a)', '#4c0045', 'a')
        model.addPrivateLabel('b)', '#f94aff', 'b')
        model.addPrivateLabel('c)', '#6a3b01', 'c')
        model.addPrivateLabel('d)', '#ca7e22', 'd')

        for i in range(self._size):
            name = 'Image #%d' % (i + 1)
            coords = [ThresholdCoord(x, y, None, randrange(0, 100) * 0.01)
                      for x, y in {(randrange(0, w), randrange(0, h))
                      for i in range(randrange(1, self._picks))}]
            s = randrange(len(coords))

            coordsA = coords[:s]
            coordsB = coords[s:]
            markCoordinates(coordsA, coordsB, self._radius)

            mic = dv.models.Micrograph(-1, name, coords)
            model.addMicrograph(mic)

        return PickerCmp(None, model, **kwargs)


class ThresholdCoord(dv.models.Coordinate):
    """ Coordinate with threshold quality value """
    def __init__(self, x, y, label="Manual", threshold=1.0):
        dv.models.Coordinate.__init__(self, x, y, label)
        self.threshold = threshold


class PickerCmp(dv.views.PickerView):

    def __init__(self, parent, model, threshold=0, **kwargs):
        pickerParams = kwargs.get('pickerParams') or []
        pickerParams.append([
            {
                'name': 'threshold',
                'type': 'enum',
                'value': threshold * 100,
                'choices': (0, 100),
                'label': 'Quality threshold',
                'help': 'Quality threshold',
                'display': 'slider',
                'slot': self.__onThresoldChanged
            }
        ])
        self.__threshold = threshold
        kwargs['pickerParams'] = pickerParams
        kwargs['readOnly'] = True
        kwargs['coordClass'] = ThresholdCoord
        dv.views.PickerView.__init__(self, parent, model, **kwargs)

    def _showMicrograph(self, mic):
        dv.views.PickerView._showMicrograph(self, mic)
        self.__onPickShowHideTriggered(self._actionPickShowHide.get())

    def __onThresoldChanged(self, threshold):
        """ Invoked when the user changes the threshold value"""
        self.__threshold = threshold * 0.01
        for coordRoi in self._roiList:
            roi = coordRoi.getROI()
            roi.setVisible(coordRoi.getCoord().threshold >= self.__threshold)

    @qtc.pyqtSlot(int)
    def __onPickShowHideTriggered(self, state):
        """ Invoked when action pick-show-hide is triggered """
        if state:
            self.__onThresoldChanged(self.__threshold * 100)
        else:
            self._showHidePickCoord(bool(state))


def markCoordinates(listA, listB, radius):
    """
    Set the labels for the given list of Coordinates according to the following:
     - a) The coordinates of A and are not close to any of B
     - b) The coordinates of A and that are close to ones of B.
          (color similar to a))
     - c) Those of B that do not have close ones in A
     - d) Those of B that are close in A (color similar to c))
    :param listA: (list of Coordinate)
    :param listB: (list of Coordinate)
    :param radius: (int) Radius
    """
    for a in listA:
        a.setLabel('a')  # case a)

        for b in listB:
            if b.getLabel() is None:
                b.setLabel('c')  # case c)

            d = sqrt((b.x - a.x)**2 + (b.y - a.y)**2)
            if d <= radius:
                a.setLabel('b')  # case b)
                b.setLabel('d')  # case d)


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
