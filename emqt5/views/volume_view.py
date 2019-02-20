#!/usr/bin/python
# -*- coding: utf-8 -*-


from PyQt5.QtCore import Qt, pyqtSlot, QSize
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QToolBar, QAction, QSpinBox,
                             QLabel, QComboBox, QStackedLayout, QActionGroup)
from PyQt5.QtGui import QIcon, QStandardItemModel, QStandardItem
import qtawesome as qta

from .model import VolumeDataModel
from .base import PageBar
from .multislice_view import MultiSliceView
from .gallery import GalleryView

PIXEL_UNITS = 1
PERCENT_UNITS = 2


class VolumeView(QWidget):
    """
    Allow to display a volume and switch between MultiSlicesView​and GalleryView
    In case of multiple volumes, this view could be extended with a way
    to select which volume to display.
    """
    def __init__(self, parent, **kwargs):
        """
        Constructor
         For init params use the same as GalleryView and MultiSlicesView.
         """
        QWidget.__init__(self, parent=parent)
        self._model = None
        self.__initProperties(**kwargs)
        self.__setupUi(**kwargs)
        self.setup(**kwargs)
        self.setView(kwargs.get('view', 2))

    def __setupUi(self, **kwargs):
        self._mainLayout = QVBoxLayout(self)
        self._mainLayout.setSpacing(0)
        self._mainLayout.setContentsMargins(1, 1, 1, 1)
        self._toolBar = QToolBar(self)
        self._mainLayout.addWidget(self._toolBar)
        self._stackedLayoud = QStackedLayout(self._mainLayout)
        self._stackedLayoud.setSpacing(0)
        # actions
        self._actionGroupViews = QActionGroup(self._toolBar)
        self._actionGroupViews.setExclusive(True)

        self._aSlices = self.__createNewAction(self._toolBar,
                                               'Multi Slices View',
                                               'Multi Slices View',
                                               'fa.sliders',
                                               True,
                                               self._onMultiSlicesViewTriggered)
        self._actionGroupViews.addAction(self._aSlices)
        self._toolBar.addAction(self._aSlices)
        self._aSlices.setChecked(True)
        self._aGallery = self.__createNewAction(self._toolBar, 'Gallery View',
                                                'Gallery View', 'fa.th', True,
                                                self._onGalleryViewTriggered)
        self._actionGroupViews.addAction(self._aGallery)
        self._toolBar.addAction(self._aGallery)
        self._toolBar.addSeparator()
        # cell size
        self._labelLupe = QLabel(self._toolBar)
        self._labelLupe.setPixmap(qta.icon('fa.search').pixmap(28,
                                                               QIcon.Normal,
                                                               QIcon.On))
        self._toolBar.addWidget(self._labelLupe)
        self._spinBoxCellSize = QSpinBox(self._toolBar)
        self._spinBoxCellSize.setSuffix(' px' if self._zoomUnits == PIXEL_UNITS
                                        else ' %')
        self._spinBoxCellSize.setRange(self._minRowHeight,
                                       self._maxRowHeight)
        self._spinBoxCellSize.setValue(self._defaultRowHeight)
        self._spinBoxCellSize.editingFinished.connect(self._onChangeCellSize)
        self._spinBoxCellSize.setValue(self._defaultRowHeight)
        self._toolBar.addWidget(self._spinBoxCellSize)
        self._toolBar.addSeparator()
        # for axis selection in GalleryView
        self._labelCurrentVolume = QLabel(parent=self._toolBar, text=" Axis ")
        self._toolBar.addWidget(self._labelCurrentVolume)
        self._comboBoxCurrentAxis = QComboBox(self._toolBar)
        self._comboBoxCurrentAxis.currentIndexChanged.\
            connect(self._onAxisChanged)
        self._toolBar.addWidget(self._comboBoxCurrentAxis)
        self._toolBar.addSeparator()
        # for multiple volumes
        self._pageBar = PageBar(self._toolBar)
        self._pageBar.setMaximumWidth(150)
        self._actPageBar = self._toolBar.addWidget(self._pageBar)
        self._pageBar.sigPageChanged.connect(self._onVolumeChanged)

        # views
        self._multiSlicesView = MultiSliceView(self, **kwargs)
        self._stackedLayoud.addWidget(self._multiSlicesView)

        self._galleryView = GalleryView(self, **kwargs)
        self._galleryView.sigCurrentRowChanged.connect(
            self._onGalleryRowChanged)
        self._stackedLayoud.addWidget(self._galleryView)

    def __initProperties(self, **kwargs):
        """ Configure all properties  """
        self._defaultRowHeight = kwargs.get("size", 120)
        self._maxRowHeight = kwargs.get("max_cell_size", 300)
        self._minRowHeight = kwargs.get("min_cell_size", 20)
        self._zoomUnits = kwargs.get("zoom_units", PIXEL_UNITS)

    def __setupComboBoxAxis(self):
        """
        Configure the elements in combobox currentVolume for user selection.
        """
        blocked = self._comboBoxCurrentAxis.blockSignals(True)
        model = self._comboBoxCurrentAxis.model()
        if not model:
            model = QStandardItemModel(self._comboBoxCurrentVolume)

        model.clear()

        t = None if self._model is None else self._model.getTitles()
        if t is not None:
            for axis in self._model.getTitles():
                item = QStandardItem(axis)
                item.setData(0, Qt.UserRole)  # use UserRole for store
                model.appendRow([item])

        self._comboBoxCurrentAxis.blockSignals(blocked)

    def __setupPageBar(self):
        """ Configure the page bar """
        block = self._pageBar.blockSignals(True)
        if self._model is None:
            self._pageBar.setup(0, 0, 0)
        else:
            self._pageBar.setup(self._model.getVolumeIndex(), 0,
                                self._model.getVolumeCount() - 1)
        self._pageBar.blockSignals(block)

    def __setupAllWidgets(self):
        """ Setups all widgets """
        self.__setupComboBoxAxis()
        self._multiSlicesView.setModel(self._model)
        self._galleryView.setModel(self._model)
        if self._model is None:
            self._pageBar.setVisible(False)
        else:
            self._actPageBar.setVisible(self._model.getVolumeCount() > 1)
            self._galleryView.setModelColumn(2)
        self.__setupPageBar()

    def __createNewAction(self, parent, actionName, text="", faIconName=None,
                            checkable=False, slot=None):
        """
        Create a QAction with the given name, text and icon. If slot is not None
        then the signal QAction.triggered is connected to it
        :param actionName: The action name
        :param text: Action text
        :param faIconName: qtawesome icon name
        :param checkable: if this action is checkable
        :param slot: the slot to connect QAction.triggered signal
        :return: The QAction
        """
        a = QAction(parent)
        a.setObjectName(str(actionName))
        if faIconName:
            a.setIcon(qta.icon(faIconName))
        a.setCheckable(checkable)
        a.setText(str(text))

        if slot:
            a.triggered.connect(slot)
        return a

    @pyqtSlot()
    def _onChangeCellSize(self):
        """
        This slot is invoked when the cell size need to be rearranged
        """
        size = self._spinBoxCellSize.value()
        if self._model is not None:
            self._model.setIconSize(QSize(size, size))

        self._galleryView.setIconSize((size, size))

    @pyqtSlot(bool)
    def _onMultiSlicesViewTriggered(self, checked):
        if checked:
            self._stackedLayoud.setCurrentWidget(self._multiSlicesView)
            if self._model is not None:
                self._multiSlicesView.setAxis(
                    self._comboBoxCurrentAxis.currentIndex())
        self._aGallery.setChecked(not checked)

    @pyqtSlot(int)
    def _onGalleryRowChanged(self, row):
        """ Invoked when change the current gallery row """
        self._multiSlicesView.setSlice(row)

    @pyqtSlot(bool)
    def _onGalleryViewTriggered(self, checked):
        if checked:
            self._stackedLayoud.setCurrentWidget(self._galleryView)
            if self._model is not None:
                self._comboBoxCurrentAxis.setCurrentIndex(
                    self._multiSlicesView.getAxis())
                self._galleryView.selectRow(self._multiSlicesView.getSlice())
        self._aSlices.setChecked(not checked)

    @pyqtSlot(int)
    def _onAxisChanged(self, index):
        if self._model is not None:
            self._model.setAxis(index)
            self._multiSlicesView.setAxis(index)
            if self._galleryView.isVisible():
                self._galleryView.selectRow(0)
                self._multiSlicesView.setSlice(0)
            else:
                self._multiSlicesView.setSlice(
                    self._multiSlicesView.getPreferredSliceIndex(index))

    @pyqtSlot(int)
    def _onVolumeChanged(self, index):
        if self._model is not None:
            self._model.setVolumeIndex(index)
            self._multiSlicesView.setModel(self._model)
            self._multiSlicesView.setAxis(
                self._comboBoxCurrentAxis.currentIndex())
            if self._galleryView.isVisible():
                self._galleryView.selectRow(0)
                self._multiSlicesView.setSlice(0)

    def setup(self, path=None, model=None, **kwargs):
        """
        Setups this VolumeView.
        TODO: see kwargs for other configurations
        """
        self._model = model or VolumeDataModel(path, parent=self) \
            if path is not None else None
        self.__setupAllWidgets()
        self._onChangeCellSize()

    def loadPath(self, path):
        """ Load the volume form the given path """
        self.setup(path)

    def clear(self):
        """ Clear the volume view """
        self.setup(path=None)

    def setView(self, view):
        """
        Sets the current view. See DataView for view values.
        2: GALLERY
        8: SLICES
        """
        if view == 2:
            self._aGallery.setChecked(True)
            self._onGalleryViewTriggered(True)
        elif view == 8:
            self._aSlices.setChecked(True)
            self._onMultiSlicesViewTriggered(True)


