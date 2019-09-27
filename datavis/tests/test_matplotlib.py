#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import random

from datavis.widgets import PlotConfigWidget
from datavis.views import TableModel
from datavis.core import EmTable

from matplotlib.figure import Figure
from matplotlib.backends.qt_compat import QtCore, QtWidgets, is_pyqt5
if is_pyqt5():
    from matplotlib.backends.backend_qt5agg \
        import (FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
else:
    from matplotlib.backends.backend_qt4agg \
        import (FigureCanvas, NavigationToolbar2QT as NavigationToolbar)


path = '/media/pedro/Data/Work/Project/Repo/test-data/existing.star'
testDataPath = os.environ.get("EM_TEST_DATA", None)

# use the code below when yue have a properly configured environment
#if testDataPath is not None:
#    path = os.path.join(testDataPath, "relion_tutorial", "import", "classify2d",
#                        "extra", "existing.star")


class ApplicationWindow(QtWidgets.QMainWindow):
    def __init__(self, plotData, **kwargs):
        QtWidgets.QMainWindow.__init__(self)
        self._plotData = plotData
        self._leftContainer = QtWidgets.QWidget(self)
        self._plotConfigWidget = PlotConfigWidget(parent=self, **kwargs)
        self._plotConfigWidget.setMaximumWidth(
            self._plotConfigWidget.sizeHint().width())
        self._leftContainer.setMaximumWidth(
            self._plotConfigWidget.maximumWidth())
        self._plotConfigWidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                             QtWidgets.QSizePolicy.Expanding)
        self._plotConfigWidget.sigError.connect(self.__showMsgBox)
        layout = QtWidgets.QBoxLayout(QtWidgets.QBoxLayout.TopToBottom,
                                      self._leftContainer)
        layout.addWidget(self._plotConfigWidget)
        self._buttonPlot = QtWidgets.QPushButton(self)
        self._buttonPlot.setText('Plot')
        self._buttonPlot.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
                                       QtWidgets.QSizePolicy.Fixed)
        self._buttonPlot.clicked.connect(self.__onButtonPlotClicked)
        layout.addWidget(self._buttonPlot)
        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal, self)
        #  The Canvas
        self.__canvas = FigureCanvas(Figure(figsize=(5, 3)))
        self.__canvas.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                    QtWidgets.QSizePolicy.Expanding)

        splitter.addWidget(self._leftContainer)
        splitter.setCollapsible(0, False)
        splitter.addWidget(self.__canvas)
        self.setCentralWidget(splitter)
        self.addToolBar(QtCore.Qt.TopToolBarArea,
                        NavigationToolbar(self.__canvas, self))

    def __showMsgBox(self, text):
        """
        Show a message box with the given text, icon and details.
        The icon of the message box can be specified with one of the Qt values:
            QMessageBox.NoIcon
            QMessageBox.Question
            QMessageBox.Information
            QMessageBox.Warning
            QMessageBox.Critical
        """
        msgBox = QtWidgets.QMessageBox()
        msgBox.setText(text)
        msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msgBox.setDefaultButton(QtWidgets.QMessageBox.Ok)
        msgBox.exec_()

    def __plot(self, **kwargs):
        ax = self.__canvas.figure.add_subplot(111)
        ax.plot(self._plotData, 'r-')
        ax.set_title(kwargs.get('title', ""))
        self.__canvas.draw()

    def __onButtonPlotClicked(self):
        """ Invoked when the plot button is clicked """
        config = self._plotConfigWidget.getConfiguration()
        print('Plot configuration: ', config)
        if config is not None:
            scipion = os.environ.get('SCIPION_HOME', 'scipion')
            pwplot = os.path.join(scipion, 'pyworkflow', 'apps',
                                  'pw_plot.py')
            fileName = path
            plotConfig = config['config']
            params = config['params']
            plotType = plotConfig['plot-type']
            labels = ""
            colors = ""
            styles = ""
            markers = ""
            sortColumn = None
            for key in params.keys():
                p = params[key]
                labels += ' %s' % key
                colors += ' %s' % p['color']
                styles += ' %s' % p['line-style']
                markers += ' %s' % p['marker']
                if sortColumn is None:  # take the first key as sortColumn
                    sortColumn = key

            # sorted column
            if sortColumn is not None:
                sOrder = 'ASC'

            cmd = '%s --file %s --type %s --columns %s ' \
                  '--colors %s --styles %s --markers %s ' % \
                  (pwplot, fileName, plotType, labels, colors, styles,
                   markers)
            if sOrder is not None:
                cmd += ' --orderColumn %s --orderDir %s ' % (sortColumn,
                                                             sOrder)
            xLabel = plotConfig.get('x-label')
            yLabel = plotConfig.get('y-label')
            title = plotConfig.get('title')
            xAxis = plotConfig.get('x-axis')
            block = 'table-name'  # use the table name

            if xAxis:
                cmd += ' --xcolumn %s ' % xAxis
            if len(block):
                cmd += ' --block %s ' % block
            if title:
                cmd += ' --title %s ' % title
            if xLabel:
                cmd += ' --xtitle %s ' % xLabel
            if yLabel:
                cmd += ' --ytitle %s ' % yLabel
            if plotType == 'Histogram':
                cmd += ' --bins %d ' % plotConfig.get('bins', 0)

            print('Plot command: ', cmd)
            self.__plot(title=title)
        else:
            print("Invalid plot configuration")


qapp = QtWidgets.QApplication(sys.argv)

t = EmTable.load(path)
data = [random.random() for i in range(25)]
tableViewConfig = TableModel.fromTable(t[1])
#  We could pass the table instead of random data, but this is a test app.
#  Modify according to what you need
win = ApplicationWindow(data, params=[col.getName() for col in tableViewConfig])
win.resize(1200, 800)
win.show()
sys.exit(qapp.exec_())
