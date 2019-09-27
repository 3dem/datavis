#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import PyQt5.QtWidgets as qtw
import PyQt5.QtCore as qtc

from datavis.core import ModelsFactory
from datavis.views import ColumnsView
from test_commons import TestView


class MultiColumnsView(ColumnsView):

    def _createContentWidget(self):
        """ Should be implemented in subclasses to build the content widget
        and return it. """
        content = qtw.QWidget(parent=self)
        layout = qtw.QHBoxLayout(content)
        layout.setSpacing(10)
        layout.setContentsMargins(1, 1, 1, 1)
        content.setLayout(layout)

        # Add first a combobox with all possible tables
        label = qtw.QLabel('Tables: ')
        layout.addWidget(label)
        combo = qtw.QComboBox(parent=content)
        combo.setGeometry(qtc.QRect(40, 40, 491, 31))
        for tableName in self._model.getTableNames():
            combo.addItem(tableName)
        layout.addWidget(combo)
        combo.activated[str].connect(self.onChanged)
        # Add the content of the ColumnsView
        cvWidget = ColumnsView._createContentWidget(self)
        layout.addWidget(cvWidget)

        return content

    def onChanged(self, text):
        self._model.loadTable(text)
        self.setModel(self._model)


class TestMultiColumnsView(TestView):
    """ This is a very simple test that illustrate how to create a new View,
    that is basically a ColumnsView, but adding the possibility to load other
    tables.
    """
    __title = "Multi-ColumnsView example"

    def getDataPaths(self):
        return [
            self.getPath("relion_tutorial", "import", "refine3d", "extra",
                         "relion_it001_half2_model.star")
        ]

    def createView(self):
        return MultiColumnsView(model=ModelsFactory.createTableModel(self._path))


if __name__ == '__main__':
    TestMultiColumnsView().runApp()
