#!/usr/bin/python
# -*- coding: utf-8 -*-

from emviz.core import ModelsFactory
from emviz.views import VolumeListView, CIRCLE_ROI
from emviz.models import AXIS_X, AXIS_Y, AXIS_Z, AXIS_XYZ
from test_commons import TestView


class TestRoiMaskVolumeListView(TestView):
    __title = "RoiMaskVolumeListView example"

    def getDataPaths(self):
        return [
            self.getPath("relion_tutorial", "volumes", "reference_rotated.vol"),
            self.getPath("xmipp_programs", "gold", "xmipp_ctf_correct_wiener3d",
                         "wiener_deconvolved.vol"),
            self.getPath("emx", "reconstRotandShiftFlip_Gold_output.vol"),
            self.getPath("emx", "reconstRotandShift_Gold_output.vol"),
            self.getPath("xmipp_programs", "gold", "xmipp_image_resize_02",
                         "volume_64.vol")
        ]

    def createView(self):
        maskColor = '#154BBC23'
        slicesKwargs = {AXIS_X: {'imageViewKwargs': {'mask': CIRCLE_ROI,
                                                     'maskColor': maskColor,
                                                     'maskSize': 20}
                                 },
                        AXIS_Y: {'imageViewKwargs': {'mask': CIRCLE_ROI,
                                                     'maskColor': maskColor,
                                                     'maskSize': 20}
                                 },
                        AXIS_Z: {'imageViewKwargs': {'mask': CIRCLE_ROI,
                                                     'maskColor': maskColor,
                                                     'maskSize': 20}
                                 }
                        }
        return VolumeListView(
            None, ModelsFactory.createListModel(self.getDataPaths()),
            slicesKwargs=slicesKwargs, slicesMode=AXIS_XYZ)


if __name__ == '__main__':
    TestRoiMaskVolumeListView().runApp()