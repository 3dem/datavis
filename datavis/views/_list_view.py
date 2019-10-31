
import PyQt5.QtCore as qtc
import PyQt5.QtWidgets as qtw

from datavis.widgets import ViewPanel, SpinSlider, FormWidget
from datavis.models import EmptyTableModel, ImageModel
from datavis.views import (ColumnsView, ImageView, VolumeView, RECT_ROI,
                           CIRCLE_ROI)

import numpy as np


class ImageListView(qtw.QWidget):
    """ Base class to display a list of images.

    Basically, it will contain a left panel with the
    list, and a right panel with ImagePanel (top) and InfoPanel (bottom). """

    """ Signal for current item changed. The connected slots will receive 
    the item index. """
    sigCurrentItemChanged = qtc.pyqtSignal(int)

    def __init__(self, model, parent=None, **kwargs):
        """
        Creates an ImageListView instance.

        Args:
            model:  Input :class:`~datavis.models.TableModel` model
            parent: Specifies the parent widget to which this ImageListView
                    will belong. If None, then the ImageListView is created
                    with no parent.

        Keyword Args: Keyword arguments for the internal :class:`~datavis.views.ImageView`
        """
        qtw.QWidget.__init__(self, parent=parent)
        self._model = model
        self.currentItem = -1
        default = {'toolBar': False}
        default.update(kwargs)
        self.__setupGUI(**default)
        self._connectSignals()

        self.setModel(model)

    def __setupGUI(self, **kwargs):
        """ This is the standard method for the GUI creation """
        mainLayout = qtw.QHBoxLayout(self)
        mainLayout.setSpacing(0)
        mainLayout.setContentsMargins(1, 1, 1, 1)
        self._splitter = qtw.QSplitter(orientation=qtc.Qt.Horizontal, 
                                       parent=self)
        self._leftPanel = self._createLeftPanel(**kwargs)
        self._splitter.addWidget(self._leftPanel)
        self._rightPanel = self._createRightPanel(**kwargs)
        self._splitter.addWidget(self._rightPanel)
        self._splitter.setStretchFactor(0, 1)
        self._splitter.setStretchFactor(1, 3)
        mainLayout.addWidget(self._splitter)

    def _createLeftPanel(self, **kwargs):
        """
        Build the left panel: List of images. The ColumnsView will be accessed
        from the returned ViewPanel using the 'columnsView' key.

        Keyword Args:
            The kwargs arguments for the ColumnsView

        Returns:
            :class:`~datavis.widgets.ViewPanel`
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

        Keyword Args:
            The kwargs arguments for the top right panel (ImageView)

        Return:
            :class:`ViewPanel <datavis.widgets.ViewPanel>`
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

        Keyword Args:
                The kwargs arguments for the ImageView

        Return:
            :class:`ViewPanel <datavis.widgets.ViewPanel>`
        """
        panel = ViewPanel(self)
        kwargs['parent'] = self
        panel.addWidget(ImageView(**kwargs), 'imageView')
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

    @qtc.pyqtSlot(int)
    def onItemChanged(self, index):
        """ Slot for sigCurrentRowChanged signal """
        if not self.currentItem == index:
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
        imageView.setModel(imgModel, imageView.isEmpty())

    def setModel(self, model):
        """ Set the model used for the left panel.

        Args:
            model: New :class:`~datavis.models.TableModel` model that
                will be set. This model should implement the getModel() method
                that should return a :class:`~datavis.models.ImageModel` used
                for the Image panel.
        """
        self._model = model
        self.currentItem = -1
        cv = self._leftPanel.getWidget('columnsView')
        cv.setModel(model)


