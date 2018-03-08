import sys
import os

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import (pyqtSlot, Qt, QDir, QModelIndex, QItemSelectionModel,
                          QFile, QIODevice, QJsonDocument, QJsonParseError)
from PyQt5.QtWidgets import (QMainWindow, QFileDialog, QMessageBox, QCompleter,
                             QPushButton, QActionGroup, QButtonGroup, QLabel,
                             QSpinBox, QAbstractItemView)
from PyQt5.QtGui import QStandardItemModel, QStandardItem
import pyqtgraph as pg
import qtawesome as qta
from pyqtgraph import ROI, RectROI, EllipseROI
import numpy as np
import em


from model import PPSystem, ImageElem, PPCoordinate, PPBox
from utils import ImageElemParser


class PPWindow(QMainWindow):

    def __init__(self, parent=None, **kwargs):
        """
        Constructor

        @param parent reference to the parent widget
        @type QWidget
        """
        QMainWindow.__init__(self, parent)
        self.ppSystem = PPSystem()
        self.__setupUi__()
        self.ppSystem = PPSystem()
        self._setupTreeView()

        # Completer init
        self.completer = QCompleter()
        self.lineEdit.setCompleter(self.completer)
        # self.completer.setFilterMode(Qt.MatchCaseSensitive)
        self.completer.setModel(self.treeViewImages.model())
        self.completer.activated[QModelIndex].connect(self.on_treeViewImages_clicked)

        # picking dim in pixels, respect to the image size
        self.pickingW = 200
        self.pickingH = 200
        self.actualImage = None
        self.removeROIKeyModifier = QtCore.Qt.ControlModifier

        self.disableZoom = kwargs.get('--disable-zoom', False)
        self.disableHistogram = kwargs.get('--disable-histogram', False)
        self.disableROI = kwargs.get('--disable-roi', False)
        self.disableMenu = kwargs.get('--disable-menu', False)
        self.disableRemoveROIs = kwargs.get('--disable-remove-rois', False)
        self.disableROIAspectLocked = kwargs.get('--disable-roi-aspect-locked',
                                                 False)
        self.disableROICentered = kwargs.get('--disable-roi-centered', False)
        self.disableXAxis = kwargs.get('--disable-x-axis', False)
        self.disableYAxis = kwargs.get('--disable-y-axis', False)

        for pickFile in kwargs.get('--pick-files', []):
            self._openFile(pickFile)

        self._setupImageView()

        self.spinBoxBoxSize.setValue(self.pickingW)
        #self.spinBoxBoxSize.valueChanged[int].connect(self._boxSizeChanged)
        self.spinBoxBoxSize.editingFinished.connect(
            self._boxSizeEditingFinished)

    @pyqtSlot()
    def showError(self, msg):
        """
        Popup the error msg
        :param msg: The message for the user
        """
        QMessageBox.critical(self, "Particle Picking", msg)

    @pyqtSlot()
    def _on_imageAdded(self, imgElem):
        """
        Add an image to the treeview widget. The user can invoke this method
        when he wants to add an image or connect it to a signal that notifies
        the action of add an ImageElem.
        We use the fa.archive icon from qtawesome temporarily.
        :param imgElem: The image
        """

        if imgElem:
            column1 = PPItem(imgElem, qta.icon("fa.archive"))

            column2 = PPItem(imgElem)
            column2.setText(os.path.basename(imgElem.getPath()))

            column3 = PPItem(imgElem)
            column3.setText("%i" % imgElem.getPickCount())

            self.model.appendRow([column1, column2, column3])

            self.treeViewImages.resizeColumnToContents(0)

    @pyqtSlot()
    def on_actionOpenPick_triggered(self):
        """
        Show a FileDialog for the picking file (.json) selection.
        Open the file, if was selected, and add a new node corresponding
        to the image specified in the file.
        """
        fileName, _ = QFileDialog.getOpenFileName(self, "Open File",
                                                  QDir.currentPath())
        if fileName:
            self._openFile(fileName)

    @pyqtSlot()
    def on_actionNextImage_triggered(self):
        """
        Select the next node in the treeview widget
        """
        indexes = self.treeViewImages.selectedIndexes()

        if indexes:
            selectedIndex = indexes[0]
            nextIndex = self.treeViewImages.indexBelow(selectedIndex)
            if nextIndex:
                if not nextIndex.isValid():  # take first index
                    nextIndex = self.treeViewImages.model().index(0, 0)

                selectionModel = self.treeViewImages.selectionModel()
                selectionModel.select(selectedIndex, QItemSelectionModel.Toggle
                                      | QItemSelectionModel.Rows)
                selectionModel.select(nextIndex, QItemSelectionModel.Toggle
                                      | QItemSelectionModel.Rows)
                self.on_treeViewImages_clicked(nextIndex)

    @pyqtSlot()
    def on_actionPrevImage_triggered(self):
        """
        Select the previous node in the treeview widget
        """
        indexes = self.treeViewImages.selectedIndexes()

        if indexes:
            selectedIndex = indexes[0]
            nextIndex = self.treeViewImages.indexAbove(selectedIndex)
            if nextIndex:
                if not nextIndex.isValid():  # select last row
                    model = self.treeViewImages.model()
                    nextIndex = model.index(model.rowCount()-1, 0)

                selectionModel = self.treeViewImages.selectionModel()
                selectionModel.select(selectedIndex, QItemSelectionModel.Toggle
                                      | QItemSelectionModel.Rows)
                selectionModel.select(nextIndex, QItemSelectionModel.Toggle
                                      | QItemSelectionModel.Rows)
                self.on_treeViewImages_clicked(nextIndex)

    @pyqtSlot()
    def on_actionPickEllipse_triggered(self):
        """
        Activate the pick elipse ROI.
        Change all boxes to ellipse ROI
        """
        v = self._getViewBox()

        for r in v.addedItems[:]:
            if isinstance(r, PPRectROI):
                self._roiRemoveRequested(r, False)
                roi = self._createEllipseROI(r.pos(),
                                             (self.pickingW, self.pickingH),
                                             centered=
                                             not self.disableROICentered,
                                             aspectLocked=not
                                             self.disableROIAspectLocked,
                                             removable=
                                             not self.disableRemoveROIs,
                                             pen=r.pen)
                roi.pickCoord = r.pickCoord
                v.addItem(roi)

    @pyqtSlot()
    def on_actionPickRect_triggered(self):
        """
        Activate the pick rect ROI.
        Change all boxes to rect ROI
        """
        v = self._getViewBox()

        for r in v.addedItems[:]:
            if isinstance(r, PPEllipseROI):
                self._roiRemoveRequested(r, False)
                roi = self._createRectROI(r.pos(),
                                          (self.pickingW, self.pickingH),
                                          centered=not self.disableROICentered,
                                          aspectLocked=not
                                          self.disableROIAspectLocked,
                                          removable=
                                          not self.disableRemoveROIs,
                                          pen=r.pen)
                roi.pickCoord = r.pickCoord
                v.addItem(roi)

    @pyqtSlot(QModelIndex)
    def on_treeViewImages_clicked(self, index):
        """
        This slot is invoked when de user clicks one node in the treeview widget
        :param index: Index for the selected node (or item)
        :return:
        """
        item = self.model.itemFromIndex(index)

        if item:
            self.showImage(item.getImageElem())

    def showImage(self, imgElem):
        """
        Show the an image in the ImageView
        :param imgElem: the ImageElem
        """
        if imgElem:
            self.actualImage = imgElem
            self._clearImageView()  # clean the widget for the new image
            img = em.Image()
            loc2 = em.ImageLocation(imgElem.getPath())
            img.read(loc2)
            array = np.array(img, copy=False)
            self.imageView.setImage(array)
            viewBox = self.imageView.getView()

            for ppCoord in imgElem.getCoordinates():
                roi = None
                if self.actionPickEllipse.isChecked():
                    roi = self._createEllipseROI((ppCoord.x-imgElem.box.width/2,
                                                ppCoord.y-imgElem.box.height/2),
                                                 (imgElem.box.width,
                                                 imgElem.box.height),
                                                 centered=
                                                 not self.disableROICentered,
                                                 aspectLocked=not
                                                 self.disableROIAspectLocked,
                                                 removable=
                                                 not self.disableRemoveROIs,
                                                 pen=(0, 9))
                else:
                    roi = self._createRectROI((ppCoord.x-imgElem.box.width/2,
                                              ppCoord.y-imgElem.box.height/2),
                                              (imgElem.box.width,
                                              imgElem.box.height),
                                              aspectLocked=not
                                              self.disableROIAspectLocked,
                                              centered=not
                                              self.disableROICentered,
                                              pen=(0, 9))

                roi.pickCoord = ppCoord
                viewBox.addItem(roi)

    def _openFile(self, path):
        _, ext = os.path.splitext(path)

        if ext == '.json':
            self.openPickingFile(path)
        else:
            self.openImageFile(path)

    def openImageFile(self, path):
        """
        Open an em image for picking
        :param path: file path
        """
        if path:
            try:
                imgElem = ImageElem(0,
                                    path,
                                    PPBox(self.pickingW, self.pickingH),
                                    [])
                imgElem.setId(self.ppSystem.getImgCount()+1)
                self.ppSystem.addImage(imgElem)
                self._on_imageAdded(imgElem)
            except:
                print(sys.exc_info())
                self.showError(sys.exc_info()[2])

    def openPickingFile(self, path):
        """
        Open the picking specification file an add the ImageElem
        to the treeview widget
        :param path: file path
        """
        file = None
        if path:
            try:
                file = QFile(path)

                if file.open(QIODevice.ReadOnly):
                    error = QJsonParseError()
                    json = QJsonDocument.fromJson(file.readAll(), error)

                    if not error.error == QJsonParseError.NoError:
                        self.showError("Parsing pick file: " +
                                       error.errorString())
                    else:
                        parser = ImageElemParser()
                        imgElem = parser.parseImage(json.object())
                        if imgElem:
                            imgElem.setId(self.ppSystem.getImgCount()+1)
                            self.ppSystem.addImage(imgElem)
                            self._on_imageAdded(imgElem)
                else:
                    self.showError("Error opening file.")
                    file = None

            except:
                print(sys.exc_info())
            finally:
                if file:
                    file.close()

    def _setupImageView(self):
        """
        Setup the ImageView widget used to show the images
        """
        if self.imageView:
            self._setupViewBox()

            if self.disableHistogram:
                self.imageView.ui.histogram.hide()
            if self.disableMenu:
                self.imageView.ui.menuBtn.hide()
            if self.disableROI:
                self.imageView.ui.roiBtn.hide()
            if self.disableZoom:
                self.imageView.getView().setMouseEnabled(False, False)

            plotItem = self.imageView.getView()

            if isinstance(plotItem, pg.PlotItem):
                plotItem.showAxis('bottom', not self.disableXAxis)
                plotItem.showAxis('left', not self.disableYAxis)
                plotItem.showAxis('top', False)

    def _setupTreeView(self):
        """
        Setup the treeview
        """
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(["Id", "Micrograph",
                                              "Coordinates"])
        self.treeViewImages.setModel(self.model)
        self.treeViewImages.setSelectionBehavior(
            QAbstractItemView.SelectRows)

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
        self.imageView = pg.ImageView(self, view=pg.PlotItem())
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

        def _createNewAction(parent, actionName, text="", faIconName=None,
                             checkable=False):
            a = QtWidgets.QAction(parent)
            a.setObjectName(actionName)
            if faIconName:
                a.setIcon(qta.icon(faIconName))
            a.setCheckable(checkable)
            a.setText(text)
            return a

        self.actionPickRect = _createNewAction(self, "actionPickRect", "",
                                               "fa.square",
                                               checkable=True)
        self.actionPickRect.setShortcut(QtGui.QKeySequence(Qt.CTRL + Qt.Key_1))
        self.actionPickRect.setChecked(True)

        self.actionPickEllipse = _createNewAction(self, "actionPickEllipse", "",
                                                  "fa.circle",
                                                  checkable=True)
        self.actionPickEllipse.setShortcut(QtGui.QKeySequence(Qt.CTRL +
                                                              Qt.Key_2))
        self.actionPickEllipse.setChecked(False)

        self.actionErasePickBox = _createNewAction(self, "actionErasePickBox",
                                                   "",
                                                   "fa.eye-slash",
                                                   checkable=True)
        self.actionErasePickBox.setShortcut(
            QtGui.QKeySequence(Qt.CTRL + Qt.Key_0))
        self.actionErasePickBox.setChecked(False)

        self.actionOpenPick = _createNewAction(self, "actionOpenPick",
                                               "Open Pick File",
                                               "fa.folder-open")
        self.actionNextImage = _createNewAction(self, "actionNextImage",
                                                "",
                                                "fa.arrow-right")
        self.actionPrevImage = _createNewAction(self, "actionPrevImage", "",
                                                "fa.arrow-left")

        self.labelBoxSize = QLabel("Size (px)", self)
        self.spinBoxBoxSize = QSpinBox(self)
        self.spinBoxBoxSize.setRange(3, 65535)
        self.labelMouseCoord = QLabel(self)

        self.toolBar.addAction(self.actionOpenPick)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionPrevImage)
        self.toolBar.addAction(self.actionNextImage)
        self.toolBar.addSeparator()
        self.toolBar.addWidget(self.labelBoxSize)
        self.toolBar.addWidget(self.spinBoxBoxSize)
        self.toolBar.addSeparator()

        self.buttonGroup = QButtonGroup(self)
        hasLabels = False
        for label in self.ppSystem.getLabels().values():
            hasLabels = True
            btn = QPushButton(self)
            btn.setText(label["name"])
            btn.setStyleSheet("color: %s;" % label["color"])
            btn.setCheckable(True)
            self.buttonGroup.addButton(btn)
            btn.clicked.connect(self._labelAction_triggered)

            self.toolBar.addWidget(btn)
            self.toolBar.addSeparator()

        if not hasLabels:
            self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionErasePickBox)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionPickRect)
        self.toolBar.addAction(self.actionPickEllipse)
        self.toolBar.addSeparator()
        self.toolBar.addWidget(self.labelMouseCoord)
        self.menuFile.addAction(self.actionOpenPick)
        self.menuFile.addSeparator()
        self.menuBar.addAction(self.menuFile.menuAction())

        self.actionGroupPick = QActionGroup(self)
        self.actionGroupPick.setExclusive(True)
        self.actionGroupPick.addAction(self.actionPickRect)
        self.actionGroupPick.addAction(self.actionPickEllipse)
        self.actionGroupPick.addAction(self.actionErasePickBox)

        self.retranslateUi()
        QtCore.QMetaObject.connectSlotsByName(self)

    def retranslateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.toolBar.setWindowTitle(_translate("MainWindow", "toolBar"))
        self.menuFile.setTitle(_translate("MainWindow", "File"))
        self.actionPickRect.setText(_translate("MainWindow", "Pick Rect"))
        self.actionPickEllipse.setText(_translate("MainWindow", "Pick Ellipse"))
        self.actionOpenPick.setText(_translate("MainWindow", "Open Pick"))
        self.actionNextImage.setText(_translate("MainWindow", "Next Image"))
        self.actionPrevImage.setText(_translate("MainWindow", "Prev Image"))
        self.actionErasePickBox.setText(_translate("MainWindow", "Erase pick"))

    def viewBoxMouseClickEvent(self, ev):
        """
        Invoked when the user clicks
        on the ViewBox (ImageView contains a ViewBox).
        :param ev: Mouse event
        :return:
        """
        if ev.button() == QtCore.Qt.LeftButton:

            pos = ev.pos()
            pos = self._getViewBox().mapToView(pos)

            roi = None
            if self.actionPickRect.isChecked():
                roi = self._createRectROI((pos.x()-self.pickingH/2,
                                           pos.y()-self.pickingW/2),
                                          (self.pickingW, self.pickingH),
                                          centered=not self.disableROICentered,
                                          aspectLocked=not
                                          self.disableROIAspectLocked,
                                          removable=
                                          not self.disableRemoveROIs,
                                          pen=self._getSelectedPen())
            elif self.actionPickEllipse.isChecked():
                roi = self._createEllipseROI((pos.x() - self.pickingH / 2,
                                             pos.y() - self.pickingW / 2),
                                             (self.pickingW, self.pickingH),
                                             centered=
                                             not self.disableROICentered,
                                             aspectLocked=not
                                             self.disableROIAspectLocked,
                                             removable=
                                             not self.disableRemoveROIs,
                                             pen=(0, 9))

            if roi:
                roi.pickCoord = PPCoordinate(pos.x(), pos.y())
                self.imageView.getView().addItem(roi)

                # add coordinate to actual image elem
                if self.actualImage:
                    self.actualImage.\
                        addPPCoordinate(roi.pickCoord)

                    item = self.model.itemFromIndex(self.treeViewImages.
                                                    selectedIndexes()[2])
                    if item:
                        item.setText("%i" % self.actualImage.getPickCount())

    @pyqtSlot(object)
    def viewBoxMouseMoved(self, pos):
        """
        This slot is invoked when the mouse is moved hover de View
        :param pos: The mouse pos
        """
        if pos:
            pos = self._getViewBox().mapSceneToView(pos)
            imgItem = self.imageView.getImageItem()
            (x, y) = (pos.x(), pos.y())
            value = "x"
            (w, h) = (imgItem.width(), imgItem.height())

            if w and h:
                if x>=0 and x<w and y>=0 and y<h:
                    value = "%0.2f" % imgItem.image[int(x), int(y)]

            self.labelMouseCoord.setText(
                    "<span style='font-size: 12pt'>x=%0.1f,   "
                    "<span style='color: red'>y=%0.1f</span>,   "
                    "<span style='color: green'>value=%s</span>" % (
                    pos.x(), pos.y(), value))


    @pyqtSlot()
    def completerSelection(self):
        QMessageBox.information(self, "Information", "Not yet implemented")

    @pyqtSlot(int)
    def _boxSizeChanged(self, value):
        """
        This slot is invoked when de value of spinBoxBoxSize is changed
        :param value: The value
        """
        self.pickingH = value
        self.pickingW = value

        self._updateActualPickBox(self.pickingW, self.pickingH)

    @pyqtSlot()
    def _boxSizeEditingFinished(self):
        """
        This slot is invoked when spinBoxBoxSize editing is finished
        """
        v = self.spinBoxBoxSize.value()
        if not self.pickingW == v:
            self.pickingW = v
            self.pickingH = v
            self._updateActualPickBox(self.pickingW, self.pickingH)
            # update box size to all images ?
            self.ppSystem.setBoxToImages(PPBox(self.pickingW, self.pickingH))

    @pyqtSlot(bool)
    def _labelAction_triggered(self, checked):
        """
        This slot is invoked when clicks on label
        """
        pass

    def _updateActualPickBox(self, w, h):
        """
        Update the box size for the actual image
        :param w: Box width
        :param h: Box height
        """
        if self.actualImage:
            roiSize = (w, h)
            for r in self.imageView.getView().addedItems:
                if isinstance(r, (PPRectROI, PPEllipseROI)):
                    r.setPos(r.pos() + (r.size()-roiSize)/2,
                             update=False, finish=False)
                    r.setSize(roiSize)  # By default finish=True cause
                    # emmit sigRegionChangeFinished signal and all ROIs updated
                    return

    def _getSelectedPen(self):
        """
        :return: The selected pen(PPSystem label depending)
        """
        for btn in self.buttonGroup.buttons():
            if btn.isChecked():
                return pg.mkPen(self.ppSystem.labels[btn.text()]["color"])

        return pg.mkPen(0, 9)

    def _setupROI(self, roi):
        """
        Configure the roi.

        We connect the following slots:

        PPWindow._roiSizeChanged
        PPWindow._roiMouseHover
        PPWindow._roiRemoveRequested
        PPWindow._roiMouseClicked

        :param roi:
        :return:
        """
        if roi:
            roi.setAcceptedMouseButtons(QtCore.Qt.LeftButton)

            roi.sigRegionChangeFinished.connect(self._roiSizeChanged)
            roi.sigHoverEvent.connect(self._roiMouseHover)
            roi.sigRemoveRequested.connect(self._roiRemoveRequested)
            roi.sigClicked.connect(self._roiMouseClicked)

            for h in roi.getHandles():
                h.hide()  # Hide all handlers

    def _createRectROI(self, pos, size, centered=False, sideScalers=False,
                       aspectLocked=True, removable=True, pen=(0, 9)):
        """
        Create a RectROI. The params are in agreement to the constructor
        of the class.
        We connect the following slots:
        See _setupROI for details

        :param pos:
        :param size:
        :param centered:
        :param sideScalers:
        :param args:
        :return:
        """
        roi = PPRectROI(pos, size, centered=centered,
                        sideScalers=sideScalers,
                        aspectLocked=aspectLocked,
                        removable=removable,
                        pen=pen)

        self._setupROI(roi)

        return roi

    def _createEllipseROI(self, pos, size, centered=False, aspectLocked=True,
                          removable=True, pen=(0, 9)):
        """
        Create a EllipseROI. The params are in agreement to the constructor
        of the class.
        We connect the following slots:
        See _setupROI for details

        :param pos:
        :param size:
        :param centered:
        :param sideScalers:
        :param args:
        :return:
        """
        roi = PPEllipseROI(pos, size,
                           aspectLocked=aspectLocked,
                           centered=centered,
                           removable=removable,
                           pen=pen)

        self._setupROI(roi)

        return roi

    @pyqtSlot(object)
    def _roiMouseHover(self, roi):
        """
        This slot is invoked when the mouse enters the ROI.
        We need to show the handlers for user operations
        :param roi: The roi
        """
        for h in roi.getHandles():
            h.show()  # Show all handlers

    @pyqtSlot(object, object)
    def _roiMouseClicked(self, roi, ev):
        """
        This slot is invoked when the user clicks on a ROI
        :param roi:
        :param ev:
        """
        if ev.button() == QtCore.Qt.LeftButton:
            if self.actionErasePickBox.isChecked() or \
                QtGui.QGuiApplication.keyboardModifiers() == \
                    self.removeROIKeyModifier:
                roi.sigRemoveRequested.emit(roi)

    @pyqtSlot(object)
    def _roiSizeChanged(self, roi):
        """
        This slot is invoked when a roi change its size
        :param roi:
        :return:
        """
        if isinstance(roi, (PPRectROI, PPEllipseROI)):  # Only PPRectROI for now
            roiSize = roi.size()
            pos = roi.pos() + roiSize/2

            roi.pickCoord.set(pos.x(), pos.y())

            v = self._getViewBox()

            for r in v.addedItems:
                if isinstance(r, (PPRectROI, PPEllipseROI)) and not r == roi:
                    r.setPos(r.pos() + (r.size()-roiSize)/2,
                             update=False, finish=False)
                    r.setSize(roiSize, finish=False)

            if self.actualImage:
                self.actualImage.setBox(PPBox(roiSize.x(), roiSize.y()))

            self.ppSystem.setBoxToImages(PPBox(int(roiSize.x()),
                                               int(roiSize.y())))
            self.spinBoxBoxSize.setValue(int(roiSize.x()))
            self.pickingH = self.pickingW = int(roiSize.x())

    @pyqtSlot(object)
    def _roiRemoveRequested(self, roi, removePick=True):
        """
        This slot is invoked when the roi will be removed
        :param roi: The roi
        """
        if roi:
            self._getViewBox().removeItem(roi)
            self._disconnectAllSlots(roi)

        if self.actualImage and removePick:
            self.actualImage.removeCoordinate(roi.pickCoord)
            item = self.model.itemFromIndex(self.treeViewImages.
                                            selectedIndexes()[2])
            if item:
                item.setText("%i" % self.actualImage.getPickCount())

    def _disconnectAllSlots(self, roi):
        """
        Disconnect from roi the slots:
        PPWindow._roiSizeChanged
        PPWindow._roiMouseHover
        PPWindow._roiRemoveRequested
        PPWindow._roiMouseClicked
        :param roi:
        :return:
        """
        if roi:
            roi.sigRegionChangeFinished.disconnect(self._roiSizeChanged)
            roi.sigHoverEvent.disconnect(self._roiMouseHover)
            roi.sigRemoveRequested.disconnect(self._roiRemoveRequested)
            roi.sigClicked.disconnect(self._roiMouseClicked)

    def _clearImageView(self):
        """
        Clear the ImageView.
        Note: ImageView has the clear() method, but we need to make others
        operations like disconnect
              the sigRegionChangeFinished signal
        :return:
        """
        v = self._getViewBox()

        for r in v.addedItems[:]:
            if isinstance(r, (PPRectROI, PPEllipseROI)):
                v.removeItem(r)
                self._disconnectAllSlots(r)

        self.imageView.clear()

    def _getViewBox(self):
        """
        :return: The ViewBox for the self.imageView
        """
        v = self.imageView.getView()
        if isinstance(v, pg.PlotItem):
            return v.getViewBox()

        return v

    def _setupViewBox(self):
        """
        Configures the View Widget for self.imageView
        """
        v = self._getViewBox()

        if v:
            v.invertY(False)
            v.mouseClickEvent = self.viewBoxMouseClickEvent
            scene = v.scene()
            if scene:
                scene.sigMouseMoved.connect(self.viewBoxMouseMoved)


