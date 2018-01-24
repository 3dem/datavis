# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QWidget, QMessageBox, QDialog
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QSize
from PyQt5.QtGui import QPainter


class WindowLevels(QWidget):
    # signal for window and level change
    windowLevelChanged = pyqtSignal(int, int)
    # Button "Reset" clicked signal
    resetWindowLevels = pyqtSignal()
    # Button "Auto" clicked signal
    autoWindowLevels = pyqtSignal()
    # Button "Set" clicked signal
    configNewWindowLevels = pyqtSignal()
    # Button "Apply" clicked signal
    applyWindowLevels = pyqtSignal()

    def __init__(self, parent=None):
        """
        Constructor

        @param parent reference to the parent widget
        @type QWidget
        """
        super(WindowLevels, self).__init__(parent)
        self.setupUi()
        # we need the last scoll values
        self.lastLevelValue = self.levelScroll.minimum() - 1
        self.lastWindowValue = self.windowScroll.minimum() - 1

        self.btnAuto.clicked.connect(self.autoWindowLevels)
        self.btnReset.clicked.connect(self.resetWindowLevels)
        self.btnSet.clicked.connect(self.configNewWindowLevels)

    def setupUi(self):
        self.setObjectName("WindowLevels")
        self.setMinimumSize(QtCore.QSize(230, 300))
        self.setMaximumSize(QtCore.QSize(230, 300))
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.histogramWidget = HistogramChart(self)
        self.histogramWidget.setMinimumSize(QSize(100, 80))
        self.histogramWidget.setStyleSheet(
            "background-color: rgb(166, 166, 166);")
        self.histogramWidget.setObjectName("histogramWidget")
        self.verticalLayout_2.addWidget(self.histogramWidget)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.formLayout = QtWidgets.QFormLayout()
        self.formLayout.setHorizontalSpacing(7)
        self.formLayout.setObjectName("formLayout")
        self.levelScroll = QtWidgets.QScrollBar(self)
        self.levelScroll.setOrientation(QtCore.Qt.Horizontal)
        self.levelScroll.setObjectName("levelScroll")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.SpanningRole,
                                  self.levelScroll)
        self.levelLavel = QtWidgets.QLabel(self)
        self.levelLavel.setObjectName("levelLavel")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole,
                                  self.levelLavel)
        self.levelLabelValue = QtWidgets.QLabel(self)
        self.levelLabelValue.setObjectName("levelLabelValue")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole,
                                  self.levelLabelValue)
        self.windowScroll = QtWidgets.QScrollBar(self)
        self.windowScroll.setOrientation(QtCore.Qt.Horizontal)
        self.windowScroll.setObjectName("windowScroll")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.SpanningRole,
                                  self.windowScroll)
        self.windowLabel = QtWidgets.QLabel(self)
        self.windowLabel.setObjectName("windowLabel")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.LabelRole,
                                  self.windowLabel)
        self.windowLabelValue = QtWidgets.QLabel(self)
        self.windowLabelValue.setObjectName("windowLabelValue")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.FieldRole,
                                  self.windowLabelValue)
        self.verticalLayout.addLayout(self.formLayout)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        spacerItem = QtWidgets.QSpacerItem(40, 20,
                                           QtWidgets.QSizePolicy.Expanding,
                                           QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setSpacing(2)
        self.gridLayout.setObjectName("gridLayout")
        self.btnAuto = QtWidgets.QPushButton(self)
        self.btnAuto.setObjectName("btnAuto")
        self.gridLayout.addWidget(self.btnAuto, 0, 0, 1, 1)
        self.btnReset = QtWidgets.QPushButton(self)
        self.btnReset.setObjectName("btnReset")
        self.gridLayout.addWidget(self.btnReset, 0, 1, 1, 1)
        self.btnSet = QtWidgets.QPushButton(self)
        self.btnSet.setObjectName("btnSet")
        self.gridLayout.addWidget(self.btnSet, 1, 0, 1, 1)
        self.btnApply = QtWidgets.QPushButton(self)
        self.btnApply.setObjectName("btnApply")
        self.gridLayout.addWidget(self.btnApply, 1, 1, 1, 1)
        self.horizontalLayout.addLayout(self.gridLayout)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20,
                                            QtWidgets.QSizePolicy.Expanding,
                                            QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem1)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.verticalLayout_2.addLayout(self.verticalLayout)
        self.btnApply.setVisible(False)
        self.dlgSetWCWW = None

        self.retranslateUi()
        QtCore.QMetaObject.connectSlotsByName(self)

    def retranslateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("WindowLevels", "WindowLevels"))
        self.levelLavel.setText(_translate("WindowLevels", "Level:"))
        self.levelLabelValue.setText(_translate("WindowLevels", "x"))
        self.windowLabel.setText(_translate("WindowLevels", "Window:"))
        self.windowLabelValue.setText(_translate("WindowLevels", "x"))
        self.btnAuto.setText(_translate("WindowLevels", "Auto"))
        self.btnReset.setText(_translate("WindowLevels", "Reset"))
        self.btnSet.setText(_translate("WindowLevels", "Set"))
        self.btnApply.setText(_translate("WindowLevels", "Apply"))

    def getHistogramWidget(self):
        return self.histogramWidget

    @pyqtSlot(int, int)
    def setWindowLevels(self, window, level):
        """
        Not emit windowLevelChanged signal
        """
        if self.lastWindowValue != window:
            self.lastWindowValue = window
            self.windowScroll.setValue(window)

        if self.lastLevelValue != level:
            self.lastLevelValue = level
            self.levelScroll.setValue(level)

    @pyqtSlot(int)
    def on_levelScroll_valueChanged(self, value):

        if self.lastLevelValue != value:
            self.lastLevelValue = value
            v = "%i" % value
            self.levelLabelValue.setText(v)
            self.windowLevelChanged.emit(self.windowScroll.value(), value)

    @pyqtSlot(int)
    def on_windowScroll_valueChanged(self, value):

        if self.lastWindowValue != value:
            self.lastWindowValue = value
            v = "%i" % value
            self.windowLabelValue.setText(v)
            self.windowLevelChanged.emit(value, self.levelScroll.value())

    @pyqtSlot()
    def on_btnSet_clicked(self):
        self.__createDlgWCWW__()
        self.dlgSetWCWW.show()

    def __createDlgWCWW__(self):
        if not self.dlgSetWCWW:
           self.dlgSetWCWW = WLDialog(self)
        hData = self.histogramWidget.getData()
        if hData:
            self.dlgSetWCWW.setLevelsRange(hData.getMin(), hData.getMax())

