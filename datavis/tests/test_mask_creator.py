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
    argParser.add_argument('data', default=0, type=int,
                           choices=[0, 1],
                           help='Choose 1 to initialize the mask with all ones '
                                'and operation remove by default')
    argParser.add_argument('--color', default='#66212a55', type=str,
                           help='The mask color in ARGB format.')
    argParser.add_argument('--pen', default=40, type=int,
                           help='Pen size')

    print("TIP: Use --help for more options.")

    args = argParser.parse_args()

    kwargs['maskCreatorColor'] = args.color
    kwargs['maskCreatorData'] = args.data
    kwargs['maskCreatorOp'] = bool(args.data)
    kwargs['maskPenSize'] = args.pen

    TestMaskCreator(**kwargs).runApp(argv=['0'])
