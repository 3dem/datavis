#!/usr/bin/python
# -*- coding: utf-8 -*-

from datavis.core import ModelsFactory
from datavis.views import ImageListView
from test_commons import TestView


class TestImageListView(TestView):
    __title = "ImageListView example"

    def getDataPaths(self):
        return [
            self.getPath("relion_tutorial", "import", "classify2d", "extra",
                         "relion_it015_classes.mrcs")
        ]

    def createView(self):
        return ImageListView(
            None, ModelsFactory.createTableModel(self.getDataPaths()[0]))


if __name__ == '__main__':
    TestImageListView().runApp()
