#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys

from emviz.core import ModelsFactory
from emviz.views import DataView
from test_commons import TestView


class TestDataView(TestView):
    __title = "DataView example"

    def getDataPaths(self):
        return [
            self.getPath("relion_tutorial", "import", "refine3d", "extra",
                         "relion_it025_data.star")
        ]

    def createView(self):
        names, model = ModelsFactory.createTableModel(self._path)
        return DataView(parent=None, model=model)


if __name__ == '__main__':
    TestDataView(sys.argv).run()
