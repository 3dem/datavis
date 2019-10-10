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
        model = dv.tests.createListImageModel(
            ['image %d' % i for i in range(10)], 'Image', (512, 512))
        return dv.views.DualImageListView(
            None, model, options=tool_params1, method=printFunc)


def printFunc(*args):
    print(args)


if __name__ == '__main__':
    TestDualImageListView().runApp()