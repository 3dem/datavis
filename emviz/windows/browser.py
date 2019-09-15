#!/usr/bin/python
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QFrame, QSizePolicy,
                             QSplitter, QTreeView, QStackedLayout,
                             QFileSystemModel, QVBoxLayout,
                             QListWidget, QMainWindow, QAction, QToolBar,
                             QLabel, QMessageBox, QCompleter)
from PyQt5.QtCore import (Qt, QCoreApplication, QMetaObject, QDir,
                          QItemSelectionModel, QEvent, pyqtSignal, pyqtSlot)

from emviz.views import (DataView,  VolumeView, ImageView, SlicesView, ITEMS,
                         COLUMNS, GALLERY)
from emviz.widgets import FileNavigatorPanel, FileBrowser
from emviz.models import EmptyTableModel, EmptySlicesModel, EmptyVolumeModel
from emviz.core import ModelsFactory, ImageManager

import qtawesome as qta

from emviz.core import EmPath, MOVIE_SIZE


class BrowserWindow(QMainWindow):
    """
    Declaration of the class Browser
    This class construct a Browser User Interface
    """
    sigTreeViewSizeChanged = pyqtSignal()  # when the treeview has been resized

    def __init__(self, parent, path, **kwargs):
        """
        kwargs:
         - imageManager: the ImageManager for read/manage image operations. Will
                         be passed to the internal views
        """
        QMainWindow.__init__(self, parent=parent)

        self._dataView = DataView(self, model=EmptyTableModel(), **kwargs)
        self._imageView = ImageView(self, **kwargs)
        self._slicesView = SlicesView(self, EmptySlicesModel(), **kwargs)

        self._volumeView = VolumeView(parent=self, model=EmptyVolumeModel(),
                                      **kwargs)
        self._emptyWidget = QWidget(parent=self)
        kwargs['path'] = path
        self.__setupUi(kwargs)

    def __setupUi(self, kwargs):

        self._centralWidget = QWidget(self)
        self._horizontalLayout = QHBoxLayout(self._centralWidget)
        self._splitter = QSplitter(self._centralWidget)
        self._splitter.setOrientation(Qt.Horizontal)
        self._widget = QWidget(self._splitter)
        self._leftVerticalLayout = QVBoxLayout(self._widget)

        # Create a Tree View
        if kwargs.get('mode') is None:
            kwargs['mode'] = FileBrowser.DIR_MODE
        kwargs['navigate'] = True
        self._navigator = FileNavigatorPanel(self, **kwargs)
        self._navigator.sigIndexSelected.connect(self.__onIndexSelected)
        self._leftVerticalLayout.addWidget(self._navigator)

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
        self._frame.setMinimumHeight(500)
        self._frame.setMinimumWidth(505)

        sizePolicy.setHeightForWidth(self._frame.sizePolicy().
                                     hasHeightForWidth())
        self._frame.setSizePolicy(sizePolicy)
        self._frame.setFrameShape(QFrame.Box)
        self._frame.setFrameShadow(QFrame.Raised)

        self._labelImage = QLabel(self._frame)

        self._imageLayout = QHBoxLayout(self._frame)
        self._stackLayout = QStackedLayout(self._imageLayout)

        self._stackLayout.addWidget(self._volumeView)
        self._stackLayout.addWidget(self._dataView)
        self._stackLayout.addWidget(self._imageView)
        self._stackLayout.addWidget(self._slicesView)
        self._stackLayout.addWidget(self._emptyWidget)

        self._infoWidget = QListWidget(self._imageSplitter)

        self._imageVerticalLayout.addWidget(self._imageSplitter)

        self._widgetsVerticalLayout.addLayout(self._imageVerticalLayout)
        self._horizontalLayout.addWidget(self._splitter)
        self.setCentralWidget(self._centralWidget)

        self.retranslateUi(self)
        QMetaObject.connectSlotsByName(self)

        self.setWindowTitle('EM-BROWSER')
        self._splitter.setStretchFactor(0, 3)
        self._splitter.setStretchFactor(1, 1)

        self._dataView.sigCurrentTableChanged.connect(
            self.__onDataViewTableChanged)

        self.__onIndexSelected(self._navigator.getCurrentIndex())

    def __onIndexSelected(self, index):
        """ Invoked when the selection is changed in the FileNavigator """
        self.showFile(self._navigator.getModel().filePath(index))

    def __onDataViewTableChanged(self):
        model = self._dataView.getModel()
        if model is not None:
            info = dict()
            info["Type"] = "TABLE"
            info["Dimensions (Rows x Columns)"] = \
                "%d x %d" % (model.totalRowCount(), model.columnCount())
            self.__showInfo(info)

    def __showMsgBox(self, text, icon=None, details=None):
        """
        Show a message box with the given text, icon and details.
        The icon of the message box can be specified with one of the Qt values:
            QMessageBox.NoIcon
            QMessageBox.Question
            QMessageBox.Information
            QMessageBox.Warning
            QMessageBox.Critical
        """
        msgBox = QMessageBox()
        msgBox.setText(text)
        msgBox.setStandardButtons(QMessageBox.Ok)
        msgBox.setDefaultButton(QMessageBox.Ok)
        if icon is not None:
            msgBox.setIcon(icon)
        if details is not None:
            msgBox.setDetailedText(details)

        msgBox.exec_()

    def __showInfo(self, info):
        """
        Show the information in the corresponding widget.
        info is a dict
        """
        self.__clearInfoWidget()
        if isinstance(info, dict):
            for key in info.keys():
                self._infoWidget.addItem("%s: %s" % (str(key).capitalize(),
                                                     str(info[key])))

    def __clearInfoWidget(self):
        """ Clear the info widget """
        self._infoWidget.clear()

    def __showVolumeSlice(self):
        """Show the Volume Slicer component"""
        self._stackLayout.setCurrentWidget(self._volumeView)

    def __showDataView(self):
        """Show the Table View component"""
        self._stackLayout.setCurrentWidget(self._dataView)

    def __showImageView(self):
        """ Show the ImageView component """
        self._stackLayout.setCurrentWidget(self._imageView)

    def __showSlicesView(self):
        """ Show the SlicesView component """
        self._stackLayout.setCurrentWidget(self._slicesView)

    def __showEmptyWidget(self):
        """Show an empty widget"""
        self._stackLayout.setCurrentWidget(self._emptyWidget)

    def showFile(self, imagePath):
        """
        This method display an image using of pyqtgraph ImageView, a volume
        using the VOLUME-SLICER or GALLERY-VIEW components, a image stack or
        a Table characteristics.

        pageBar provides:

        1. A zoomable region for displaying the image
        2. A combination histogram and gradient editor (HistogramLUTItem) for
           controlling the visual appearance of the image
        3. Tools for very basic analysis of image data (see ROI and Norm
           buttons)

        :param imagePath: the image path
        """
        try:
            info = {'Type': 'UNKNOWN'}
            self._imagePath = imagePath
            if EmPath.isTable(imagePath):
                model = ModelsFactory.createTableModel(imagePath)
                self._dataView.setModel(model)
                if not model.getRowsCount() == 1:
                    self._dataView.setView(COLUMNS)
                else:
                    self._dataView.setView(ITEMS)

                self.__showDataView()
                # Show the Table dimensions
                info['Type'] = 'TABLE'
                dimStr = "%d x %d" % (model.getRowsCount(),
                                      model.getColumnsCount())
                info['Dimensions (Rows x Columns)'] = dimStr
            elif EmPath.isData(imagePath) or EmPath.isStandardImage(imagePath):
                info = ImageManager().getInfo(imagePath)
                d = info['dim']
                if d.n == 1:  # Single image or volume
                    if d.z == 1:  # Single image
                        model = ModelsFactory.createImageModel(imagePath)
                        self._imageView.setModel(model)
                        self._imageView.setImageInfo(
                            path=imagePath, format=info['ext'],
                            data_type=str(info['data_type']))
                        info['Type'] = 'SINGLE-IMAGE'
                        self.__showImageView()
                    else:  # Volume
                        # The image has a volume. The data is a numpy 3D array.
                        # In this case, display the Top, Front and the Right
                        # View planes.
                        self._frame.setEnabled(True)
                        info['type'] = "VOLUME"
                        model = ModelsFactory.createVolumeModel(imagePath)
                        self._volumeView.setModel(model)
                        self.__showVolumeSlice()
                else:
                    # Image stack
                    if d.z > 1:  # Volume stack
                        raise Exception("Volume stack is not supported")
                    elif d.x <= MOVIE_SIZE:
                        info['type'] = 'IMAGES STACK'
                        model = ModelsFactory.createTableModel(imagePath)
                        self._dataView.setModel(model)
                        self._dataView.setView(GALLERY)
                        self.__showDataView()
                    else:
                        info['type'] = 'MOVIE'
                        model = ModelsFactory.createStackModel(imagePath)
                        self._slicesView.setModel(model)
                        self.__showSlicesView()
                    # TODO Show the image type
            else:
                self.__showEmptyWidget()

            self.__showInfo(info)
        except Exception as ex:
            self.__showMsgBox("Error opening the file", QMessageBox.Critical,
                              str(ex))
            self.__showEmptyWidget()
        except RuntimeError as ex:
            self.__showMsgBox("Error opening the file", QMessageBox.Critical,
                              str(ex))
            self.__showEmptyWidget()

    def retranslateUi(self, MainWindow):
        _translate = QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Browser"))
