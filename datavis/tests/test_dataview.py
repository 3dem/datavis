#!/usr/bin/python
# -*- coding: utf-8 -*-

from datavis.core import ModelsFactory
from datavis.views import DataView
from test_commons import TestView


class TestDataView(TestView):
    __title = "DataView example"

    def getDataPaths(self):
        return [
            self.getPath("relion_tutorial", "import", "refine3d", "extra",
                         "relion_it025_data.star")
        ]

    def createView(self):
        print("File: %s" % self._path)
        return DataView(model=ModelsFactory.createTableModel(self._path))


if __name__ == '__main__':
    TestDataView().runApp()

