#!/usr/bin/python
# -*- coding: utf-8 -*-

import datavis as dv


class TestDualImageListView(dv.tests.TestView):
    __title = "DualImageListView example"

    def getDataPaths(self):
        return ['']

    def createView(self):
        Param = dv.models.Param
        threshold = Param('threshold', 'float', value=0.55,
                          label='Quality threshold',
                          help='If this is...bla bla bla')
        thresholdBool = Param('threshold', 'bool', value=True,
                              label='Quality checked',
                              help='If this is a boolean param')

        threshold2 = Param('threshold2', 'float', value=0.67,
                           label='Quality', help='If this is...bla bla bla')

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

        form = dv.models.Form([
            [threshold, thresholdBool],
            [threshold2, threshold3],
            threshold4,
            threshold5,
            threshold6,
            [picking, apply]
        ])
        model = dv.tests.createListImageModel(
            ['image %d' % i for i in range(10)], 'Image', (512, 512))
        return dv.views.DualImageListView(model, form=form, method=printFunc)


def printFunc(*args):
    print(args)


if __name__ == '__main__':
    TestDualImageListView().runApp()