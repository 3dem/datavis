#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
from glob import glob

import emcore as emc
from datavis.views import PagingView, SHAPE_CIRCLE, DEFAULT_MODE, PickerView
from datavis.models import PickerDataModel, Micrograph, Coordinate
from datavis.core import EmPickerDataModel
from test_commons import TestView


class TestPickerView(TestView):
    __title = "Relion picking viewer"

    def __init__(self, projectFolder, micStar, pickingFolder):
        self.projectFolder = projectFolder
        self.pickingFolder = pickingFolder
        self.micStar = micStar

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

        projectFolder = self.projectFolder  #'/Users/josem/work/data/relion30_tutorial_precalculated_results/'
        pickingFolder = self.pickingFolder  # 'AutoPick/LoG_based'
        pickingPath = os.path.join(projectFolder, pickingFolder)
        micsStar = self.micStar  # 'Select/job005/micrographs_selected.star'

        # For some reason Relion store input micrographs star filename
        # in the following star file, that is not a STAR file
        # suffixMicFn = os.path.join(pickingPath, 'coords_suffix_autopick.star')
        #
        # if not os.path.exists(suffixMicFn):
        #     raise Exception("Missing expected file: %s" % suffixMicFn)
        #
        # with open(suffixMicFn) as f:
        #     micsStar = f.readline().strip()

        micsStarPath = os.path.join(projectFolder, micsStar)
        if not os.path.exists(micsStarPath):
            raise Exception("Missing expected file %s" % micsStarPath)

        print("Relion Project: %s" % projectFolder)
        print("   Micrographs: %s" % micsStar)
        print("       Picking: %s" % pickingFolder)

        # FIXME: Read Table data from the constructor
        table = emc.Table()
        coordTable = emc.Table()
        table.read(micsStarPath)

        model = EmPickerDataModel()
        model.setBoxSize(64)

        def _getMicPath(micName):
            micPath = os.path.join(projectFolder, micName)
            if os.path.exists(micPath):
                return micPath
            micPath = os.path.join(pickingPath, micName)
            if os.path.exists(micPath):
                return micPath

            raise Exception("Can not find root path for mic: %s" % micName)

        for i, row in enumerate(table):
            micPath = _getMicPath(str(row['rlnMicrographName']))
            mic = Micrograph(i + 1, micPath)
            micCoordsFn = os.path.join(
                pickingPath,
                os.path.basename(micPath).replace(".mrc", "_autopick.star"))
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

    if n != 4:
        raise Exception(
            "Expecting only two arguments: PROJECT_PATH MICROGRAPHS_STAR COORDINATES_PATH \n\n"
            "Where: \n"
            "   PROJECT_PATH: Project path, root of all other inputs are found. \n"
            "   MICROGRAPHS_STAR: Star file with micrographs. \n"
            "   COORDINATES_PATH: Where the coordinates star files are. \n"
            "Example: \n"
            "   python datavis/tests/test_picking_relion.py "
            "/Users/josem/work/data/relion30_tutorial_precalculated_results/ "
            "AutoPick/LoG_based/Movies")

    projectFolder = sys.argv[1]
    micStar = sys.argv[2]
    pickingFolder = sys.argv[3]

    TestPickerView(projectFolder, micStar, pickingFolder).runApp()
