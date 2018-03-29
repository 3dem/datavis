#!/usr/bin/python
# -*- coding: utf-8 -*-


import os

from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QFrame, QSizePolicy,
                             QSplitter, QApplication, QTreeView, QFileSystemModel,
                             QLineEdit, QVBoxLayout, QListWidget, QMainWindow,
                             QAction, QToolBar, QLabel, QPushButton, QRadioButton,
                             QSpacerItem, QCompleter, QGridLayout, QDialog,
                             QSlider, QSpinBox, QFormLayout, QComboBox,
                             QTableWidget, QItemDelegate, QTableView)
from PyQt5.QtCore import Qt, QCoreApplication, QMetaObject, QRect, QDir,\
                         QItemSelectionModel, QAbstractTableModel, QModelIndex,\
                         QSize
from PyQt5.QtGui import QImage, QPalette, QPainter, QPainterPath, QPen, QColor
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

        self.disableZoom = kwargs.get('--disable-zoom', False)
        self.disableHistogram = kwargs.get('--disable-histogram', False)
        self.disableROI = kwargs.get('--disable-roi', False)
        self.disableMenu = kwargs.get('--disable-menu', False)
        self.enableAxis = kwargs.get('--enable-axis', False)

        self._imagePath = None
        self._image = None
        self._image2D = None
        self._image2DView = pg.ImageView(view=pg.PlotItem())
        self._imageBox = ImageBox()
        self._volumeSlice = VolumeSlice(imagePath=self._imagePath)
        self._galleryView = GalleryView(imagePath=self._imagePath,
                                        iconWidth=150, iconHeight=150)
        self._initGUI()

    def _onPathDoubleClick(self, signal):
        """
        This slot is executed when the action "double click"  inside the tree
        view is realized. The tree view path change
        :param signal: double clicked signal
        """
        file_path = self.model.filePath(signal)
        self.browser.setLineCompleter(self, file_path)

    def _onPathEntered(self):
        """
        This slot is executed when the Return or Enter key is pressed
        """
        self._imagePath = self.lineCompleter.text()
        self.setLineCompleter(self._imagePath)
        self.imagePlot(self._imagePath)

    def _onPathClick(self, signal):
        """
        This slot is executed when the action "click" inside the tree view
        is realized. The tree view path change
        :param signal: clicked signal
        """
        file_path = self.model.filePath(signal)
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
            index = self.model.index(QDir.toNativeSeparators(self._imagePath))
            self.treeView.collapse(index)

    def _onExpandTreeView(self):

         self._imagePath = self.lineCompleter.text()
         index = self.model.index(QDir.toNativeSeparators(self._imagePath))
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

    def _onVolumeSliceButtonClicked(self):
        """
        This Slot is executed when volume slice button was clicked.
        Select an em-image to display the slice views
        """
        self._galleryView.setupProperties()
        self._volumeSlice = VolumeSlice(imagePath=self._imagePath)
        self.imageLayout.addWidget(self._volumeSlice)
        self.galeryViewButton.setEnabled(True)
        self.volumeSliceButton.setEnabled(False)

    def _onGalleryViewButtonClicked(self):
        """
        This Slot is executed when gallery view button was clicked.
        Select an em-image to display as gallery view
        """
        self._volumeSlice.setupProperties()
        self._galleryView = GalleryView(imagePath=self._imagePath, iconWidth=150,
                                        iconHeight=150)
        self.imageLayout.addWidget(self._galleryView)
        self.galeryViewButton.setEnabled(False)
        self.volumeSliceButton.setEnabled(True)

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

        self.selectButton = QPushButton(self.widget)
        self.selectButton.setGeometry(QRect(160, 190, 101, 22))
        self.selectButton.setIcon(qta.icon('fa.check'))
        self.selectButton.clicked.connect(self._onSelectButtonClicked)

        buttonHorizontalLayout.addWidget(self.selectButton)

        self.closeButton = QPushButton(self.widget)
        self.closeButton.setGeometry(QRect(160, 190, 101, 22))
        self.closeButton.setIcon(qta.icon('fa.times'))
        self.closeButton.clicked.connect(self._onCloseButtonClicked)

        buttonHorizontalLayout.addWidget(self.closeButton)

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

        # Create Gallery View and Volume Slice Buttons
        self.changeViewFrame = QFrame()
        self.gridLayoutViews = QHBoxLayout()
        self.changeViewFrame.setLayout(self.gridLayoutViews.layout())

        self.galeryViewButton = QPushButton(self)
        self.galeryViewButton.setIcon(qta.icon('fa.th'))
        self.galeryViewButton.setMaximumSize(25, 25)
        self.galeryViewButton.setEnabled(True)
        self.galeryViewButton.clicked.connect(self._onGalleryViewButtonClicked)

        self.volumeSliceButton = QPushButton(self)
        self.volumeSliceButton.setIcon(qta.icon('fa.sliders'))
        self.volumeSliceButton.setMaximumSize(25, 25)
        self.volumeSliceButton.setEnabled(False)
        self.volumeSliceButton.clicked.connect(self._onVolumeSliceButtonClicked)

        self.buttonsSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding,
                                       QSizePolicy.Minimum)

        self.gridLayoutViews.addItem(self.buttonsSpacer)

        self.gridLayoutViews.addWidget(self.volumeSliceButton)
        self.gridLayoutViews.addWidget(self.galeryViewButton)

        self.imageVerticalLayout.addWidget(self.changeViewFrame)
        self.changeViewFrame.setVisible(False)

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

        self._imagePath = QDir.separator()
        self.lineCompleter.setText(self._imagePath)
        self.model.setRootPath(self._imagePath)
        self.treeView.setModel(self.model)
        self.treeView.setRootIndex(self.model.index(self._imagePath))
        self.treeView.setSortingEnabled(True)
        self.treeView.resize(640, 380)

        # Config the treeview completer
        self.completer = QCompleter()
        self.lineCompleter.setCompleter(self.completer)
        self.completer.setFilterMode(Qt.MatchCaseSensitive)
        self.completer.setModel(self.treeView.model())
        self.treeView.setModel(self.completer.model())
        self.lineCompleter.textChanged.connect(self._onExpandTreeView)
        self.lineCompleter.returnPressed.connect(self._onPathEntered)

        self.retranslateUi(self)
        QMetaObject.connectSlotsByName(self)

        # Configure the Main Window
        self.setGeometry(200, 100, 900, 600)
        self.setWindowTitle('EM-Browser')

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
        self._imagePath = newPath
        self.lineCompleter.setText(self._imagePath)

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
            self.imageLayout.removeItem(item)
            self._image2DView.close()
            self._image2DView = pg.ImageView(view=pg.PlotItem())
            plotItem = self._image2DView.getView()
            plotItem.showAxis('bottom', False)
            plotItem.showAxis('left', False)
            self._imageBox.setupProperties()
            self._volumeSlice.setupProperties()
            self._galleryView.setupProperties()

        if self.isEmImage(imagePath):

            self.frame.setEnabled(True)

            # Create an image from imagePath using em-bindings
            self._image = em.Image()
            loc2 = em.ImageLocation(imagePath)
            self._image.read(loc2)

            # Determinate the image dimension
            z = self._image.getDim().z

            if z == 1:  # The data is a 2D numpy array

                self._image2D = np.array(self._image, copy=False)

                # A plot area (ViewBox + axes) for displaying the image
                self.imageLayout.addWidget(self._image2DView)
                self._image2DView.setImage(self._image2D)

                # Disable image operations
                if self.disableHistogram:
                    self.imageView.ui.histogram.hide()
                if self.disableMenu:
                    self.imageView.ui.menuBtn.hide()
                if self.disableROI:
                    self.imageView.ui.roiBtn.hide()
                if self.disableZoom:
                    self.imageView.getView().setMouseEnabled(False, False)

                if self.enableAxis:
                    plotItem = self.imageView.getView()
                    plotItem.showAxis('bottom', True)
                    plotItem.showAxis('left', True)

                # Show the image dimension and type
                self.listWidget.clear()
                self.listWidget.addItem("Dimension: " + str(self._image.getDim()))
                self.listWidget.addItem("Type: " + str(self._image.getType()))

                # Hide Volume Slice and Gallery View Buttons
                self.changeViewFrame.setVisible(False)

            else:  # The image has a volume. The data is a numpy 3D array. In
                # this case, display the Top, Front and the Right View planes

                if self.galeryViewButton.isEnabled():
                    self._galleryView.setupProperties()
                    self._volumeSlice = VolumeSlice(imagePath=self._imagePath)
                    self.imageLayout.addWidget(self._volumeSlice)
                    self.changeViewFrame.setVisible(True)
                else:
                    self._volumeSlice.setupProperties()
                    self._galleryView = GalleryView(imagePath=self._imagePath,
                                                    iconWidth=150,
                                                    iconHeight=150)
                    self.imageLayout.addWidget(self._galleryView)
                    self.changeViewFrame.setVisible(True)

                # Show the image dimension and type
                self.listWidget.clear()
                self.listWidget.addItem("Dimension: " + str(self._image.getDim()))
                self.listWidget.addItem("Type: " + str(self._image.getType()))

        elif self.isImage(imagePath):

                self.frame.setEnabled(False)

                # Create and display a standard image using ImageBox class
                self._imageBox = ImageBox()
                self.imageLayout.addWidget(self._imageBox)
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
            self.changeViewFrame.setVisible(False)

            self.listWidget.addItem("NO IMAGE FORMAT")

    @staticmethod
    def isEmImage(imagePath):
        """ Return True if imagePath has an extension recognized as supported
            EM-image """
        _, ext = os.path.splitext(imagePath)
        return ext in ['.mrc', '.mrcs', '.spi', '.stk', '.map']

    @staticmethod
    def isImage(imagePath):
        """ Return True if imagePath has a standard image format. """
        _, ext = os.path.splitext(imagePath)
        return ext in ['.jpg', '.jpeg', '.png', '.tif', '.bmp']








