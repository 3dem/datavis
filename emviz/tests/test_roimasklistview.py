#!/usr/bin/python
# -*- coding: utf-8 -*-

from emviz.core import ModelsFactory
from emviz.views import ImageMaskListView, CIRCLE_ROI
from test_commons import TestView


class TestRoiMaskListView(TestView):
    __title = "ImageMaskListView example"

    def getDataPaths(self):
        return [
            self.getPath("relion_tutorial", "micrographs", "006.mrc"),
            self.getPath("relion_tutorial", "micrographs", "008.mrc"),
            self.getPath("relion_tutorial", "micrographs", "016.mrc")
        ]

    def createView(self):
        return ImageMaskListView(
            None, ModelsFactory.createListModel(self.getDataPaths()),
            maskColor='#220A1F88', mask=CIRCLE_ROI, maskSize=500)


if __name__ == '__main__':
    TestRoiMaskListView().runApp()
