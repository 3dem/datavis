import sys
import os

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import (pyqtSlot, Qt, QDir, QItemSelectionModel, QModelIndex,
                          QFile, QIODevice, QJsonDocument, QJsonParseError,
                          QItemSelection)
from PyQt5.QtWidgets import (QSplitter, QFileDialog, QMessageBox, QCompleter,
                             QPushButton, QActionGroup, QButtonGroup, QLabel,
                             QSpinBox, QAbstractItemView, QWidget, QVBoxLayout,
                             QLineEdit, QTreeView, QToolBar, QAction,
                             QSizePolicy, QSpacerItem, QFrame)
from PyQt5.QtGui import (QStandardItemModel, QStandardItem,
                         QGuiApplication as QtGuiApp)
import pyqtgraph as pg
import qtawesome as qta

from .picker_model import Micrograph, Coordinate
from .utils import ImageElemParser
from .image_view import ImageView
from ..utils import EmImage, EmPath

SHAPE_RECT = 0
SHAPE_CIRCLE = 1


class PickerView(QWidget):
    def __init__(self, parent, model, **kwargs):
        """ Constructor
        @param parent reference to the parent widget
        @model input PickerDataModel
        kwargs:
           UI config params.
           sources (dict): dict with tuples (mic-path, coordinates-path) or
                           (mic-path, list) where list contains the coordinates
        """
        QWidget.__init__(self, parent)
        self._model = model
        self.currentLabelName = None
        self.__setupUi(**kwargs)
        self._setupTreeView()

        # Completer init
        self._completer = QCompleter()
        self._lineEdit.setCompleter(self._completer)
        # self.completer.setFilterMode(Qt.MatchCaseSensitive)
        self._completer.setModel(self._tvImages.model())
        self._completer.setCompletionColumn(1)
        self._completer.activated[QModelIndex].connect(
            self._onCompleterItemActivated)
        self._currentMic = None
        self._roiList = []
        self._roiAspectLocked = True
        self._roiCentered = True
        self._shape = SHAPE_RECT
        self.removeROIKeyModifier = Qt.ControlModifier

        self.__setup(**kwargs)
        self._spinBoxBoxSize.editingFinished.connect(
            self._boxSizeEditingFinished)

        # Load the input model and check there is at least one micrograph
        #if len(self._model) == 0:
        #    raise Exception("There are not micrographs in the current model.")

        if len(self._model) > 0:
            for mic in self._model:
                self._addMicToTreeView(mic)

        self._setupViewBox()

        sources = kwargs.get("sources", None)
        if isinstance(sources, dict):
            for k in sources.keys():
                mic_path, coord = sources.get(k)
                self._openFile(mic_path, coord=coord, showMic=False,
                               appendCoord=True)

        # By default select the first micrograph in the list
        self._changeTreeViewMic(lambda i: self._tvImages.model().index(0, 0))
        #self._showMicrograph(self._model.images[0])

    def __setup(self, **kwargs):
        """ Configure the PickerView. """
        v = kwargs.get("remove_rois", "on") == "on"
        self._actionErasePickBox.setEnabled(v)
        self._roiAspectLocked = kwargs.get("roi_aspect_locked", "on") == "on"
        self._roiCentered = kwargs.get("roi_centered", "on") == "on"

        self._shape = kwargs.get('shape', SHAPE_RECT)
        if self._shape == SHAPE_RECT:
            self._actionPickRect.setChecked(True)
        else:
            self._actionPickEllipse.setChecked(True)

        self._spinBoxBoxSize.setValue(kwargs.get("boxsize", 100))

    def __setupUi(self, **kwargs):
        self.resize(1097, 741)
        self._horizontalLayout = QtWidgets.QHBoxLayout(self)
        self._splitter = QSplitter(self)
        self._splitter.setObjectName("splitter")
        self._splitter.setOrientation(Qt.Horizontal)
        self._leftPanel = QWidget(self._splitter)
        self._verticalLayout = QVBoxLayout(self._leftPanel)
        self._verticalLayout.setContentsMargins(0, 0, 0, 0)
        toolBarMic = QToolBar(self)
        toolBarMic.setObjectName("toolBarMic")
        self._verticalLayout.addWidget(toolBarMic)
        self._lineEdit = QLineEdit(self._leftPanel)
        self._lineEdit.setObjectName("lineEdit")
        self._verticalLayout.addWidget(self._lineEdit)
        self._tvImages = QTreeView(self._leftPanel)
        self._tvImages.setSortingEnabled(True)
        self._tvImages.setObjectName("treeViewImages")
        self._verticalLayout.addWidget(self._tvImages)
        self._imageView = ImageView(self, **kwargs)
        self._imageView.setObjectName("imageView")
        self._viewWidget = QWidget(self)
        self._viewLayout = QVBoxLayout(self._viewWidget)
        self._viewLayout.setContentsMargins(1, 1, 1, 1)
        self._viewLayout.addWidget(self._imageView)
        self._labelMouseCoord = QLabel(self)
        self._labelMouseCoord.setMaximumHeight(22)
        self._labelMouseCoord.setAlignment(Qt.AlignRight)
        self._viewLayout.addWidget(self._labelMouseCoord)
        self._splitter.addWidget(self._viewWidget)
        self._splitter.setStretchFactor(1, 3)

        def _createNewAction(parent, actionName, text="", faIconName=None,
                             checkable=False):
            a = QtWidgets.QAction(parent)
            a.setObjectName(actionName)
            if faIconName:
                a.setIcon(qta.icon(faIconName))
            a.setCheckable(checkable)
            a.setText(text)
            return a

        imgViewToolBar = self._imageView.getToolBar()

        # picker operations
        actPickerROIS = QAction(imgViewToolBar)
        actPickerROIS.setIcon(qta.icon('fa.object-group'))
        actPickerROIS.setText('Picker Tools')

        boxPanel = QWidget()
        boxPanel.setObjectName('boxPanel')
        boxPanel.setStyleSheet(
            'QWidget#boxPanel{border-left: 1px solid lightgray;}')
        vLayout = QVBoxLayout(boxPanel)
        toolbar = QToolBar(boxPanel)

        self._actionPickRect = _createNewAction(self, "actionPickRect",
                                                "", "fa.square-o",
                                                checkable=True)
        self._actionPickRect.setShortcut(QtGui.QKeySequence(Qt.CTRL + Qt.Key_1))
        self._actionPickRect.setChecked(True)

        self._actionPickEllipse = _createNewAction(self, "actionPickEllipse",
                                                   "", "fa.circle-o",
                                                   checkable=True)
        self._actionPickEllipse.setShortcut(QtGui.QKeySequence(Qt.CTRL +
                                                               Qt.Key_2))
        self._actionPickEllipse.setChecked(False)

        self._actionErasePickBox = _createNewAction(self, "actionErasePickBox",
                                                    "", "fa.eraser",
                                                    checkable=True)
        self._actionErasePickBox.setShortcut(
            QtGui.QKeySequence(Qt.CTRL + Qt.Key_0))
        self._actionErasePickBox.setChecked(False)

        toolbar.addAction(self._actionErasePickBox)
        toolbar.addSeparator()
        toolbar.addAction(self._actionPickRect)
        toolbar.addAction(self._actionPickEllipse)

        vLayout.addWidget(toolbar)

        self._labelBoxSize = QLabel("Size (px)", toolbar)
        self._spinBoxBoxSize = QSpinBox(toolbar)
        self._spinBoxBoxSize.setRange(3, 65535)
        vLayout.addWidget(self._labelBoxSize)
        vLayout.addWidget(self._spinBoxBoxSize)
        vLayout.addWidget(self.__createHLine(boxPanel))

        self._buttonGroup = QButtonGroup(self)
        self._buttonGroup.setExclusive(True)

        for label in self._model.getLabels().values():
            btn = QPushButton(self)
            btn.setText(label["name"])
            btn.setStyleSheet("color: %s;" % label["color"])
            btn.setCheckable(True)
            self._buttonGroup.addButton(btn)
            btn.clicked.connect(self._labelAction_triggered)
            if self.currentLabelName is None:
                self.currentLabelName = label["name"]
                btn.setChecked(True)

            vLayout.addWidget(btn)

        vLayout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum,
                                    QSizePolicy.Expanding))
        imgViewToolBar.addAction(actPickerROIS, boxPanel, exclusive=False)
        # End-picker operations

        self._actionOpenPick = _createNewAction(self, "actionOpenPick",
                                                "Open Pick File",
                                                "fa.folder-open")
        self._actionNextImage = _createNewAction(self, "actionNextImage",
                                                 "",
                                                 "fa.arrow-right")
        self._actionPrevImage = _createNewAction(self, "actionPrevImage", "",
                                                 "fa.arrow-left")

        self._actionGroupPick = QActionGroup(self)
        self._actionGroupPick.setExclusive(True)
        self._actionGroupPick.addAction(self._actionPickRect)
        self._actionGroupPick.addAction(self._actionPickEllipse)

        toolBarMic.addAction(self._actionOpenPick)
        toolBarMic.addSeparator()
        toolBarMic.addAction(self._actionPrevImage)
        toolBarMic.addAction(self._actionNextImage)

        self._horizontalLayout.addWidget(self._splitter)

        self.setWindowTitle("Picker")
        self.retranslateUi()
        QtCore.QMetaObject.connectSlotsByName(self)

    def __createHLine(self, parent):
        line = QFrame(parent)
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        return line

    def _showError(self, msg):
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
            mode = QItemSelectionModel.ClearAndSelect | \
                   QItemSelectionModel.Rows
            self._tvImages.selectionModel().select(nextIndex, mode)

    def _showMicrograph(self, mic):
        """
        Show the an image in the ImageView
        :param mic: the ImageElem
        """
        try:
            self._destroyROIs()
            self._imageView.clear()
            self._currentMic = mic
            path = mic.getPath()
            image = EmImage.load(path)
            self._imageView.setImage(EmImage.getNumPyArray(image))
            self._imageView.setImageInfo(path=path,
                                         format=EmPath.getExt(path),
                                         data_type=str(image.getType()))
            self._createROIs()
        except RuntimeError as ex:
            raise ex
        except Exception as ex:
            raise ex

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
                         for coord in self._currentMic] if self._currentMic \
            else []

    def _updateROIs(self):
        """ Update all ROIs that need to be shown in the current micrographs.
        Remove first the old ones and then create new ones.
        """
        # First destroy the ROIs
        self._destroyROIs()
        # then create new ones
        self._createROIs()

    def _loadMicCoordinates(self, path, parserFunc, clear=True, showMic=True):
        """ Load coordinates for the current selected micrograph.
        Params:
            path: Path that will be parsed and search for coordinates.
            parserFunc: function that will parse the file and yield
                all coordinates.
            clear: Remove all previous coordinates.
            showMic: Show current mic
        """
        if clear:
            self._currentMic.clear()  # remove all coordinates
        for (x, y) in parserFunc(path):
            coord = Coordinate(x, y)
            self._currentMic.addCoordinate(coord)

        if showMic:
            self._showMicrograph(self._currentMic)

    def _openFile(self, path, **kwargs):
        """
        Open de given file.
        kwargs:
             showMic (boolean): True if you want to show the micrograph
                                immediately. False for add to the micrographs
                                list. Default=True.
             coord (path or list): The path to the coordinates file or a list of
                                   tuples for coordinates.
             appendCoord (boolean): True if you want to append the coordinates
                                    to the current coordinates. False to clear
                                    the current coordinates and add.
                                    Default=False.
        """
        _, ext = os.path.splitext(path)

        if ext == '.json':
            self.openPickingFile(path)
        elif ext == '.box':
            from .utils import parseTextCoordinates
            self._loadMicCoordinates(path, parserFunc=parseTextCoordinates,
                                     clear=not kwargs.get("appendCoord", False),
                                     showMic=kwargs.get("showMic", True))
        else:
            from .utils import parseTextCoordinates
            c = kwargs.get("coord", None)
            coord = parseTextCoordinates(c) if isinstance(c, str) else c

            self.openImageFile(path, coord)

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

    def _handleViewBoxClick(self, event):
        """ Invoked when the user clicks on the ViewBox
        (ImageView contains a ViewBox).
        """
        if self._currentMic is None:
            print("not selected micrograph....")
            return

        if (event.button() == QtCore.Qt.LeftButton and
            not self._actionErasePickBox.isChecked()):
            pos = self._imageView.getViewBox().mapToView(event.pos())
            # Create coordinate with event click coordinates and add it
            coord = Coordinate(pos.x(), pos.y(), self.currentLabelName)
            self._currentMic.addCoordinate(coord)
            self._createCoordROI(coord)
            item = self._tvModel.itemFromIndex(
                self._tvImages.selectedIndexes()[2])
            item.setText("%i" % len(self._currentMic))

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
        btn = self._buttonGroup.checkedButton()

        if btn:
            return pg.mkPen(color=self._model.getLabel(btn.text())["color"])

        return pg.mkPen(0, 9)

    def _createCoordROI(self, coord):
        """ Create the CoordROI for a given coordinate.
        This function will take into account the selected ROI shape
        and other global properties.
        """
        if isinstance(coord, tuple):
            coord = Coordinate(coord[0], coord[1], self.currentLabelName)
        roiDict = {
            # 'centered': not self.disableROICentered,
            # 'aspectLocked': self.aspectLocked,
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

        self._imageView.getViewBox().addItem(roi)
        self._roiList.append(coordROI)

        coordROI.showHandlers(False)  # initially hide ROI handlers

        return coordROI

    def _destroyCoordROI(self, roi):
        """ Remove a ROI from the view, from our list and
        disconnect all related slots.
        """
        view = self._imageView.getViewBox()
        view.removeItem(roi)
        # Disconnect from roi the slots.
        roi.sigHoverEvent.disconnect(self._roiMouseHover)
        # roi.sigRemoveRequested.disconnect(self._roiRemoveRequested)
        roi.sigClicked.disconnect(self._roiMouseClicked)

    def _setupViewBox(self):
        """
        Configures the View Widget for self.imageView
        """
        v = self._imageView.getViewBox()

        if v:
            v.mouseClickEvent = self._handleViewBoxClick
            scene = v.scene()
            if scene:
                scene.sigMouseMoved.connect(self.viewBoxMouseMoved)

    @pyqtSlot(object)
    def viewBoxMouseMoved(self, pos):
        """
        This slot is invoked when the mouse is moved hover de View
        :param pos: The mouse pos
        """
        if pos:
            pos = self._imageView.getViewBox().mapSceneToView(pos)
            imgItem = self._imageView.getImageItem()
            (x, y) = (pos.x(), pos.y())
            value = "x"
            (w, h) = (imgItem.width(), imgItem.height())

            if w and h:
                if x >= 0 and x < w and y >= 0 and y < h:
                    value = "%0.4f" % imgItem.image[int(x), int(y)]
            text = "<table width=\"279\" border=\"0\" align=\"right\">" \
                   "<tbody><tr><td width=\"18\" align=\"right\">x=</td>" \
                   "<td width=\"38\" align=\"left\" nowrap>%i</td>" \
                   "<td width=\"28\" align=\"right\">y=</td>" \
                   "<td width=\"42\" nowrap>%i</td>" \
                   "<td width=\"46\" align=\"right\">value=</td>" \
                   "<td width=\"67\" align=\"left\">%s</td></tr>" \
                   "</tbody></table>"
            self._labelMouseCoord.setText(text % (pos.x(), pos.y(), value))

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
        """ Select the next node in the treeview. """
        self._changeTreeViewMic(
            lambda i: self._tvImages.indexBelow(i)
            if i and i.row() < len(self._model) - 1 else
            self._tvImages.model().index(0, 0))

    @pyqtSlot()
    def on_actionPrevImage_triggered(self):
        """ Select the previous micrograph in the treeview. """
        model = self._tvImages.model()
        self._changeTreeViewMic(
            lambda i: self._tvImages.indexAbove(i) if i and i.row() > 0 else
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

    @pyqtSlot(QModelIndex)
    def _onCompleterItemActivated(self, index):
        self._tvImages.setCurrentIndex(
            self._completer.completionModel().mapToSource(index))

    @pyqtSlot(QItemSelection, QItemSelection)
    def _onTreeViewSeleccionChanged(self, selected, deselected):
        """ This should be triggered when the selection changes
        in the TreeView. """

        indexes = self._tvImages.selectedIndexes()
        if indexes:
            item = self._tvModel.itemFromIndex(indexes[0])
            try:
                self._showMicrograph(item.getMicrograph())
            except RuntimeError as ex:
                self._showError(ex.message)

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
        self._updateBoxSize(self._spinBoxBoxSize.value())

    @pyqtSlot(bool)
    def _labelAction_triggered(self, checked):
        """
        This slot is invoked when clicks on label
        """
        btn = self._buttonGroup.checkedButton()

        if checked and btn:
            self.currentLabelName = btn.text()

    @pyqtSlot(object, object)
    def _roiMouseClicked(self, roi, ev):
        """ This slot is invoked when the user clicks on a ROI. """
        e = self._actionErasePickBox.isEnabled() and \
            ev.button() == Qt.LeftButton
        if (e and self._actionErasePickBox.isChecked() or e and
                QtGuiApp.keyboardModifiers() == self.removeROIKeyModifier):
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

    def openImageFile(self, path, coord=None):
        """
        Open an em image for picking
        :param path: file path
        :param coord: coordinate list ([(x1,y1), (x2,y2)...])
        """
        if path:
            try:
                imgElem = Micrograph(0,
                                     path,
                                     coord)
                imgElem.setId(self._model.nextId())
                self._model.addMicrograph(imgElem)
                self._addMicToTreeView(imgElem)
            except:
                print(sys.exc_info())
                self._showError(sys.exc_info()[2])

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
                        self._showError("Parsing pick file: " +
                                        error.errorString())
                    else:
                        parser = ImageElemParser()
                        imgElem = parser.parseImage(json.object())
                        if imgElem:
                            imgElem.setId(self._model.getImgCount()+1)
                            self._model.addMicrograph(imgElem)
                            self._addMicToTreeView(imgElem)
                else:
                    self._showError("Error opening file.")
                    file = None

            except:
                print(sys.exc_info())
            finally:
                if file:
                    file.close()

    def retranslateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self._actionPickRect.setText(_translate("MainWindow", "Pick Rect"))
        self._actionPickEllipse.setText(_translate("MainWindow", "Pick Ellipse"))
        self._actionOpenPick.setText(_translate("MainWindow", "Open Pick"))
        self._actionNextImage.setText(_translate("MainWindow", "Next Image"))
        self._actionPrevImage.setText(_translate("MainWindow", "Prev Image"))
        self._actionErasePickBox.setText(_translate("MainWindow", "Erase pick"))


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


