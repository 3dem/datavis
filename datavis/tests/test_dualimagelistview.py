#!/usr/bin/python
# -*- coding: utf-8 -*-

from datavis.core import ModelsFactory
from datavis.views import DualImageListView
from test_commons import TestView


class TestDualImageListView(TestView):
    __title = "DualImageListView example"

    def getDataPaths(self):
        return [
            self.getPath("relion_tutorial", "micrographs", "006.mrc"),
            self.getPath("relion_tutorial", "micrographs", "008.mrc"),
            self.getPath("relion_tutorial", "micrographs", "016.mrc")
        ]

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
                # display should be optional, for most params, a textbox is the default
                # for enum, a combobox is the default, other options could be sliders
                'display': 'combo'
            # or 'combo' or 'vlist' or 'hlist' or 'slider'
            },
            {
                'name': 'threshold3',
                'type': 'bool',
                'value': True,
                'label': 'Checked',
                'help': 'If this is a boolean param'
            }
        ]
        return DualImageListView(
            None, ModelsFactory.createListModel(self.getDataPaths()),
            options=tool_params1, method=printFunc)

def printFunc(*args):
    print(args)


if __name__ == '__main__':
    TestDualImageListView().runApp()