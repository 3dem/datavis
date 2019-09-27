#!/usr/bin/python
# -*- coding: utf-8 -*-

from datavis.views import SlicesView
from datavis.core import ModelsFactory, ImageManager

from test_commons import TestView


class TestSlicesView(TestView):
    __title = "Slices View example"

    def getDataPaths(self):
        return [
            self.getPath("relion_tutorial", "import", "classify2d", "extra",
                         "relion_it015_classes.mrcs"),
            self.getPath('resmap', 'betaGal.mrc')
        ]

    def createView(self):
        print("File: %s" % self._path)
        x, y, z, n = ImageManager().getDim(self._path)
        if z > 1:
            model = ModelsFactory.createVolumeModel(self._path)
            text = "Volume, Z slice: "
            value = z / 2
        elif n > 1:
            model = ModelsFactory.createStackModel(self._path)
            text = "Stack, image number: "
            value = 1
        else:
            raise Exception("Invalid input, it should be either volume or stack")

        return SlicesView(None, model, text=text, currentValue=value)


if __name__ == '__main__':
    TestSlicesView().runApp()
