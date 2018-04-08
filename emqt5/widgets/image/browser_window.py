#!/usr/bin/python
# -*- coding: utf-8 -*-


import os

from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QFrame, QSizePolicy,
                             QSplitter, QApplication, QTreeView,
                             QFileSystemModel, QLineEdit, QVBoxLayout,
                             QListWidget, QMainWindow,
                             QAction, QToolBar, QLabel, QPushButton,
                             QSpacerItem, QCompleter)
from PyQt5.QtCore import Qt, QCoreApplication, QMetaObject, QRect, QDir,\
                         QItemSelectionModel

from PyQt5.QtGui import QImage
from emqt5.widgets.image import ImageBox
from emqt5.widgets.image import VolumeSlice
from emqt5.widgets.image import GalleryView

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

        self._disableZoom = kwargs.get('--disable-zoom', False)
        self._disableHistogram = kwargs.get('--disable-histogram', False)
        self._disableROI = kwargs.get('--disable-roi', False)
        self._disableMenu = kwargs.get('--disable-menu', False)
        self._enableAxis = kwargs.get('--enable-slicesAxis', False)
        self._imagePath = kwargs.get('--path', None)
        self._image = None
        self._image2D = None
        self._image2DView = pg.ImageView(view=pg.PlotItem())
        self._imageBox = ImageBox()
        self._volumeSlice = VolumeSlice(imagePath='')
        self._galleryView = GalleryView(imagePath='',
                                        iconWidth=150, iconHeight=150)
        self.__initGUI__()

    def _onPathDoubleClick(self, signal):
        """
        This slot is executed when the action "double click"  inside the tree
        view is realized. The tree view path change
        :param signal: double clicked signal
        """
        file_path = self._model.filePath(signal)
        self.browser.setLineCompleter(self, file_path)

    def _onPathEntered(self):
        """
        This slot is executed when the Return or Enter key is pressed
        """
        self._imagePath = self._lineCompleter.text()
        self.setLineCompleter(self._imagePath)
        self.imagePlot(self._imagePath)

    def _onPathClick(self, signal):
        """
        This slot is executed when the action "click" inside the tree view
        is realized. The tree view path change
        :param signal: clicked signal
        """
        file_path = self._model.filePath(signal)
        self._imagePath = file_path
        self.setLineCompleter(self._imagePath)
        self.imagePlot(self._imagePath)

    def _onCloseButtonClicked(self):
        """
        This Slot is executed when a exit signal was fire. The application is
        terminate
        """
        import sys
        sys.exit()

    def _onSelectButtonClicked(self):
        """
        This Slot is executed when select button signal was clicked.
        Select an em-image to realize a simple data-slicing
        """
        if self.isEmImage(self._imagePath):
            self.volumeSliceView = VolumeSlice(imagePath=self._imagePath)

    def _onHomeActionClicked(self):
        """
        This Slot lead the TreeView to the user home directory
        """
        self._imagePath = QDir.homePath()
        self.setLineCompleter(self._imagePath)

    def _onRefreshActionClicked(self):
        """
        Refreshes the directory information
        :return:
        """
        dir = QDir(self._imagePath)
        canUp = dir.cdUp()
        if canUp:
           dir.refresh()

    def _onfolderUpActionClicked(self):
        """
        Changes directory by moving one directory up from the QDir's current
        directory
        """
        dir = QDir(self._imagePath)
        canUp = dir.cdUp()
        if canUp:
            self._imagePath = dir.path()
            self.setLineCompleter(self._imagePath)
            index = self._model.index(QDir.toNativeSeparators(self._imagePath))
            self._treeView.collapse(index)

    def _onExpandTreeView(self):

         self._imagePath = self._lineCompleter.text()
         index = self._model.index(QDir.toNativeSeparators(self._imagePath))
         self._treeView.selectionModel().select(index,
                                                QItemSelectionModel.ClearAndSelect |
                                                QItemSelectionModel.Rows)

         self._treeView.expand(index)
         self._treeView.scrollTo(index)
         self._treeView.resizeColumnToContents(index.column())

    def _onVolumeSliceButtonClicked(self):
        """
        This Slot is executed when volume slice button was clicked.
        Select an em-image to display the slice views
        """
        self._galleryView.setupProperties()
        self._volumeSlice = VolumeSlice(imagePath=self._imagePath)
        self._imageLayout.addWidget(self._volumeSlice)
        self._galeryViewButton.setEnabled(True)
        self._volumeSliceButton.setEnabled(False)

    def _onGalleryViewButtonClicked(self):
        """
        This Slot is executed when gallery view button was clicked.
        Select an em-image to display as gallery view
        """
        self._volumeSlice.setupProperties()
        self._galleryView = GalleryView(imagePath=self._imagePath, iconWidth=150,
                                        iconHeight=150)
        self._imageLayout.addWidget(self._galleryView)
        self._galeryViewButton.setEnabled(False)
        self._volumeSliceButton.setEnabled(True)

    def __initGUI__(self):

        self._centralWidget = QWidget(self)
        self._horizontalLayout = QHBoxLayout(self._centralWidget)
        self._splitter = QSplitter(self._centralWidget)
        self._splitter.setOrientation(Qt.Horizontal)
        self._widget = QWidget(self._splitter)
        self._leftVerticalLayout = QVBoxLayout(self._widget)
        self._verticalLayout = QVBoxLayout()

        # Create a line edit to handle a path completer
        completerLayoutWidget = QWidget(self._widget)
        horizontalLayout = QHBoxLayout(completerLayoutWidget)

        self._label = QLabel(completerLayoutWidget)
        horizontalLayout.addWidget(self._label)

        self._lineCompleter = QLineEdit(completerLayoutWidget)
        horizontalLayout.addWidget(self._lineCompleter)
        self._verticalLayout.addWidget(completerLayoutWidget)
        self._leftVerticalLayout.addLayout(completerLayoutWidget.layout())

        # Create a Tree View
        self._treeView = QTreeView(self._widget)
        self._verticalLayout.addWidget(self._treeView)
        self._treeView.clicked.connect(self._onPathClick)

        # Create a Select Button and Close Button
        buttonHorizontalLayout = QHBoxLayout(self._widget)
        buttonHorizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding,
                                         QSizePolicy.Minimum)
        buttonHorizontalLayout.addItem(buttonHorizontalSpacer)

        self._selectButton = QPushButton(self._widget)
        self._selectButton.setGeometry(QRect(160, 190, 101, 22))
        self._selectButton.setIcon(qta.icon('fa.check'))
        self._selectButton.clicked.connect(self._onSelectButtonClicked)

        buttonHorizontalLayout.addWidget(self._selectButton)

        self._closeButton = QPushButton(self._widget)
        self._closeButton.setGeometry(QRect(160, 190, 101, 22))
        self._closeButton.setIcon(qta.icon('fa.times'))
        self._closeButton.clicked.connect(self._onCloseButtonClicked)

        buttonHorizontalLayout.addWidget(self._closeButton)

        self._verticalLayout.addLayout(buttonHorizontalLayout.layout())

        self._leftVerticalLayout.addLayout(self._verticalLayout)

        # Create right Panel
        self._rightWidget = QWidget(self._splitter)

        self._widgetsVerticalLayout = QVBoxLayout(self._rightWidget)
        self._imageVerticalLayout = QVBoxLayout()

        self._imageSplitter = QSplitter(self._rightWidget)
        self._imageSplitter.setOrientation(Qt.Vertical)

        self._frame = QFrame(self._imageSplitter)

        sizePolicy = QSizePolicy(QSizePolicy.Maximum,
                                 QSizePolicy.Maximum)
        sizePolicy.setHorizontalStretch(100)
        sizePolicy.setVerticalStretch(100)
        self._frame.setMinimumHeight(440)
        self._frame.setMinimumWidth(440)

        sizePolicy.setHeightForWidth(self._frame.sizePolicy().hasHeightForWidth())
        self._frame.setSizePolicy(sizePolicy)
        self._frame.setFrameShape(QFrame.Box)
        self._frame.setFrameShadow(QFrame.Raised)

        self._labelImage = QLabel(self._frame)

        self._imageLayout = QHBoxLayout(self._frame)

        self.listWidget = QListWidget(self._imageSplitter)

        # Create Gallery View and Volume Slice Buttons
        self._changeViewFrame = QFrame()
        self._gridLayoutViews = QHBoxLayout()
        self._changeViewFrame.setLayout(self._gridLayoutViews.layout())

        self._galeryViewButton = QPushButton(self)
        self._galeryViewButton.setIcon(qta.icon('fa.th'))
        self._galeryViewButton.setMaximumSize(25, 25)
        self._galeryViewButton.setEnabled(True)
        self._galeryViewButton.clicked.connect(self._onGalleryViewButtonClicked)

        self._volumeSliceButton = QPushButton(self)
        self._volumeSliceButton.setIcon(qta.icon('fa.sliders'))
        self._volumeSliceButton.setMaximumSize(25, 25)
        self._volumeSliceButton.setEnabled(False)
        self._volumeSliceButton.clicked.connect(self._onVolumeSliceButtonClicked)

        self._buttonsSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding,
                                          QSizePolicy.Minimum)

        self._gridLayoutViews.addItem(self._buttonsSpacer)

        self._gridLayoutViews.addWidget(self._volumeSliceButton)
        self._gridLayoutViews.addWidget(self._galeryViewButton)

        self._imageVerticalLayout.addWidget(self._changeViewFrame)
        self._changeViewFrame.setVisible(False)

        self._imageVerticalLayout.addWidget(self._imageSplitter)

        self._widgetsVerticalLayout.addLayout(self._imageVerticalLayout)
        self._horizontalLayout.addWidget(self._splitter)
        self.setCentralWidget(self._centralWidget)

        # Create a Tool Bar
        self._toolBar = QToolBar(self)
        self.addToolBar(Qt.TopToolBarArea, self._toolBar)

        def _addAction(iconName):
            action = QAction(self)
            action.setIcon(qta.icon(iconName))
            self._toolBar.addAction(action)
            return action

        self._homeAction = _addAction('fa.home')
        self._homeAction.triggered.connect(self._onHomeActionClicked)

        self._folderUpAction = _addAction('fa.arrow-up')
        self._folderUpAction.triggered.connect(self._onfolderUpActionClicked)

        self._refreshAction = _addAction('fa.refresh')
        self._refreshAction.triggered.connect(self._onRefreshActionClicked)

        # Create and define the file system model
        self._model = QFileSystemModel()
        # filters = []
        # filters.append("*.mrc")
        # self.model.setNameFilters(filters)
        # self.model.setNameFilterDisables(False)

        self._lineCompleter.setText(QDir.separator())
        self._model.setRootPath(QDir.separator())
        self._treeView.setModel(self._model)
        self._treeView.setRootIndex(self._model.index(QDir.separator()))
        self._treeView.setSortingEnabled(True)
        self._treeView.resize(640, 380)

        if not self._imagePath:
            self._imagePath = QDir.separator()
        else:
            self._lineCompleter.setText(self._imagePath)
            self._onExpandTreeView()
            self._onPathEntered()

        # Config the treeview completer
        self._completer = QCompleter()
        self._lineCompleter.setCompleter(self._completer)
        #self._completer.setFilterMode(Qt.MatchCaseSensitive)
        self._completer.setModel(self._treeView.model())
        self._treeView.setModel(self._completer.model())
        self._lineCompleter.textChanged.connect(self._onExpandTreeView)
        self._lineCompleter.returnPressed.connect(self._onPathEntered)

        self.retranslateUi(self)
        QMetaObject.connectSlotsByName(self)

        # Configure the Main Window
        self.setGeometry(200, 100, 900, 600)
        self.setWindowTitle('EM-Browser')

    def retranslateUi(self, MainWindow):
        _translate = QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Browser"))
        self._homeAction.setText(_translate("MainWindow", "Home"))
        self._refreshAction.setText(_translate("MainWindow", "Refresh"))
        self._folderUpAction.setText(_translate("MainWindow", "Parent Directory"))
        self._label.setText(_translate("MainWindow", "Path"))
        self._selectButton.setText(QApplication.translate("MainWindow", "Select"))
        self._closeButton.setText(QApplication.translate("MainWindow", "Close"))

    def setLineCompleter(self, newPath):
        """
        Set the path in the Line Edit
        :param imagePath: new path
        :return:
        """
        self._imagePath = newPath
        self._lineCompleter.setText(self._imagePath)

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

        if not (self._imageLayout.isEmpty()):
            item = self._imageLayout.takeAt(0)
            self._imageLayout.removeItem(item)
            self._imageLayout.removeItem(item)
            self._image2DView.close()
            self._image2DView = pg.ImageView(view=pg.PlotItem())
            plotItem = self._image2DView.getView()
            plotItem.showAxis('bottom', False)
            plotItem.showAxis('left', False)
            self._imageBox.setupProperties()
            self._volumeSlice.setupProperties()
            self._galleryView.setupProperties()

        if self.isEmImage(imagePath):

            self._frame.setEnabled(True)

            # Create an image from imagePath using em-bindings
            self._image = em.Image()
            loc2 = em.ImageLocation(imagePath)
            self._image.read(loc2)

            # Determinate the image dimension
            z = self._image.getDim().z

            if z == 1:  # The data is a 2D numpy array

                self._image2D = np.array(self._image, copy=False)

                # A plot area (ViewBox + axes) for displaying the image
                self._imageLayout.addWidget(self._image2DView)
                self._image2DView.setImage(self._image2D)

                # Disable image operations
                if self._disableHistogram:
                    self._image2DView.ui.histogram.hide()
                if self._disableMenu:
                    self._image2DView.ui.menuBtn.hide()
                if self._disableROI:
                    self._image2DView.ui.roiBtn.hide()
                if self._disableZoom:
                    self._image2DView.getView().setMouseEnabled(False, False)

                if self._enableAxis:
                    plotItem = self._image2DView.getView()
                    plotItem.showAxis('bottom', True)
                    plotItem.showAxis('left', True)

                # Show the image dimension and type
                self.listWidget.clear()
                self.listWidget.addItem("Dimension: " + str(self._image.getDim()))
                self.listWidget.addItem("Type: " + str(self._image.getType()))

                # Hide Volume Slice and Gallery View Buttons
                self._changeViewFrame.setVisible(False)

            else:  # The image has a volume. The data is a numpy 3D array. In
                # this case, display the Top, Front and the Right View planes

                if self._galeryViewButton.isEnabled():
                    self._galleryView.setupProperties()
                    self._volumeSlice = VolumeSlice(imagePath=self._imagePath)
                    self._imageLayout.addWidget(self._volumeSlice)
                    self._changeViewFrame.setVisible(True)
                else:
                    self._volumeSlice.setupProperties()
                    self._galleryView = GalleryView(imagePath=self._imagePath,
                                                    iconWidth=150,
                                                    iconHeight=150)
                    self._imageLayout.addWidget(self._galleryView)
                    self._changeViewFrame.setVisible(True)

                # Show the image dimension and type
                self.listWidget.clear()
                self.listWidget.addItem("Dimension: " + str(self._image.getDim()))
                self.listWidget.addItem("Type: " + str(self._image.getType()))

        elif self.isImage(imagePath):

                self._frame.setEnabled(False)

                # Create and display a standard image using ImageBox class
                self._imageBox = ImageBox()
                self._imageLayout.addWidget(self._imageBox)
                image = QImage(imagePath)
                self._imageBox.setImage(image)
                self._imageBox.update()
                self._imageBox.fitToWindow()

                width = image.width()
                height = image.height()
                type = image.format()

                # Show the image dimension and type
                self.listWidget.clear()
                self.listWidget.addItem("Dimension: " + str(width) + " x "
                                        + str(height))
        else:
            self._imageBox.setupProperties()
            self._imageBox.update()
            self.listWidget.clear()
            self._volumeSlice.setupProperties()
            self._galleryView.setupProperties()

            # Hide Volume Slice and Gallery View Buttons
            self._changeViewFrame.setVisible(False)

            self.listWidget.addItem("NO IMAGE FORMAT")

    @staticmethod
    def isEmImage(imagePath):
        """ Return True if imagePath has an extension recognized as supported
            EM-image """
        _, ext = os.path.splitext(imagePath)
        return ext in ['.mrc', '.mrcs', '.spi', '.stk', '.map', '.vol']

    @staticmethod
    def isImage(imagePath):
        """ Return True if imagePath has a standard image format. """
        _, ext = os.path.splitext(imagePath)
        return ext in ['.jpg', '.jpeg', '.png', '.tif', '.bmp']








