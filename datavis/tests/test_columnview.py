#!/usr/bin/python
# -*- coding: utf-8 -*-

import datavis as dv


class TestColumnsView(dv.tests.TestView):
    __title = "ColumnsView example"

    def getDataPaths(self):
        return [
            self.getPath("relion_tutorial", "import", "refine3d", "extra",
                         "relion_it025_data.star")
        ]

    def createView(self):
        return dv.views.ColumnsView(
            model=self.__readStarFile(self.getDataPaths()[0]))

    def __readStarFile(self, path):
        """ Construct a SimpleTableModel reading a .star file """
        ColumnInfo = dv.models.ColumnInfo
        colInfo = []
        model = None
        q = 0
        with open(path) as f:
            for line in f:
                line = line.strip()
                if q == 0:
                    if line == 'loop_':
                        q = 1
                elif q == 1:
                    if line.startswith('_'):
                        colInfo.append(ColumnInfo(line[1:line.index(' #')],
                                                  dv.models.TYPE_STRING))
                    else:
                        model = dv.models.SimpleTableModel(colInfo)
                        model.addRow(line.split())
                        q = 2
                else:
                    model.addRow(line.split())

        if model is None and colInfo:
            model = dv.models.SimpleTableModel(colInfo)

        return model


if __name__ == '__main__':
    TestColumnsView().runApp()
