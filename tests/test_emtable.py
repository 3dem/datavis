#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import sys

from emviz.core import ModelsFactory
from test_commons import TestView


# FIXME: This test is not strickly a TestView...so we might extract
# some of the TestView functions into a more general base class
class TestEmTableModel(TestView):
    __title = "EmTableModel example"

    def getDataPaths(self):
        return [
            self.getPath("relion_tutorial", "import", "refine3d", "extra",
                         "relion_it001_half2_model.star"),
            self.getPath("relion_tutorial", "import", "refine3d", "extra",
                         "relion_it025_data.star")
        ]

    def run(self):
        print("\nTest file: \n   ", self._path, "\n")
        model = ModelsFactory.createTableModel(self._path)

        tableNames = model.getTableNames()
        print("Table names: ", tableNames)

        expectedTableNames = [u'model_general', u'model_classes', u'model_class_1', u'model_groups', u'model_group_1']

        assert tableNames == expectedTableNames, "Different table names"

        # First table 'model_general' should have only one row
        assert model.getRowsCount() == 1, "Expecting only 1 row"

        # Load a different table
        model.loadTable('model_class_1')
        assert model.getRowsCount() == 31, "Expecting 31 rows"

        expectedColNames = ['rlnSpectralIndex', 'rlnResolution', 'rlnAngstromResolution', 'rlnSsnrMap',
                            'rlnGoldStandardFsc', 'rlnReferenceSigma2', 'rlnReferenceTau2']
        colNames = [c.getName() for c in model.iterColumns()]

        assert colNames == expectedColNames, "Different column names for table 'model_class_1'"


if __name__ == '__main__':
    TestEmTableModel(sys.argv).run()

