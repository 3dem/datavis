#!/usr/bin/python
# -*- coding: utf-8 -*-


from datavis.models import AXIS_X, AXIS_Y, AXIS_Z
from datavis.views import MultiSliceView
from datavis.core import ModelsFactory

from test_commons import TestView


class TestMultiSliceView(TestView):
    __title = "MultiSliceView example"

    def getDataPaths(self):
        return [
            self.getPath('resmap', 'betaGal.mrc'),
            self.getPath("xmipp_tutorial", "volumes",
                         "BPV_scale_filtered_windowed_110.vol")
        ]

    def createView(self):
        print("File: %s" % self._path)
        volModel = ModelsFactory.createVolumeModel(self._path)
        msv = MultiSliceView(None,
                             {axis: {'model': volModel.getSlicesModel(axis),
                                     'normalize': True}
                              for axis in [AXIS_X, AXIS_Y, AXIS_Z]})
        return msv


if __name__ == '__main__':
    TestMultiSliceView().runApp()

