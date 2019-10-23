
import collections
from math import cos, sin
from numpy import pi

import PyQt5.QtCore as qtc
import PyQt5.QtGui as qtg
import PyQt5.QtWidgets as qtw

import pyqtgraph as pg
import qtawesome as qta


from datavis.widgets import (TriggerAction, OnOffAction, FormWidget)
from datavis.models import (Coordinate, TableConfig, ImageModel)

from ._image_view import ImageView, PenROI
from ._columns import ColumnsView


SHAPE_RECT = 0
SHAPE_CIRCLE = 1
SHAPE_CENTER = 2
SHAPE_SEGMENT = 3

PICK = 0
ERASE = 1

DEFAULT_MODE = 0
FILAMENT_MODE = 1


class PickerView(qtw.QWidget):

    """ Signal emitted when any of the PickerModel parameters have changed. """
    sigPickerParamChanged = qtc.pyqtSignal(int, str, object)

    def __init__(self, parent, model, **kwargs):
        """
        Constructor

        :param parent:  Reference to the parent widget
        :param model:  (datavis.models.PickerDataModel) The input picker model
        :param kwargs:
        """
        qtw.QWidget.__init__(self, parent)
        self._model = model
        self.__currentLabelName = 'Manual'
        self._readOnly = kwargs.get('readOnly', False)
        self._handleSize = 8
        self.__pickerMode = kwargs.get('pickerMode', FILAMENT_MODE)
        self._roiAspectLocked = kwargs.get("roiAspectLocked", True)
        self._roiCentered = kwargs.get("roiCentered", True)

        self._currentMic = None
        self._currentImageDim = None
        self.__segmentROI = None
        self.__mousePressed = False

        self._roiList = []
        self._clickAction = PICK

        if self.__pickerMode == DEFAULT_MODE:
            self._shape = kwargs.get('shape', SHAPE_CIRCLE)
        elif self.__pickerMode == FILAMENT_MODE:
            self._shape = SHAPE_SEGMENT
        else:
            raise Exception("Unknown picking mode '%s'" % self.__pickerMode)

        self.__setupGUI(**kwargs)

        self._spinBoxBoxSize.editingFinished.connect(
            self._boxSizeEditingFinished)

        self._setupViewBox()
        self.__setupErase()

        cols = list(self._model.iterColumns())
        print("cols: %s" % len(cols))
        self._cvImages.setModel(self._model, TableConfig(*cols))
        self._cvImages.setSelectionBehavior(qtw.QAbstractItemView.SelectRows)
        self._cvImages.sigCurrentRowChanged.connect(self.__onCurrentRowChanged)

        # By default select the first micrograph in the list
        if self._model.getRowsCount() > 0:
            self._cvImages.selectRow(0)

        self._validateReadOnlyWidgets()

    def __setupGUI(self, **kwargs):
        """ Create the main GUI of the PickerView.
        The GUI is composed of an ImageView. New action panels will be added to
        the ImageView toolbar
        """
        self.resize(1097, 741)
        horizontalLayout = qtw.QHBoxLayout(self)
        horizontalLayout.setContentsMargins(1, 1, 1, 1)
        self._imageView = ImageView(self, **kwargs)
        imgViewToolBar = self._imageView.getToolBar()

        viewWidget = qtw.QWidget(self)
        viewLayout = qtw.QVBoxLayout(viewWidget)
        viewLayout.setContentsMargins(1, 1, 1, 1)
        viewLayout.addWidget(self._imageView)
        self._labelMouseCoord = qtw.QLabel(self)
        self._labelMouseCoord.setMaximumHeight(22)
        self._labelMouseCoord.setAlignment(qtc.Qt.AlignRight)
        viewLayout.addWidget(self._labelMouseCoord)
        horizontalLayout.addWidget(viewWidget)

        self._actionGroupPick = qtw.QActionGroup(self)
        self._actionGroupPick.setExclusive(True)

        self.__addControlsAction(imgViewToolBar)
        self.__addMicrographsAction(imgViewToolBar, **kwargs)
        self.__addPickerToolAction(imgViewToolBar, self._model.getParams())

        self._spinBoxBoxSize.setValue(self._model.getBoxSize())

        self.setWindowTitle("Picker")

    def __setupErase(self):
        self.__eraseList = []
        self.__eraseSize = 300

        roi = PenROI((0, 0), self.__eraseSize,
                     pen=pg.mkPen(color="FFF", width=1, dash=[2, 2, 2]))
        roi.setVisible(False)
        roi.sigRegionChanged.connect(self.__eraseRoiChanged)
        self._imageView.getViewBox().addItem(roi)
        self.__eraseROI = roi

        roiText = pg.TextItem(text="", color=(220, 220, 0),
                              fill=pg.mkBrush(color=(0, 0, 0, 128)))
        roiText.setVisible(False)
        self._imageView.getViewBox().addItem(roiText)
        self.__eraseROIText = roiText

    def _validateReadOnlyWidgets(self):
        """ Enable/Disable those widgets related to read-only mode. """
        enabled = not self._readOnly
        for attrName in ['_actionPick', '_actionErase', '_actionPickSegment',
                         '_spinBoxBoxSize', '_actionPick', '_actionErase']:
            if hasattr(self, attrName):
                getattr(self, attrName).setEnabled(enabled)

    def __addMicrographsAction(self, toolbar, **kwargs):
        """
        Add micrographs actions to the given toolBar
        :param toolbar: The ImageView toolbar
        :param kwargs: Kwargs arguments for the micrographs ColumnsView
        """
        micPanel = toolbar.createPanel('Micrographs')
        micPanel.setSizePolicy(qtw.QSizePolicy.Ignored, qtw.QSizePolicy.Minimum)
        #  setting a reasonable panel width for micrographs table
        micPanel.setGeometry(0, 0, 200, micPanel.height())
        verticalLayout = qtw.QVBoxLayout(micPanel)
        verticalLayout.setContentsMargins(0, 0, 0, 0)
        cvImages = ColumnsView(micPanel, model=self._model, **kwargs)
        cvImages.setObjectName("columnsViewImages")
        verticalLayout.addWidget(cvImages)
        # keep reference to cvImages
        self._cvImages = cvImages
        self.__createColumsViewModel()
        actMics = TriggerAction(parent=toolbar, actionName='AMics',
                                text='Micrographs', faIconName='fa.list-alt')
        toolbar.addAction(actMics, micPanel, index=0, exclusive=False,
                          checked=True)

    def __addPickerToolAction(self, toolbar, pickerParams=None):
        """
        Add the picker tool actions to the given toolBar
        :param toolbar: The ImageView toolbar
        """
        # picker operations
        actPickerROIS = TriggerAction(parent=None, actionName='APRois',
                                      text='Picker Tools',
                                      faIconName='fa.object-group')

        boxPanel = toolbar.createPanel('boxPanel')

        gLayout = qtw.QVBoxLayout(boxPanel)
        tb = qtw.QToolBar(boxPanel)
        tb.addWidget(qtw.QLabel("<strong>Action:</strong>", tb))

        self._actGroupPickErase = qtw.QActionGroup(self)
        self._actGroupPickErase.setExclusive(True)

        self._actionPick = TriggerAction(
            parent=self, actionName='actionPick', faIconName='fa5s.crosshairs',
            checkable=True, tooltip='Pick',
            shortCut=qtg.QKeySequence(qtc.Qt.Key_1),
            slot=self.__onPickTriggered)
        self._actGroupPickErase.addAction(self._actionPick)
        self._actionPick.setChecked(True)
        self._imageView.addAction(self._actionPick)
        tb.addAction(self._actionPick)

        if self.__pickerMode == DEFAULT_MODE:
            self._actionErase = TriggerAction(
                parent=self, actionName='actionErase',
                faIconName='fa5s.eraser', checkable=True, tooltip='Erase',
                shortCut=qtg.QKeySequence(qtc.Qt.Key_2),
                slot=self.__onEraseTriggered)
            self._actGroupPickErase.addAction(self._actionErase)
            self._imageView.addAction(self._actionErase)
            tb.addAction(self._actionErase)

        gLayout.addWidget(tb)

        tb = qtw.QToolBar(boxPanel)
        tb.addWidget(qtw.QLabel("<strong>Box:</strong>", tb))
        self._labelBoxSize = qtw.QLabel("  Size", tb)
        self._spinBoxBoxSize = qtw.QSpinBox(tb)
        self._spinBoxBoxSize.setRange(3, 65535)
        tb.addWidget(self._labelBoxSize)
        tb.addWidget(self._spinBoxBoxSize)
        tb.addSeparator()

        def _action(name, iconName, checked=False, tooltip='', **kwargs):
            a = TriggerAction(parent=self, actionName=name,
                              faIconName=iconName, checkable=True,
                              tooltip=tooltip, **kwargs)
            a.setChecked(checked)
            tb.addAction(a)
            self._imageView.addAction(a)
            return a

        def _shapeAction(name, iconName, shape, **kwargs):
            a = _action(name, iconName, checked=(self._shape == shape),
                        slot=lambda: self.__onPickShapeChanged(shape),
                        **kwargs)
            self._actionGroupPick.addAction(a)
            return a

        tb.addWidget(qtw.QLabel("  Shape", tb))

        if self.__pickerMode == DEFAULT_MODE:
            self._actionPickRect = _shapeAction(
                'actionPickRect', 'fa5.square', SHAPE_RECT,
                shortCut=qtg.QKeySequence(qtc.Qt.Key_3))

            self._actionPickEllipse = _shapeAction(
                'actionPickEllipse', 'fa5.circle', SHAPE_CIRCLE,
                shortcut=qtg.QKeySequence(qtc.Qt.Key_4))  # FIXME: Not working
        else:
            self._actionPickSegment = _shapeAction(
                'actionPickSegment', 'fa5s.arrows-alt-h', SHAPE_SEGMENT,
                shortCut=qtg.QKeySequence(qtc.Qt.Key_3))

        self._actionPickCenter = _shapeAction(
            'actionPickCenter', 'fa5s.circle', SHAPE_CENTER,
            shortcut=qtg.QKeySequence(qtc.Qt.Key_5),  # FIXME: Not working
            options=[{'scale_factor': 0.25}])

        tb.addSeparator()

        self._actionPickShowHide = OnOffAction(
            tb, toolTipOn='Hide coordinates', toolTipOff='Show coordinates',
            shortCut=qtg.QKeySequence(qtc.Qt.Key_N))
        self._actionPickShowHide.set(True)
        self._actionPickShowHide.sigStateChanged.connect(
            self.__onPickShowHideTriggered)
        tb.addAction(self._actionPickShowHide)
        self._imageView.addAction(self._actionPickShowHide)

        gLayout.addWidget(tb)

        if pickerParams is not None:
            dw = FormWidget(pickerParams, parent=boxPanel, name='pickerParams')
            vLayout = qtw.QVBoxLayout()
            label = qtw.QLabel(self)
            label.setText("<strong>Params:</strong>")
            vLayout.addWidget(label, 0, qtc.Qt.AlignLeft)
            vLayout.addWidget(dw)
            gLayout.addLayout(vLayout)
            dw.setMinimumSize(dw.sizeHint())
            dw.sigValueChanged.connect(self.__onPickerParamChanged)
        else:
            dw = None

        self.__paramsWidget = dw
        sh = gLayout.totalSizeHint()
        boxPanel.setFixedHeight(sh.height())
        toolbar.setPanelMinSize(sh.width())
        self._actionGroupPick.addAction(self._actionPickCenter)
        toolbar.addAction(actPickerROIS, boxPanel, index=0, exclusive=False,
                          checked=True)
        # End-picker operations

    def __onPickerParamChanged(self, paramName, value):
        """ Invoked when a picker-param value is changed """
        micId = self._model.getMicrographByIndex(self._cvImages.getCurrentRow())
        # self._currentMic = self._model[micId]
        # self._showMicrograph(self._currentMic)
        self.sigPickerParamChanged.emit(micId, paramName, value)

    def __addControlsAction(self, toolbar):
        """
        Add the controls actions to the given toolBar
        :param toolbar: The ImageView toolbar
        """
        actControls = TriggerAction(parent=toolbar, actionName='AMics',
                                    text='Controls',
                                    faIconName='fa5s.sliders-h')
        controlsPanel = toolbar.createPanel('Controls')

        gLayout = qtw.QGridLayout(controlsPanel)

        self._controlTable = qtw.QTableWidget(controlsPanel)
        self.__setupControlsTable()
        gLayout.addWidget(self._controlTable)
        toolbar.addAction(actControls, controlsPanel, index=0, exclusive=False,
                          checked=False)

    def __removeHandles(self, roi):
        """ Remove all handles from the given roi """
        if roi is not None:
            for h in roi.getHandles():
                roi.removeHandle(h)

    def __setupControlsTable(self):
        """ Setups the controls table (Help) """
        self._controlTable.setColumnCount(2)
        # Set table header
        self._controlTable.setHorizontalHeaderItem(0,
                                                   qtw.QTableWidgetItem("Tool"))
        self._controlTable.setHorizontalHeaderItem(1,
                                                   qtw.QTableWidgetItem("Help"))
        # Add table items
        # Add row1
        flags = qtc.Qt.ItemIsSelectable | qtc.Qt.ItemIsEnabled
        self.__addRowToControls([(qtw.QTableWidgetItem(qta.icon('fa.list-alt'),
                                                   "Title1"), flags),
                                 (qtw.QTableWidgetItem("Help text"), flags)])
        # Add row2
        self.__addRowToControls([(qtw.QTableWidgetItem(qta.icon('fa5s.user'),
                                                   "Ok ok"), flags),
                                 (qtw.QTableWidgetItem("Help text 2"), flags)])

        # other configurations
        self._controlTable.setSelectionBehavior(
            qtw.QAbstractItemView.SelectRows)
        self._controlTable.setSortingEnabled(True)
        self._controlTable.horizontalHeader().setStretchLastSection(True)
        self._controlTable.resizeColumnsToContents()

    def __updateFilemantText(self, angle, size, pos):
        """ Update the filament text, and pos """
        self.__eraseROIText.setPos(pos)
        self.__eraseROIText.setText('angle=%.2f len=%.2f' % (angle, size))

    def __addRowToControls(self, row):
        """ Add a row to controls table """
        rows = self._controlTable.rowCount()
        self._controlTable.setRowCount(rows + 1)
        for col, v in enumerate(row):
            item = v[0]
            item.setFlags(v[1])
            self._controlTable.setItem(rows, col, item)

    def __updateEraseTextPos(self):
        """ Update the erase text position according to the erase-roi. """
        pos = self.__eraseROI.pos()
        size = self.__eraseROI.size()
        rect2 = self.__eraseROIText.boundingRect()
        rect2 = self.__eraseROIText.mapRectToView(rect2)
        self.__eraseROIText.setPos(pos.x() + size[0] / 2 - rect2.width(),
                                   pos.y() + size[0] / 2)

    def __removeROI(self, roi):
        """ This slot is invoked when the user clicks on a ROI. """
        if roi:
            self._destroyCoordROI(roi)
            self._roiList.remove(roi.parent)  # remove the coordROI
            self._model.removeCoordinates(self._currentMic.getId(),
                                          [roi.coordinate])
            row = self._cvImages.getCurrentRow() % self._cvImages.getPageSize()
            # TODO: Notify deletion
            # self._tvModel.setValue(row, self._coordIndex, len(self._currentMic))
            self._cvImages.updatePage()

    def __createColumsViewModel(self):
        """ Setup the em table """
        self._idIndex = self._model.getColumnsCount() - 1
        self._nameIndex = 0
        self._coordIndex = 1

    def __showHandlers(self, roi, show=True):
        """ Show or hide the ROI handlers. """
        if not isinstance(roi, pg.ScatterPlotItem):
            funcName = 'show' if show else 'hide'
            for h in roi.getHandles():
                getattr(h, funcName)()  # show/hide

    def __openImageFile(self, path, coord=None):
        """
        Open an em image for picking
        :param path: file path
        :param coord: coordinate list ([(x1,y1), (x2,y2)...])
        """
        # FIXME: Check how this will be used in practice
        raise Exception('Not implemented!')

    def _showError(self, msg):
        """
        Popup the error msg
        :param msg: The message for the user
        """
        qtw.QMessageBox.critical(self, "Particle Picking", msg)

    def _showMicrograph(self, mic, fitToSize=False):
        """
        Show the an image in the ImageView
        :param mic: the ImageElem
        """
        self.__eraseROI.setVisible(False)
        self.__eraseROIText.setVisible(False)
        self._destroyROIs()
        self._imageView.clear()
        self._currentMic = mic
        self._currentImageDim = None
        micId = mic.getId()
        self._imageView.setModel(ImageModel(self._model.getData(micId)),
                                 fitToSize)
        self._imageView.setImageInfo(**self._model.getImageInfo(micId))
        self._createROIs()

    def _destroyROIs(self):
        """
        Remove and destroy all ROIs from the pageBar
        """
        if self._roiList:
            for coordROI in self._roiList:
                self._destroyCoordROI(coordROI.getROI())
            self._roiList = []

    def _createROIs(self):
        """ Create the ROIs for current micrograph """
        self._roiList = [
            self._createCoordROI(coord)
            for coord in self._model.iterCoordinates(self._currentMic.getId())
        ]

    def _updateROIs(self):
        """ Update all ROIs that need to be shown in the current micrographs.
        Remove first the old ones and then create new ones.
        """
        if self._roiList:
            size = self._model.getBoxSize()
            for coordROI in self._roiList:
                coordROI.updateSize(size)

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
        # FIXME: Check how this will be used in practice
        raise Exception('Not implemented!')

    def _makePen(self, labelName, width=1):
        """
        Make the Pen for labelName
        :param labelName: the label name
        :return: pg.makePen
        """
        label = self._model.getLabel(labelName)
        if label:
            return pg.mkPen(color=label.color, width=width)

        return pg.mkPen(color="#1EFF00", width=width)

    def _handleViewBoxClick(self, event):
        """ Invoked when the user clicks on the ViewBox
        (ImageView contains a ViewBox).
        """
        pick = event.button() == qtc.Qt.LeftButton and self._clickAction == PICK
        if self._readOnly or not pick:
            return

        if self._currentMic is None:
            print("not selected micrograph....")  # Fixme: can this happens?
            return

        viewBox = self._imageView.getViewBox()
        pos = viewBox.mapToView(event.pos())
        bounds = self._imageView.getImageItem().boundingRect()
        r = self._spinBoxBoxSize.value() / 2
        x, y = pos.x(), pos.y()
        w, h = bounds.width(), bounds.height()

        if not (0 <= x + r <= w and 0 <= x - r <= w and
                0 <= y + r <= h and 0 <= y - r <= h):
            return  # Point out

        def _addCoord(x, y, **kwargs):
            # Create coordinate with event click coordinates and add it
            coord = Coordinate(x, y, label=self.__currentLabelName, **kwargs)
            self._roiList.append(self._createCoordROI(coord))
            self._model.addCoordinates(self._currentMic.getId(), [coord])
            self._cvImages.updatePage()

        if self.__pickerMode == DEFAULT_MODE:
            _addCoord(x, y)

        elif self.__segmentROI is None:  # filament mode
            self.__segPos = pos
            self.__segmentROI = pg.LineSegmentROI(
                [(x, y), (x, y)], pen=self._makePen(self.__currentLabelName, 2))
            viewBox.addItem(self.__segmentROI)
            self.__eraseROIText.setPos(pos)
            self.__eraseROIText.setText("angle=")
            self.__eraseROIText.setVisible(True)

        elif not self.__segPos == pos:  # filament mode
            _addCoord(self.__segPos.x(), self.__segPos.y(), x2=x, y2=y)
            viewBox.removeItem(self.__segmentROI)
            self.__segmentROI = None  # TODO[hv] delete, memory leak???
            self.__eraseROIText.setVisible(False)

    def _updateBoxSize(self, newBoxSize):
        """ Update the box size to be used. """
        if newBoxSize != self._model.getBoxSize():
            self._model.setBoxSize(newBoxSize)
            self._updateROIs()
            self.__eraseROIText.setVisible(False)

    def _getSelectedPen(self):
        """ Return the selected pen(PPSystem label depending) """
        btn = self._buttonGroup.checkedButton()

        if btn:
            return pg.mkPen(color=self._model.getLabel(btn.text())["color"])

        return pg.mkPen(0, 9)

    def _createCoordROI(self, coord):
        """ Create the CoordROI for a given coordinate.
        This function will take into account the selected ROI shape
        and other global properties.
        """
        roiDict = {'pen': self._makePen(coord.label, 2)}
        size = self._model.getBoxSize()

        if self.__pickerMode == DEFAULT_MODE:
            if self._actionPickCenter.isChecked():
                roiClass = pg.ScatterPlotItem
                roiDict['symbol'] = 'o'
                color = qtg.QColor(roiDict['pen'].color())
                roiDict['brush'] = qtg.QBrush(color)
                roiDict['pen'] = pg.mkPen({'color': "FFF", 'width': 1})
                size = 3
            else:
                if self._shape == SHAPE_RECT:
                    roiClass = pg.ROI
                elif self._shape == SHAPE_CIRCLE:
                    roiClass = CircleROI
                else:
                    raise Exception("Unknown shape value: %s" % self._shape)
        else:  # picker-mode : filament
            pickCenter = self._actionPickCenter.isChecked()
            roiClass = pg.LineSegmentROI if pickCenter else pg.ROI

        coordROI = CoordROI(coord, size, roiClass, self._handleSize, **roiDict)
        roi = coordROI.getROI()

        # Connect some slots we are interested in
        roi.setAcceptedMouseButtons(qtc.Qt.LeftButton)
        if not isinstance(roi, pg.ScatterPlotItem):
            roi.setAcceptHoverEvents(True)
            mouseDoubleClickEvent = roi.mouseDoubleClickEvent
            hoverEnterEvent = roi.hoverEnterEvent
            hoverLeaveEvent = roi.hoverLeaveEvent

            def __hoverEnterEvent(ev):
                hoverEnterEvent(ev)
                self.__showHandlers(roi, True)

            def __hoverLeaveEvent(ev):
                hoverLeaveEvent(ev)
                self.__showHandlers(roi, False)

            def __mouseDoubleClickEvent(ev):
                mouseDoubleClickEvent(ev)
                if self._clickAction == PICK:
                    self.__removeROI(roi)

            roi.mouseDoubleClickEvent = __mouseDoubleClickEvent
            roi.hoverEnterEvent = __hoverEnterEvent
            roi.hoverLeaveEvent = __hoverLeaveEvent
            roi.sigRegionChanged.connect(self._roiRegionChanged)
            roi.sigRegionChangeFinished.connect(self._roiRegionChangeFinished)

        roi.setVisible(self._actionPickShowHide.get())
        self._imageView.getViewBox().addItem(roi)
        roi.setFlag(qtw.QGraphicsItem.ItemIsSelectable,
                    self._clickAction == ERASE)
        if self._clickAction == ERASE:
            roi.setAcceptedMouseButtons(qtc.Qt.NoButton)

        roi.translatable = not self._readOnly

        return coordROI

    def _destroyCoordROI(self, roi):
        """ Remove a ROI from the view, from our list and
        disconnect all related slots.
        """
        # Disconnect from roi the slots.
        if not isinstance(roi, pg.ScatterPlotItem):
            roi.sigRegionChanged.disconnect(self._roiRegionChanged)
            roi.sigRegionChangeFinished.disconnect(
                self._roiRegionChangeFinished)
        view = self._imageView.getViewBox()
        view.removeItem(roi)

    def _setupViewBox(self):
        """ Configures the View Widget for self.pageBar """
        v = self._imageView.getViewBox()

        if v:
            v.mouseClickEvent = self._handleViewBoxClick
            wheelEvent = v.wheelEvent

            def __wheelEvent(ev, axis=None):
                mod = ev.modifiers() & qtc.Qt.ControlModifier
                if self._readOnly:
                    wheelEvent(ev, axis=axis)
                elif mod == qtc.Qt.ControlModifier:
                    ex, ey = v.mouseEnabled()
                    v.setMouseEnabled(False, False)
                    d = 1 if ev.delta() > 0 else -1
                    self._spinBoxBoxSize.setValue(
                        self._spinBoxBoxSize.value() + d * 5)
                    self._boxSizeEditingFinished()
                    v.setMouseEnabled(ex, ey)
                    ev.accept()
                else:
                    wheelEvent(ev, axis=axis)
                    if self._clickAction == ERASE:
                        block = self.__eraseROI.blockSignals(True)
                        self.__eraseROI.setVisible(True)
                        self.__eraseROIText.setVisible(True)
                        size = self.__eraseROI.size()[0]
                        dif = -ev.delta() * v.state['wheelScaleFactor']
                        size += dif
                        if size:
                            self.__eraseROI.setSize((size, size), update=False)
                            pos = v.mapToView(ev.pos())
                            self.__eraseROI.setPos((pos.x() - size / 2,
                                                    pos.y() - size / 2))
                            self.__eraseROIText.setText(str(size))
                            self.__updateEraseTextPos()
                        self.__eraseROI.blockSignals(block)

            v.wheelEvent = __wheelEvent

            scene = v.scene()
            if scene:
                scene.sigMouseMoved.connect(self.viewBoxMouseMoved)
                mousePressEvent = scene.mousePressEvent
                mouseReleaseEvent = scene.mouseReleaseEvent

                def __mousePressEvent(ev):
                    mousePressEvent(ev)
                    self.__mousePressed = True

                    if not self._readOnly and self._clickAction == ERASE:
                        self.__eraseROI.setVisible(True)
                        size = self.__eraseROI.size()[0]
                        pos = v.mapSceneToView(ev.pos())
                        pos.setX(pos.x() - size / 2)
                        pos.setY(pos.y() - size / 2)
                        self.__eraseROIText.setVisible(True)
                        self.__eraseROIText.setText(str(size))
                        self.__updateEraseTextPos()
                        self.__eraseRoiChanged(self.__eraseROI)

                def __mouseReleaseEvent(ev):
                    mouseReleaseEvent(ev)
                    if self._readOnly:
                        return
                    self.__mousePressed = False
                    if self._clickAction == ERASE:
                        for item in self.__eraseList:
                            self._roiList.remove(item.parent)
                            self._destroyCoordROI(item)
                            self._model.removeCoordinates(
                                self._currentMic.getId(), [item.coordinate])
                            self._cvImages.updatePage()
                        self.__eraseList = []
                    else:
                        self.__eraseROIText.setVisible(False)

                scene.mousePressEvent = __mousePressEvent
                scene.mouseReleaseEvent = __mouseReleaseEvent

    @qtc.pyqtSlot(object)
    def viewBoxMouseMoved(self, pos):
        """
        This slot is invoked when the mouse is moved hover de View
        :param pos: The mouse pos
        """
        if pos:
            origPos = pos
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

            if self._readOnly:
                pass
            elif self._clickAction == ERASE:
                size = self.__eraseROI.size()[0]
                pos.setX(pos.x() - size / 2)
                pos.setY(pos.y() - size / 2)
                self.__eraseROI.setPos((pos.x(), pos.y()), update=False,
                                       finish=False)
                self.__eraseROI.setVisible(True)
                self.__eraseROIText.setVisible(False)
                if self.__mousePressed:
                    self.__eraseRoiChanged(self.__eraseROI)
            elif self._clickAction == PICK and self.__segmentROI is not None:
                handler = self.__segmentROI.getHandles()[1]
                handler.movePoint(origPos)
                d = pg.Point(pos) - pg.Point(self.__segPos)
                angle = pg.Point(1, 0).angle(d)
                if angle is not None:
                    self.__updateFilemantText(-angle, d.x(), self.__segPos)
                    self.__eraseROIText.setVisible(True)

    def __onPickShapeChanged(self, newShape):
        self._shape = newShape
        self._destroyROIs()
        self._createROIs()

    # @qtc.pyqtSlot()
    # def on_actionPickEllipse_triggered(self):
    #     """ Activate the coordinates to ellipse ROI. """
    #     self._shape = SHAPE_CIRCLE
    #     self._destroyROIs()
    #     self._createROIs()
    #
    # @qtc.pyqtSlot()
    # def on_actionPickSegment_triggered(self):
    #     """ Activate the coordinates to filament ROI. """
    #     self._shape = SHAPE_SEGMENT
    #     self._destroyROIs()
    #     self._createROIs()
    #
    # @qtc.pyqtSlot()
    # def on_actionPickRect_triggered(self):
    #     """
    #     Activate the pick rect ROI.
    #     Change all boxes to rect ROI
    #     """
    #     self._shape = SHAPE_RECT
    #     self._destroyROIs()
    #     self._createROIs()
    #
    # @qtc.pyqtSlot()
    # def on_actionPickCenter_triggered(self):
    #     """
    #     Activate the pick center ROI.
    #     Change all boxes to center ROI
    #     """
    #     self._shape = SHAPE_CENTER
    #     self._destroyROIs()
    #     self._createROIs()

    @qtc.pyqtSlot()
    def __onPickTriggered(self):
        """ Invoked when action pick is triggered """
        view = self._imageView.getViewBox()
        view.setMouseEnabled(True, True)
        self._clickAction = PICK
        self._imageView.getImageView().setCursor(qtc.Qt.ArrowCursor)
        self.__eraseROI.setVisible(False)
        self.__eraseROIText.setVisible(False)
        for roi in view.addedItems:
            isBox = isinstance(roi, CircleROI) or isinstance(roi, pg.ROI)
            if isBox or isinstance(roi, pg.ScatterPlotItem):
                roi.setFlag(qtw.QGraphicsItem.ItemIsSelectable, False)
                roi.setAcceptedMouseButtons(qtc.Qt.LeftButton)

    @qtc.pyqtSlot()
    def __onEraseTriggered(self):
        """ Invoked when action erase is triggered """
        view = self._imageView.getViewBox()
        view.setMouseEnabled(False, False)
        self._clickAction = ERASE
        self._imageView.getImageView().setCursor(qtc.Qt.CrossCursor)
        for roi in view.addedItems:
            isBox = isinstance(roi, CircleROI) or isinstance(roi, pg.ROI)
            isErase = roi == self.__eraseROI
            if (isBox or isinstance(roi, pg.ScatterPlotItem)) and not isErase:
                roi.setFlag(qtw.QGraphicsItem.ItemIsSelectable, True)
                roi.setAcceptedMouseButtons(qtc.Qt.NoButton)

    @qtc.pyqtSlot(int)
    def __onPickShowHideTriggered(self, state):
        """ Invoked when action pick-show-hide is triggered """
        visible = bool(state)
        for roi in self._roiList:
            roi.getROI().setVisible(visible)

    @qtc.pyqtSlot(int)
    def __onCurrentRowChanged(self, row):
        """ Invoked when current row change in micrographs list """
        mic = self._model.getMicrographByIndex(row)
        try:
            if mic != self._currentMic:
                self._showMicrograph(mic)
        except RuntimeError as ex:
            self._showError(ex.message)

    @qtc.pyqtSlot(int)
    def _boxSizeChanged(self, value):
        """
        This slot is invoked when de value of spinBoxBoxSize is changed
        :param value: The value
        """
        self._updateBoxSize(value)

    @qtc.pyqtSlot()
    def _boxSizeEditingFinished(self):
        """
        This slot is invoked when spinBoxBoxSize editing is finished
        """
        self._updateBoxSize(self._spinBoxBoxSize.value())

    @qtc.pyqtSlot(bool)
    def _labelAction_triggered(self, checked):
        """
        This slot is invoked when clicks on label
        """
        btn = self._buttonGroup.checkedButton()

        if checked and btn:
            self.__currentLabelName = btn.text()

    @qtc.pyqtSlot(object)
    def _roiMouseHover(self, roi):
        """ Handler invoked when the roi is hovered by the mouse. """
        self.__showHandlers(roi, roi.mouseHovering)

    @qtc.pyqtSlot(object)
    def __eraseRoiChanged(self, eraseRoi):
        """ Handler invoked when the roi is moved. """
        self.__eraseROIText.setVisible(False)
        viewBox = self._imageView.getViewBox()
        scene = viewBox.scene()
        pos = self.__eraseROI.pos()
        size = self.__eraseROI.size()
        shape = qtg.QPainterPath()
        shape.addEllipse(pos.x(), pos.y(), size[0], size[1])
        scene.setSelectionArea(viewBox.mapViewToScene(shape),
                               qtc.Qt.IntersectsItemShape)
        items = scene.selectedItems()
        for item in items:
            if (not item == self.__eraseROI and item.isVisible() and
                    (isinstance(item, CircleROI) or
                     isinstance(item, pg.ROI) or
                     isinstance(item, pg.ScatterPlotItem))):
                pos = item.pos()
                if not isinstance(item, pg.ScatterPlotItem):
                    size = item.size()
                    pos += size / 2
                    rem = False
                else:
                    rem = True

                if rem or shape.contains(pos):
                    item.setVisible(False)
                    self.__eraseList.append(item)
                    # TODO: Notify the model about changes?
                    # if self._tvModel is not None:
                    #     r = self._cvImages.getCurrentRow()
                    #     self._tvModel.setValue(
                    #         r, self._coordIndex,
                    #         len(self._currentMic) - len(self.__eraseList))
                    #     self._cvImages.updatePage()

    @qtc.pyqtSlot(object)
    def _roiRegionChanged(self, roi):
        """
        Handler invoked when the roi region is changed.
        For example:
           When the user stops dragging the ROI (or one of its handles)
           or if the ROI is changed programatically.
        """
        if self.__pickerMode == DEFAULT_MODE:
            pos = roi.pos()
            size = roi.size()
            if roi.coordinate is not None:
                roi.coordinate.set(x=int(pos.x() + size[0]/2.0),
                                   y=int(pos.y() + size[1]/2.0))
        else:  # filament mode
            self.__updateFilemantText(roi.angle(), roi.size()[0], roi.pos())
            self.__eraseROIText.setVisible(True)

    @qtc.pyqtSlot(object)
    def _roiRegionChangeFinished(self, roi):
        """
        Handler invoked when the roi region is changed.
        For example:
           When the user stops dragging the ROI (or one of its handles)
           or if the ROI is changed programatically.
        """
        if self.__pickerMode == DEFAULT_MODE:
            pos = roi.pos()
            size = roi.size()
            if roi.coordinate is not None:
                roi.coordinate.set(x=int(pos.x() + size[0] / 2.0),
                                   y=int(pos.y() + size[1] / 2.0))
        else:  # filament mode
            viewBox = self._imageView.getViewBox()
            pos1 = viewBox.mapSceneToView(roi.getSceneHandlePositions(0)[1])
            pos2 = viewBox.mapSceneToView(roi.getSceneHandlePositions(1)[1])
            coord = roi.coordinate
            coord.set(x=pos1.x(), y=pos1.y(), x2=pos2.x(), y2=pos2.y())
            if isinstance(roi, pg.ROI):
                width = roi.size().y()
                if not width == self._model.getBoxSize():
                    self._spinBoxBoxSize.setValue(width)
                    self._boxSizeEditingFinished()

    def getPreferredSize(self):
        """
        Returns a tuple (width, height), which represents
        the preferred dimensions to contain all the data
        """
        w, h = self._imageView.getPreferredSize()
        toolBar = self._imageView.getToolBar()

        return w + 100, max(h, toolBar.height())

    def getToolBar(self):
        return self._imageView.getToolBar()


