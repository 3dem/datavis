import sys
import os

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import (pyqtSlot, Qt, QDir, QModelIndex, QItemSelectionModel,
                          QFile, QIODevice, QJsonDocument, QJsonParseError)
from PyQt5.QtWidgets import (QMainWindow, QFileDialog, QMessageBox, QCompleter,
                             QPushButton, QActionGroup, QButtonGroup, QLabel,
                             QSpinBox, QAbstractItemView, QSizePolicy)
from PyQt5.QtGui import QStandardItemModel, QStandardItem
import pyqtgraph as pg
import qtawesome as qta
import numpy as np
import em


from model import Micrograph, Coordinate
from utils import ImageElemParser

SHAPE_RECT = 0
SHAPE_CIRCLE = 1


class PickerWindow(QMainWindow):
    def __init__(self, model, parent=None, **kwargs):
        """ Constructor
        @param parent reference to the parent widget
        @model input PickerDataModel
        """
        QMainWindow.__init__(self, parent)
        self._model = model
        self.__setupUi__()
        self._setupTreeView()

        # Completer init
        self.completer = QCompleter()
        self.lineEdit.setCompleter(self.completer)
        # self.completer.setFilterMode(Qt.MatchCaseSensitive)
        self.completer.setModel(self._tvImages.model())
        # self.completer.activated[QModelIndex].connect(self.on_treeViewImages_clicked)

        self._currentMic = None
        self._roiList = []
        self.currentLabelName = None
        self.removeROIKeyModifier = QtCore.Qt.ControlModifier

        self.disableZoom = kwargs.get('--disable-zoom', False)
        self.disableHistogram = kwargs.get('--disable-histogram', False)
        self.disableROI = kwargs.get('--disable-roi', True)
        self.disableMenu = kwargs.get('--disable-menu', True)
        self.disableRemoveROIs = kwargs.get('--disable-remove-rois', False)
        self.aspectLocked = not kwargs.get('--disable-roi-aspect-locked', False)
        self.disableROICentered = kwargs.get('--disable-roi-centered', False)
        self.disableXAxis = kwargs.get('--disable-x-axis', False)
        self.disableYAxis = kwargs.get('--disable-y-axis', False)

        self._shape = kwargs.get('--shape', SHAPE_RECT)
        if self._shape == SHAPE_RECT:
            self.actionPickRect.setChecked(True)
        else:
            self.actionPickEllipse.setChecked(True)

        self._setupImageView()
        self.spinBoxBoxSize.setValue(self._model.getBoxSize())
        self.spinBoxBoxSize.editingFinished.connect(self._boxSizeEditingFinished)

        # Load the input model and check there is at least one micrograph
        if len(self._model) == 0:
            raise Exception("There are not micrographs in the current model.")

        for mic in self._model:
            self._addMicToTreeView(mic)

        # By default select the first micrograph in the list
        self._changeTreeViewMic(lambda i: self._tvImages.model().index(0, 0))
        #self._showMicrograph(self._model.images[0])

    def showError(self, msg):
        """
        Popup the error msg
        :param msg: The message for the user
        """
        QMessageBox.critical(self, "Particle Picking", msg)

    def _addMicToTreeView(self, mic):
        """
        Add an image to the treeview widget. The user can invoke this method
        when he wants to add an image or connect it to a signal that notifies
        the action of add an ImageElem.
        """
        column1 = MicrographItem(mic, qta.icon("fa.file-o"))

        column2 = MicrographItem(mic)
        column2.setText(os.path.basename(mic.getPath()))

        column3 = MicrographItem(mic)
        column3.setText("%i" % len(mic))

        self._tvModel.appendRow([column1, column2, column3])

        self._tvImages.resizeColumnToContents(0)

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

    def _changeTreeViewMic(self, nextIndexFunc):
        """ This method will change to a different micrograph in the
        TreeView. It should be invoked both for move 'next' or 'back'.
        Params:
           nextIndexFunc: function to return the next index based on
                the current selected index. If None is returned, no
                change will be done
        """
        indexes = self._tvImages.selectedIndexes()
        selectedIndex = indexes[0] if indexes else None
        nextIndex = nextIndexFunc(selectedIndex)

        if nextIndex:
            mode = QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows
            self._tvImages.selectionModel().select(nextIndex, mode)

    @pyqtSlot()
    def on_actionNextImage_triggered(self):
        """ Select the next node in the treeview. """
        self._changeTreeViewMic(lambda i: self._tvImages.indexBelow(i) or
                                          self._tvImages.model().index(0, 0))

    @pyqtSlot()
    def on_actionPrevImage_triggered(self):
        """ Select the previous micrograph in the treeview. """
        model = self._tvImages.model()
        self._changeTreeViewMic(lambda i: self._tvImages.indexAbove(i) or
                                          model.index(model.rowCount()-1, 0))

    @pyqtSlot()
    def on_actionPickEllipse_triggered(self):
        """ Activate the coordinates to ellipse ROI. """
        self._shape = SHAPE_CIRCLE
        self._updateROIs()

    @pyqtSlot()
    def on_actionPickRect_triggered(self):
        """
        Activate the pick rect ROI.
        Change all boxes to rect ROI
        """
        self._shape = SHAPE_RECT
        self._updateROIs()

    def _onTreeViewSeleccionChanged(self, newIndex, oldIndex=None):
        """ This should be triggered when the selection changes in the TreeView. """
        indexes = self._tvImages.selectedIndexes()
        if indexes:
            item = self._tvModel.itemFromIndex(indexes[0])
            self._showMicrograph(item.getMicrograph())

    def _showMicrograph(self, mic):
        """
        Show the an image in the ImageView
        :param mic: the ImageElem
        """
        self._destroyROIs()
        self.imageView.clear()
        self._currentMic = mic
        img = em.Image()
        loc2 = em.ImageLocation(mic.getPath())
        img.read(loc2)
        array = np.array(img, copy=False)
        self.imageView.setImage(array)
        self._createROIs()

    def _destroyROIs(self):
        """
        Remove and destroy all ROIs from the imageView
        """
        for coordROI in self._roiList:
            self._destroyCoordROI(coordROI.getROI())

    def _createROIs(self):
        """ Create the ROIs for current micrograph
        """
        # Create new ROIs and add to the list
        self._roiList = [self._createCoordROI(coord)
<<<<<<< HEAD
                         for coord in self._currentMic.getCoordinates()] \
            if self._currentMic else []

    def _updateROIs(self):
        """ Update all ROIs that need to be shown in the current micrographs.
        Remove first the old ones and then create new ones.
        """
        # First destroy the ROIs
        self._destroyROIs()
        # then create new ones
        self._createROIs()
