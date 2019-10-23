#!/usr/bin/python
# -*- coding: utf-8 -*-

import datavis as dv


class MyPickerDataModel(dv.tests.SimplePickerDataModel):
    def __init__(self, *args, **kwargs):
        dv.tests.SimplePickerDataModel.__init__(self, *args, **kwargs)

    def _createParams(self):
        Param = dv.models.Param
        threshold = Param('threshold', 'float', value=0.55,
                          label='Quality threshold',
                          help='If this is...bla bla bla')
        thresholdBool = Param('threshold', 'bool', value=True,
                              label='Quality checked',
                              help='If this is a boolean param')

        threshold2 = Param('threshold2', 'float', value=0.67,
                           display='slider', range=(0, 1.0),
                           label='Slider quality', help='Select value')

        threshold3 = Param('threshold3', 'float', value=14.55,
                           label='Quality threshold2',
                           help='If this is a boolean param')

        threshold4 = Param('threshold4', 'string', value='Explanation text',
                           label='Threshold ex',
                           help='Showing some explanation in a text')

        threshold5 = Param('threshold5', 'string', value='Another text',
                           label='Another text example',
                           help='Showing more text')

        threshold6 = Param('threshold6', 'float', value=1.5,
                           label='Another float',
                           help='Just another float example')

        picking = Param('picking', 'enum', value=1,
                        choices=['LoG', 'Swarm', 'SVM'],
                        label='Picking method', display='combo',
                        help='Select the picking strategy that you want to use.')

        apply = Param('apply', 'button', label='Pick Again')

        return dv.models.Form([
            [threshold, thresholdBool],
            [threshold2, threshold3],
            threshold4,
            threshold5,
            threshold6,
            [picking, apply]
        ])


class TestPickerView(dv.tests.TestView):
    __title = "PickerView Example"

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

        model = MyPickerDataModel((1024, 1024), 10, 64, 150, False)
        return dv.views.PickerView(None, model, **kwargs)


if __name__ == '__main__':
    TestPickerView().runApp()