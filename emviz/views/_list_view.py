

from PyQt5.QtWidgets import QWidget, QSplitter, QHBoxLayout, QPushButton
from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal

from emviz.widgets import ViewPanel, DynamicWidgetsFactory
from emviz.models import EmptyTableModel, ImageModel, EmptyVolumeModel

from emviz.views import ColumnsView, ImageView, VolumeView

import numpy as np


class ImageListView(QWidget):
    """ View that will show a list of images. It will serve as the base class
    for other implementations basically, it will contain a left panel with the
    list, and a right panel with ImagePanel (top) and InfoPanel (bottom). """

    """ Signal for current item changed. The connected slots will receive 
    the item index. """
    sigCurrentItemChanged = pyqtSignal(int)

    def __init__(self, parent, model, **kwargs):
        """
        Creates an ImageListView.
        :param parent:  (QWidget) Specifies the parent widget to which this
                        ImageListView will belong. If None, then the
                        ImageListView is created with no parent.
        :param kwargs:
             - model: (TableModel) The data model
        """
        QWidget.__init__(self, parent=parent)
        self.__setupGUI(**kwargs)
        self._connectSignals()

        self.setModel(model)

    def __setupGUI(self, **kwargs):
        """ This is the standard method for the GUI creation """
        self._mainLayout = QHBoxLayout(self)
        self._mainLayout.setSpacing(0)
        self._mainLayout.setContentsMargins(1, 1, 1, 1)
        self._splitter = QSplitter(orientation=Qt.Horizontal, parent=self)
        self._leftPanel = self._createLeftPanel(**kwargs)
        self._splitter.addWidget(self._leftPanel)
        self._rightPanel = self._createRightPanel(**kwargs)
        self._splitter.addWidget(self._rightPanel)
        self._splitter.setStretchFactor(0, 1)
        self._splitter.setStretchFactor(1, 3)
        self._mainLayout.addWidget(self._splitter)

    def _createLeftPanel(self, **kwargs):
        """
        Build the left panel: List of images. The ColumnsView will be accessed
        from the returned ViewPanel using the 'columnsView' key.
        :param kwargs: The kwargs arguments for the ColumnsView
        :return: (ViewPanel) The panel.
        """
        panel = ViewPanel(self, layoutType=ViewPanel.VERTICAL)
        panel.addWidget(ColumnsView(parent=panel, model=EmptyTableModel(),
                                    **kwargs), 'columnsView')
        return panel

    def _createRightPanel(self, **kwargs):
        """
        Build the right panel: (Top) ViewPanel with ImageView(but subclasses
        might create different widgets). (Botton) ViewPanel with an InfoPanel
        (in subclasses should be implemented).
        The top right panel should be accessed using the 'topRightPanel' key.
        The bottom right panel should be accessed using the 'topRightPanel' key.
        :param kwargs: The kwargs arguments for the top right panel (ImageView)
        :return:       (ViewPanel)
        """
        rightPanel = ViewPanel(self, ViewPanel.VSPLITTER)
        topRightPanel = self._createTopRightPanel(**kwargs)
        bottomRightPanel = self._createBottomRightPanel(**kwargs)
        rightPanel.addWidget(topRightPanel, 'topRightPanel')
        if bottomRightPanel is not None:
            rightPanel.addWidget(bottomRightPanel, 'bottomRightPanel')

        return rightPanel

    def _createTopRightPanel(self, **kwargs):
        """
        Build the top right panel: ViewPanel with ImageView
        The ImageView should be accessed using the 'imageView' key.
        :param kwargs: The kwargs arguments for the ImageView
        :return:       (ViewPanel)
        """
        panel = ViewPanel(self)
        panel.addWidget(ImageView(self, **kwargs), 'imageView')
        return panel

    def _createBottomRightPanel(self, **kwargs):
        """ Build the bottom right panel. Should be implemented in subclasses
        to build the content widget and return it. """
        return None

    def _connectSignals(self):
        """ Connects signals/slots according to the view widget used in the left
        panel. Should be implemented in subclasses to connect all signals"""
        cv = self._leftPanel.getWidget('columnsView')
        if cv is not None:
            cv.sigCurrentRowChanged.connect(self.onItemChanged)

    @pyqtSlot(int)
    def onItemChanged(self, index):
        """ Slot for sigCurrentRowChanged signal """
        self.currentItem = index
        self.updateImagePanel()
        self.sigCurrentItemChanged.emit(index)

    def updateImagePanel(self):
        """
        Update the information of the image panel. Implement this method in
        subclasses for image data visualization
        """
        panel = self._rightPanel.getWidget('topRightPanel')

        imageView = panel.getWidget('imageView')
        data = self._model.getData(self.currentItem, 0)
        imgModel = ImageModel(data)
        imageView.setModel(imgModel)

    def setModel(self, model):
        """
        Set the model used for the left panel
        :param model: (TableModel) the model
        """
        self._model = model
        cv = self._leftPanel.getWidget('columnsView')
        cv.setModel(model)