class MicrographItem(qtg.QStandardItem):
    """
    The MicrographItem is the item that we use in the ColumnsView
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


def isFilament(coord):
    """ Helper function to check if the coord is a filament.
    Returns true if coords has 'x2' and 'y2' attributes.
    """
    return all(hasattr(coord, a) for a in ['x2', 'y2'])


class CoordROI:
    """ Class to match between ROI objects and corresponding coordinate """
    def __init__(self, coord, boxSize, roiClass, handleSize, **kwargs):
        # Lets compute the left-upper corner for the ROI
        if roiClass == pg.ScatterPlotItem:
            self._roi = pg.ScatterPlotItem(pos=[(coord.x, coord.y)], **kwargs)

        elif isFilament(coord):
            self._roi = self.__createFilament((coord.x, coord.y),
                                              (coord.x2, coord.y2),
                                              boxSize, roiClass,
                                              handleSize, **kwargs)
        else:
            half = boxSize / 2
            x = coord.x - half
            y = coord.y - half
            self._roi = roiClass((x, y), (boxSize, boxSize), **kwargs)

        # Set a reference to the corresponding coordinate
        self._roi.coordinate = coord
        self._roi.parent = self

    def __calcFilamentSize(self, pos1, pos2, width):
        """
        Calculate the filament size (width x height)
        :param pos1:  (pg.Point) Fist point
        :param pos2:  (pg.Point) Second point
        :param width: (int) The new size
        :return:      (pg.Point, pg.Point, float) A Tuple (pos, size, angle)
        """
        d = pg.Point(pos2) - pg.Point(pos1)
        angle = pg.Point(1, 0).angle(d)
        if angle is None:
            angle = 0
        ra = -angle * pi / 180.
        c = pg.Point(width / 2. * sin(ra), -width / 2. * cos(ra))
        pos1 = pos1 + c

        return pos1, pg.Point(d.length(), width), -angle

    def __createFilament(self, pos1, pos2, width, roiClass, handleSize,
                         **kwargs):
        """
        Create a line or filament according to the given roi class:
        pg.LineSegmentROI or pg.ROI
        """
        if roiClass == pg.ROI:
            pos, size, angle = self.__calcFilamentSize(pos1, pos2, width)
            seg = pg.ROI(pos, size=size, angle=angle, **kwargs)
            seg.handleSize = handleSize
            seg.addScaleRotateHandle([0, 0.5], [1, 0.5])
            seg.addScaleRotateHandle([1, 0.5], [0, 0.5])
            seg.addScaleHandle([1, 0], [1, 1])
            seg.addScaleHandle([0, 1], [0, 0])
            seg.addScaleHandle([0.5, 1], [0.5, 0.5])
        else:
            seg = pg.LineSegmentROI([pos1, pos2], **kwargs)

        return seg

    def getCoord(self):
        """ Return the internal coordinate. """
        return self._roi.coordinate

    def getROI(self):
        return self._roi

    def showHandlers(self, show=True):
        """ Show or hide the ROI handlers. """
        if self._roi and not isinstance(self._roi, pg.ScatterPlotItem):
            funcName = 'show' if show else 'hide'
            for h in self._roi.getHandles():
                getattr(h, funcName)()  # show/hide

    def updateSize(self, size):
        """
        Update the roi size
        :param size: (int) The new size
        """
        if isinstance(self._roi, pg.ROI):
            coord = self._roi.coordinate
            if isFilament(coord):
                pos1 = pg.Point(coord.x, coord.y)
                pos2 = pg.Point(coord.x2, coord.x2)
                pos, size, angle = self.__calcFilamentSize(pos1, pos2, size)
                self._roi.setPos(pos, update=False, finish=False)
                self._roi.setSize(size, update=False, finish=False)
                self._roi.setAngle(angle, update=False, finish=False)
                self._roi.stateChanged(False)
            else:  # CIRCLE or RECT
                self._roi.setSize((size, size), update=False, finish=False)
                half = size / 2
                x = self._roi.coordinate.x - half
                y = self._roi.coordinate.y - half
                self._roi.setPos((x, y), update=False, finish=False)


class CircleROI(pg.CircleROI):
    """ Circular ROI subclass without handles """
    def __init__(self, pos, size, **args):
        pg.ROI.__init__(self, pos, size, **args)
