#!/usr/bin/python
# -*- coding: utf-8 -*-


import os

from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QFrame, QSizePolicy,
                             QSplitter, QApplication, QTreeView, QFileSystemModel,
                             QLineEdit, QVBoxLayout, QListWidget, QMainWindow,
                             QAction, QToolBar, QLabel, QPushButton,
                             QSpacerItem, QCompleter)
from PyQt5.QtCore import Qt, QCoreApplication, QMetaObject, QRect, QDir,\
                         QItemSelectionModel, QEvent
from PyQt5.QtGui import QImage, QPixmap
from emqt5.widgets.image import ImageBox

import qtawesome as qta
import numpy as np
import pyqtgraph as pg
import em


class BrowserWindow(QMainWindow):
    """
    Declaration of the class Browser
    This class construct a Browser User Interface
    """

    def __init__(self, parent=None, **kwargs):
        super(QMainWindow, self).__init__(parent)

        self.disableZoom = kwargs.get('--disable-zoom', False)
        self.disableHistogram = kwargs.get('--disable-histogram', False)
        self.disableROI = kwargs.get('--disable-roi', False)
        self.disableMenu = kwargs.get('--disable-menu', False)
        self.image = pg.ImageView()
        self.imageBox = ImageBox()

        self._initGUI()

    def _onPathDoubleClick(self, signal):
        """
        This slot is executed when the action "double click"  inside the tree
        view is realized. The tree view path change
        :param signal: double clicked signal
        """
        file_path = self.model.filePath(signal)
        self.browser.setLineCompleter(self, file_path)

    def _onPathClick(self, signal):
        """
        This slot is executed when the action "click" inside the tree view
        is realized. The tree view path change
        :param signal: clicked signal
        """
        file_path = self.model.filePath(signal)
        self.path = file_path
        self.setLineCompleter(file_path)
        self.imagePlot(file_path)

    def _onImagePlot(self, signal):
        """
        This slot is executed when the action "entered" inside the line edit
        is realized.
        :param signal: entered signal
        """
        file_path = self.model.filePath(signal)
        self.browser.imagePlot(self, file_path)

    def _onCloseButtonClicked(self):
        """
        This Slot is executed when a exit signal was fire. The application is
        terminate
        """
        import sys
        sys.exit()

    def _onHomeActionClicked(self):
        """
        This Slot lead the TreeView to the user home directory
        """
        self.path = QDir.homePath()
        self.setLineCompleter(self.path)

    def _onRefreshActionClicked(self):
        """
        Refreshes the directory information
        :return:
        """
        dir = QDir(self.path)
        canUp = dir.cdUp()
        if canUp:
           dir.refresh()

    def _onfolderUpActionClicked(self):
        """
        Changes directory by moving one directory up from the QDir's current
        directory
        """
        dir = QDir(self.path)
        canUp = dir.cdUp()
        if canUp:
            self.path = dir.path()
            self.setLineCompleter(self.path)
            index = self.model.index(QDir.toNativeSeparators(self.path))
            self.treeView.collapse(index)

    def _onExpandTreeView(self):

         self.path = self.lineCompleter.text()
         index = self.model.index(QDir.toNativeSeparators(self.path))
         self.treeView.selectionModel().select(index,
                                               QItemSelectionModel.ClearAndSelect |
                                               QItemSelectionModel.Rows)

         self.treeView.expand(index)
         self.treeView.scrollTo(index)
         self.treeView.resizeColumnToContents(index.column())

    def _onSplitterMove(self, pos, index):
        if index > 0:
            print('Derecha')
        else:
            print('Izquierda')

    def _initGUI(self):

        self.centralWidget = QWidget(self)
        self.horizontalLayout = QHBoxLayout(self.centralWidget)
        self.splitter = QSplitter(self.centralWidget)
        self.splitter.setOrientation(Qt.Horizontal)
        self.widget = QWidget(self.splitter)
        self.splitter.splitterMoved.connect(self._onSplitterMove)
        self.leftVerticalLayout = QVBoxLayout(self.widget)
        self.verticalLayout = QVBoxLayout()

        # Create a line edit to handle a path completer
        completerLayoutWidget = QWidget(self.widget)
        horizontalLayout = QHBoxLayout(completerLayoutWidget)

        self.label = QLabel(completerLayoutWidget)
        horizontalLayout.addWidget(self.label)

        self.lineCompleter = QLineEdit(completerLayoutWidget)
        horizontalLayout.addWidget(self.lineCompleter)
        self.verticalLayout.addWidget(completerLayoutWidget)
        self.leftVerticalLayout.addLayout(completerLayoutWidget.layout())

        # Create a Tree View
        self.treeView = QTreeView(self.widget)
        self.verticalLayout.addWidget(self.treeView)
        self.treeView.clicked.connect(self._onPathClick)

        # Create a Select Button and Close Button
        buttonHorizontalLayout = QHBoxLayout(self.widget)
        buttonHorizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding,
                                         QSizePolicy.Minimum)
        buttonHorizontalLayout.addItem(buttonHorizontalSpacer)

        self.closeButton = QPushButton(self.widget)
        self.closeButton.setGeometry(QRect(160, 190, 101, 22))
        self.closeButton.setIcon(qta.icon('fa.times'))
        self.closeButton.clicked.connect(self._onCloseButtonClicked)

        buttonHorizontalLayout.addWidget(self.closeButton)

        self.selectButton = QPushButton(self.widget)
        self.selectButton.setGeometry(QRect(160, 190, 101, 22))
        self.selectButton.setIcon(qta.icon('fa.check'))

        buttonHorizontalLayout.addWidget(self.selectButton)

        self.verticalLayout.addLayout(buttonHorizontalLayout.layout())

        self.leftVerticalLayout.addLayout(self.verticalLayout)

        # Create right Panel

        self.rightWidget = QWidget(self.splitter)
        self.widgetsVerticalLayout = QVBoxLayout(self.rightWidget)
        self.imageVerticalLayout = QVBoxLayout()

        self.imageSplitter = QSplitter(self.rightWidget)
        self.imageSplitter.setOrientation(Qt.Vertical)


        self.frame = QFrame(self.imageSplitter)
        sizePolicy = QSizePolicy(QSizePolicy.Maximum,
                                 QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(100)
        sizePolicy.setVerticalStretch(100)
        sizePolicy.setHeightForWidth(self.frame.sizePolicy().hasHeightForWidth())
        self.frame.setSizePolicy(sizePolicy)
        self.frame.setFrameShape(QFrame.Box)
        self.frame.setFrameShadow(QFrame.Raised)
        self.labelImage = QLabel(self.frame)

        self.imageLayout = QHBoxLayout(self.frame)
        self.listWidget = QListWidget(self.imageSplitter)

        self.imageVerticalLayout.addWidget(self.imageSplitter)

        self.widgetsVerticalLayout.addLayout(self.imageVerticalLayout)
        self.horizontalLayout.addWidget(self.splitter)
        self.setCentralWidget(self.centralWidget)

        # Create a Tool Bar
        self.toolBar = QToolBar(self)
        self.addToolBar(Qt.TopToolBarArea, self.toolBar)

        def _addAction(iconName):
            action = QAction(self)
            action.setIcon(qta.icon(iconName))
            self.toolBar.addAction(action)
            return action

        self.homeAction = _addAction('fa.home')
        self.homeAction.triggered.connect(self._onHomeActionClicked)

        self.folderUpAction = _addAction('fa.arrow-up')
        self.folderUpAction.triggered.connect(self._onfolderUpActionClicked)

        self.refreshAction = _addAction('fa.refresh')
        self.refreshAction.triggered.connect(self._onRefreshActionClicked)

        # Create and define the file system model
        self.model = QFileSystemModel()
        # filters = []
        # filters.append("*.mrc")
        # self.model.setNameFilters(filters)
        # self.model.setNameFilterDisables(False)

        self.path = QDir.separator()
        self.lineCompleter.setText(self.path)
        self.model.setRootPath(self.path)
        self.treeView.setModel(self.model)
        self.treeView.setRootIndex(self.model.index(self.path))
        self.treeView.setSortingEnabled(True)
        self.treeView.resize(640, 380)

        # Config the treeview completer
        self.completer = QCompleter()
        self.lineCompleter.setCompleter(self.completer)
        self.completer.setFilterMode(Qt.MatchCaseSensitive)
        self.completer.setModel(self.treeView.model())
        self.treeView.setModel(self.completer.model())
        self.lineCompleter.textChanged.connect(self._onExpandTreeView)

        self.retranslateUi(self)
        QMetaObject.connectSlotsByName(self)

        # Show the Main Window
        self.setGeometry(200, 100, 900, 600)
        self.setWindowTitle('EM-Browser')
        self.show()

    def retranslateUi(self, MainWindow):
        _translate = QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Browser"))
        self.homeAction.setText(_translate("MainWindow", "Home"))
        self.refreshAction.setText(_translate("MainWindow", "Refresh"))
        self.folderUpAction.setText(_translate("MainWindow", "Parent Directory"))
        self.label.setText(_translate("MainWindow", "Path"))
        self.selectButton.setText(QApplication.translate("MainWindow", "Select"))
        self.closeButton.setText(QApplication.translate("MainWindow", "Close"))

    def setLineCompleter(self, newPath):
        """
        Set the path in the Line Edit
        :param imagePath: new path
        :return:
        """
        self.path = newPath
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

        if not (self.imageLayout.isEmpty()):
            item = self.imageLayout.takeAt(0)
            self.imageLayout.removeItem(item)
            self.image.clear()
            self.image.close()
            self.image = pg.ImageView()
            self.imageBox.setupProperties()

        if self.isEmImage(imagePath):

            self.frame.setEnabled(True)

            # Create an image from imagePath using em-bindings
            img = em.Image()
            loc2 = em.ImageLocation(imagePath)
            img.read(loc2)
            array = np.array(img, copy=False)

            # Display an image using pyqtgraph
            self.imageLayout.addWidget(self.image)
            self.image.setImage(array)

            # Disable image operations
            if self.disableHistogram:
                self.image.ui.histogram.hide()
            if self.disableMenu:
                self.image.ui.menuBtn.hide()
            if self.disableROI:
                self.image.ui.roiBtn.hide()
            if self.disableZoom:
                self.image.getView().setMouseEnabled(False, False)

            # Show the image dimension and type
            self.listWidget.clear()
            self.listWidget.addItem("Dimension: " + str(img.getDim()))
            self.listWidget.addItem("Type: " + str(img.getType()))

        elif self.isImage(imagePath):

                self.frame.setEnabled(False)
                # Create and dsiplay a conventional image using ImageBox class
                self.imageBox = ImageBox()
                self.imageLayout.addWidget(self.imageBox)
                image = QImage(imagePath)
                self.imageBox.setImage(image)
                self.imageBox.update()
                self.imageBox.fitToWindow()

                width = image.width()
                height = image.height()
                type = image.format()

                # Show the image dimension and type
                self.listWidget.clear()
                self.listWidget.addItem("Dimension: " + str(width) + " x "
                                        + str(height))
                #self.listWidget.addItem("Type: " + str(type))
        else:
            self.imageBox.setupProperties()
            self.imageBox.update()
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
        return ext in ['.jpg', '.jpeg', '.png', '.tif', '.bmp']





