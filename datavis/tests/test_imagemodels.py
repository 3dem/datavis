
import os
import sys
import unittest

import emcore as emc
import datavis.models as models
from datavis.core import ImageManager
from test_commons import TestBase


class TestImageModels(TestBase):
    def getDataPaths(self):
        return [
            self.getPath("xmipp_tutorial", "micrographs", "BPV_1386.mrc"),
            self.getPath("emx", "alignment", "Test2", "stack2D.mrc"),
            self.getPath("resmap", "t20s_proteasome_full.map"),
        ]

    def _checkPrefix(self, tableFn, expectedPrefix):
        table = emc.Table()
        table.read(tableFn)
        row = table[0]
        imgPath = str(row['rlnImageName'])

        im = ImageManager()
        realPath = imgPath.split('@')[1]
        imgPrefix = im.findImagePrefix(realPath, tableFn)
        self.assertEqual(imgPrefix, expectedPrefix)

    def test_ImageModel(self):
        # 2D image (a big one): micrograph
        micName = self.getDataPaths()[0]
        print("Checking %s" % micName)

        imageModel = models.ImageModel(data=ImageManager().getData(micName))
        minValue, maxValue = imageModel.getMinMax()

        self.assertEqual(imageModel.getDim(), (9216, 9441))
        self.assertAlmostEqual(minValue, 0.0)
        self.assertAlmostEqual(maxValue, 255.0)
        self.assertIsNotNone(imageModel.getData())

        imageModel.setData(None)
        self.assertIsNone(imageModel.getData())
        self.assertIsNone(imageModel.getDim())

        return

    def test_VolumeModel(self):
        volName = self.getDataPaths()[2]
        print("Checking %s" % volName)

        volModel = models.VolumeModel(data=ImageManager().getData(volName))
        minValue, maxValue = volModel.getMinMax()

        def _check(model):
            self.assertEqual(model.getDim(), (300, 300, 300))
            self.assertAlmostEqual(minValue, -0.011036, places=5)
            self.assertAlmostEqual(maxValue, 0.027878, places=5)
            self.assertIsNotNone(model.getData())

        _check(volModel)
        sliceModel = volModel.getSlicesModel(models.AXIS_Z)
        _check(sliceModel)
        imageModel = volModel.getSliceImageModel(0, models.AXIS_Z)
        self.assertEqual(imageModel.getDim(), (300, 300))

        volModel.setData(None)
        self.assertIsNone(volModel.getData())
        self.assertIsNone(volModel.getDim())

        return

        # 2D stack of particles
        stackName = "emx/alignment/Test2/stack2D.mrc"
        stackDim = emc.ArrayDim(128, 128, 1, 100)
        # 3D volumes
        vol1Name = "resmap/t20s_proteasome_full.map"
        vol1Dim = emc.ArrayDim(300, 300, 300, 1)

        fileDims = {volName: (micDim, 87008256),
                    stackName: (stackDim, 65536),  # 128 * 128 * 4
                    vol1Name: (vol1Dim, 108000000)
                    }

        for fn, (dim, size) in fileDims.items():
            img = emc.Image()
            loc = emc.ImageLocation(os.path.join(testDataPath, fn), 1)
            print(">>> Reading image: ", loc.path)
            img.read(loc)
            dim.n = 1
            self.assertEqual(img.getDim(), dim)
            self.assertEqual(img.getDataSize(), size)


if __name__ == '__main__':
    unittest.main()

