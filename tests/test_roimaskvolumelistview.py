#!/usr/bin/python
# -*- coding: utf-8 -*-

from emviz.core import ModelsFactory
from emviz.views import VolumeListView, CIRCLE_ROI
from emviz.models import AXIS_X, AXIS_Y, AXIS_Z
from test_commons import TestView


class TestRoiMaskVolumeListView(TestView):
    __title = "RoiMaskVolumeListView example"

    def getDataPaths(self):
        return [
            self.getPath("relion_tutorial", "volumes", "reference_rotated.vol"),
            self.getPath("xmipp_programs", "gold", "xmipp_image_resize_02",
                         "volume_64.vol"),
            self.getPath("xmipp_programs", "gold", "xmipp_ctf_correct_wiener3d",
                         "wiener_deconvolved.vol")
        ]

    def createView(self):
        slicesKwargs = {AXIS_X: {'imageViewKwargs': {'mask': CIRCLE_ROI,
                                                     'maskColor': '#440826E0',
                                                     'maskSize': 40}
                                 },
                        AXIS_Y: {'imageViewKwargs': {'mask': CIRCLE_ROI,
                                                     'maskColor': '#44E72929',
                                                     'maskSize': 40}
                                 },
                        AXIS_Z: {'imageViewKwargs': {'mask': CIRCLE_ROI,
                                                     'maskColor': '#444BBC23',
                                                     'maskSize': 40}
                                 }
                        }
        return VolumeListView(
            None, ModelsFactory.createListModel(self.getDataPaths()),
            slicesKwargs=slicesKwargs)


if __name__ == '__main__':
    TestRoiMaskVolumeListView().runApp()