class VolumeListView(ImageListView):
    """ View that will show a list of volume images """
    def __init__(self, model, parent=None, **kwargs):
        """ Construct a VolumeListView instance

        Args:
            parent: The parent widget
            model:  :class:`~datavis.models.TableModel`. The model must
                provide a :class:`~datavis.models.VolumeModel` in getModel()
                method.

        Keyword Args:
            kwargs: The keyword arguments for the internal
                :class:`~datavis.views.VolumeView` widget.
        """
        ImageListView.__init__(self, model, parent=parent, **kwargs)

    def __getVolumeView(self):
        panel = self._rightPanel.getWidget('topRightPanel')
        view = panel.getWidget('volumeView')
        return view

    def _createTopRightPanel(self, **kwargs):
        """ Build the top right panel: ViewPanel with VolumeView widget
        The VolumeView should be accessed using the 'volumeView' key.

        Keyword Args:
            kwargs: The keyword arguments for the :class:`~datavis.views.VolumeView`

        Returns:
            :class:`~datavis.widgets.ViewPanel`
        """
        panel = ViewPanel(self)
        kwargs['parent'] = panel
        view = VolumeView(self._model.getModel(0), **kwargs)
        panel.addWidget(view, 'volumeView')
        return panel

    def updateImagePanel(self):
        """ Reimplemented from :class:`~datavis.views.ImageListView` """
        model = self._model.getModel(self.currentItem)
        view = self.__getVolumeView()
        view.setModel(model)

    def setModel(self, model):
        """ Reimplemented from :class:`~datavis.views.ImageListView`.

        The model must provide a :class:`~datavis.models.VolumeModel>`
        in getModel() method
        """
        ImageListView.setModel(self, model)
        view = self.__getVolumeView()
        view.fitToSize()


class DualImageListView(ImageListView):
    """ View that will show a list of images. The ImagePanel contains two
    ImageView:  (Left) original image that is load from the input list.
    (Right) the same image after some modification is applied """
    def __init__(self, model, parent=None, **kwargs):
        """
        Construct an DualImageListView instance.

        Args:
            parent: The parent widget
            model:  :class:`ListModel <datavis.models.ListModel>`.
                    The list of images

        Keyword Args:
            kwargs arguments for the two ImageView
            options:   (dict) Dynamic widget options
            method:    Function to invoke when the apply button is clicked
        """
        ImageListView.__init__(self, model, parent=parent, **kwargs)

    @qtc.pyqtSlot()
    def __onApplyButtonClicked(self):
        """ Slot for apply button clicked """
        if self._method is not None:
            if self._paramsForm is None:
                self._method()
            else:
                if self._formWidget is not None:
                    self._paramsForm = self._formWidget.getParams()
                self._method(self._paramsForm)

    def _createTopRightPanel(self, **kwargs):
        """ Build the top right panel: ViewPanel with two ImageView widgets
        The left ImageView should be accessed using the 'leftImageView' key.
        The right ImageView should be accessed using the 'rightImageView' key.

        Keyword Args:
            The kwargs arguments for the two
            :class:`ImageView <datavis.views.ImageView>`.

        Returns:
            :class:`ViewPanel <datavis.widgets.ViewPanel>`.
        """
        panel = ViewPanel(self)
        defaultImgViewKargs = {'histogram': False,
                               'toolBar': False,
                               }
        k = dict(defaultImgViewKargs)
        k.update(kwargs)
        leftImageView = ImageView(parent=self, model=None, **k)
        panel.addWidget(leftImageView, 'leftImageView')
        rightImageView = ImageView(parent=self, model=None, **k)
        leftImageView.setXLink(rightImageView)
        leftImageView.setYLink(rightImageView)
        panel.addWidget(rightImageView, 'rightImageView')
        return panel

    def _createBottomRightPanel(self, **kwargs):
        """ Creates a FormWidget from the given 'options' param.
        The FormWidget should be accessed using the 'optionsWidget' key.

        Keyword Args:
            options: params options. See FormWidget specifications
            method:  Function to invoke when the apply button is clicked
        """
        self._paramsForm = kwargs.get('form', None)
        self._method = kwargs.get('method')

        panel = ViewPanel(self, layoutType=ViewPanel.VERTICAL)
        if self._paramsForm is not None:
            self._formWidget = FormWidget(self._paramsForm,
                                          parent=panel, name='params')
            panel.addWidget(self._formWidget, 'optionsWidget',
                            alignment=qtc.Qt.AlignLeft)
        else:
            self._formWidget = None

        self._applyButton = qtw.QPushButton(panel)
        self._applyButton.setText('Apply')
        self._applyButton.setFixedWidth(90)
        self._applyButton.clicked.connect(self.__onApplyButtonClicked)
        panel.addWidget(self._applyButton, 'applyButton',
                        alignment=qtc.Qt.AlignBottom)
        return panel

    def updateImagePanel(self):
        """ Reimplemented from
        :class:`ImageListView <datavis.views.ImageListView>` """
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

        e = leftImageView.isEmpty()
        leftImageView.setModel(leftModel, e)
        rightImageView.setModel(rightModel, e)


