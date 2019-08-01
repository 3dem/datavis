#!/usr/bin/python
# -*- coding: utf-8 -*-

from emviz.core import ModelsFactory
from emviz.views import ImageMaskListView
from .test_commons import TestView


class TestImageMaskListView(TestView):
    __title = "ImageMaskListView example"

    def getDataPaths(self):
        return [
            self.getPath("relion_tutorial", "micrographs", "006.mrc"),
            self.getPath("relion_tutorial", "micrographs", "008.mrc"),
            self.getPath("relion_tutorial", "micrographs", "016.mrc")
        ]

    def createView(self):
        return ImageMaskListView(
            None, ModelsFactory.createListModel(self.getDataPaths()))


if __name__ == '__main__':
    TestImageMaskListView().runApp()
