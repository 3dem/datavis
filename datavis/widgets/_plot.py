
import qtawesome as qta

import PyQt5.QtCore as qtc
import PyQt5.QtWidgets as qtw
import PyQt5.QtGui as qtg

from ._delegates import (ColorItemDelegate, ComboBoxStyleItemDelegate,
                         ColumnPropertyItemDelegate)


class PlotConfigWidget(qtw.QWidget):
    """ The plot configuration widget """

    """ 
    This signal is emitted when the current configuration contains errors
    emit(str:error)     
    """
    # TODO[hv] emit error code, not str message
    sigError = qtc.pyqtSignal(str)

    def __init__(self, parent=None, **kwargs):
        """
        kwargs:
          params (str list): The rows for the configuration table
          colors (str list): The initial colors for params ('#FF34AA')
          styles (str list): The styles for user selection
                             ['solid', 'dashed', 'dotted', ...]
          markers (str list): The markers for user selection
                             ['none', '.', ',', 'o', ...]
          plot-types (str list): The plot types
                                 ['Plot', 'Histogram', 'Scatter']
        """
        qtw.QWidget.__init__(self, parent=parent)
        self.__params = kwargs.get('params', [])
        self.__markers = kwargs.get('markers', ["none", ".", ",", "o", "v", "^",
                                                "<", ">", "1", "2", "3", "4",
                                                "s", "p", "h", "H", "+", "x",
                                                "D", "d", "|", "_"])
        self.__styles = kwargs.get('styles', ['solid', 'dashed', 'dotted'])
        self.__colors = kwargs.get('colors', [qtc.Qt.blue, qtc.Qt.green, 
                                              qtc.Qt.red, qtc.Qt.black, 
                                              qtc.Qt.darkYellow, qtc.Qt.yellow, 
                                              qtc.Qt.magenta, qtc.Qt.cyan])
        self.__plotTypes = kwargs.get('plot-types',
                                      ['Plot', 'Histogram', 'Scatter'])
        self.__markerDelegate = \
            ComboBoxStyleItemDelegate(parent=self,
                                      values=self.__markers)
        self.__lineStyleDelegate = \
            ComboBoxStyleItemDelegate(
                parent=self, values=[stl.capitalize() for stl in self.__styles])
        self.__colorDelegate = ColorItemDelegate(parent=self)
        checkedIcon = qta.icon('fa5s.file-signature')
        unCheckedIcon = qta.icon('fa5s.file-signature', color='#d4d4d4')
        self.__checkDelegate = \
            ColumnPropertyItemDelegate(self, checkedIcon.pixmap(16).toImage(),
                                       unCheckedIcon.pixmap(16).toImage())
        self.__setupUi()
        self.__initPlotConfWidgets()

    def __setupUi(self):
        vLayout = qtw.QVBoxLayout(self)
        formLayout = qtw.QFormLayout()
        formLayout.setLabelAlignment(
            qtc.Qt.AlignRight | qtc.Qt.AlignTrailing | qtc.Qt.AlignVCenter)
        formLayout.setWidget(0, qtw.QFormLayout.LabelRole,
                             qtw.QLabel(text='Title: ', parent=self))
        self._lineEditPlotTitle = qtw.QLineEdit(parent=self)
        self._lineEditPlotTitle.setSizePolicy(qtw.QSizePolicy.Expanding,
                                              qtw.QSizePolicy.Preferred)
        formLayout.setWidget(0, qtw.QFormLayout.FieldRole, self._lineEditPlotTitle)
        formLayout.setWidget(1, qtw.QFormLayout.LabelRole,
                             qtw.QLabel(text='X label: ', parent=self))
        self._lineEditXlabel = qtw.QLineEdit(parent=self)
        formLayout.setWidget(1, qtw.QFormLayout.FieldRole,
                             self._lineEditXlabel)
        formLayout.setWidget(2, qtw.QFormLayout.LabelRole,
                             qtw.QLabel(text='Y label: ', parent=self))
        self._lineEditYlabel = qtw.QLineEdit(parent=self)
        formLayout.setWidget(2, qtw.QFormLayout.FieldRole, self._lineEditYlabel)
        formLayout.setWidget(3, qtw.QFormLayout.LabelRole,
                             qtw.QLabel(text='Type: ', parent=self))
        self._comboBoxPlotType = qtw.QComboBox(parent=self)
        for plotType in self.__plotTypes:
            self._comboBoxPlotType.addItem(plotType)

        self._comboBoxPlotType.currentIndexChanged.connect(
            self.__onCurrentPlotTypeChanged)

        formLayout.setWidget(3, qtw.QFormLayout.FieldRole, self._comboBoxPlotType)
        self._labelBins = qtw.QLabel(parent=self)
        self._labelBins.setText('Bins')
        self._lineEditBins = qtw.QLineEdit(self)
        self._lineEditBins.setText('50')
        formLayout.setWidget(4, qtw.QFormLayout.LabelRole, self._labelBins)
        formLayout.setWidget(4, qtw.QFormLayout.FieldRole, self._lineEditBins)
        self._labelBins.setVisible(False)
        self._lineEditBins.setVisible(False)
        self._lineEditBins.setFixedWidth(80)
        self._lineEditBins.setValidator(qtg.QIntValidator())
        formLayout.setWidget(5, qtw.QFormLayout.LabelRole,
                             qtw.QLabel(text='X Axis: ', parent=self))
        self._comboBoxXaxis = qtw.QComboBox(parent=self)
        self._comboBoxXaxis.currentIndexChanged.connect(
            self.__onCurrentXaxisChanged)
        formLayout.setWidget(5, qtw.QFormLayout.FieldRole, self._comboBoxXaxis)
        vLayout.addLayout(formLayout)
        label = qtw.QLabel(parent=self,
                       text="<strong>Plot columns:</strong>")
        label.setSizePolicy(qtw.QSizePolicy.Expanding, qtw.QSizePolicy.Fixed)
        vLayout.addWidget(label, 0, qtc.Qt.AlignLeft)
        self._tablePlotConf = qtw.QTableWidget(self)
        self._tablePlotConf.setObjectName("tablePlotConf")
        self._tablePlotConf.setSelectionMode(qtw.QTableWidget.NoSelection)
        self._tablePlotConf.setSelectionBehavior(qtw.QTableWidget.SelectRows)
        self._tablePlotConf.setFocusPolicy(qtc.Qt.NoFocus)
        self._tablePlotConf.setMinimumSize(self._tablePlotConf.sizeHint())
        self._tablePlotConf.setSizePolicy(qtw.QSizePolicy.Expanding,
                                          qtw.QSizePolicy.Expanding)
        self._tablePlotConf.setColumnCount(5)
        self._tablePlotConf.setHorizontalHeaderLabels(['Label', 'Plot',
                                                       'Color', 'Line Style',
                                                       'Marker'])
        self._tablePlotConf.setItemDelegateForColumn(1, self.__checkDelegate)
        self._tablePlotConf.setItemDelegateForColumn(
            2, ColorItemDelegate(parent=self._tablePlotConf))
        self._tablePlotConf.setItemDelegateForColumn(
            3, self.__lineStyleDelegate)
        self._tablePlotConf.setItemDelegateForColumn(
            4, self.__markerDelegate)
        self._tablePlotConf.verticalHeader().setVisible(False)
        self._tablePlotConf.setEditTriggers(qtw.QTableWidget.AllEditTriggers)

        vLayout.addWidget(self._tablePlotConf)

    def __initPlotConfWidgets(self):
        """ Initialize the plot configurations widgets """
        self._comboBoxXaxis.clear()
        self._comboBoxXaxis.addItem(" ")
        self._tablePlotConf.clearContents()
        row = 0
        self._tablePlotConf.setRowCount(len(self.__params))
        nColors = len(self.__colors)

        for i, colName in enumerate(self.__params):
            self._comboBoxXaxis.addItem(colName)
            item = qtw.QTableWidgetItem(colName)
            item.setFlags(qtc.Qt.ItemIsEnabled)
            itemPlot = qtw.QTableWidgetItem("")  # for plot option
            itemPlot.setCheckState(qtc.Qt.Unchecked)
            itemColor = qtw.QTableWidgetItem("")  # for color option
            itemColor.setData(qtc.Qt.BackgroundRole,
                              qtg.QColor(self.__colors[i % nColors]))
            itemLineStye = qtw.QTableWidgetItem("")  # for line style option
            itemLineStye.setData(qtc.Qt.DisplayRole,
                                 self.__styles[0].capitalize())
            itemLineStye.setData(qtc.Qt.UserRole, 0)
            itemMarker = qtw.QTableWidgetItem("")  # for marker option
            itemMarker.setData(qtc.Qt.DisplayRole, self.__markers[0])
            itemMarker.setData(qtc.Qt.UserRole, 0)
            self._tablePlotConf.setItem(row, 0, item)
            self._tablePlotConf.setItem(row, 1, itemPlot)
            self._tablePlotConf.setItem(row, 2, itemColor)
            self._tablePlotConf.setItem(row, 3, itemLineStye)
            self._tablePlotConf.setItem(row, 4, itemMarker)
            row += 1

        self._tablePlotConf.resizeColumnsToContents()
        self._tablePlotConf.horizontalHeader().setStretchLastSection(True)

    def __getSelectedPlotProperties(self):
        """
        Return a dict with all plot properties for each row (param).
        Example:
             {
                'param1': {
                           'color': '#4565FF',
                           'line-style': 'dashed',
                           'marker':'o'
                          }
                ...
                param-n
             }
        """
        ret = dict()
        for i in range(self._tablePlotConf.rowCount()):
            if self._tablePlotConf.item(i, 1).checkState() == qtc.Qt.Checked:
                p = dict()
                p['color'] = self._tablePlotConf.item(i, 2).data(
                    qtc.Qt.BackgroundRole).name()
                p['line-style'] = self._tablePlotConf.item(i, 3).text().lower()
                p['marker'] = self._tablePlotConf.item(i, 4).text()
                ret[self.__params[i]] = p

        return ret

    @qtc.pyqtSlot()
    def __onCurrentPlotTypeChanged(self):
        """ Invoked when the current plot type is changed """
        visible = self._comboBoxPlotType.currentText() == 'Histogram'
        self._labelBins.setVisible(visible)
        self._lineEditBins.setVisible(visible)

    @qtc.pyqtSlot()
    def __onCurrentXaxisChanged(self):
        """
        Invoked when the current x axis is changed configuring the plot
        operations
        """
        self._lineEditXlabel.setText(self._comboBoxXaxis.currentText())

    def setParams(self, params=[], **kwargs):
        """ Initialize the configuration parameters """
        self.__params = params
        self.__markers = kwargs.get('markers', self.__markers)
        self.__styles = kwargs.get('styles', self.__styles)
        self.__colors = kwargs.get('colors', self.__colors)
        self.__plotTypes = kwargs.get('plot-types', self.__plotTypes)
        self.__initPlotConfWidgets()

    def setTitleText(self, text):
        """ Sets the title label text """
        self._titleLabel.setText(text)

    def getConfiguration(self):
        """
        Return a dict with the configuration parameters or None
        for invalid configuration.
        emit sigError
        dict: {
        'params': {
                    'param1': {
                               'color': '#4565FF',
                               'line-style': 'dashed',
                               'marker':'o'
                              }
                    ...
                    param-n
                  }
        'config':{
                  'title': 'Plot title',
                  'x-label': 'xlabel',
                  'y-label': 'ylabel',
                  'plot-type': 'Plot' or 'Histogram' or 'Scatter',
                  'x-axis': 'x-axis',
                  'bins': int (if type=Histogram)
                 }
        }
        """
        plotProp = self.__getSelectedPlotProperties()
        if len(plotProp) > 0:
            config = dict()
            plotType = self._comboBoxPlotType.currentText()
            config['plot-type'] = plotType

            xLabel = self._lineEditXlabel.text().strip()
            yLabel = self._lineEditYlabel.text().strip()
            title = self._lineEditPlotTitle.text().strip()
            xAxis = self._comboBoxXaxis.currentText().strip()

            if len(xAxis):
                config['x-axis'] = xAxis
            if len(title):
                config['title'] = title
            if len(xLabel):
                config['x-label'] = xLabel
            if len(yLabel):
                config['y-label'] = yLabel
            if plotType == 'Histogram':
                bins = self._lineEditBins.text().strip()
                if len(bins):
                    config['bins'] = int(self._lineEditBins.text())
                else:
                    self.sigError.emit('Invalid bins value')
                    return None
            ret = dict()
            ret['params'] = plotProp
            ret['config'] = config
            return ret
        else:
            self.sigError.emit('No columns selected for plotting')
            return None

    def sizeHint(self):
        """ Reimplemented from QWidget """
        s = qtw.QWidget.sizeHint(self)
        w = 4 * self.layout().contentsMargins().left()
        for column in range(self._tablePlotConf.columnCount()):
            w += self._tablePlotConf.columnWidth(column)
        s.setWidth(w)
        return s

