# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'E:\Work\Project\example\Jose\ImageView\MainWindow.ui'
#
# Created by: PyQt5 UI code generator 5.6
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(984, 769)
        self.centralWidget = QtWidgets.QWidget(MainWindow)
        self.centralWidget.setObjectName("centralWidget")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout(self.centralWidget)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.tabWidget = QtWidgets.QTabWidget(self.centralWidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tabWidget.sizePolicy().hasHeightForWidth())
        self.tabWidget.setSizePolicy(sizePolicy)
        self.tabWidget.setMinimumSize(QtCore.QSize(290, 0))
        self.tabWidget.setMouseTracking(True)
        self.tabWidget.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.tabWidget.setTabPosition(QtWidgets.QTabWidget.West)
        self.tabWidget.setTabShape(QtWidgets.QTabWidget.Triangular)
        self.tabWidget.setElideMode(QtCore.Qt.ElideNone)
        self.tabWidget.setObjectName("tabWidget")
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.tab)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.verticalLayout_11 = QtWidgets.QVBoxLayout()
        self.verticalLayout_11.setObjectName("verticalLayout_11")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.formLayout = QtWidgets.QFormLayout()
        self.formLayout.setLabelAlignment(QtCore.Qt.AlignCenter)
        self.formLayout.setFormAlignment(QtCore.Qt.AlignHCenter|QtCore.Qt.AlignTop)
        self.formLayout.setObjectName("formLayout")
        self.verticalLayout_5 = QtWidgets.QVBoxLayout()
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.label = QtWidgets.QLabel(self.tab)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setObjectName("label")
        self.verticalLayout_5.addWidget(self.label)
        self.horizontalSlider = QtWidgets.QSlider(self.tab)
        self.horizontalSlider.setMaximum(360)
        self.horizontalSlider.setPageStep(1)
        self.horizontalSlider.setOrientation(QtCore.Qt.Horizontal)
        self.horizontalSlider.setObjectName("horizontalSlider")
        self.verticalLayout_5.addWidget(self.horizontalSlider)
        self.formLayout.setLayout(0, QtWidgets.QFormLayout.LabelRole, self.verticalLayout_5)
        self.verticalLayout_6 = QtWidgets.QVBoxLayout()
        self.verticalLayout_6.setObjectName("verticalLayout_6")
        self.label_2 = QtWidgets.QLabel(self.tab)
        self.label_2.setAlignment(QtCore.Qt.AlignCenter)
        self.label_2.setObjectName("label_2")
        self.verticalLayout_6.addWidget(self.label_2)
        self.horizontalSlider_2 = QtWidgets.QSlider(self.tab)
        self.horizontalSlider_2.setMinimum(-100)
        self.horizontalSlider_2.setMaximum(100)
        self.horizontalSlider_2.setSingleStep(1)
        self.horizontalSlider_2.setPageStep(1)
        self.horizontalSlider_2.setOrientation(QtCore.Qt.Horizontal)
        self.horizontalSlider_2.setObjectName("horizontalSlider_2")
        self.verticalLayout_6.addWidget(self.horizontalSlider_2)
        self.formLayout.setLayout(1, QtWidgets.QFormLayout.LabelRole, self.verticalLayout_6)
        self.groupBox = QtWidgets.QGroupBox(self.tab)
        self.groupBox.setAlignment(QtCore.Qt.AlignCenter)
        self.groupBox.setObjectName("groupBox")
        self.verticalLayout_7 = QtWidgets.QVBoxLayout(self.groupBox)
        self.verticalLayout_7.setObjectName("verticalLayout_7")
        self.VerticalFlipsButton = QtWidgets.QPushButton(self.groupBox)
        self.VerticalFlipsButton.setObjectName("VerticalFlipsButton")
        self.verticalLayout_7.addWidget(self.VerticalFlipsButton)
        self.HorizontalFlipsButton = QtWidgets.QPushButton(self.groupBox)
        self.HorizontalFlipsButton.setObjectName("HorizontalFlipsButton")
        self.verticalLayout_7.addWidget(self.HorizontalFlipsButton)
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.groupBox)
        self.FitToSizeCheckBox = QtWidgets.QCheckBox(self.tab)
        self.FitToSizeCheckBox.setObjectName("FitToSizeCheckBox")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.LabelRole, self.FitToSizeCheckBox)
        self.pushButton = QtWidgets.QPushButton(self.tab)
        self.pushButton.setEnabled(False)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.pushButton.sizePolicy().hasHeightForWidth())
        self.pushButton.setSizePolicy(sizePolicy)
        self.pushButton.setObjectName("pushButton")
        self.formLayout.setWidget(5, QtWidgets.QFormLayout.LabelRole, self.pushButton)
        self.pushButtonAddRect = QtWidgets.QPushButton(self.tab)
        self.pushButtonAddRect.setObjectName("pushButtonAddRect")
        self.formLayout.setWidget(4, QtWidgets.QFormLayout.LabelRole, self.pushButtonAddRect)
        self.horizontalLayout_2.addLayout(self.formLayout)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem1)
        self.verticalLayout_11.addLayout(self.horizontalLayout_2)
        spacerItem2 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout_11.addItem(spacerItem2)
        self.verticalLayout_2.addLayout(self.verticalLayout_11)
        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.layoutWidget = QtWidgets.QWidget(self.tab_2)
        self.layoutWidget.setGeometry(QtCore.QRect(2, 10, 261, 711))
        self.layoutWidget.setObjectName("layoutWidget")
        self.verticalLayout_8 = QtWidgets.QVBoxLayout(self.layoutWidget)
        self.verticalLayout_8.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_8.setObjectName("verticalLayout_8")
        self.tabWidget.addTab(self.tab_2, "")
        self.tab_3 = QtWidgets.QWidget()
        self.tab_3.setObjectName("tab_3")
        self.tabWidget.addTab(self.tab_3, "")
        self.horizontalLayout.addWidget(self.tabWidget)
        self.widget = QtWidgets.QWidget(self.centralWidget)
        self.widget.setObjectName("widget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.widget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.verticalLayout_4 = QtWidgets.QVBoxLayout()
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.verticalLayout.addLayout(self.verticalLayout_4)
        self.horizontalLayout.addWidget(self.widget)
        self.verticalLayout_3.addLayout(self.horizontalLayout)
        MainWindow.setCentralWidget(self.centralWidget)
        self.menuBar = QtWidgets.QMenuBar(MainWindow)
        self.menuBar.setGeometry(QtCore.QRect(0, 0, 984, 26))
        self.menuBar.setObjectName("menuBar")
        self.menuFile = QtWidgets.QMenu(self.menuBar)
        self.menuFile.setObjectName("menuFile")
        self.menuTools = QtWidgets.QMenu(self.menuBar)
        self.menuTools.setObjectName("menuTools")
        MainWindow.setMenuBar(self.menuBar)
        self.actionOpen = QtWidgets.QAction(MainWindow)
        self.actionOpen.setObjectName("actionOpen")
        self.actionExit = QtWidgets.QAction(MainWindow)
        self.actionExit.setObjectName("actionExit")
        self.actionRigth_Rotation = QtWidgets.QAction(MainWindow)
        self.actionRigth_Rotation.setObjectName("actionRigth_Rotation")
        self.actionLeft_Rotation = QtWidgets.QAction(MainWindow)
        self.actionLeft_Rotation.setObjectName("actionLeft_Rotation")
        self.actionFlip_Vertical = QtWidgets.QAction(MainWindow)
        self.actionFlip_Vertical.setObjectName("actionFlip_Vertical")
        self.actionFlip_Horizontal = QtWidgets.QAction(MainWindow)
        self.actionFlip_Horizontal.setObjectName("actionFlip_Horizontal")
        self.actionZoom_In = QtWidgets.QAction(MainWindow)
        self.actionZoom_In.setObjectName("actionZoom_In")
        self.actionZoom_Out = QtWidgets.QAction(MainWindow)
        self.actionZoom_Out.setObjectName("actionZoom_Out")
        self.actionMove = QtWidgets.QAction(MainWindow)
        self.actionMove.setObjectName("actionMove")
        self.actionFit_to_Size = QtWidgets.QAction(MainWindow)
        self.actionFit_to_Size.setObjectName("actionFit_to_Size")
        self.actionLoad_Raw_Data = QtWidgets.QAction(MainWindow)
        self.actionLoad_Raw_Data.setObjectName("actionLoad_Raw_Data")
        self.actionSave_As_Raw_Data = QtWidgets.QAction(MainWindow)
        self.menuFile.addAction(self.actionOpen)
        self.menuFile.addAction(self.actionLoad_Raw_Data)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionExit)
        self.menuTools.addAction(self.actionZoom_In)
        self.menuTools.addAction(self.actionZoom_Out)
        self.menuTools.addSeparator()
        self.menuTools.addAction(self.actionRigth_Rotation)
        self.menuTools.addAction(self.actionLeft_Rotation)
        self.menuTools.addSeparator()
        self.menuTools.addAction(self.actionFlip_Vertical)
        self.menuTools.addAction(self.actionFlip_Horizontal)
        self.menuTools.addSeparator()
        self.menuTools.addAction(self.actionMove)
        self.menuTools.addAction(self.actionFit_to_Size)
        self.menuBar.addAction(self.menuFile.menuAction())
        self.menuBar.addAction(self.menuTools.menuAction())

        self.retranslateUi(MainWindow)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.label.setText(_translate("MainWindow", "Rotation"))
        self.label_2.setText(_translate("MainWindow", "Zoom"))
        self.groupBox.setTitle(_translate("MainWindow", "Flips"))
        self.VerticalFlipsButton.setText(_translate("MainWindow", "Vertical"))
        self.HorizontalFlipsButton.setText(_translate("MainWindow", "Horizontal"))
        self.FitToSizeCheckBox.setText(_translate("MainWindow", "Fit To Size"))
        self.pushButton.setText(_translate("MainWindow", "Reset Transformations"))
        self.pushButtonAddRect.setText(_translate("MainWindow", "AddRect"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), _translate("MainWindow", "Transformations"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _translate("MainWindow", "Setting"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_3), _translate("MainWindow", "Page"))
        self.menuFile.setTitle(_translate("MainWindow", "File"))
        self.menuTools.setTitle(_translate("MainWindow", "Tools"))
        self.actionOpen.setText(_translate("MainWindow", "Open"))
        self.actionExit.setText(_translate("MainWindow", "Exit"))
        self.actionRigth_Rotation.setText(_translate("MainWindow", "Rigth Rotation"))
        self.actionLeft_Rotation.setText(_translate("MainWindow", "Left Rotation"))
        self.actionFlip_Vertical.setText(_translate("MainWindow", "Flip Vertical"))
        self.actionFlip_Horizontal.setText(_translate("MainWindow", "Flip Horizontal"))
        self.actionZoom_In.setText(_translate("MainWindow", "Zoom In"))
        self.actionZoom_Out.setText(_translate("MainWindow", "Zoom Out"))
        self.actionMove.setText(_translate("MainWindow", "Move"))
        self.actionFit_to_Size.setText(_translate("MainWindow", "Fit to Size"))
        self.actionLoad_Raw_Data.setText(_translate("MainWindow", "Load Raw Data"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())

