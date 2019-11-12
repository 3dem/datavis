
import os
import unittest

import datavis as dv
import numpy as np


class TestImageModels(dv.tests.TestBase):

    def test_ImageModel(self):
        imgModel = dv.models.ImageModel()  # Empty ImageModel
        # Data and dimensions should be None
        self.assertIsNone(imgModel.getData())
        self.assertIsNone(imgModel.getDim())

        # self.assertEqual(imageModel.getDim(), (9216, 9441))
        # self.assertAlmostEqual(minValue, 0.0)
        # self.assertAlmostEqual(maxValue, 255.0)
        # self.assertIsNotNone(imageModel.getData())

        data = np.ones((100, 200))
        imgModel.setData(data)

        # Data should not be None, neither dimensions
        self.assertIsNotNone(imgModel.getData())
        self.assertEqual(imgModel.getDim(), (200, 100))
        self.assertEqual(imgModel.getMinMax(), (1, 1))

        return

    # def test_VolumeModel(self):
    #     volName = self.getDataPaths()[2]
    #     print("Checking %s" % volName)
    #
    #     volModel = dv.models.VolumeModel(
    #         data=emv.utils.ImageManager().getData(volName))
    #     minValue, maxValue = volModel.getMinMax()
    #
    #     def _check(model):
    #         self.assertEqual(model.getDim(), (300, 300, 300))
    #         self.assertAlmostEqual(minValue, -0.011036, places=5)
    #         self.assertAlmostEqual(maxValue, 0.027878, places=5)
    #         self.assertIsNotNone(model.getData())
    #
    #     _check(volModel)
    #     sliceModel = volModel.getSlicesModel(dv.models.AXIS_Z)
    #     _check(sliceModel)
    #     imageModel = volModel.getSliceImageModel(dv.models.AXIS_Z, 0)
    #     self.assertEqual(imageModel.getDim(), (300, 300))
    #
    #     volModel.setData(None)
    #     self.assertIsNone(volModel.getData())
    #     self.assertIsNone(volModel.getDim())
    #
    #     return
    #
    #     # 2D stack of particles
    #     stackName = "emx/alignment/Test2/stack2D.mrc"
    #     stackDim = emc.ArrayDim(128, 128, 1, 100)
    #     # 3D volumes
    #     vol1Name = "resmap/t20s_proteasome_full.map"
    #     vol1Dim = emc.ArrayDim(300, 300, 300, 1)
    #
    #     fileDims = {volName: (micDim, 87008256),
    #                 stackName: (stackDim, 65536),  # 128 * 128 * 4
    #                 vol1Name: (vol1Dim, 108000000)
    #                 }
    #
    #     for fn, (dim, size) in fileDims.items():
    #         img = emc.Image()
    #         loc = emc.ImageLocation(os.path.join(testDataPath, fn), 1)
    #         print(">>> Reading image: ", loc.path)
    #         img.read(loc)
    #         dim.n = 1
    #         self.assertEqual(img.getDim(), dim)
    #         self.assertEqual(img.getDataSize(), size)
    #

if __name__ == '__main__':
    unittest.main()