class WLDialog(QDialog):
    # emit this signal when user click Ok button
    newWindowLevel = pyqtSignal(int, int)

    def __init__(self, parent=None):
        """
        Constructor

        @param parent reference to the parent widget
        @type QWidget
        """
        super(WLDialog, self).__init__(parent)
        self.setupUi()

    def setWindowRange(self, min, max):
        self.spinBoxWW.setMinimum(min)
        self.spinBoxWW.setMaximum(max)

    def setLevelsRange(self, min, max):
        self.spinBoxWC.setMinimum(min)
        self.spinBoxWC.setMaximum(max)

    def initWindowLevel(self, window, level):
        self.spinBoxWC.setValue(window)
        self.spinBoxWW.setValue(level)

    def getWindowValue(self):
        return self.spinBoxWW.value()

    def getLevelValue(self):
        return self.spinBoxWC.value()

    def setupUi(self):
        self.setObjectName("WLDialog")
        self.setWindowModality(QtCore.Qt.WindowModal)
        self.resize(237, 119)
        self.setSizeGripEnabled(True)
        self.formLayout = QtWidgets.QFormLayout(self)
        self.formLayout.setObjectName("formLayout")
        self.label = QtWidgets.QLabel(self)
        self.label.setAlignment(
            QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter)
        self.label.setObjectName("label")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole,
                                  self.label)
        self.spinBoxWC = QtWidgets.QSpinBox(self)
        self.spinBoxWC.setObjectName("spinBoxWC")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole,
                                  self.spinBoxWC)
        self.label_2 = QtWidgets.QLabel(self)
        self.label_2.setAlignment(
            QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter)
        self.label_2.setObjectName("label_2")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole,
                                  self.label_2)
        self.spinBoxWW = QtWidgets.QSpinBox(self)
        self.spinBoxWW.setObjectName("spinBoxWW")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole,
                                  self.spinBoxWW)
        self.hboxlayout = QtWidgets.QHBoxLayout()
        self.hboxlayout.setContentsMargins(0, 0, 0, 0)
        self.hboxlayout.setSpacing(6)
        self.hboxlayout.setObjectName("hboxlayout")
        spacerItem = QtWidgets.QSpacerItem(131, 31,
                                           QtWidgets.QSizePolicy.Expanding,
                                           QtWidgets.QSizePolicy.Minimum)
        self.hboxlayout.addItem(spacerItem)
        self.okButton = QtWidgets.QPushButton(self)
        self.okButton.setObjectName("okButton")
        self.hboxlayout.addWidget(self.okButton)
        self.cancelButton = QtWidgets.QPushButton(self)
        self.cancelButton.setObjectName("cancelButton")
        self.hboxlayout.addWidget(self.cancelButton)
        self.formLayout.setLayout(2, QtWidgets.QFormLayout.SpanningRole,
                                  self.hboxlayout)

        self.retranslateUi()
        QtCore.QMetaObject.connectSlotsByName(self)

    def retranslateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("WLDialog", "Set W/L"))
        self.label.setText(_translate("WLDialog", "Window Center(Level):"))
        self.label_2.setText(_translate("WLDialog", "Window Width:"))
        self.okButton.setText(_translate("WLDialog", "&OK"))
        self.cancelButton.setText(_translate("WLDialog", "&Cancel"))

    @pyqtSlot()
    def on_okButton_clicked(self):
        self.newWindowLevel.emit(self.spinBoxWC.value(), self.spinBoxWW.value())
        self.close()

    @pyqtSlot()
    def on_cancelButton_clicked(self):
        self.close()

