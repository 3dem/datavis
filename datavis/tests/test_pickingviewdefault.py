#!/usr/bin/python
# -*- coding: utf-8 -*-

import random
import numpy as np
import pyqtgraph as pg

import datavis as dv


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
      # display should be optional, for most params, a textbox is the default
      # for enum, a combobox is the default, other options could be sliders
      'display': 'combo'  # or 'combo' or 'vlist' or 'hlist' or 'slider'
    },
    {
        'name': 'threshold3',
        'type': 'bool',
        'value': True,
        'label': 'Checked',
        'help': 'If this is a boolean param'
    }
]


class TestPickerView(dv.tests.TestView):
    __title = "PickerView Example"

    def getDataPaths(self):
        return ['']

    def createView(self):
        kwargs = dict()
        kwargs['selectionMode'] = dv.views.PagingView.SINGLE_SELECTION
        kwargs['pickerParams'] = tool_params1
        kwargs['boxSize'] = 64
        kwargs['pickerMode'] = dv.views.DEFAULT_MODE
        kwargs['shape'] = dv.views.SHAPE_CIRCLE
        kwargs['removeRois'] = True
        kwargs['roiAspectLocked'] = True
        kwargs['roiCentered'] = True
        return dv.views.PickerView(None,
                                   SimplePickerDataModel((512, 512), 10,
                                                         kwargs.get('boxSize',
                                                                    40)),
                                   **kwargs)


class SimplePickerDataModel(dv.models.PickerDataModel):
    """ Simple picker data model with random images and picks """

    def __init__(self, imageSize, size, boxSize=40):
        dv.models.PickerDataModel.__init__(self)
        self._imageSize = imageSize
        self._size = size
        self._images = dict()
        self._cache = {}
        for i in range(size):
            self.addMicrograph(self.__simulateMic(i + 1,
                                                  random.randrange(0, 150)))
        self.setBoxSize(boxSize)

    def __simulateMic(self, micId, picks):
        """ Return a Micrograph object with random pick coordinates """
        w, h = self._imageSize
        coords = [(random.randrange(0, w),
                   random.randrange(0, h)) for i in range(picks)]
        return dv.models.Micrograph(micId, 'Image %d' % micId, coords)

    def getData(self, micId):
        """
        Return the micrograph image data
        :param micId: (int) The micrograph id
        :return: The micrograph image data
        """
        if micId in self._cache:
            data = self._cache[micId]
        else:
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
    TestPickerView().runApp()