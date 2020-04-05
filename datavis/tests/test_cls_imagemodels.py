
import unittest

import datavis as dv
import numpy as np


class TestImageModels(dv.tests.TestBase):

    def test_ImageModel(self):
        imgModel = dv.models.ImageModel()  # Empty ImageModel

        self.assertIsNone(imgModel.getData(), 'Data should be None')
        self.assertIsNone(imgModel.getDim(), 'Dim should be None')

        data = np.ones((100, 100))
        imgModel = dv.models.ImageModel(data)
        self.assertEqual(imgModel.getDim(), (100, 100),
                         'Dimensions should be (100,100)')
        self.assertIsNotNone(imgModel.getData(), 'Data should not be None')
        self.assertEqual(imgModel.getMinMax(), (1, 1),
                         'min,max should be (1,1)')

        print('test_ImageModel: OK')
        return

    def test_SlicesModel(self):
        s = 5, 1, 1  # 5 slices of dim=(1,1)
        data = np.arange(5)
        data = data.reshape(s)

        sm = dv.models.SlicesModel(data)
        self.assertEqual(sm.getDim(), (1, 1, 5),
                         'Dimensions should be (x=1, y=1, z=5)')
        for i in range(s[0]):
            self.assertEqual(sm.getData(i)[0][0], i,
                             'Data value should be %d' % i)

        print('test_SlicesModel: OK')

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