class ImageMaskListView(ImageListView):
    """ View that will show a list of images. The ImagePanel contains a
    circular or rectangular mask depending on the type of mask configured.
    """

    def __init__(self, model, parent=None, **kwargs):
        """ Construct an ImageMaskListView instance.

        Args:
            parent: Specifies the parent widget to which this
                    ImageMaskListView will belong. If None, then the
                    ImageMaskListView is created with no parent.
            model: :class:`~datavis.models.TableModel`

        Keyword Args:
            kwargs: The keyword arguments for the internal
                :class:`~datavis.views.ImageView`.
        """
        ImageListView.__init__(self, model, parent=parent, **kwargs)

        spinSlider = self.__getSpinSlider()
        spinSlider.sigValueChanged.connect(self.__onSpinSliderValueChanged)
        spinSlider.sigSliderReleased.connect(self.__onSpinSliderReleased)
        imageView = self.__getImageView()
        maskParams = kwargs.get('maskParams', dict())
        maskType = maskParams.get('type')
        if maskType == CIRCLE_ROI or maskType == RECT_ROI:  # ROI MASK
            imageView.sigMaskSizeChanged.connect(self.__onRoiSizeChanged)
        else:
            panel = self._rightPanel.getWidget('bottomRightPanel')
            panel.setVisible(False)

    def __onSpinSliderValueChanged(self, value):
        """ Slot for SpinSlider value changed """
        imageView = self.__getImageView()
        size = imageView.getMaskSize()
        if size is not None and not size == 2*value:
            imageView.setRoiMaskSize(2 * value)
            imageView.setRoiMaskSizeVisible(True)

    def __onSpinSliderReleased(self):
        """ Slot for SpinSlider released """
        imageView = self.__getImageView()
        imageView.setRoiMaskSizeVisible(False)

    def __onRoiSizeChanged(self, size):
        """ Slot for roi region changed """
        spinSlider = self.__getSpinSlider()
        value = spinSlider.getValue()
        r = int(size/2)
        if not r == value:
            spinSlider.setValue(r)

    def __getSpinSlider(self):
        """ Return the SpinSlider widget """
        panel = self._rightPanel.getWidget('bottomRightPanel')
        return panel.getWidget('spinSlider')

    def __getImageView(self):
        """ Return the ImageView widget """
        panel = self._rightPanel.getWidget('topRightPanel')
        return panel.getWidget('imageView')

    def _createBottomRightPanel(self, **kwargs):
        """ Creates the bottom right panel, containing the SpinSlider """
        panel = ViewPanel(self, layoutType=ViewPanel.HORIZONTAL)
        spinSlider = SpinSlider(panel, text='Radius ', minValue=1,
                                maxValue=10000, currentValue=100)
        panel.addWidget(spinSlider, 'spinSlider')

        return panel

    def updateImagePanel(self):
        """ Reimplemented from
        :class:`ImageListView <datavis.views.ImageListView>` """
        ImageListView.updateImagePanel(self)
        spinSlider = self.__getSpinSlider()
        imgView = self.__getImageView()
        b = imgView.getImageItem().boundingRect()
        spinSlider.setRange(
            1, int(min(b.width(), b.height()) / 2))
        s = imgView.getMaskSize()
        if s is not None:
            spinSlider.setValue(int(s / 2))

    def setMaskColor(self, color):
        """
         Set the mask color.

        Args:
            color: (str) The color in #ARGB format. Example: #22AAFF00
                   or (QColor)
        """
        imageView = self.__getImageView()
        imageView.setMaskColor(color)
