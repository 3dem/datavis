#!/usr/bin/python
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QFrame, QSizePolicy,
                             QSplitter, QTreeView, QStackedLayout,
                             QFileSystemModel, QLineEdit, QVBoxLayout,
                             QListWidget, QMainWindow, QAction, QToolBar,
                             QLabel, QMessageBox, QCompleter)
from PyQt5.QtCore import (Qt, QCoreApplication, QMetaObject, QDir,
                          QItemSelectionModel, QEvent, pyqtSignal, pyqtSlot)

from emqt5.views import (DataView, createTableModel, createStackModel,
                         VolumeView, ImageView, SlicesView, MOVIE_SIZE)

import qtawesome as qta

from emqt5.utils import EmPath, ImageManager


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
        self._imagePath = path
        self._dataView = DataView(self, **kwargs)
        self._imageView = ImageView(self, **kwargs)
        self._slicesView = SlicesView(self, **kwargs)

        kwargs['tool_bar'] = 'off'
        kwargs['axis'] = 'off'
        self._volumeView = VolumeView(parent=self, **kwargs)
        self._emptyWidget = QWidget(parent=self)
        self.__setupUi()

    def __changePath(self, newPath):
        self._imagePath = newPath
        self.setLineCompleter(self._imagePath)
        self.showFile(self._imagePath)

    def _onPathEntered(self):
        """
        This slot is executed when the Return or Enter key is pressed
        """
        self.__changePath(self._lineCompleter.text())

    def _onPathClick(self, signal):
        """
        This slot is executed when the action "click" inside the tree view
        is realized. The tree view path change
        :param signal: clicked signal
        """
        self.__changePath(self._model.filePath(signal))

    def _onHomeActionClicked(self):
        """
        This Slot lead the TreeView to the user home directory
        """
        self._imagePath = QDir.homePath()
        self.setLineCompleter(self._imagePath)

    def _onRefreshActionClicked(self):
        """
        Refreshes the directory information
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
        """
        Expand the Tree View item specified by the path
        """
        self._imagePath = self._lineCompleter.text()
        index = self._model.index(QDir.toNativeSeparators(self._imagePath))
        self._treeView.selectionModel().select(index,
                                            QItemSelectionModel.ClearAndSelect |
                                            QItemSelectionModel.Rows)

        self._treeView.expand(index)
        self._treeView.scrollTo(index)
        self._treeView.resizeColumnToContents(index.column())

    def eventFilter(self, obj, event):
        """
        Filters events if this object has been installed as an event filter for
        the watched object
        :param obj: watched object
        :param event: event
        :return: True if this object has been installed, False i.o.c
        """

        if event.type() == QEvent.KeyRelease:
            ret = QMainWindow.eventFilter(self, obj, event)
            index = self._treeView.currentIndex()
            file_path = self._model.filePath(index)
            self._imagePath = file_path
            self.setLineCompleter(self._imagePath)
            self.showFile(self._imagePath)
            return ret

        return QMainWindow.eventFilter(self, obj, event)

    def __setupUi(self):

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
        self._treeView.resizeEvent = self.__treeViewResizeEvent
        self.sigTreeViewSizeChanged.connect(self.__treeViewSizeChanged)
        self._treeView.installEventFilter(self)
        self._verticalLayout.addWidget(self._treeView)
        self._treeView.clicked.connect(self._onPathClick)

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
        self._model.setRootPath(QDir.separator())
        self._treeView.setModel(self._model)
        self._treeView.setRootIndex(self._model.index(QDir.separator()))
        self._treeView.setSortingEnabled(True)

        # Config the TreeView completer
        self._completer = QCompleter()
        self._lineCompleter.setCompleter(self._completer)
        self._completer.setModel(self._treeView.model())
        self._treeView.setModel(self._completer.model())

        if not self._imagePath:
            self._imagePath = QDir.separator()
        else:
            self._lineCompleter.setText(self._imagePath)
            self._onPathEntered()
            self._onExpandTreeView()

        self._lineCompleter.textChanged.connect(self._onExpandTreeView)
        self._lineCompleter.returnPressed.connect(self._onPathEntered)

        self.retranslateUi(self)
        QMetaObject.connectSlotsByName(self)

        self.setWindowTitle('EM-BROWSER')
        self._splitter.setStretchFactor(0, 3)
        self._splitter.setStretchFactor(1, 1)

        self._dataView.sigCurrentTableChanged.connect(
            self.__onDataViewTableChanged)

    def __treeViewResizeEvent(self, evt):
        QTreeView.resizeEvent(self._treeView, evt)
        self.sigTreeViewSizeChanged.emit()

    @pyqtSlot()
    def __treeViewSizeChanged(self):
        self._onExpandTreeView()

    @pyqtSlot()
    def __onDataViewTableChanged(self):
        model = self._dataView.getModel()
        if model is not None:
            info = dict()
            info["Type"] = "TABLE"
            info["Dimensions (Rows x Columns)"] = \
                "%d x %d" % (model.totalRowCount(), model.columnCount())
            self.__showInfo(info)

    def retranslateUi(self, MainWindow):
        _translate = QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Browser"))
        self._homeAction.setText(_translate("MainWindow", "Home"))
        self._refreshAction.setText(_translate("MainWindow", "Refresh"))
        self._folderUpAction.setText(_translate("MainWindow",
                                                "Parent Directory"))
        self._label.setText(_translate("MainWindow", "Path"))

    def setLineCompleter(self, newPath):
        """
        Set the path in the Line Edit
        :param imagePath: new path
        :return:
        """
        self._imagePath = newPath
        self._lineCompleter.setText(self._imagePath)

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

        imageView provides:

        1. A zoomable region for displaying the image
        2. A combination histogram and gradient editor (HistogramLUTItem) for
           controlling the visual appearance of the image
        3. Tools for very basic analysis of image data (see ROI and Norm
           buttons)

        :param imagePath: the image path
        """
        try:
            info = {"Type": "UNKNOWN"}
            self._imagePath = imagePath
            if EmPath.isTable(imagePath):
                model = createTableModel(imagePath)
                self._dataView.setModel(model)

                if model is not None and not model.totalRowCount() == 1:
                    self._dataView.setView(DataView.COLUMNS)

                self.__showDataView()
                # Show the Table dimensions
                info["Type"] = "TABLE"
                info["Dimensions (Rows x Columns)"] = \
                    "%d x %d" % (model.totalRowCount(), model.columnCount())

            elif EmPath.isImage(imagePath) or EmPath.isStack(imagePath) \
                    or EmPath.isVolume(imagePath) \
                    or EmPath.isStandardImage(imagePath):
                inf = ImageManager.getInfo(imagePath)
                d = inf['dim']
                info["Dimensions"] = str(d)
                if d.n == 1:  # Single image or volume
                    if d.z == 1:  # Single image
                        image = ImageManager.readImage(imagePath)
                        data = ImageManager.getNumPyArray(image)
                        self._imageView.setImage(data)
                        self._imageView.setImageInfo(
                            path=imagePath, format=inf['ext'],
                            data_type=str(inf['data_type']))
                        info["Type"] = "SINGLE-IMAGE: " + str(inf['data_type'])
                        self.__showImageView()
                    else:  # Volume
                        # The image has a volume. The data is a numpy 3D array.
                        # In this case, display the Top, Front and the Right
                        # View planes.
                        self._frame.setEnabled(True)
                        info["Type"] = "VOLUME: " + str(inf['data_type'])
                        self._volumeView.loadPath(imagePath)
                        self.__showVolumeSlice()
                else:
                    # Image stack
                    if d.z > 1:  # Volume stack
                        self._volumeView.loadPath(self._imagePath)
                        info["Type"] = "VOLUME STACK: " + str(inf['data_type'])
                        self.__showVolumeSlice()
                    else:
                        if d.x <= MOVIE_SIZE:
                            info["Type"] = "IMAGES STACK: " + \
                                           str(inf['data_type'])
                            model = createStackModel(imagePath)
                            self._dataView.setModel(model)
                            self._dataView.setView(DataView.GALLERY)
                            self._dataView.setDataInfo(
                                path=imagePath,
                                format=inf['ext'],
                                data_type=str(inf['data_type']))
                            self.__showDataView()
                        else:
                            info["Type"] = "MOVIE: " + str(inf['data_type'])
                            self._slicesView.setPath(imagePath)
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
                self._infoWidget.addItem("%s: %s" % (str(key), str(info[key])))

    def __clearInfoWidget(self):
        """ Clear the info widget """
        self._infoWidget.clear()
