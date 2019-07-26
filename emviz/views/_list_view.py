

from PyQt5.QtWidgets import QWidget, QSplitter, QHBoxLayout
from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal

from emviz.widgets import ViewPanel
from emviz.models import EmptyTableModel, ImageModel

from ._columns import ColumnsView
from ._image_view import ImageView


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
        self.sigCurrentItemChanged.emit(index)
        self.updateImagePanel()

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
