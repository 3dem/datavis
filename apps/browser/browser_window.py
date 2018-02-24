#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import numpy as np

from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QFrame, QSizePolicy,
                             QSplitter, QTreeView,
                             QFileSystemModel, QLineEdit, QVBoxLayout,
                             QListWidget, QMainWindow, QMenuBar, QMenu,
                             QAction, QToolBar, QLabel)
from PyQt5.QtCore import Qt, QDir, QCoreApplication, QMetaObject, pyqtSlot
from PyQt5.QtGui import QIcon, QPixmap
import pyqtgraph as pg
import qtawesome as qta

import em


class BrowserWindow(QMainWindow):
    """
    Declaration of the class Browser
    This class construct a Browser User Interface
    """
    def __init__(self, parent=None, **kwargs):
        super(QMainWindow, self).__init__(parent)
        self._initGUI()

    @pyqtSlot()
    def on_actionExit_triggered(self):
        """
        This Slot is executed when a exit signal was fire. The application is
        terminate
        """
        import sys
        sys.exit()

    def _onPathDoubleClick(self, signal):
        """
        This slot is executed when the action "double click"  inside the tree
        view is realized. The tree view path change
        :param signal: double clicked signal
        """
        file_path = self.model.filePath(signal)
        self.setLineCompleter(file_path)

    def _onPathClick(self, signal):
        """
        This slot is executed when the action "click" inside the tree view
        is realized. The tree view path change
        :param signal: clicked signal
        """
        file_path = self.model.filePath(signal)
        self.setLineCompleter(file_path)
        self.imagePlot(file_path)

    def _initGUI(self):
        self.centralWidget = QWidget(self)
        self.horizontalLayout = QHBoxLayout(self.centralWidget)
        self.splitter = QSplitter(self.centralWidget)
        self.splitter.setOrientation(Qt.Horizontal)
        self.widget = QWidget(self.splitter)

        self.verticalLayout_4 = QVBoxLayout(self.widget)
        self.verticalLayout = QVBoxLayout()

        # Create a line edit to handle a path completer
        completerLayoutWidget = QWidget(self.widget)
        horizontalLayout = QHBoxLayout(completerLayoutWidget)

        self.label = QLabel(completerLayoutWidget)
        horizontalLayout.addWidget(self.label)

        self.lineCompleter = QLineEdit(completerLayoutWidget)
        horizontalLayout.addWidget(self.lineCompleter)
        self.verticalLayout.addWidget(completerLayoutWidget)
        self.verticalLayout_4.addLayout(completerLayoutWidget.layout())

        # Create a Tree View
        self.treeView = QTreeView(self.widget)
        self.verticalLayout.addWidget(self.treeView)
        self.treeView.clicked.connect(self._onPathClick)

        self.verticalLayout_4.addLayout(self.verticalLayout)

        # Create right Panel
        self.widget_2 = QWidget(self.splitter)
        self.verticalLayout_3 = QVBoxLayout(self.widget_2)
        self.verticalLayout_2 = QVBoxLayout()

        self.frame = QFrame(self.widget_2)
        sizePolicy = QSizePolicy(QSizePolicy.MinimumExpanding,
                                 QSizePolicy.MinimumExpanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frame.sizePolicy().hasHeightForWidth())
        self.frame.setSizePolicy(sizePolicy)
        self.frame.setFrameShape(QFrame.Box)
        self.frame.setFrameShadow(QFrame.Raised)

        self.imageLayout = QHBoxLayout(self.frame)
        self.listWidget = QListWidget(self.widget_2)

        self.verticalLayout_2.addWidget(self.frame)
        self.verticalLayout_2.addWidget(self.listWidget)

        self.verticalLayout_3.addLayout(self.verticalLayout_2)
        self.horizontalLayout.addWidget(self.splitter)
        self.setCentralWidget(self.centralWidget)

        # Create a Menu Bar
        self.menuBar = QMenuBar(self)
        self.menuBar.setObjectName("menuBar")
        self.menuFile = QMenu(self.menuBar)
        self.menuFile.setObjectName("menuFile")
        self.setMenuBar(self.menuBar)
        self.actionExit = QAction(self)
        self.actionExit.setObjectName("actionExit")
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionExit)
        self.menuBar.addAction(self.menuFile.menuAction())

        # Create a Tool Bar
        self.toolBar = QToolBar(self)
        self.addToolBar(Qt.TopToolBarArea, self.toolBar)

        def _addAction(iconName):
            action = QAction(self)
            action.setIcon(qta.icon(iconName))
            self.toolBar.addAction(action)
            return action

        self.homeAction = _addAction('fa.home')
        self.refreshAction = _addAction('fa.arrow-up')
        self.folderUpAction = _addAction('fa.refresh')

        # Create and define the file system model
        self.model = QFileSystemModel()
        # filters = []
        # filters.append("*.mrc")
        # self.model.setNameFilters(filters)
        # self.model.setNameFilterDisables(False)
        rootPath = QDir.homePath()
        self.lineCompleter.setText(QDir.homePath())
        self.model.setRootPath(rootPath)
        self.treeView.setModel(self.model)
        self.treeView.setRootIndex(self.model.index(rootPath))
        self.treeView.setSortingEnabled(True)
        self.treeView.resize(640, 380)

        self.retranslateUi()
        QMetaObject.connectSlotsByName(self)

        # Show the Main Window
        self.setGeometry(200, 100, 900, 600)
        self.setWindowTitle('EM-Browser')
        self.show()

    def retranslateUi(self):
        _translate = QCoreApplication.translate
        self.setWindowTitle(_translate("MainWindow", "Browser"))
        self.menuFile.setTitle(_translate("MainWindow", "File"))
        self.toolBar.setWindowTitle(_translate("MainWindow", "toolBar"))
        self.actionExit.setText(_translate("MainWindow", "Exit"))
        self.homeAction.setText(_translate("MainWindow", "Home"))
        self.refreshAction.setText(_translate("MainWindow", "Refresh"))
        self.folderUpAction.setText(_translate("MainWindow", "Parent Directory"))
        self.label.setText(_translate("MainWindow", "Path"))

    def setLineCompleter(self, newPath):
        """
        Set the path in the Line Edit
        :param imagePath: new path
        :return:
        """
        self.lineCompleter.setText(newPath)

    def imagePlot(self, imagePath):
        """
        This method display an image using of pyqtgraph ImageView.
        imageView provides:

        1. A zoomable region for displaying the image
        2. A combination histogram and gradient editor (HistogramLUTItem) for
           controlling the visual appearance of the image
        3. Tools for very basic analysis of image data (see ROI and Norm buttons)
        :param imagePath: the image path
        """

        if self.isEmImage(imagePath):
            # Create an image from imagePath using em-bindings
            img = em.Image()
            loc2 = em.ImageLocation(imagePath)
            img.read(loc2)
            array = np.array(img, copy=False)
            dim = img.getDim()

            if not(self.imageLayout.isEmpty()):
                item = self.imageLayout.takeAt(0)
                self.imageLayout.removeItem(item)

            # Display an image using pyqtgraph
            self.v1 = pg.ImageView()
            self.imageLayout.addWidget(self.v1)
            self.v1.setImage(array)

            # Show the image dimension and type
            self.listWidget.clear()
            self.listWidget.addItem("Dimension: " + str(img.getDim()))
            self.listWidget.addItem("Type: " + str(img.getType()))

        elif self.isImage(imagePath):
            # TODO: Also show normal images using QImage
            pass
        else:
            if not (self.imageLayout.isEmpty()):
                item = self.imageLayout.takeAt(0)
                self.imageLayout.removeItem(item)
                self.v1.clear()
                self.v1.close()

            self.listWidget.clear()
            self.listWidget.addItem("NO IMAGE FORMAT")

    @staticmethod
    def isEmImage(imagePath):
        """ Return True if imagePath has an extension recognized as supported
        EM-image """
        _, ext = os.path.splitext(imagePath)
        return ext in ['.mrc', '.mrcs', '.spi', '.stk']

    @staticmethod
    def isImage(imagePath):
        """ Return True if imagePath has a standard image format. """
        _, ext = os.path.splitext(imagePath)
        return ext in ['.jpg', '.jpeg', '.png', '.tif']


