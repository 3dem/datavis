#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
from glob import glob

import em
from emviz.views import PagingView, SHAPE_CIRCLE, DEFAULT_MODE, PickerView
from emviz.models import PickerDataModel, Micrograph, Coordinate
from emviz.core import EmPickerDataModel
from test_commons import TestView


class TestPickerView(TestView):
    __title = "Relion picking viewer"

    def __init__(self, projectFolder, pickingFolder):
        self.projectFolder = projectFolder
        self.pickingFolder = pickingFolder

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

        projectFolder = self.projectFolder #'/Users/josem/work/data/relion30_tutorial_precalculated_results/'
        pickingFolder = self.pickingFolder # 'AutoPick/LoG_based'
        pickingPath = os.path.join(projectFolder, pickingFolder)
        micsStar = 'Select/job005/micrographs_selected.star'

        # For some reason Relion store input micrographs star filename
        # in the following star file, that is not a STAR file
        suffixMicFn = os.path.join(pickingPath, 'coords_suffix_autopick.star')

        if not os.path.exists(suffixMicFn):
            raise Exception("Missing expected file: %s" % suffixMicFn)

        with open(suffixMicFn) as f:
            micsStar = f.readline().strip()

        micsStarPath = os.path.join(projectFolder, micsStar)
        print("file: '%s', exists: %s" % (micsStarPath, os.path.exists(micsStarPath)))
        if not os.path.exists(micsStarPath):
            raise Exception("Missing expected file %s" % micsStarPath)

        print("Relion Project: %s" % projectFolder)
        print("   Micrographs: %s" % micsStar)
        print("       Picking: %s" % pickingFolder)

        # FIXME: Read Table data from the constructor
        table = em.Table()
        coordTable = em.Table()
        table.read(micsStarPath)

        model = EmPickerDataModel()
        model.setBoxSize(300)

        for i, row in enumerate(table):
            micPath = os.path.join(projectFolder, str(row['rlnMicrographName']))
            mic = Micrograph(i + 1, micPath)
            coordFn = os.path.join(pickingPath, 'Movies')
            micCoordsFn = os.path.join(
                coordFn, os.path.basename(micPath).replace(".mrc", "_autopick.star"))
            if os.path.exists(micCoordsFn):
                coordTable.read(micCoordsFn)
                for coordRow in coordTable:
                    mic.addCoordinate(
                        Coordinate(round(float(coordRow['rlnCoordinateY'])),
                                   round(float(coordRow['rlnCoordinateX']))))
            model.addMicrograph(mic)

        return PickerView(None, model=model, **kwargs)

if __name__ == '__main__':
    n = len(sys.argv)

    if n != 3:
        raise Exception(
            "Expecting only two arguments: PROJECT_PATH PICKING_SUBFOLDER \n\n"
            "Example: \n"
            "   python emviz/tests/test_picking_relion.py "
            "/Users/josem/work/data/relion30_tutorial_precalculated_results/ "
            "AutoPick/LoG_based")

    projectFolder = sys.argv[1]
    pickingFolder = sys.argv[2]

    TestPickerView(projectFolder, pickingFolder).runApp()