class PPItem(QStandardItem):
    """
    The PPItem is the item that we use in the treeview
    where the images are displayed
    """
    def __init__(self, imgElem, icon=None):

        super(PPItem, self).__init__("%i" % imgElem.getImageId())

        self.imgElem = imgElem

        if icon:
            self.setIcon(icon)

    def getImageElem(self):
        """
        :return: The image elem corresponding to this node (or item)
        """
        return self.imgElem


class PPRectROI(RectROI):
    """
    Rect roi for particle picking
    """

    def __init__(self, pos, size, centered=False,
                 sideScalers=False, aspectLocked=True, removable=True,
                 pen=(0,9)):
        RectROI.__init__(self, pos, size,
                         centered=centered, sideScalers=sideScalers,
                         removable=removable, pen=pen)
        self.pickCoord = None
        self.aspectLocked = aspectLocked

    def hoverEvent(self, ev):
        """
        Reimplementation of hoverEvent.
        Hide all handlers
        :param ev: Mouse event
        """
        if ev.isExit():
            for h in self.getHandles():
                h.hide()  # Hide all handlers
        ROI.hoverEvent(self, ev)

    def setPickCoordinate(self, coordinate):
        """
        Set de picking coordinate
        :param coordinate: The PPCoordinate
        """
        self.pickCoord = coordinate

    def getPickCoordinate(self):
        """
        :return:  The PPCoordinate
        """
        return self.pickCoord


class PPEllipseROI(EllipseROI):
    """
    Ellipse roi for particle picking
    """

    def __init__(self, pos, size, aspectLocked=True, centered=True,
                 removable=True, pen=(0, 9)):
        EllipseROI.__init__(self, pos, size,
                            pen=pen)

        self.pickCoord = None
        self.aspectLocked = aspectLocked
        self.removable = removable

        if centered:
            center = [0.5, 0.5]
        else:
            center = [0, 0]

        self.addScaleHandle([0.5 * 2. ** -0.5 + 0.5, 0.5 * 2. ** -0.5 + 0.5],
                            center)

    def hoverEvent(self, ev):
        """
        Reimplementation of hoverEvent.
        Hide all handlers
        :param ev: Mouse event
        """
        if ev.isExit():
            for h in self.getHandles():
                h.hide()  # Hide all handlers
        ROI.hoverEvent(self, ev)

    def setPickCoordinate(self, coordinate):
        """
        Set de picking coordinate
        :param coordinate: The PPCoordinate
        """
        self.pickCoord = coordinate

    def getPickCoordinate(self):
        """
        :return:  The PPCoordinate
        """
        return self.pickCoord