=======
                         for coord in self._currentMic]
>>>>>>> 973ed37938999a3113a152d7019d17f8e65894cd

    def openImageFile(self, path):
        """
        Open an em image for picking
        :param path: file path
        """
        if path:
            try:
                imgElem = Micrograph(0,
                                     path,
                                     [])
                imgElem.setId(self._model.getImgCount()+1)
                self._model.addMicrograph(imgElem)
                self._addMicToTreeView(imgElem)
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
                            imgElem.setId(self._model.getImgCount()+1)
                            self._model.addMicrograph(imgElem)
                            self._addMicToTreeView(imgElem)
                else:
                    self.showError("Error opening file.")
                    file = None

            except:
                print(sys.exc_info())
            finally:
                if file:
                    file.close()

    def _loadMicCoordinates(self, path, parserFunc):
        """ Load coordinates for the current selected micrograph.
        Params:
            path: Path that will be parsed and search for coordinates.
            parserFunc: function that will parse the file and yield
                all coordinates.
        """
        self._currentMic.clear()  # remove all coordinates
        for (x, y) in parserFunc(path):
            coord = Coordinate(x, y)
            self._currentMic.addCoordinate(coord)

        self._showMicrograph(self._currentMic)

    def _openFile(self, path):
        _, ext = os.path.splitext(path)

        if ext == '.json':
            self.openPickingFile(path)
        elif ext == '.box':
            from utils import parseTextCoordinates
            self._loadMicCoordinates(path, parserFunc=parseTextCoordinates)
        else:
            self.openImageFile(path)

    def _makePen(self, labelName):
        """
        Make the Pen for labelName
        :param labelName: the label name
        :return: pg.makePen
        """
        label = self._model.getLabel(labelName)

        if label:
            return pg.mkPen(color=label["color"])

        return pg.mkPen(color="#FF0004")

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
        self._tvModel = QStandardItemModel()
        self._tvModel.setHorizontalHeaderLabels(["Id",
                                                 "Micrograph",
                                                 "Coordinates"])
        self._tvImages.setModel(self._tvModel)
        self._tvImages.setSelectionBehavior(QAbstractItemView.SelectRows)
        sModel = self._tvImages.selectionModel()
        sModel.selectionChanged.connect(self._onTreeViewSeleccionChanged)

    def __setupUi__(self):
        self.setObjectName("MainWindow")
        self.resize(1097, 741)
        self.centralWidget = QtWidgets.QWidget(self)
        self.centralWidget.setObjectName("centralWidget")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.centralWidget)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.splitter = QtWidgets.QSplitter(self.centralWidget)
        self.splitter.setObjectName("splitter")
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.widget = QtWidgets.QWidget(self.splitter)
        self.verticalLayout = QtWidgets.QVBoxLayout(self.widget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.lineEdit = QtWidgets.QLineEdit(self.widget)
        self.lineEdit.setObjectName("lineEdit")
        self.verticalLayout.addWidget(self.lineEdit)
        self._tvImages = QtWidgets.QTreeView(self.widget)
        self._tvImages.setObjectName("treeViewImages")
        self.verticalLayout.addWidget(self._tvImages)
        self.imageView = pg.ImageView(self, view=pg.PlotItem())
        self.imageView.setObjectName("imageView")
        self.viewWidget = QtWidgets.QWidget(self)
        self.viewLayout = QtWidgets.QVBoxLayout(self.viewWidget)
        self.viewLayout.setContentsMargins(1, 1, 1, 1)
        self.viewLayout.addWidget(self.imageView)
        self.labelMouseCoord = QLabel(self)
        self.labelMouseCoord.setMaximumHeight(22)
        self.labelMouseCoord.setAlignment(Qt.AlignRight)
        self.viewLayout.addWidget(self.labelMouseCoord)
        self.splitter.addWidget(self.viewWidget)
        self.splitter.setStretchFactor(1, 3)
        self.horizontalLayout.addWidget(self.splitter)
        self.setCentralWidget(self.centralWidget)
        self.toolBar = QtWidgets.QToolBar(self)
        self.toolBar.setObjectName("toolBar")
        self.addToolBar(QtCore.Qt.TopToolBarArea, self.toolBar)
        self.menuBar = QtWidgets.QMenuBar(self)
        self.menuBar.setObjectName("menuBar")
        self.menuBar.setGeometry(QtCore.QRect(0, 0, 1097, 26))
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
                                               "fa.square-o",
                                               checkable=True)
        self.actionPickRect.setShortcut(QtGui.QKeySequence(Qt.CTRL + Qt.Key_1))
        self.actionPickRect.setChecked(True)

        self.actionPickEllipse = _createNewAction(self, "actionPickEllipse", "",
                                                  "fa.circle-o",
                                                  checkable=True)
        self.actionPickEllipse.setShortcut(QtGui.QKeySequence(Qt.CTRL +
                                                              Qt.Key_2))
        self.actionPickEllipse.setChecked(False)

        self.actionErasePickBox = _createNewAction(self, "actionErasePickBox",
                                                   "",
                                                   "fa.eraser",
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

        self.toolBar.addAction(self.actionOpenPick)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionPrevImage)
        self.toolBar.addAction(self.actionNextImage)
        self.toolBar.addSeparator()
        self.toolBar.addWidget(self.labelBoxSize)
        self.toolBar.addWidget(self.spinBoxBoxSize)
        self.toolBar.addSeparator()

        self.buttonGroup = QButtonGroup(self)
        self.buttonGroup.setExclusive(True)
        hasLabels = False
        for label in self._model.getLabels().values():
            hasLabels = True
            btn = QPushButton(self)
            btn.setText(label["name"])
            btn.setStyleSheet("color: %s;" % label["color"])
            btn.setCheckable(True)
            btn.setChecked(True)
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
        self.menuFile.addAction(self.actionOpenPick)
        self.menuFile.addSeparator()
        self.menuBar.addAction(self.menuFile.menuAction())

        self.actionGroupPick = QActionGroup(self)
        self.actionGroupPick.setExclusive(True)
        self.actionGroupPick.addAction(self.actionPickRect)
        self.actionGroupPick.addAction(self.actionPickEllipse)

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

    def _handleViewBoxClick(self, event):
        """ Invoked when the user clicks on the ViewBox
        (ImageView contains a ViewBox).
        """
        if self._currentMic is None:
            print "not selected micrograph...."
            return

        if (event.button() == QtCore.Qt.LeftButton and
            not self.actionErasePickBox.isChecked()):
            viewBox = self._getViewBox()
            pos = viewBox.mapToView(event.pos())
            # Create coordinate with event click coordinates and add it
