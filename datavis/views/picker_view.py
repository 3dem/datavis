
from math import cos, sin
from numpy import pi

import PyQt5.QtCore as qtc
import PyQt5.QtGui as qtg
import PyQt5.QtWidgets as qtw

import pyqtgraph as pg
import qtawesome as qta


from datavis.widgets import (TriggerAction, OnOffAction, FormWidget)
from datavis.models import (TableConfig, ImageModel)

from ._image_view import ImageView, PenROI
from ._columns import ColumnsView
from ._constants import DATA


SHAPE_RECT = 0
SHAPE_CIRCLE = 1
SHAPE_CENTER = 2
SHAPE_SEGMENT = 3
SHAPE_SEGMENT_LINE = 4

PICK = 0
ERASE = 1

DEFAULT_MODE = 0
FILAMENT_MODE = 1


class PickerView(qtw.QWidget):
    """ The PickerView widget provides functionality for displaying picking
    operations provided by a PickerModel. Additionally, operations can be
    carried out on the model, previously configured based on the parameters
    provided by the model. """

    """ Signal emitted when any of the PickerModel parameters have changed. """
    sigPickerParamChanged = qtc.pyqtSignal(int, str, object)

    def __init__(self, model, **kwargs):
        """
        Construct an PickerView instance

        Args:
            model:  :class:`~datavis.models.PickerModel`

        Keyword Args:
            parent:   Reference to the parent widget
            readOnly: (boolean) If True, the PickerView will be in read-only
                      mode in which case users will not be able to pick.
            pickerMode: (int) Specify the picker mode: FILAMENT_MODE or
                        DEFAULT_MODE.
            shape:     (int) The initial shape type: SHAPE_RECT, SHAPE_CIRCLE,
                       SHAPE_CENTER, SHAPE_SEGMENT.
            The :class:`ImageView <datavis.views.ImageView>` kwargs

        """
        qtw.QWidget.__init__(self, parent=kwargs.get('parent'))
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

        self._isFilament = self.__pickerMode == FILAMENT_MODE

        self.__setupGUI(**kwargs)

        self._spinBoxBoxSize.editingFinished.connect(
            self._boxSizeEditingFinished)

        self._setupViewBox()
        self.__setupErase()

        cols = list(self._model.iterColumns())
        self._cvImages.setModel(self._model, TableConfig(*cols))
        self._cvImages.setSelectionBehavior(qtw.QAbstractItemView.SelectRows)
        self._cvImages.sigCurrentRowChanged.connect(self.__onCurrentRowChanged)

        # By default select the first micrograph in the list
        if self._model.getRowsCount() > 0:
            self._cvImages.selectRow(0)

        self._validateReadOnlyWidgets()
        w, h = self.getPreferredSize()
        self.setGeometry(0, 0, w, h)

    def __setupGUI(self, **kwargs):
        """ Create the main GUI of the PickerView.
        The GUI is composed of an ImageView. New action panels will be added to
        the ImageView toolbar
        """
        self.resize(1097, 741)
        horizontalLayout = qtw.QHBoxLayout(self)
        horizontalLayout.setContentsMargins(1, 1, 1, 1)
        kwargs['parent'] = self
        self._imageView = ImageView(**kwargs)
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
        """ Setup the ERASE objects """
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

        Args:
            toolbar: The toolbar

        Keyword Args:
            Arguments for the micrographs ColumnsView
        """
        micPanel = toolbar.createPanel('Micrographs')
        micPanel.setSizePolicy(qtw.QSizePolicy.Ignored, qtw.QSizePolicy.Minimum)
        #  setting a reasonable panel width for micrographs table
        micPanel.setGeometry(0, 0, 200, micPanel.height())
        verticalLayout = qtw.QVBoxLayout(micPanel)
        verticalLayout.setContentsMargins(0, 0, 0, 0)
        kwargs['parent'] = micPanel
        cvImages = ColumnsView(self._model, **kwargs)
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

        Args:
            toolbar: The ImageView toolbar
            pickerParams: Picker params provided by the model for the
                          :class:`FormWidget <datavis.widgets.FormWidget>`
                          creation.
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
                shortCut=qtg.QKeySequence(qtc.Qt.Key_4))
        else:
            self._actionPickSegment = _shapeAction(
                'actionPickSegment', 'fa5s.arrows-alt-h', SHAPE_SEGMENT,
                shortCut=qtg.QKeySequence(qtc.Qt.Key_3))

        self._actionPickCenter = _shapeAction(
            'actionPickCenter', 'fa5s.circle', SHAPE_CENTER,
            shortCut=qtg.QKeySequence(qtc.Qt.Key_5),
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
            fw = FormWidget(pickerParams, parent=boxPanel, name='pickerParams')
            vLayout = qtw.QVBoxLayout()
            label = qtw.QLabel(self)
            label.setText("<strong>Params:</strong>")
            vLayout.addWidget(label, 0, qtc.Qt.AlignLeft)
            vLayout.addWidget(fw)
            gLayout.addLayout(vLayout)
            fw.setMinimumSize(fw.sizeHint())
            fw.sigValueChanged.connect(self.__onPickerParamChanged)
        else:
            fw = None

        self.__formWidget = fw
        sh = gLayout.totalSizeHint()
        boxPanel.setFixedHeight(sh.height())
        toolbar.setPanelMinSize(sh.width())
        self._actionGroupPick.addAction(self._actionPickCenter)
        toolbar.addAction(actPickerROIS, boxPanel, index=0, exclusive=False,
                          checked=True)
        # End-picker operations

    def __onPickerParamChanged(self, paramName, value):
        """ Invoked when a picker-param value is changed """
        micId = self._currentMic.getId()
        self.sigPickerParamChanged.emit(micId, paramName, value)
        result = self._model.changeParam(micId, paramName, value,
                                         self.__formWidget.getParamValues)
        self.__handleModelResult(result)

    def __addControlsAction(self, toolbar):
        """
        Add the controls actions to the given toolBar

        Args:
            toolbar: The ImageView toolbar
        """
        actControls = TriggerAction(parent=toolbar, actionName='AMics',
                                    text='Controls',
                                    faIconName='fa5s.sliders-h')
        controlsPanel = toolbar.createPanel('Controls')
        controlsPanel.setSizePolicy(qtw.QSizePolicy.Ignored,
                                    qtw.QSizePolicy.Minimum)

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
        flags = qtc.Qt.ItemIsSelectable | qtc.Qt.ItemIsEnabled
        # Add pick
        self.__addRowToControls([
            (qtw.QTableWidgetItem(qta.icon('fa5s.crosshairs'), "Pick"), flags),
            (qtw.QTableWidgetItem("Activate the picking tool"), flags)])
        # Add erase
        self.__addRowToControls([
            (qtw.QTableWidgetItem(qta.icon('fa5s.eraser'), "Erase"), flags),
            (qtw.QTableWidgetItem("Activate the erase tool"), flags)])

        if self.__pickerMode == DEFAULT_MODE:
            # Add RECT
            self.__addRowToControls([
                (qtw.QTableWidgetItem(qta.icon('fa5.square'), "Rect shape"),
                 flags),
                (qtw.QTableWidgetItem("Use a RECT shape"), flags)])
            # Add CIRCLE
            self.__addRowToControls([
                (qtw.QTableWidgetItem(qta.icon('fa5.circle'), "Circle shape"),
                 flags),
                (qtw.QTableWidgetItem("Use a CIRCLE shape"), flags)])
        else:
            # Add SEGMENT
            self.__addRowToControls([
                (qtw.QTableWidgetItem(qta.icon('fa5s.arrows-alt-h'),
                                      "Segment shape"), flags),
                (qtw.QTableWidgetItem("Use a SEGMENT shape"), flags)])
        # Add CENTER
        self.__addRowToControls([
            (qtw.QTableWidgetItem(qta.icon('fa5s.circle'), "Center shape"),
             flags),
            (qtw.QTableWidgetItem("Use a CENTER shape"), flags)])
        # Add On/Off
        self.__addRowToControls([
            (qtw.QTableWidgetItem(qta.icon('fa.toggle-on'), "Show/Hide"),
             flags),
            (qtw.QTableWidgetItem("Show/Hide coordinates"), flags)])

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

    def _onRoiDoubleClick(self, roi):
        """ Invoked when the mouse is double-clicked on a roi. Used to remove
        the corresponding Coordinate """
        if self._clickAction == PICK and not self._readOnly:
            self.__removeCoordinates([roi])

    def _createRoiHandlers(self, coords=None, clear=True):
        """
        Create the one RoiHandler for each coordinate and append to the
        current list.

        Args:
            coords: iterable over the input coordinates. If None, use the
                    coordinates for current micrograph
            clear: If True, the current list will be cleared first, if not
                   new RoiHandlers will be added
        """
        if clear:
            self._roiList[:] = []

        if coords is None:
            coords = self._model.iterCoordinates(self._currentMic.getId())

        kwargs = {
            'size': self._model.getBoxSize(),
            'handleSize': self._handleSize,
            'visible': self._actionPickShowHide.get(),
            'readOnly': self._readOnly,
            'clickAction': self._clickAction,
            'onRoiDoubleClick': self._onRoiDoubleClick,
            'signals': {
                'sigRegionChanged': self._roiRegionChanged,
                'sigRegionChangeFinished': self._roiRegionChangeFinished
            }
        }
        RoiHandlerClass = FilamentRoiHandler if self._isFilament else RoiHandler
        viewBox = self._imageView.getViewBox()

        for coord in coords:
            roiDict = {
                'pen': self._makePen(coord.label, 2)
            }
            roiHandler = RoiHandlerClass(coord, self._shape, roiDict, **kwargs)
            viewBox.addItem(roiHandler.getROI())
            self._roiList.append(roiHandler)

    def _destroyRoiHandlers(self, roiHandlerList=None):
        """
        This function is called when the user remove coordinates
        by double-clicking or by using the Eraser. The existing ROIs
        will be destroyed and the action will be notified to the
        picking model.

        Args:
            roiHandlerList: list of RoiHandles that need to be deleted.
        """
        if roiHandlerList is None:
            roiHandlerList = list(self._roiList)
        viewBox = self._imageView.getViewBox()

        for roiHandler in roiHandlerList:
            roi = roiHandler.getROI()
            roiHandler.disconnectSignals(roi)
            viewBox.removeItem(roi)
            self._roiList.remove(roi.parent)  # remove the coordROI

    def __removeCoordinates(self, roiList):
        """ Remove all coordinates contained in the given roi list """

        result = self._model.removeCoordinates(
            self._currentMic.getId(), [roi.coordinate for roi in roiList])
        result.tableModelChanged = True
        self._destroyRoiHandlers([roi.parent for roi in roiList])
        self.__handleModelResult(result)

    def __createColumsViewModel(self):
        """ Setup the micrograph ColumnsView """
        self._idIndex = self._model.getColumnsCount() - 1
        self._nameIndex = 0
        self._coordIndex = 1

    def __showHandlers(self, roi, show=True):
        """ Show or hide the ROI handlers. """
        if not isinstance(roi, pg.ScatterPlotItem):
            funcName = 'show' if show else 'hide'

            for h in roi.getHandles():
                getattr(h, funcName)()  # show/hide

    def _showError(self, msg):
        """
        Popup the error msg
        Args:
            msg: The message for the user
        """
        qtw.QMessageBox.critical(self, "Particle Picking", msg)

    def _showMicrograph(self, fitToSize=False):
        """ Show the current micrograph """
        self.__eraseROI.setVisible(False)
        self.__eraseROIText.setVisible(False)
        self._destroyRoiHandlers()
        self._imageView.clear()
        micId = self._currentMic.getId()
        imgModel = ImageModel(self._model.getData(micId))
        self._imageView.setModel(imgModel, fitToSize)
        self._imageView.setImageMask(
            type=DATA, data=self._model.getMicrographMask(micId),
            color=self._model.getMicrographMaskColor(micId))
        self._imageView.setImageInfo(**self._model.getImageInfo(micId))
        self._createRoiHandlers()

    def _updateROIs(self, clear=False):
        """
        Update all ROIs that need to be shown in the current micrograph.

        Args:
            clear: If True, all ROIs will be removed and created again.
            If false, then the size will be updated.
        """
        if clear:
            self._destroyRoiHandlers()
            self._createRoiHandlers()
        else:
            size = self._model.getBoxSize()
            for roiHandler in self._roiList:
                roiHandler.updateSize(size)  # FIXME: Update shape?

    def _makePen(self, labelName, width=1):
        """
        Make the Pen for the given label name

        Args:
            labelName: the label name

        Returns:
            pyqtgraph.makePen
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
            coordList = [self._model.createCoordinate(
                x, y, label=self.__currentLabelName, **kwargs)]
            self._createRoiHandlers(coords=coordList, clear=False)
            result = self._model.addCoordinates(self._currentMic.getId(),
                                                coordList)
            result.tableModelChanged = True
            self.__handleModelResult(result)

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
            self._updateROIs(False)
            self.__eraseROIText.setVisible(False)

    def _getSelectedPen(self):
        """ Return the selected pen(model label depending) """
        btn = self._buttonGroup.checkedButton()

        if btn:
            return pg.mkPen(color=self._model.getLabel(btn.text())["color"])

        return pg.mkPen(0, 9)

    def _setupViewBox(self):
        """ Configures the pyqtgraph.ViewBox widget used by the internal
        ImageView to show the micrograph image """
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
                        self.__removeCoordinates(self.__eraseList)
                        self.__eraseList = []
                    else:
                        self.__eraseROIText.setVisible(False)

                scene.mousePressEvent = __mousePressEvent
                scene.mouseReleaseEvent = __mouseReleaseEvent

    @qtc.pyqtSlot(object)
    def viewBoxMouseMoved(self, pos):
        """
        This slot is invoked when the mouse is moved hover de pyqtgraph.ViewBox
        widget used by the internal ImageView to show the micrograph image.

        Args:
            pos: The mouse pos
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

    def __handleModelResult(self, result):
        """ Refresh different components depending on the result
        from the action of the model.
        """
        if result.tableModelChanged:
            self._cvImages.updatePage()

        if result.currentMicChanged:
            self._showMicrograph()  # This already update coordiantes

        elif result.currentCoordsChanged:
            self._updateROIs(clear=True)

    def __onPickShapeChanged(self, newShape):
        """ Update the current selected shape type """
        self._shape = newShape
        self._updateROIs(clear=True)  # FIXME: Change for updateShape???

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
        """ Invoked when current row change in micrographs list.
        Show the new micrograph """
        mic = self._model.getMicrographByIndex(row)
        try:
            if mic != self._currentMic:
                self._currentMic = mic
                self._currentImageDim = None
                result = self._model.selectMicrograph(mic.getId())
                self.__handleModelResult(result)
        except RuntimeError as ex:
            self._showError(ex.message)

    @qtc.pyqtSlot(int)
    def _boxSizeChanged(self, value):
        """
        This slot is invoked when de value of spinBoxBoxSize is changed

        Args:
            value: The value
        """
        self._updateBoxSize(value)

    @qtc.pyqtSlot()
    def _boxSizeEditingFinished(self):
        """ This slot is invoked when spinBoxBoxSize editing is finished
        """
        self._updateBoxSize(self._spinBoxBoxSize.value())

    @qtc.pyqtSlot(bool)
    def _labelAction_triggered(self, checked):
        """ This slot is invoked when clicks on label """
        btn = self._buttonGroup.checkedButton()

        if checked and btn:
            self.__currentLabelName = btn.text()

    @qtc.pyqtSlot(object)
    def _roiMouseHover(self, roi):
        """ Handler invoked when the roi is hovered by the mouse.
        Show the roi handles """
        self.__showHandlers(roi, roi.mouseHovering)

    @qtc.pyqtSlot(object)
    def __eraseRoiChanged(self, eraseRoi):
        """ Handler invoked when the erase roi is moved. """
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

    @qtc.pyqtSlot(object)
    def _roiRegionChanged(self, roi):
        """
        Handler invoked when the roi region is changed.
        For example when the user stops dragging the ROI
        (or one of its handles) or if the ROI is changed programatically.
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
        Returns a tuple (width, height), which represents the preferred
        dimensions to contain all the data
        """
        w, h = self._imageView.getPreferredSize()
        toolBar = self._imageView.getToolBar()

        return w, max(h, toolBar.height())

    def getToolBar(self):
        return self._imageView.getToolBar()


def isFilament(coord):
    """ Helper function to check if the coord is a filament.
    Returns true if coord has 'x2' and 'y2' attributes.
    """
    return all(hasattr(coord, a) for a in ['x2', 'y2'])


class RoiHandler:
    """
    Helper class that creates the appropriated ROI according
    to the shape of a given coordinate.
    """
    def __init__(self, coord, shape, roiDict, **kwargs):
        self._shape = shape
        self._roi = self._createRoi(coord, shape, roiDict, **kwargs)
        self._roi.coordinate = coord
        self._roi.parent = self

        # Ignore the signals for center shape
        if self._shape != SHAPE_CENTER:
            self._signals = kwargs.get('signals', {})
        else:
            self._signals = {}
        self._setupRoi(self._roi, **kwargs)

    def _createRoi(self, coord, shape, roiDict, **kwargs):
        """ Create the required ROI. """
        x, y = coord.x, coord.y
        size = kwargs['size']

        if shape == SHAPE_CENTER:
            roiDict['symbol'] = 'o'
            color = qtg.QColor(roiDict['pen'].color())
            roiDict['brush'] = qtg.QBrush(color)
            roiDict['pen'] = pg.mkPen({'color': "FFF", 'width': 1})
            # TODO: Check if ScatterPlotItem is the best one for this case
            return pg.ScatterPlotItem(pos=[(x, y)], **roiDict)

        RoiClass = CircleROI if shape == SHAPE_CIRCLE else pg.ROI
        half = size / 2
        x -= half
        y -= half
        return RoiClass((x, y), (size, size), **roiDict)

    def _setupRoi(self, roi, **kwargs):
        erase = kwargs['clickAction'] == ERASE
        # Connect some slots we are interested in
        roi.setAcceptedMouseButtons(qtc.Qt.LeftButton)
        roi.setAcceptHoverEvents(True)
        mouseDoubleClickEvent = roi.mouseDoubleClickEvent
        hoverEnterEvent = roi.hoverEnterEvent
        hoverLeaveEvent = roi.hoverLeaveEvent

        def __hoverEnterEvent(ev):
            hoverEnterEvent(ev)
            self._showHideHandlers('show')

        def __hoverLeaveEvent(ev):
            hoverLeaveEvent(ev)
            self._showHideHandlers('hide')

        def __mouseDoubleClickEvent(ev):
            mouseDoubleClickEvent(ev)
            kwargs['onRoiDoubleClick'](roi)

        roi.mouseDoubleClickEvent = __mouseDoubleClickEvent
        if self._shape != SHAPE_CENTER:
            roi.hoverEnterEvent = __hoverEnterEvent
            roi.hoverLeaveEvent = __hoverLeaveEvent

        self.connectSignals(roi)

        roi.setFlag(qtw.QGraphicsItem.ItemIsSelectable, erase)
        if erase:
            roi.setAcceptedMouseButtons(qtc.Qt.NoButton)

        roi.setVisible(kwargs['visible'])
        roi.translatable = not kwargs['readOnly']

    def getCoord(self):
        """ Return the internal coordinate. """
        return self._roi.coordinate

    def getROI(self):
        return self._roi

    def _showHideHandlers(self, funcName='show'):
        """ Show or hide the ROI handlers. """
        for h in self._roi.getHandles():
            getattr(h, funcName)()  # show/hide

    def updateSize(self, size):
        """
        Update the roi size

        Args:
            size: (int) The new size
        """
        if self._shape == SHAPE_CENTER:
            return  # No size update required in this case

        coord = self._roi.coordinate
        self._roi.setSize((size, size), update=False, finish=False)
        half = size / 2

        self._roi.setPos((coord.x - half, coord.y - half), update=False,
                         finish=False)

    def connectSignals(self, roi):
        """ Connect the roi signals """
        for signalName, slot in self._signals.items():
            getattr(roi, signalName).connect(slot)

    def disconnectSignals(self, roi):
        """ Disconnect the roi signals, connected previously """
        for signalName, slot in self._signals.items():
            getattr(roi, signalName).disconnect(slot)


class FilamentRoiHandler(RoiHandler):
    """ RoiHandler subclass that deals with filaments. """

    def __calcFilamentSize(self, pos1, pos2, width):
        """
        Calculate the filament size (width x height)

        Args:
            pos1:  (pyqtgrapgh.Point) Fist point
            pos2:  (pyqtgrapgh.Point) Second point
            width: (int) The new size

        Returns:
            (pyqtgrapgh.Point, pyqtgrapgh.Point, float).
             A Tuple (pos, size, angle)
        """
        d = pg.Point(pos2) - pg.Point(pos1)
        angle = pg.Point(1, 0).angle(d)
        if angle is None:
            angle = 0
        ra = -angle * pi / 180.
        c = pg.Point(width / 2. * sin(ra), -width / 2. * cos(ra))
        pos1 += c

        return pos1, pg.Point(d.length(), width), -angle

    def _createRoi(self, coord, shape, roiDict, **kwargs):
        """ Create a line or filament according to the given shape. """

        point1 = (coord.x, coord.y)
        point2 = (coord.x2, coord.y2)

        if shape == SHAPE_CENTER:
            return pg.LineSegmentROI([point1, point2], **roiDict)

        pos, size, angle = self.__calcFilamentSize(point1, point2,
                                                   kwargs['size'])
        roi = pg.ROI(pos, size=size, angle=angle, **roiDict)
        roi.handleSize = kwargs['handleSize']
        h = roi.addScaleRotateHandle([0, 0.5], [1, 0.5])
        h.hide()
        h = roi.addScaleRotateHandle([1, 0.5], [0, 0.5])
        h.hide()
        h = roi.addScaleHandle([1, 0], [1, 1])
        h.hide()
        h = roi.addScaleHandle([0, 1], [0, 0])
        h.hide()
        h = roi.addScaleHandle([0.5, 1], [0.5, 0.5])
        h.hide()

        return roi

    def updateSize(self, size):
        """
        Update the filament roi size.

        Args:
            size: (int) The new size
        """
        if self._shape == SHAPE_CENTER:
            return

        coord = self._roi.coordinate
        point1 = (coord.x, coord.y)
        point2 = (coord.x2, coord.y2)

        pos, size, angle = self.__calcFilamentSize(point1, point2, size)
        self._roi.setPos(pos, update=False, finish=False)
        self._roi.setSize(size, update=False, finish=False)
        self._roi.setAngle(angle, update=False, finish=False)
        self._roi.stateChanged(False)


class CircleROI(pg.CircleROI):
    """ Circular ROI subclass without handles. """
    def __init__(self, pos, size, **args):
        pg.ROI.__init__(self, pos, size, **args)