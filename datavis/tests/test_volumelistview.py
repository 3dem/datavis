#!/usr/bin/python
# -*- coding: utf-8 -*-

from datavis.core import ModelsFactory
from datavis.views import VolumeListView
from test_commons import TestView


class TestVolumeListView(TestView):
    __title = "VolumeListView example"

    def getDataPaths(self):
        return [
            self.getPath("relion_tutorial", "volumes", "reference_rotated.vol"),
            self.getPath("xmipp_programs", "gold", "xmipp_image_resize_02",
                         "volume_64.vol"),
            self.getPath("xmipp_programs", "gold", "xmipp_ctf_correct_wiener3d",
                         "wiener_deconvolved.vol")
        ]

    def createView(self):
        return VolumeListView(
            None, ModelsFactory.createListModel(self.getDataPaths()))


if __name__ == '__main__':
    TestVolumeListView().runApp()
