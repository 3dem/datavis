#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
from glob import glob

import em
from emviz.views import PagingView, SHAPE_CIRCLE, DEFAULT_MODE, PickerView
from emviz.models import PickerDataModel, Micrograph
from emviz.core import EmPickerDataModel
from test_commons import TestView


class TestPickerView(TestView):
    __title = "PickerView Example"

    def __parseFiles(self, values):
        """
        Try to matching a path pattern for micrographs
        and another for coordinates.

        Return a list of tuples [mic_path, pick_path].
        """
        length = len(values)
        result = dict()
        if length > 2:
            raise ValueError("Invalid number of arguments. Only 2 "
                             "arguments are supported.")

        if length > 0:
            mics = glob(values[0])
            for i in mics:
                basename = os.path.splitext(os.path.basename(i))[0]
                result[basename] = (i, None)

        if length > 1:
            coords = glob(values[1])
            for i in coords:
                basename = os.path.splitext(os.path.basename(i))[0]
                t = result.get(basename)
                if t:
                    result[basename] = (t[0], i)

        return result

    def getDataPaths(self):
        return [
            self.getPath("tmv_helix", "micrographs", "TMV_Krios_Falcon")
        ]

    def createView(self):
        kwargs = dict()
        kwargs['selectionMode'] = PagingView.SINGLE_SELECTION
        kwargs['boxSize'] = 300
        kwargs['pickerMode'] = DEFAULT_MODE
        kwargs['shape'] = SHAPE_CIRCLE
        kwargs['removeRois'] = True
        kwargs['roiAspectLocked'] = True
        kwargs['roiCentered'] = True
        dataPaths = self.getDataPaths()
        kwargs['sources'] = self.__parseFiles(["%s*" % dataPaths[0]])
        projectFolder = '/Users/josem/work/data/relion30_tutorial_precalculated_results/'
        pickingFolder = projectFolder + 'AutoPick/LoG_based'
        inputMics = 'Select/job005/micrographs_selected.star'

        # FIXME: Read Table data from the constructor
        table = em.Table()
        table.read(projectFolder + inputMics)

        model = EmPickerDataModel()
        model.setBoxSize(100)
        for i, row in enumerate(table):
            micPath = os.path.join(projectFolder, str(row['rlnMicrographName']))
            mic = Micrograph(i + 1, micPath)
            model.addMicrograph(mic)

        return PickerView(None, model=model, **kwargs)

if __name__ == '__main__':
    TestPickerView().runApp()
