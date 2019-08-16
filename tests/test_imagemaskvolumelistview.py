#!/usr/bin/python
# -*- coding: utf-8 -*-

from emviz.core import ModelsFactory
from emviz.views import VolumeListView
from emviz.models import AXIS_X, AXIS_Y, AXIS_Z
from test_commons import TestView


class TestImageMaskVolumeListView(TestView):
    __title = "ImageMaskVolumeListView example"

    def getDataPaths(self):
        return [
            self.getPath("xmipp_programs", "gold",
                         "xmipp_ctf_correct_amplitude3d",
                         "wiener_ctffiltered_group000001.vol"),
            self.getPath("xmipp_programs", "gold",
                         "xmipp_ctf_correct_wiener3d_01",
                         "wiener_deconvolved.vol"),
            self.getPath("xmipp_programs", "gold",
                         "xmipp_ctf_correct_amplitude3d",
                         "wiener_deconvolved.vol")
        ]

    def createView(self):
        import numpy as np
        # creating the image mask
        mask = np.zeros(shape=(64, 64), dtype=np.int8)
        for i in range(20, 44):
            for j in range(20, 44):
                mask[i][j] = 1
        slicesKwargs = {AXIS_X: {'imageViewKwargs': {'mask': mask,
                                                     'maskColor': '#330826E0'
                                                     }
                                 },
                        AXIS_Y: {'imageViewKwargs': {'mask': mask,
                                                     'maskColor': '#33E72929'
                                                     }
                                 },
                        AXIS_Z: {'imageViewKwargs': {'mask': mask,
                                                     'maskColor': '#334BBC23'
                                                     }
                                 }
                        }
        return VolumeListView(
            None, ModelsFactory.createListModel(self.getDataPaths()),
            slicesKwargs=slicesKwargs)


if __name__ == '__main__':
    TestImageMaskVolumeListView().runApp()