class BrightnessContrast(QWidget):
    """
    Class documentation goes here.
    """

    def __init__(self, parent=None):
        """
        Constructor

        @param parent reference to the parent widget
        @type QWidget
        """
        super(BrightnessContrast, self).__init__(parent)
        self.setupUi()

    def setupUi(self):
        self.setObjectName("BrightnessContrast")
        self.setMinimumSize(QtCore.QSize(230, 350))
        self.setMaximumSize(QtCore.QSize(230, 350))
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.histogramWidget = HistogramChart(self)
        self.histogramWidget.setMinimumSize(QSize(100, 80))
        self.histogramWidget.setObjectName("histogramWidget")
        self.verticalLayout_3.addWidget(self.histogramWidget)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setSpacing(2)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setSpacing(2)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.minLabelValue = QtWidgets.QLabel(self)
        self.minLabelValue.setObjectName("minLabelValue")
        self.horizontalLayout.addWidget(self.minLabelValue)
        self.maxLabelValue = QtWidgets.QLabel(self)
        self.maxLabelValue.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.maxLabelValue.setAlignment(
            QtCore.Qt.AlignRight | QtCore.Qt.AlignTrailing | QtCore.Qt.AlignVCenter)
        self.maxLabelValue.setObjectName("maxLabelValue")
        self.horizontalLayout.addWidget(self.maxLabelValue)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.minScroll = QtWidgets.QScrollBar(self)
        self.minScroll.setOrientation(QtCore.Qt.Horizontal)
        self.minScroll.setObjectName("minScroll")
        self.verticalLayout.addWidget(self.minScroll)
        self.label_3 = QtWidgets.QLabel(self)
        self.label_3.setAlignment(QtCore.Qt.AlignCenter)
        self.label_3.setObjectName("label_3")
        self.verticalLayout.addWidget(self.label_3)
        self.maxScroll = QtWidgets.QScrollBar(self)
        self.maxScroll.setOrientation(QtCore.Qt.Horizontal)
        self.maxScroll.setObjectName("maxScroll")
        self.verticalLayout.addWidget(self.maxScroll)
        self.label_4 = QtWidgets.QLabel(self)
        self.label_4.setAlignment(QtCore.Qt.AlignCenter)
        self.label_4.setObjectName("label_4")
        self.verticalLayout.addWidget(self.label_4)
        self.brightnessScroll = QtWidgets.QScrollBar(self)
        self.brightnessScroll.setOrientation(QtCore.Qt.Horizontal)
        self.brightnessScroll.setObjectName("brightnessScroll")
        self.verticalLayout.addWidget(self.brightnessScroll)
        self.label_5 = QtWidgets.QLabel(self)
        self.label_5.setAlignment(QtCore.Qt.AlignCenter)
        self.label_5.setObjectName("label_5")
        self.verticalLayout.addWidget(self.label_5)
        self.contrastScroll = QtWidgets.QScrollBar(self)
        self.contrastScroll.setOrientation(QtCore.Qt.Horizontal)
        self.contrastScroll.setObjectName("contrastScroll")
        self.verticalLayout.addWidget(self.contrastScroll)
        self.label_6 = QtWidgets.QLabel(self)
        self.label_6.setAlignment(QtCore.Qt.AlignCenter)
        self.label_6.setObjectName("label_6")
        self.verticalLayout.addWidget(self.label_6)
        self.verticalLayout_2.addLayout(self.verticalLayout)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        spacerItem = QtWidgets.QSpacerItem(40, 20,
                                           QtWidgets.QSizePolicy.Expanding,
                                           QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setSpacing(2)
        self.gridLayout.setObjectName("gridLayout")
        self.btnAuto = QtWidgets.QPushButton(self)
        self.btnAuto.setObjectName("btnAuto")
        self.gridLayout.addWidget(self.btnAuto, 0, 0, 1, 1)
        self.btnReset = QtWidgets.QPushButton(self)
        self.btnReset.setObjectName("btnReset")
        self.gridLayout.addWidget(self.btnReset, 0, 1, 1, 1)
        self.btnSet = QtWidgets.QPushButton(self)
        self.btnSet.setObjectName("btnSet")
        self.gridLayout.addWidget(self.btnSet, 1, 0, 1, 1)
        self.btnApply = QtWidgets.QPushButton(self)
        self.btnApply.setObjectName("btnApply")
        self.gridLayout.addWidget(self.btnApply, 1, 1, 1, 1)
        self.horizontalLayout_2.addLayout(self.gridLayout)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20,
                                            QtWidgets.QSizePolicy.Expanding,
                                            QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem1)
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)
        self.verticalLayout_3.addLayout(self.verticalLayout_2)

        self.retranslateUi()
        QtCore.QMetaObject.connectSlotsByName(self)

    def retranslateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(
            _translate("BrightnessContrast", "BrightnessContrast"))
        self.minLabelValue.setText(_translate("BrightnessContrast", "0"))
        self.maxLabelValue.setText(_translate("BrightnessContrast", "255"))
        self.label_3.setText(_translate("BrightnessContrast", "Minimum"))
        self.label_4.setText(_translate("BrightnessContrast", "Maximum"))
        self.label_5.setText(_translate("BrightnessContrast", "Brightness"))
        self.label_6.setText(_translate("BrightnessContrast", "Contrast"))
        self.btnAuto.setText(_translate("BrightnessContrast", "Auto"))
        self.btnReset.setText(_translate("BrightnessContrast", "Reset"))
        self.btnSet.setText(_translate("BrightnessContrast", "Set"))
        self.btnApply.setText(_translate("BrightnessContrast", "Apply"))

    def getHistogramWidget(self):
        return self.histogramWidget

    @pyqtSlot(int)
    def on_minScroll_sliderMoved(self, position):
        """
        Slot documentation goes here.

        @param position DESCRIPTION
        @type int
        """
        # TODO: not implemented yet
        raise NotImplementedError

    @pyqtSlot(int)
    def on_maxScroll_sliderMoved(self, position):
        """
        Slot documentation goes here.

        @param position DESCRIPTION
        @type int
        """
        # TODO: not implemented yet
        raise NotImplementedError

    @pyqtSlot(int)
    def on_brightnessScroll_sliderMoved(self, position):
        """
        Slot documentation goes here.

        @param position DESCRIPTION
        @type int
        """
        # TODO: not implemented yet
        raise NotImplementedError

    @pyqtSlot(int)
    def on_contrastScroll_sliderMoved(self, position):
        """
        Slot documentation goes here.

        @param position DESCRIPTION
        @type int
        """
        # TODO: not implemented yet
        raise NotImplementedError

    @pyqtSlot()
    def on_btnAuto_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        raise NotImplementedError

    @pyqtSlot()
    def on_btnReset_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        raise NotImplementedError

    @pyqtSlot()
    def on_btnSet_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        raise NotImplementedError

    @pyqtSlot()
    def on_btnApply_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        raise NotImplementedError


