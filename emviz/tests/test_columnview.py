#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys

from emviz.core import ModelsFactory
from emviz.views import ColumnsView
from test_commons import TestView


class TestColumnsView(TestView):
    __title = "ColumnsView example"

    def getDataPaths(self):
        return [
            self.getPath("relion_tutorial", "import", "refine3d", "extra",
                         "relion_it025_data.star")
        ]

    def createView(self):
        return ColumnsView(model=ModelsFactory.createTableModel(self._path))


if __name__ == '__main__':
    TestColumnsView(sys.argv).run()
