#!/usr/bin/python
# -*- coding: utf-8 -*-


import os

from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QFrame, QSizePolicy,
                             QSplitter, QApplication, QTreeView, QFileSystemModel,
                             QLineEdit, QVBoxLayout, QListWidget, QMainWindow,
                             QAction, QToolBar, QLabel, QPushButton, QRadioButton,
                             QSpacerItem, QCompleter, QGridLayout, QDialog,
                             QSlider, QSpinBox, QFormLayout, QComboBox,
                             QTableWidget)
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

        self.image = pg.ImageView(view=pg.PlotItem())
        plotItem = self.image.getView()
        plotItem.showAxis('bottom', False)
        plotItem.showAxis('left', False)
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

    def _onPathEntered(self):
        """
        This slot is executed when the Return or Enter key is pressed
        """
        self.path = self.lineCompleter.text()
        self.setLineCompleter(self.path)
        self.imagePlot(self.path)

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
        if self.isEmImage(self.path):
            self.volumeSlice(self.path)

    def _onGalleryViewButtonClicked(self):
        """
        This Slot is executed when gallery view button was clicked.
        Select an em-image to display a gallery view
        """
        self.galleryView()

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

    def _onTopSliderChange(self, value):
        """
        Display a Top View Slice in a specific value
        :param value: value of Slide
        """
        self.sliceY = value
        self.topLabelValue.setText(str(value))
        self.topView.setImage(self.array3D[:, self.sliceY, :])

    def _onFrontSliderChange(self, value):
        """
         Display a Front View Slice in a specific value
        :param value: value of Slide
        """
        self.sliceZ = value
        self.frontLabelValue.setText(str(value))
        self.frontView.setImage(self.array3D[self.sliceZ:, :, :])

    def _onRightSliderChange(self, value):
        """
        Display a Front View Slice in a specific value
        :param value: value of Slide
        """
        self.sliceX = value
        self.rightLabelValue.setText(str(value))
        self.rightView.setImage(self.array3D[:, :, self.sliceX])

    def _onGalleryViewPlaneChanged(self, index):
        """
        This Slot is executed when a new coordinate plane is  selected.
        display a slices in the selected plane
        :param index: index of plane
        """
        self.tableSlices.clearContents()
        self.fillTableGalleryView(self.rowsSpinBox.value(),
                                    self.colsSpinBox.value(),
                                    index)

    def _onSliceZoom(self, value):
        """
        The slices are resized taking into account the new value (in %)
        :param value: resize factor
        """
        for row in range(0, self.rowsSpinBox.value()):
            self.tableSlices.setRowHeight(row, 50 + value)
        for col in range(0, self.colsSpinBox.value()):
            self.tableSlices.setColumnWidth(col, 50 + value)

    def _onGotoItem(self, value):
        """
        Find an especific slice represented by a number and set the focus on this
        :param value: number of slice
        :return:
        """
        # Calculate the row and col that represent the slice value
        row = int(value/self.colsSpinBox.value())
        if int(value%self.colsSpinBox.value()) != 0:
            col = int(value%self.colsSpinBox.value()-1)
        else:
            row = row - 1
            col = self.colsSpinBox.value()-1

        # Move the focus to slice in the specified row and col
        self.tableSlices.setCurrentCell(row, col)

    def _onTableWidgetSliceClicked(self, row, col):
        """
        This methods is executes whenever a cell in the table is clicked.
        The row and column specified is the slice that was clicked.
        :param row: slice row
        :param col: slice col
        """
        self.gotoItemSpinBox.setValue(row * self.colsSpinBox.value() + col + 1)

    def __onTableWidgetSliceDoubleClicked(self, row, col):
        """
        This methods is executes whenever a cell in the table is double clicked.
        The row and column specified is the slice that was clicked.
        This methods display the slice that was selected
        :param row: slice row
        :param col: slice col
        """

        # Calculate the slice selected number
        slice = row * self.colsSpinBox.value() + col

        # Create a new Window to display the slice
        self.sliceViewDialog = QDialog()
        self.sliceViewDialog.setModal(True)

        self.sliceViewDialog.setGeometry(380, 100, 550, 550)
        self.sliceViewWidget = QWidget(self.sliceViewDialog)

        self.sliceVerticalLayout = QGridLayout(self.sliceViewWidget)
        self.sliceViewDialog.setLayout(self.sliceVerticalLayout.layout())

        # Select the plane slice
        plane = self.resliceComboBox.currentIndex()

        # Select the slice in plane
        if plane == 0:
            array = np.array(self.array3D[slice, :, :])
        elif plane == 1:
            array = np.array(self.array3D[:, slice, :])
        else:
            array = np.array(self.array3D[:, :, slice])

        self.sliceViewDialog.setWindowTitle(self.resliceComboBox.currentText() +
                                            ': Slice ' + str(slice + 1))

        # Contruct an ImageView with the slice selected
        v = pg.ImageView(view=pg.PlotItem())
        self.sliceVerticalLayout.addWidget(v, 0, 0)
        v.setImage(array)

        self.sliceViewDialog.show()

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
        self.lineCompleter.returnPressed.connect(self._onPathEntered)

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

            self.image = pg.ImageView(view=pg.PlotItem())
            plotItem = self.image.getView()
            plotItem.showAxis('bottom', False)
            plotItem.showAxis('left', False)
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

                if self.enableAxis:
                    plotItem = self.image.getView()
                    plotItem.showAxis('bottom', True)
                    plotItem.showAxis('left', True)

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
        else:
            self.imageBox.setupProperties()
            self.imageBox.update()
            self.listWidget.clear()
            self.listWidget.addItem("NO IMAGE FORMAT")

    def volumeSlice(self, imagePath):
        """
        Given 3D data, select a 2D plane and interpolate data along that plane
        to generate a slice image.
        :param imagePath: an em-image
        """
        if self.isEmImage(imagePath):

            # Create an image from imagePath using em-bindings
            img = em.Image()
            loc2 = em.ImageLocation(imagePath)
            img.read(loc2)

            dim = img.getDim()

            self.dx = dim.x
            self.dy = dim.y
            self.dz = dim.z

            x1 = np.linspace(-30, 10, 128)[:, np.newaxis, np.newaxis]
            x2 = np.linspace(-20, 20, 128)[:, np.newaxis, np.newaxis]
            y = np.linspace(-30, 10, 128)[np.newaxis, :, np.newaxis]
            z = np.linspace(-20, 20, 128)[np.newaxis, np.newaxis, :]
            d1 = np.sqrt(x1 ** 2 + y ** 2 + z ** 2)
            d2 = 2 * np.sqrt(x1[::-1] ** 2 + y ** 2 + z ** 2)
            d3 = 4 * np.sqrt(x2 ** 2 + y[:, ::-1] ** 2 + z ** 2)
            data = (np.sin(d1) / d1 ** 2) + (np.sin(d2) / d2 ** 2) + (
                        np.sin(d3) / d3 ** 2)

            self.dx = 128
            self.dy = 128
            self.dz = 128

            self.array3D = np.array(data, copy=False)

            if self.dz > 1:  # The image has a volumes

                # Create a numpy 3D array with the image values pixel
                #array3D = np.array(img, copy=False)

                self.sliceZ = int(self.dz / 2)
                self.sliceY = int(self.dy / 2)
                self.sliceX = int(self.dx / 2)

                # Create a window with three ImageView widgets with
                # central slice on each axis
                self.volumeSliceDialog = QDialog()
                self.volumeSliceDialog.setModal(True)
                self.createVolumeSliceDialog(self.dx, self.dy, self.dz)

                # Display the data on the Top View
                self.topView.setImage(self.array3D[:, self.sliceY, :])
                plotItem = self.topView.getView()
                plotItem.setTitle('Top View')

                # Display the data on the Front View
                self.frontView.setImage(self.array3D[self.sliceZ:, :, :])
                plotItem = self.frontView.getView()
                plotItem.setTitle('Front View')

                # Display the data on the Right View
                self.rightView.setImage(self.array3D[:, :, self.sliceX])
                plotItem = self.rightView.getView()
                plotItem.setTitle('Right View')

                self.volumeSliceDialog.show()

    def closeDialog(self):
        """
        Close the Volume Slicer Window
        """
        self.volumeSliceDialog.close()

    def galleryView(self):
        """
        Create a window to display a Gallery View. This method show slice
        frames around the volume data in a table.
        """

        # Create a main window
        self.galleryViewDialog = QDialog()
        self.galleryViewDialog.setModal(True)

        self.galleryViewDialog.setGeometry(150, 100, 1050, 700)
        self.galleryViewDialog.setWindowTitle('Gallery View')
        self.galleryViewWidget = QWidget(self.galleryViewDialog)

        self.verticalLayout = QVBoxLayout(self.galleryViewWidget)
        self.galleryViewDialog.setLayout(self.verticalLayout.layout())

        # Create a tool bar
        self.galleryViewVerticalLayout = QVBoxLayout()

        self.optionFrame = QFrame(self.galleryViewDialog)
        self.optionFrame.setFrameShape(QFrame.StyledPanel)
        self.optionFrame.setFrameShadow(QFrame.Raised)

        self.horizontalLayout = QHBoxLayout(self.optionFrame)

        self.zoomPushButton = QPushButton(self.optionFrame)
        self.zoomPushButton.setEnabled(False)
        self.zoomPushButton.setIcon(qta.icon('fa.search'))

        self.horizontalLayout.addWidget(self.zoomPushButton)

        self.zoomSpinBox = QSpinBox(self.optionFrame)
        self.zoomSpinBox.setMaximumHeight(400)
        self.zoomSpinBox.setMinimum(50)
        self.zoomSpinBox.setMaximum(300)
        self.zoomSpinBox.setValue(100)
        self.zoomSpinBox.setSingleStep(1)
        self.horizontalLayout.addWidget(self.zoomSpinBox)
        self.zoomSpinBox.valueChanged.connect(self._onSliceZoom)

        self.goToItemPushButton = QPushButton(self.optionFrame)
        self.goToItemPushButton.setEnabled(False)
        self.goToItemPushButton.setIcon(qta.icon('fa.long-arrow-down'))
        self.horizontalLayout.addWidget(self.goToItemPushButton)

        self.gotoItemSpinBox = QSpinBox(self.optionFrame)
        self.gotoItemSpinBox.setMinimum(1)
        self.gotoItemSpinBox.valueChanged.connect(self._onGotoItem)


        self.horizontalLayout.addWidget(self.gotoItemSpinBox)

        self.colsFormLayout = QFormLayout()
        self.colsLabel = QLabel(self.optionFrame)
        self.colsLabel.setText('Cols')

        self.colsFormLayout.setWidget(0, QFormLayout.LabelRole, self.colsLabel)

        self.colsSpinBox = QSpinBox(self.optionFrame)
        self.colsSpinBox.setMinimum(1)
        self.colsSpinBox.setValue(int(np.sqrt(self.dz)))
        self.colsFormLayout.setWidget(0, QFormLayout.FieldRole, self.colsSpinBox)

        self.horizontalLayout.addLayout(self.colsFormLayout)

        self.rowsFormLayout = QFormLayout()
        self.rowsLabel = QLabel(self.optionFrame)
        self.rowsLabel.setText('Rows')

        self.rowsFormLayout.setWidget(0, QFormLayout.LabelRole, self.rowsLabel)

        self.rowsSpinBox = QSpinBox(self.optionFrame)
        self.rowsSpinBox.setValue(int(np.sqrt(self.dz)+1))
        self.rowsSpinBox.setMinimum(1)
        self.rowsFormLayout.setWidget(0, QFormLayout.FieldRole, self.rowsSpinBox)

        self.horizontalLayout.addLayout(self.rowsFormLayout)

        self.resliceComboBox = QComboBox(self.optionFrame)
        self.resliceComboBox.insertItem(0, 'Z Axis (Front View)')
        self.resliceComboBox.insertItem(1, 'Y Axis (Top View)')
        self.resliceComboBox.insertItem(2, 'X Axis (Right View)')
        self.resliceComboBox.currentIndexChanged.connect(self._onGalleryViewPlaneChanged)

        self.horizontalLayout.addWidget(self.resliceComboBox)

        self.optionsHorizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding,
                                       QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.optionsHorizontalSpacer)

        self.galleryViewVerticalLayout.addWidget(self.optionFrame)

        # Create a Table View
        self.tableSlices = QTableWidget()
        self.galleryViewVerticalLayout.addWidget(self.tableSlices)
        self.tableSlices.cellClicked.connect(self._onTableWidgetSliceClicked)
        self.tableSlices.cellDoubleClicked.connect(self.__onTableWidgetSliceDoubleClicked)

        self.verticalLayout.addLayout(self.galleryViewVerticalLayout)

        self.fillTableGalleryView(self.rowsSpinBox.value(),
                                    self.colsSpinBox.value(),
                                    self.resliceComboBox.currentIndex())

        self.galleryViewDialog.show()


    def fillTableGalleryView(self, rowsCount, colsCount, plane):
        """
        Fill the Table Widget with the slices in the specified plane. The images
        displayed represent a slice.
        :param rowCount: count of rows that the table have
        :param colCount: count of columns that the table have
        :param plane: dimension plane (x, y, z)
        :return:
        """
        self.tableSlices.setColumnCount(colsCount)
        self.tableSlices.setRowCount(rowsCount)
        self.tableSlices.clearContents()
        self.gotoItemSpinBox.setValue(1)
        row = 0
        col = 0

        if plane == 0:  # Display the slices on the Front View

            self.gotoItemSpinBox.setMaximum(self.dz)
            for sliceCount in range(0, self.dz):

                sliceZ = self.array3D[sliceCount, :, :]
                self.itemSlice = self.createNewItemSlice(sliceZ, sliceCount+1)
                self.tableSlices.setCellWidget(row, col, self.itemSlice)
                self.tableSlices.setRowHeight(row, 150)
                self.tableSlices.setColumnWidth(col, 150)
                col = col + 1
                if col == colsCount:
                    col = 0
                    row = row + 1

        elif plane == 1:  # Display data slices on the Top View

                self.gotoItemSpinBox.setMaximum(self.dy)
                for sliceCount in range(0, self.dy):

                    sliceY = self.array3D[:, sliceCount, :]
                    self.itemSlice = self.createNewItemSlice(sliceY, sliceCount+1)
                    self.tableSlices.setCellWidget(row, col, self.itemSlice)
                    self.tableSlices.setRowHeight(row, 150)
                    self.tableSlices.setColumnWidth(col, 150)
                    col = col + 1
                    if col == colsCount:
                        col = 0
                        row = row + 1

        else:  # Display the slices on the Right View

            self.gotoItemSpinBox.setMaximum(self.dx)
            for sliceCount in range(0, self.dx):

                sliceX = self.array3D[:, :, sliceCount]
                self.itemSlice = self.createNewItemSlice(sliceX, sliceCount+1)
                self.tableSlices.setCellWidget(row, col, self.itemSlice)
                self.tableSlices.setRowHeight(row, 150)
                self.tableSlices.setColumnWidth(col, 150)
                col = col + 1
                if col == colsCount:
                    col = 0
                    row = row + 1

        self.tableSlices.setCurrentCell(0, 0)

    def createNewItemSlice(self, slice, sliceCount):
        """
        Create a new item taking into account a 2D array(slice) and put this
        into the Table Widget
        return: new item-slice
        """
        frame = QFrame()
        frame.setEnabled(False)
        widget = pg.GraphicsLayoutWidget()
        layout = QGridLayout(frame)
        frame.setLayout(layout.layout())
        layout.addWidget(widget, 0, 0)
        plotArea = widget.addPlot()
        plotArea.showAxis('bottom', False)
        plotArea.showAxis('left', False)
        imageItem = pg.ImageItem()
        plotArea.addItem(imageItem)
        imageItem.setImage(slice)
        plotArea.setTitle('slice ' + str(sliceCount))

        return frame

    def createVolumeSliceDialog(self, x, y, z):
        """
        Create a window with the Volume Slice Dialog

        :param x: number of slices in the right view
        :param y: number of slices in the top view
        :param z: number of slices in the front view
        """
        self.volumeSliceDialog.setGeometry(80, 120, 1200, 500)
        self.volumeSliceDialog.setWindowTitle('Volume Slicer')
        self.sliceWidget = QWidget(self.volumeSliceDialog)
        self.gridLayoutSlice = QGridLayout()

        self.sliceWidget.setLayout(self.gridLayoutSlice)
        self.volumeSliceDialog.setLayout(self.gridLayoutSlice.layout())

        # Create a Top View Slice
        self.topWidget = QWidget()
        self.topGridlayout = QGridLayout()
        self.topWidget.setLayout(self.topGridlayout.layout())

        self.topSlider = QSlider(self.topWidget)
        self.topSlider.setMinimum(0)
        self.topSlider.setMaximum(y-1)
        self.topSlider.setValue(int(y / 2))

        self.topLabelValue = QLabel(self.topWidget)
        self.topLabelValue.setText(str(self.topSlider.value()))
        self.topLabelValue.setAlignment(Qt.AlignCenter)

        self.topSlider.valueChanged.connect(self._onTopSliderChange)
        sizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.topSlider.sizePolicy().hasHeightForWidth())
        self.topSlider.setSizePolicy(sizePolicy)
        self.topSlider.setOrientation(Qt.Horizontal)

        self.topGridlayout.addWidget(self.topLabelValue, 0, 0)
        self.topGridlayout.addWidget(self.topSlider, 1, 0)
        self.topGridlayout.setAlignment(Qt.AlignCenter)

        # Create a Front View Slice
        self.frontWidget = QWidget()
        self.frontGridlayout = QGridLayout()
        self.frontWidget.setLayout(self.frontGridlayout.layout())

        self.frontSlider = QSlider(self.frontWidget)
        self.frontSlider.setMinimum(0)
        self.frontSlider.setMaximum(z-1)
        self.frontSlider.setValue(int(z/2))

        self.frontLabelValue = QLabel(self.topWidget)
        self.frontLabelValue.setText(str(self.frontSlider.value()))
        self.frontLabelValue.setAlignment(Qt.AlignCenter)

        self.frontSlider.valueChanged.connect(self._onFrontSliderChange)
        sizePolicy = QSizePolicy(QSizePolicy.Minimum,
                                 QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.frontSlider.sizePolicy().hasHeightForWidth())
        self.frontSlider.setSizePolicy(sizePolicy)
        self.frontSlider.setOrientation(Qt.Horizontal)

        self.frontGridlayout.addWidget(self.frontLabelValue, 0, 0)
        self.frontGridlayout.addWidget(self.frontSlider, 1, 0)
        self.frontGridlayout.setAlignment(Qt.AlignCenter)

        # Create a Right View Slice
        self.rightWidget = QWidget()
        self.rightGridlayout = QGridLayout()
        self.rightWidget.setLayout(self.rightGridlayout.layout())

        self.rightSlider = QSlider(self.rightWidget)
        self.rightSlider.setMinimum(0)
        self.rightSlider.setMaximum(x-1)
        self.rightSlider.setValue(int(x / 2))

        self.rightLabelValue = QLabel(self.topWidget)
        self.rightLabelValue.setText(str(self.rightSlider.value()))
        self.rightLabelValue.setAlignment(Qt.AlignCenter)

        self.rightSlider.valueChanged.connect(self._onRightSliderChange)
        sizePolicy = QSizePolicy(QSizePolicy.Minimum,
                                 QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.rightSlider.sizePolicy().hasHeightForWidth())
        self.rightSlider.setSizePolicy(sizePolicy)
        self.rightSlider.setOrientation(Qt.Horizontal)

        self.rightGridlayout.addWidget(self.rightLabelValue, 0, 0)
        self.rightGridlayout.addWidget(self.rightSlider, 1, 0)
        self.rightGridlayout.setAlignment(Qt.AlignCenter)

        # Create three ImageView widgets with central slice on each axis
        self.topView = pg.ImageView(self, view=pg.PlotItem())
        self.frontView = pg.ImageView(self, view=pg.PlotItem())
        self.rightView = pg.ImageView(self, view=pg.PlotItem())

        self.gridLayoutSlice.addWidget(self.topView, 0, 0)
        self.gridLayoutSlice.addWidget(self.topWidget, 1, 0)

        self.gridLayoutSlice.addWidget(self.frontView, 0, 1)
        self.gridLayoutSlice.addWidget(self.frontWidget, 1, 1)

        self.gridLayoutSlice.addWidget(self.rightView, 0, 3)
        self.gridLayoutSlice.addWidget(self.rightWidget, 1, 3)

        self.topView.ui.menuBtn.hide()
        self.topView.ui.roiBtn.hide()
        #self.topView.ui.histogram.hide()
        self.frontView.ui.menuBtn.hide()
        self.frontView.ui.roiBtn.hide()
        #self.frontView.ui.histogram.hide()
        self.rightView.ui.menuBtn.hide()
        self.rightView.ui.roiBtn.hide()
        #self.rightView.ui.histogram.hide()

        self.buttonHorizontalLayout = QHBoxLayout(self.volumeSliceDialog)
        """self.buttonHorizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Maximum,
                                             QSizePolicy.Maximum)
        self.buttonHorizontalLayout.addItem(self.buttonHorizontalSpacer)"""

        # Create two Button
        self.galeryViewButton = QPushButton(self.volumeSliceDialog)
        self.galeryViewButton.setText('Galery View')
        self.galeryViewButton.setIcon(qta.icon('fa.eye'))
        self.galeryViewButton.clicked.connect(self._onGalleryViewButtonClicked)

        self.buttonHorizontalLayout.addWidget(self.galeryViewButton)

        self.closeButton = QPushButton(self.volumeSliceDialog)
        self.closeButton.setText('Close')
        self.closeButton.setIcon(qta.icon('fa.times'))
        self.closeButton.clicked.connect(self.closeDialog)

        self.buttonHorizontalLayout.addWidget(self.closeButton)

        self.gridLayoutSlice.addLayout(self.buttonHorizontalLayout, 2, 3)

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