class VolumeMaskListView(ImageListView):
    """ View that will show a list of volume images """
    def __init__(self, parent, model, **kwargs):
        """
        Construct a VolumeMaskListView
        :param parent: The parent widget
        :param model:  (TableModel) The volume list model
        :param kwargs: The kwargs arguments for the VolumeView widget
        """
        ImageListView.__init__(self, parent, model, **kwargs)

    def _createTopRightPanel(self, **kwargs):
        """Build the top right panel: ViewPanel with VolumeView widget
        The VolumeView should be accessed using the 'volumeView' key.
        :param kwargs: The kwargs arguments for the VolumeView
        :return:       (ViewPanel)
        """
        panel = ViewPanel(self)
        view = VolumeView(self, model=EmptyVolumeModel(), **kwargs)
        panel.addWidget(view, 'volumeView')
        return panel

    def updateImagePanel(self):
        model = self._model.getModel(self.currentItem)
        panel = self._rightPanel.getWidget('topRightPanel')
        view = panel.getWidget('volumeView')
        view.setModel(model)


class DualImageListView(ImageListView):
    """ View that will show a list of images. The ImagePanel contains two
    ImageView:  (Left) original image that is load from the input list.
    (Right) the same image after some modification is applied """
    def __init__(self, parent, model, **kwargs):
        """
        Construct an DualImageListView.
        :param parent: The parent widget
        :param model:  (ListModel) The list of images
        :param kwargs: kwargs arguments for the two ImageView
          - options:   (dict) Dynamic widget options
          - method:    Function to invoke when the apply button is clicked
        """
        ImageListView.__init__(self, parent, model, **kwargs)

    @pyqtSlot()
    def __onApplyButtonClicked(self):
        """ Slot for apply button clicked """
        if self._method is not None:
            if self._dynamicParams is None:
                self._method()
            else:
                if self._dynamicWidget is not None:
                    self._dynamicParams = self._dynamicWidget.getParams()
                self._method(self._dynamicParams)

    def _createTopRightPanel(self, **kwargs):
        """Build the top right panel: ViewPanel with two ImageView widgets
        The left ImageView should be accessed using the 'leftImageView' key.
        The right ImageView should be accessed using the 'rightImageView' key.
        :param kwargs: The kwargs arguments for the two ImageView
        :return:       (ViewPanel)
        """
        panel = ViewPanel(self)
        leftImageView = ImageView(self, model=None, **kwargs)
        panel.addWidget(leftImageView, 'leftImageView')
        rightImageView = ImageView(self, model=None, **kwargs)
        leftImageView.setXLink(rightImageView)
        leftImageView.setYLink(rightImageView)
        panel.addWidget(rightImageView, 'rightImageView')
        return panel

    def _createBottomRightPanel(self, **kwargs):
        """ Creates a dynamic widget from the given 'options' param.
        The dynamic widget should be accessed using the 'optionsWidget' key.
        :param kwargs:
          - options:   (dict) Dynamic widget options
          - method:  Function to invoke when the apply button is clicked
        """
        self._dynamicParams = kwargs.get('options')
        self._method = kwargs.get('method')

        panel = ViewPanel(self, layoutType=ViewPanel.VERTICAL)
        if self._dynamicParams is not None:
            factory = DynamicWidgetsFactory()
            self._dynamicWidget = factory.createWidget(self._dynamicParams)
            panel.addWidget(self._dynamicWidget, 'optionsWidget',
                            alignment=Qt.AlignLeft)
        else:
            self._dynamicWidget = None

        self._applyButton = QPushButton(panel)
        self._applyButton.setText('Apply')
        self._applyButton.setFixedWidth(90)
        self._applyButton.clicked.connect(self.__onApplyButtonClicked)
        panel.addWidget(self._applyButton, 'applyButton',
                        alignment=Qt.AlignBottom)
        return panel

    def updateImagePanel(self):
        panel = self._rightPanel.getWidget('topRightPanel')
        leftImageView = panel.getWidget('leftImageView')
        rightImageView = panel.getWidget('rightImageView')

        data = self._model.getData(self.currentItem, 0)
        if data is None:
            rightModel = None
            leftModel = None
        else:
            leftModel = ImageModel(data)
            data2 = np.ndarray.copy(data)
            rightModel = ImageModel(data2)

        leftImageView.setModel(leftModel)
        rightImageView.setModel(rightModel)

