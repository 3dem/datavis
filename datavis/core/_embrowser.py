
import PyQt5.QtWidgets as qtw

from datavis.views import (DataView,  VolumeView, ImageView, SlicesView, ITEMS,
                         COLUMNS, GALLERY)
from datavis.widgets import FileBrowser
from datavis.models import EmptyTableModel, EmptySlicesModel, EmptyVolumeModel
from datavis.core import ModelsFactory, ImageManager, EmPath, MOVIE_SIZE


class EmBrowser(FileBrowser):
    """ """

    def __init__(self, **kwargs):
        """
        Creates a EmBrowser instance
        :param kwargs: See FileBrowser params
        """
        FileBrowser.__init__(self, **kwargs)
        self._dataView.sigCurrentTableChanged.connect(
            self.__onDataViewTableChanged)

        self.updateViewPanel()

    def __onDataViewTableChanged(self):
        model = self._dataView.getModel()
        if model is not None:
            info = dict()
            info["Type"] = "TABLE"
            info["Dimensions (Rows x Columns)"] = \
                "%d x %d" % (model.totalRowCount(), model.columnCount())
            self.__showInfo(info)

    def __showMsgBox(self, text, icon=None, details=None):
        """
        Show a message box with the given text, icon and details.
        The icon of the message box can be specified with one of the Qt values:
            QMessageBox.NoIcon
            QMessageBox.Question
            QMessageBox.Information
            QMessageBox.Warning
            QMessageBox.Critical
        """
        msgBox = qtw.QMessageBox()
        msgBox.setText(text)
        msgBox.setStandardButtons(qtw.QMessageBox.Ok)
        msgBox.setDefaultButton(qtw.QMessageBox.Ok)
        if icon is not None:
            msgBox.setIcon(icon)
        if details is not None:
            msgBox.setDetailedText(details)

        msgBox.exec_()

    def __showInfo(self, info):
        """
        Show the information in the corresponding widget.
        info is a dict
        """
        self.__clearInfoWidget()
        if isinstance(info, dict):
            for key in info.keys():
                self._infoWidget.addItem("%s: %s" % (str(key).capitalize(),
                                                     str(info[key])))

    def __clearInfoWidget(self):
        """ Clear the info widget """
        self._infoWidget.clear()

    def __showVolumeSlice(self):
        """Show the Volume Slicer component"""
        self._stackLayout.setCurrentWidget(self._volumeView)

    def __showDataView(self):
        """Show the Table View component"""
        self._stackLayout.setCurrentWidget(self._dataView)

    def __showImageView(self):
        """ Show the ImageView component """
        self._stackLayout.setCurrentWidget(self._imageView)

    def __showSlicesView(self):
        """ Show the SlicesView component """
        self._stackLayout.setCurrentWidget(self._slicesView)

    def __showEmptyWidget(self):
        """Show an empty widget"""
        self._stackLayout.setCurrentWidget(self._emptyWidget)

    def _createViewPanel(self, **kwargs):
        viewPanel = qtw.QWidget(self)

        self._dataView = DataView(viewPanel, model=EmptyTableModel(), **kwargs)
        self._imageView = ImageView(viewPanel, **kwargs)
        self._slicesView = SlicesView(viewPanel, EmptySlicesModel(), **kwargs)

        self._volumeView = VolumeView(parent=viewPanel,
                                      model=EmptyVolumeModel(),
                                      **kwargs)
        self._emptyWidget = qtw.QWidget(parent=viewPanel)

        layout = qtw.QHBoxLayout(viewPanel)
        self._stackLayout = qtw.QStackedLayout(layout)
        self._stackLayout.addWidget(self._volumeView)
        self._stackLayout.addWidget(self._dataView)
        self._stackLayout.addWidget(self._imageView)
        self._stackLayout.addWidget(self._slicesView)
        self._stackLayout.addWidget(self._emptyWidget)

        return viewPanel

    def _createInfoPanel(self, **kwargs):
        self._infoWidget = qtw.QListWidget(self)
        return self._infoWidget

    def showFile(self, imagePath):
        """
        This method display an image using of pyqtgraph ImageView, a volume
        using the VOLUME-SLICER or GALLERY-VIEW components, a image stack or
        a Table characteristics.

        pageBar provides:

        1. A zoomable region for displaying the image
        2. A combination histogram and gradient editor (HistogramLUTItem) for
           controlling the visual appearance of the image
        3. Tools for very basic analysis of image data (see ROI and Norm
           buttons)

        :param imagePath: the image path
        """
        try:
            info = {'Type': 'UNKNOWN'}
            if EmPath.isTable(imagePath):
                model = ModelsFactory.createTableModel(imagePath)
                self._dataView.setModel(model)
                if not model.getRowsCount() == 1:
                    self._dataView.setView(COLUMNS)
                else:
                    self._dataView.setView(ITEMS)

                self.__showDataView()
                # Show the Table dimensions
                info['Type'] = 'TABLE'
                dimStr = "%d x %d" % (model.getRowsCount(),
                                      model.getColumnsCount())
                info['Dimensions (Rows x Columns)'] = dimStr
            elif EmPath.isData(imagePath) or EmPath.isStandardImage(imagePath):
                info = ImageManager().getInfo(imagePath)
                d = info['dim']
                if d.n == 1:  # Single image or volume
                    if d.z == 1:  # Single image
                        model = ModelsFactory.createImageModel(imagePath)
                        self._imageView.setModel(model)
                        self._imageView.setImageInfo(
                            path=imagePath, format=info['ext'],
                            data_type=str(info['data_type']))
                        info['Type'] = 'SINGLE-IMAGE'
                        self.__showImageView()
                    else:  # Volume
                        # The image has a volume. The data is a numpy 3D array.
                        # In this case, display the Top, Front and the Right
                        # View planes.
                        info['type'] = "VOLUME"
                        model = ModelsFactory.createVolumeModel(imagePath)
                        self._volumeView.setModel(model)
                        self.__showVolumeSlice()
                else:
                    # Image stack
                    if d.z > 1:  # Volume stack
                        raise Exception("Volume stack is not supported")
                    elif d.x <= MOVIE_SIZE:
                        info['type'] = 'IMAGES STACK'
                        model = ModelsFactory.createTableModel(imagePath)
                        self._dataView.setModel(model)
                        self._dataView.setView(GALLERY)
                        self.__showDataView()
                    else:
                        info['type'] = 'MOVIE'
                        model = ModelsFactory.createStackModel(imagePath)
                        self._slicesView.setModel(model)
                        self.__showSlicesView()
                    # TODO Show the image type
            else:
                self.__showEmptyWidget()
                info.clear()

            self.__showInfo(info)
        except Exception as ex:
            self.__showMsgBox("Error opening the file",
                              qtw.QMessageBox.Critical,
                              str(ex))
            self.__showEmptyWidget()
            self.__clearInfoWidget()
        except RuntimeError as ex:
            self.__showMsgBox("Error opening the file",
                              qtw.QMessageBox.Critical,
                              str(ex))
            self.__showEmptyWidget()
            self.__clearInfoWidget()

    def updateViewPanel(self):
        """
        Update the information of the view panel.
        """
        index = self._treeModelView.currentIndex()
        model = self._treeModelView.model()
        path = model.filePath(index)
        self.showFile(path)
