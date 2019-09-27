#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys

from datavis.core import ModelsFactory
from datavis.views import GalleryView
from test_commons import TestView


class TestGalleryView(TestView):
    __title = "GalleryView example"

    def getDataPaths(self):
        return [
            self.getPath("relion_tutorial", "import", "classify2d", "extra",
                         "relion_it015_classes.mrcs"),
            self.getPath("relion_tutorial", "import", "refine3d",
                         "input_particles.mrcs")
        ]

    def createView(self):
        return GalleryView(model=ModelsFactory.createTableModel(self._path))


if __name__ == '__main__':
    TestGalleryView().runApp()
