from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSlot, Qt, QDir, QModelIndex, QItemSelectionModel
from PyQt5.QtWidgets import (QMainWindow, QFileDialog, QMessageBox,
                             QAbstractItemView, QCompleter)
from PyQt5.QtGui import QStandardItemModel, QStandardItem
import pyqtgraph as pg
import qtawesome as qta
from pyqtgraph import ViewBox, GraphicsItem, GraphicsScene
import numpy as np
import em


from apps.ppicking.ppiking_utils import PPSystem, Micrograph

class PPWindow(QMainWindow):

    def __init__(self, parent=None, **kwargs):
        """
        Constructor

        @param parent reference to the parent widget
        @type QWidget
        """
        super(PPWindow, self).__init__(parent)
        self.__setupUi__()
        self.ppSystem = PPSystem()
        self.model = QStandardItemModel()
        self.treeViewImages.setModel(self.model)

        # Completer init
        self.completer = QCompleter()
        self.lineEdit.setCompleter(self.completer)
        # self.completer.setFilterMode(Qt.MatchCaseSensitive)
        self.completer.setModel(self.treeViewImages.model())
        self.completer.activated[QModelIndex].connect(self.on_treeViewImages_clicked)

        # picking dim in pixels, respect to the image size
        self.pickingW = 200
        self.pickingH = 200

    @pyqtSlot()
    def showError(self, errorCode, msg):
        QMessageBox.critical(self, "Particle Picking", "%i : %s"
                                % errorCode % msg)

    @pyqtSlot()
    def microAdded(self, micro):

        item = PPItem(micro.getName(), micro)
        item.setIcon(qta.icon('fa.archive'))
        self.model.appendRow(item)


    @pyqtSlot()
    def on_actionPickRect_triggered(self):

        self.imageView.getView().setMouseMode(ViewBox.RectMode)

    @pyqtSlot()
    def on_actionOpenMicrographs_triggered(self):
        """
        Slot documentation goes here.
        """
        fileName, _ = QFileDialog.getOpenFileName(self, "Open File",
                                                  QDir.currentPath(),
                                                  "(*.json)")
        if fileName:
            micro = self.ppSystem.openMicrograph(fileName)
            if micro:
                self.microAdded(micro)

    @pyqtSlot()
    def on_actionNextImage_triggered(self):

        indexes = self.treeViewImages.selectedIndexes()

        if indexes:
            selectedIndex = indexes[0]
            nextIndex = self.treeViewImages.indexBelow(selectedIndex)
            if nextIndex:
                selectionModel = self.treeViewImages.selectionModel()
                selectionModel.select(selectedIndex, QItemSelectionModel.Toggle)
                selectionModel.select(nextIndex, QItemSelectionModel.Toggle)
                self.on_treeViewImages_clicked(nextIndex)


    @pyqtSlot()
    def on_actionPrevImage_triggered(self):

        indexes = self.treeViewImages.selectedIndexes()

        if indexes:
            selectedIndex = indexes[0]
            nextIndex = self.treeViewImages.indexAbove(selectedIndex)
            if nextIndex:
                selectionModel = self.treeViewImages.selectionModel()
                selectionModel.select(selectedIndex, QItemSelectionModel.Toggle)
                selectionModel.select(nextIndex, QItemSelectionModel.Toggle)
                self.on_treeViewImages_clicked(nextIndex)

    @pyqtSlot(QModelIndex)
    def on_treeViewImages_clicked(self, index):

        item = self.model.itemFromIndex(index)
        if item:
            self.showImage(item.getMicrograph())

    def showImage(self, micro):

        if micro:
            self.imageView.clear()
            img = em.Image()
            loc2 = em.ImageLocation(micro.getPath())
            img.read(loc2)
            array = np.array(img, copy=False)
            self.imageView.setImage(array)
            viewBox = self.imageView.getView()

            for ppRect in micro.getCoordinates():
                roi = pg.RectROI([ppRect.x, ppRect.y], [ppRect.width, ppRect.height], pen=(0,9))
                roi.sigRegionChanged.connect(self.update)
                viewBox.addItem(roi)

    def __setupUi__(self):
        self.setObjectName("MainWindow")
        self.resize(1097, 741)
        self.centralWidget = QtWidgets.QWidget(self)
        self.centralWidget.setObjectName("centralWidget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.centralWidget)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.splitter = QtWidgets.QSplitter(self.centralWidget)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName("splitter")
        self.widget = QtWidgets.QWidget(self.splitter)
        self.widget.setObjectName("widget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.widget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.lineEdit = QtWidgets.QLineEdit(self.widget)
        self.lineEdit.setObjectName("lineEdit")
        self.verticalLayout.addWidget(self.lineEdit)
        self.treeViewImages = QtWidgets.QTreeView(self.widget)
        self.treeViewImages.setObjectName("treeViewImages")
        self.verticalLayout.addWidget(self.treeViewImages)
        self.imageView = pg.ImageView()
        vb = self.imageView.getView()
        vb.mouseClickEvent = self.viewBoxMouseClickEvent

        self.splitter.addWidget(self.imageView)
        self.imageView.setObjectName("imageView")
        self.horizontalLayout.addWidget(self.splitter)
        self.setCentralWidget(self.centralWidget)
        self.toolBar = QtWidgets.QToolBar(self)
        self.toolBar.setObjectName("toolBar")
        self.addToolBar(QtCore.Qt.TopToolBarArea, self.toolBar)
        self.menuBar = QtWidgets.QMenuBar(self)
        self.menuBar.setGeometry(QtCore.QRect(0, 0, 1097, 26))
        self.menuBar.setObjectName("menuBar")
        self.menuFile = QtWidgets.QMenu(self.menuBar)
        self.menuFile.setObjectName("menuFile")
        self.setMenuBar(self.menuBar)
        self.actionPickRect = QtWidgets.QAction(self)
        self.actionPickRect.setCheckable(True)
        self.actionPickRect.setIcon(qta.icon('fa.clone'))
        self.actionPickRect.setObjectName("actionPickRect")
        self.actionOpenMicrographs = QtWidgets.QAction(self)
        self.actionOpenMicrographs.setIcon(qta.icon('fa.folder-open'))
        self.actionOpenMicrographs.setObjectName("actionOpenMicrographs")
        self.actionNextImage = QtWidgets.QAction(self)
        self.actionNextImage.setIcon(qta.icon('fa.arrow-right'))
        self.actionNextImage.setObjectName("actionNextImage")
        self.actionPrevImage = QtWidgets.QAction(self)
        self.actionPrevImage.setIcon(qta.icon('fa.arrow-left'))
        self.actionPrevImage.setObjectName("actionPrevImage")
        self.toolBar.addAction(self.actionOpenMicrographs)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionPrevImage)
        self.toolBar.addAction(self.actionNextImage)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionPickRect)
        self.menuFile.addAction(self.actionOpenMicrographs)
        self.menuFile.addSeparator()
        self.menuBar.addAction(self.menuFile.menuAction())

        self.retranslateUi()
        QtCore.QMetaObject.connectSlotsByName(self)

    def retranslateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.toolBar.setWindowTitle(_translate("MainWindow", "toolBar"))
        self.menuFile.setTitle(_translate("MainWindow", "File"))
        self.actionPickRect.setText(_translate("MainWindow", "PickRect"))
        self.actionOpenMicrographs.setText(_translate("MainWindow", "Open Micrographs"))
        self.actionNextImage.setText(_translate("MainWindow", "Next Image"))
        self.actionPrevImage.setText(_translate("MainWindow", "Prev Image"))


    def viewBoxMouseClickEvent(self, ev):
        if ev.button() == QtCore.Qt.LeftButton and self.actionPickRect.isChecked():
            pos = ev.pos()

            pos = self.imageView.getView().mapToView(pos)
            roi = pg.RectROI([pos.x()-self.pickingH/2, pos.y()-self.pickingW/2], [self.pickingW, self.pickingH], pen=(0, 9))
            roi.sigRegionChanged.connect(self.update)
            self.imageView.getView().addItem(roi)

    @pyqtSlot()
    def completerSelection(self):
        QMessageBox.information(self, "Information", "Not yet implemented")


class PPItem(QStandardItem):


    def __init__(self, text="", micro=None):

        super(PPItem, self).__init__(text)
        self.micro = micro
        
    def getMicrograph(self):
        
        return  self.micro