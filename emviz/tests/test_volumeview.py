#!/usr/bin/python
# -*- coding: utf-8 -*-

from emviz.views import VolumeView
from emviz.core import ModelsFactory
from emviz.models import AXIS_X, AXIS_Y, AXIS_Z, AXIS_XYZ

from test_commons import TestView


class TestVolumeView(TestView):
    __title = "Volume View example"

    def getDataPaths(self):
        return [
            self.getPath('resmap', 'betaGal.mrc'),
            self.getPath("xmipp_tutorial", "volumes",
                         "BPV_scale_filtered_windowed_110.vol")
        ]

    def createView(self):
        print("File: %s" % self._path)
        self._path = self.getDataPaths()[0]
        volModel = ModelsFactory.createVolumeModel(self._path)
        return VolumeView(None, model=volModel, toolBar=True,
                          slicesMode=AXIS_XYZ)


if __name__ == '__main__':
    TestVolumeView().runApp()

