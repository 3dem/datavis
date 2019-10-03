#!/usr/bin/python
# -*- coding: utf-8 -*-

import numpy as np
import pyqtgraph as pg

import datavis as dv


class TestMaskCreator(dv.tests.TestView):
    __title = "Mask Creator example"

    def getDataPaths(self):
        return ['']

    def createView(self):
        imageView = dv.views.ImageView(parent=None, border_color='#FFAA33',
                                       showMaskCreator=True, maskPenSize=40)
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
    TestMaskCreator().runApp()