class HistogramData:
    """
    """

    def __init__(self):
        # int array of pixel values
        self.data = None
        self.min = 0
        self.max = 0

    def setData(self, intArray):
        self.data = intArray

    def setMin(self, minValue):
        self.min = minValue

    def setMax(self, maxValue):
        self.max = maxValue

    def getData(self):
        return self.data

    def getMin(self):
        return self.min

    def getMax(self):
        return self.max

    def calcMinMax(self):
        self.min = -1
        self.max = -1
        for i in range(0, len(self.data), 1):
            if self.data[i] < self.min:
                self.min = self.data[i]
            elif self.data[i] > self.max:
                self.max = self.data[i]


class HistogramChart(QWidget):
    def __init__(self, parent):
        super(HistogramChart, self).__init__(parent)
        self.histogramData = None
        self.painter = QPainter()
        self.borderColor = QtCore.Qt.black
        self.graphColor = QtCore.Qt.gray
        self.setMinimumSize(QSize(208, 129))

    def setData(self, histogramData):
        self.histogramData = histogramData

    def setGraphColor(self, qcolor):
        self.graphColor = qcolor

    def setBorderColor(self, qcolor):
        self.borderColor = qcolor

    def getData(self):
        return self.histogramData

    def paintEvent(self, event):
        self.painter.begin(self)
        self.painter.setPen(QtGui.QPen(self.borderColor, 1))
        self.painter.drawRect(0, 0, self.width() - 1, self.height() - 1)

        if self.histogramData:
            width = self.width()
            height = self.height()
            max = self.histogramData.getMax()
            # set color and width of line drawing pen
            self.painter.setPen(QtGui.QPen(QtCore.Qt.black, 2))
            # draw the baseline
            self.painter.drawLine(0, height, width, height)
            # color and width of the bars
            lineWidth = width / len(self.histogramData.getData())
            lineHeight = height / max

            self.painter.setPen(QtGui.QPen(self.graphColor, lineWidth))

            x = 0
            for pixelValue in self.histogramData.getData():
                y = height - (pixelValue * lineHeight)
                self.painter.drawLine(x, height, x, y)
                x += lineWidth
        else:
            self.painter.drawText(5, self.height() / 2, "HistogramChart")

        self.painter.end()

