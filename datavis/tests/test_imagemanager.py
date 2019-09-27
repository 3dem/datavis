
import os
import sys
import unittest

import emcore as emc
from datavis.core import ImageManager
from test_commons import TestBase


class TestImageManager(TestBase):
    def getDataPaths(self):
        return [
            self.getPath("relion_tutorial", "import", "refine3d", "extra",
                         "relion_it025_data.star"),
            self.getPath("relion_tutorial", "import", "classify2d", "extra",
                         "relion_it015_data.star"),
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

    def test_findImagePrefix(self):
        path0, path1 = self.getDataPaths()
        self._checkPrefix(path0, os.path.dirname(path0))

        # Test another case where image should be found
        # some levels up
        self._checkPrefix(path1, os.path.dirname(os.path.dirname(path1)))


if __name__ == '__main__':
    unittest.main()

