#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
from glob import glob

from datavis.core import ViewsFactory
from datavis.views import PagingView, SHAPE_CIRCLE, FILAMENT_MODE
from test_commons import TestView

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


class TestPickerView(TestView):
    __title = "PickerView Example"

    def __parseFiles(self, values):
        """
        Try to matching a path pattern for micrographs
        and another for coordinates.

        Return a list of tuples [mic_path, pick_path].
        """
        length = len(values)
        result = dict()
        if length > 2:
            raise ValueError("Invalid number of arguments. Only 2 "
                             "arguments are supported.")

        if length > 0:
            mics = glob(values[0])
            for i in mics:
                basename = os.path.splitext(os.path.basename(i))[0]
                result[basename] = (i, None)

        if length > 1:
            coords = glob(values[1])
            for i in coords:
                basename = os.path.splitext(os.path.basename(i))[0]
                t = result.get(basename)
                if t:
                    result[basename] = (t[0], i)

        return result

    def getDataPaths(self):
        return [
            self.getPath("tmv_helix", "coords", "TMV_Krios_Falcon"),
            self.getPath("tmv_helix", "micrographs", "TMV_Krios_Falcon")
        ]

    def createView(self):
        kwargs = dict()
        kwargs['selectionMode'] = PagingView.SINGLE_SELECTION
        kwargs['pickerParams'] = tool_params1
        kwargs['boxSize'] = 300
        kwargs['pickerMode'] = FILAMENT_MODE
        kwargs['shape'] = SHAPE_CIRCLE
        kwargs['removeRois'] = True
        kwargs['roiAspectLocked'] = True
        kwargs['roiCentered'] = True
        dataPaths = self.getDataPaths()
        kwargs['sources'] = self.__parseFiles(["%s*" % dataPaths[1],
                                               "%s*" % dataPaths[0]])
        files = [micPath for (micPath, _) in kwargs['sources'].values()]
        return ViewsFactory.createPickerView(files, **kwargs)


if __name__ == '__main__':
    TestPickerView().runApp()
