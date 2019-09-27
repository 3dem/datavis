#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys

from datavis.core import ModelsFactory
from datavis.views import ItemsView
from test_commons import TestView


class TestItemsView(TestView):
    __title = "ItemsView Example"

    def getDataPaths(self):
        return [
            self.getPath("relion_tutorial", "import", "refine3d", "extra",
                         "relion_it025_data.star")
        ]

    def createView(self):
        return ItemsView(model=ModelsFactory.createTableModel(self._path),
                         selectionMode=ItemsView.MULTI_SELECTION)


if __name__ == '__main__':
    TestItemsView().runApp()
