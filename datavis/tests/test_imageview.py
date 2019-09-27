#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys

from datavis.core import ModelsFactory
from datavis.views import ImageView
from test_commons import TestView


class TestImageView(TestView):
    __title = "ImageView example"

    def getDataPaths(self):
        return [
            self.getPath("relion_tutorial", "micrographs", "068.mrc")
        ]

    def createView(self):
        imageView = ImageView(parent=None, border_color='#FFAA33')
        imgModel = ModelsFactory.createImageModel(self._path)
        imageView.setModel(imgModel)
        dim_x, dim_y = imgModel.getDim()
        index, path = imgModel.getLocation()
        desc = ("<html><head/><body><p>"
                "<span style=\" color:#0055ff;\">Dimensions: </span>"
                "<span style=\" color:#000000;\">(%d,%d)</span></p>"
                "<p><strong>Path: </strong>%s</p></body>" 
                "</html>" % (dim_x, dim_y, path))
        imageView.setImageInfo(text=desc)
        return imageView


if __name__ == '__main__':
    TestImageView().runApp()