<<<<<<< HEAD
            coord = Coordinate(pos.x(), pos.y(), self.currentLabelName)
            self._currentMic.addPPCoordinate(coord)
            self._createCoordROI(coord)
            item = self.model.itemFromIndex(self.treeViewImages.selectedIndexes()[2])
            item.setText("%i" % self._currentMic.getPickCount())
=======
            coord = Coordinate(pos.x(), pos.y(), self.actualLabelName)
            self._currentMic.addCoordinate(coord)

            self._createCoordROI(coord)
            item = self._tvModel.itemFromIndex(self._tvImages.selectedIndexes()[2])
            item.setText("%i" % len(self._currentMic))
>>>>>>> 973ed37938999a3113a152d7019d17f8e65894cd

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
                    value = "%0.4f" % imgItem.image[int(x), int(y)]
            text = "<table width=\"279\" border=\"0\" align=\"right\">" \
                   "<tbody><tr><td width=\"18\" align=\"right\">x=</td>" \
                   "<td width=\"38\" align=\"left\" nowrap>%i</td>" \
                   "<td width=\"28\" align=\"right\">y=</td>" \
                   "<td width=\"42\" nowrap>%i</td>" \
                   "<td width=\"46\" align=\"right\">value=</td>" \
                   "<td width=\"67\" align=\"left\">%s</td></tr>" \
                   "</tbody></table>"
            self.labelMouseCoord.setText(text % (pos.x(), pos.y(), value))

    @pyqtSlot()
    def completerSelection(self):
        QMessageBox.information(self, "Information", "Not yet implemented")

    @pyqtSlot(int)
    def _boxSizeChanged(self, value):
        """
        This slot is invoked when de value of spinBoxBoxSize is changed
        :param value: The value
        """
        self._updateBoxSize(value)

    @pyqtSlot()
    def _boxSizeEditingFinished(self):
        """
        This slot is invoked when spinBoxBoxSize editing is finished
        """
        self._updateBoxSize(self.spinBoxBoxSize.value())

    @pyqtSlot(bool)
    def _labelAction_triggered(self, checked):
        """
        This slot is invoked when clicks on label
        """
        btn = self.buttonGroup.checkedButton()

        if checked and btn:
            self.currentLabelName = btn.text()

    def _updateBoxSize(self, newBoxSize):
        """ Update the box size to be used. """
        if newBoxSize != self._model.getBoxSize():
            self._model.setBoxSize(newBoxSize)
            # Probably is more efficient to just change size and position
            # of ROIs, but maybe re-creating is good enough
            self._updateROIs()

    def _getSelectedPen(self):
        """
        :return: The selected pen(PPSystem label depending)
        """
        btn = self.buttonGroup.checkedButton()

        if btn:
            return pg.mkPen(color=self._model.getLabel(btn.text())["color"])

        return pg.mkPen(0, 9)

    def _createCoordROI(self, coord):
        """ Create the CoordROI for a given coordinate.
        This function will take into account the selected ROI shape
        and other global properties.
        """
        roiDict = {
            #'centered': not self.disableROICentered,
            #'aspectLocked': self.aspectLocked,
            'pen': self._makePen(coord.getLabel())
        }

        if self._shape == SHAPE_RECT:
            # roiDict['sideScalers'] = sideScalers ??
            roiClass = pg.RectROI
        elif self._shape == SHAPE_CIRCLE:
            roiClass = pg.EllipseROI
        else:
            raise Exception("Unknown shape value: %s" % self._shape)

        coordROI = CoordROI(coord, self._model.getBoxSize(),
                            roiClass, **roiDict)
        roi = coordROI.getROI()

        # Connect some slots we are interested in
        roi.setAcceptedMouseButtons(QtCore.Qt.LeftButton)
        roi.sigHoverEvent.connect(self._roiMouseHover)
        # roi.sigRemoveRequested.connect(self._roiRemoveRequested)
        roi.sigClicked.connect(self._roiMouseClicked)

        self._getViewBox().addItem(roi)
        self._roiList.append(coordROI)

        coordROI.showHandlers(False)  # initially hide ROI handlers

        return coordROI

    def _destroyCoordROI(self, roi):
        """ Remove a ROI from the view, from our list and
        disconnect all related slots.
        """
        view = self._getViewBox()
        view.removeItem(roi)
        # Disconnect from roi the slots.
        roi.sigHoverEvent.disconnect(self._roiMouseHover)
        # roi.sigRemoveRequested.disconnect(self._roiRemoveRequested)
        roi.sigClicked.disconnect(self._roiMouseClicked)

    @pyqtSlot(object, object)
    def _roiMouseClicked(self, roi, event):
        """ This slot is invoked when the user clicks on a ROI. """
        if (event.button() == QtCore.Qt.LeftButton
            and self.actionErasePickBox.isChecked()
            or QtGui.QGuiApplication.keyboardModifiers() == self.removeROIKeyModifier):
            self._destroyCoordROI(roi)
            self._roiList.remove(roi.parent)  # remove the coordROI
            self._currentMic.removeCoordinate(roi.coordinate)
            item = self._tvModel.itemFromIndex(self._tvImages.
                                               selectedIndexes()[2])
            if item:
                item.setText("%i" % len(self._currentMic))

    @pyqtSlot(object)
    def _roiMouseHover(self, roi):
        """ Handler invoked when the roi is hovered by the mouse. """
        roi.parent.showHandlers(False)

    def _getViewBox(self):
        """
        :return: The ViewBox for the self.imageView
        """
        v = self.imageView.getView()
        return v.getViewBox() if isinstance(v, pg.PlotItem) else v

    def _setupViewBox(self):
        """
        Configures the View Widget for self.imageView
        """
        v = self._getViewBox()

        if v:
            v.invertY(False)
            v.mouseClickEvent = self._handleViewBoxClick
            scene = v.scene()
            if scene:
                scene.sigMouseMoved.connect(self.viewBoxMouseMoved)


class MicrographItem(QStandardItem):
    """
    The MicrographItem is the item that we use in the TreeView
    where the images are displayed
    """
    def __init__(self, imgElem, icon=None):
        super(MicrographItem, self).__init__("%i" % imgElem.getId())
        self._micrograph = imgElem
        if icon:
            self.setIcon(icon)

    def getMicrograph(self):
        """ Return the micrographs corresponding to this node (or item). """
        return self._micrograph

class CoordROI:
    """ Class to match between ROI objects and corresponding coordinate """
    def __init__(self, coord, boxSize, roiClass, **kwargs):
        # Lets compute the left-upper corner for the ROI
        half = boxSize / 2
        x = coord.x - half
        y = coord.y - half
        self._roi = roiClass((x, y), (boxSize, boxSize), **kwargs)
        # Set a reference to the corresponding coordinate
        self._roi.coordinate = coord
        self._roi.parent = self

    def getCoord(self):
        """ Return the internal coordinate. """
        return self._roi.coordinate

    def getROI(self):
        return self._roi

    def showHandlers(self, show=True):
        """ Show or hide the ROI handlers. """
        funcName = 'show' if show else 'hide'
        for h in self._roi.getHandles():
            getattr(h, funcName)()  # show/hide


