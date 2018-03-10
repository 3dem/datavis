#!/usr/bin/python
# -*- coding: utf-8 -*-


import os

from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QFrame, QSizePolicy,
                             QSplitter, QApplication, QTreeView, QFileSystemModel,
                             QLineEdit, QVBoxLayout, QListWidget, QMainWindow,
                             QAction, QToolBar, QLabel, QPushButton,
                             QSpacerItem, QCompleter, QGridLayout, QDialog)
from PyQt5.QtCore import Qt, QCoreApplication, QMetaObject, QRect, QDir,\
                         QItemSelectionModel
from PyQt5.QtGui import QImage
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
        self.enableAxis = kwargs.get('--enable-axis', False)

        self.image = pg.GraphicsLayoutWidget()
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

    def _onSelectButtonClicked(self):
        """
        This Slot is executed when a exit signal was fire.
        Select an em-image to realize a simple data-slicing
        """
        if self.isEmImage(self.path):
            self.volumeSlice(self.path)

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
        self.selectButton.clicked.connect(self._onSelectButtonClicked)

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

            self.image = pg.GraphicsLayoutWidget()
            self.imageBox.setupProperties()

        if self.isEmImage(imagePath):

            self.frame.setEnabled(True)

            # Create an image from imagePath using em-bindings
            img = em.Image()
            loc2 = em.ImageLocation(imagePath)
            img.read(loc2)

            # Determinate the image dimension
            z = img.getDim().z

            if z == 1:  # The data is a 2D numpy array

                array = np.array(img, copy=False)

                # A plot area (ViewBox + axes) for displaying the image
                self.imageLayout.addWidget(self.image)
                plotArea = self.image.addPlot()

                # Item for displaying image data
                imageItem = pg.ImageItem()
                plotArea.addItem(imageItem)
                plotArea.showAxis('bottom', False)
                plotArea.showAxis('left', False)

                # Generate image data
                imageItem.setImage(array)

                # Contrast/color control
                if not self.disableHistogram:
                    hist = pg.HistogramLUTItem()
                    hist.setImageItem(imageItem)
                    self.image.addItem(hist)

                # Zoom control
                if self.disableZoom:
                    self.frame.setEnabled(False)

                # Axis control
                if self.enableAxis:
                    plotArea.showAxis('bottom', True)
                    plotArea.showAxis('left', True)

                # Custom ROI for selecting an image region
                if self.disableROI:
                    roi = pg.ROI([-8, 14], [6, 5])
                    roi.addScaleHandle([0.5, 1], [0.5, 0.5])
                    roi.addScaleHandle([0, 0.5], [0.5, 0.5])
                    plotArea.addItem(roi)
                    roi.setZValue(10)  # make sure ROI is drawn above image

                # Show the image dimension and type
                self.listWidget.clear()
                self.listWidget.addItem("Dimension: " + str(img.getDim()))
                self.listWidget.addItem("Type: " + str(img.getType()))

            else:  # The image has a volume. The data is a numpy 3D array. In
                   # this case, we take one slice and display as a image.


                # Show the image dimension and type
                self.listWidget.clear()
                self.listWidget.addItem("Dimension: " + str(img.getDim()))
                self.listWidget.addItem("Type: " + str(img.getType()))


        elif self.isImage(imagePath):

                self.frame.setEnabled(False)

                # Create and display a standard image using ImageBox class
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
                #self.listWidget.addItem("Type: " + str(type))"""
        else:
            self.imageBox.setupProperties()
            self.imageBox.update()
            self.listWidget.clear()
            self.listWidget.addItem("NO IMAGE FORMAT")


    def volumeSlice(self, imagePath):
        """
        Given 3D data (displayed at left), select a 2D plane and interpolate data
        along that plane to generate a slice image (displayed at right).
        :param imagePath: an em-image
        """
        if self.isEmImage(imagePath):

            # Create an image from imagePath using em-bindings
            img = em.Image()
            loc2 = em.ImageLocation(imagePath)
            img.read(loc2)

            imageDim = img.getDim()

            x = imageDim.x
            y = imageDim.y
            z = imageDim.z

            if z > 1:  # The image has a volumes

                # Create a numpy 3D array with the image values pixel
                array3D = np.array(img, copy=False)

                # Create window with two ImageView widgets
                self.volumeSliceDialog = QDialog()
                self.volumeSliceDialog.setGeometry(250, 150, 800, 500)
                self.volumeSliceDialog.setWindowTitle('Volume Slicer')
                self.sliceWidget = QWidget(self.volumeSliceDialog)
                self.gridLayoutSlice = QGridLayout()
                self.sliceWidget.setLayout(self.gridLayoutSlice)
                self.volumeSliceDialog.setLayout(self.gridLayoutSlice.layout())

                self.imv1 = pg.ImageView()
                self.imv2 = pg.ImageView()
                self.gridLayoutSlice.addWidget(self.imv1, 0, 0)
                self.gridLayoutSlice.addWidget(self.imv2, 0, 1)

                self.imv1.ui.menuBtn.hide()
                self.imv1.ui.roiBtn.hide()
                self.imv2.ui.menuBtn.hide()
                self.imv2.ui.roiBtn.hide()

                self.buttonHorizontalLayout = QHBoxLayout(self.volumeSliceDialog)
                """buttonHorizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding,
                                                     QSizePolicy.Minimum)
                buttonHorizontalLayout.addItem(buttonHorizontalSpacer)"""

                self.galeryViewButton = QPushButton(self.volumeSliceDialog)
                self.galeryViewButton.setText('Galery View')
                self.galeryViewButton.setIcon(qta.icon('fa.eye'))
                self.galeryViewButton.clicked.connect(self.galeryView)

                self.buttonHorizontalLayout.addWidget(self.galeryViewButton)

                self.closeButton = QPushButton(self.volumeSliceDialog)
                self.closeButton.setText('Close')
                self.closeButton.setIcon(qta.icon('fa.times'))
                self.closeButton.clicked.connect(self.closeDialog)
    
                self.buttonHorizontalLayout.addWidget(self.closeButton)

                self.gridLayoutSlice.addLayout(self.buttonHorizontalLayout, 1, 1)

                # Create a line with two freely-moving handles to generate a
                # slice image
                roi = pg.LineSegmentROI([[10, 64], [120, 64]], pen='r')
                self.imv1.addItem(roi)

                def update():
                    """
                    Use the position of the ROI relative to an imageItem to
                    pull a slice from an array
                    """
                    d2 = roi.getArrayRegion(array3D, self.imv1.imageItem,
                                            axes=(1, 2))
                    self.imv2.setImage(d2)

                roi.sigRegionChanged.connect(update)

                # Display the data
                self.imv1.setImage(array3D)
                """self.imv1.setHistogramRange(-0.01, 0.01)
                self.imv1.setLevels(-0.003, 0.003)"""

                self.update()

                self.volumeSliceDialog.exec()

    def closeDialog(self):
        """
        Close the Volume Slicer Window
        """
        self.volumeSliceDialog.close()


    def galeryView(self, imagePath):
        """

        """
        return


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









