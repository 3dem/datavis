#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
import numpy as np
import pyqtgraph as pg

import datavis as dv


class TestMaskCreator(dv.tests.TestView):
    __title = "Mask Creator example"

    def __init__(self, **kwargs):
        self._kwargs = kwargs

    def getDataPaths(self):
        return ['']

    def createView(self):
        imageView = dv.views.ImageView(
            parent=None, border_color='#FFAA33', showMaskCreator=True,
            maskCreatorColor=self._kwargs.get('maskCreatorColor', '#66212a55'),
            maskPenSize=self._kwargs.get('maskPenSize', 40),
            maskCreatorData=self._kwargs.get('maskCreatorData', 1),
            maskCreatorOp=self._kwargs.get('maskCreatorOp', False))
        data = pg.gaussianFilter(np.random.normal(size=(512, 512)),
                                 (5, 5))
        imgModel = dv.models.ImageModel(data)
        imageView.setModel(imgModel)
        dim_x, dim_y = imgModel.getDim()
        desc = ("<html><head/><body><p>"
                "<span style=\" color:#0055ff;\">Dimensions: </span>"
                "<span style=\" color:#000000;\">(%d,%d)</span></p>"
                "</html>" % (dim_x, dim_y))
        imageView.setImageInfo(text=desc)
        return imageView


if __name__ == '__main__':
    kwargs = {}

    argParser = argparse.ArgumentParser(usage='Mask Creator',
                                        prefix_chars='--',
                                        argument_default=None)
    argParser.add_argument('--color', default='#66212a55', type=str,
                           required=False,
                           help=' the mask color in ARGB format.')
    argParser.add_argument('--data', default=0, type=int,
                           required=False, choices=[0, 1],
                           help=' the mask values')
    argParser.add_argument('--op', default='remove',
                           required=False, choices=['add', 'remove'],
                           help=' initial mask-creator operation')
    argParser.add_argument('--pen', default=40, required=False, type=int,
                           help=' pen size')

    print("TIP: Use --help for a more specific explanation.")

    args = argParser.parse_args()

    kwargs['maskCreatorColor'] = args.color
    kwargs['maskCreatorData'] = args.data
    kwargs['maskCreatorOp'] = args.op == 'add'
    kwargs['maskPenSize'] = args.pen

    TestMaskCreator(**kwargs).runApp()
