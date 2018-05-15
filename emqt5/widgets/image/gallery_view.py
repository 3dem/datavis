import os

from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QFrame, QSizePolicy,
                             QVBoxLayout, QLabel, QApplication,
                             QSpacerItem, QGridLayout, QDialog,
                             QSpinBox, QFormLayout, QComboBox, QListView,
                             QStyledItemDelegate, QStyle, QMessageBox)
from PyQt5.QtCore import Qt, QVariant, QSize, QRectF
from PyQt5.QtGui import QStandardItem, QStandardItemModel, QPalette, QPen, QIcon

import emqt5.utils.functions as utils

import qtawesome as qta
import numpy as np
import pyqtgraph as pg
import em


class GalleryView(QWidget):
    """
    Declaration of Volume Slice class
    """
    def __init__(self, parent=None, **kwargs):

        super(GalleryView, self).__init__(parent)
        self._image = None
        self._imagePath = kwargs.get('imagePath')
        self._iconWidth = kwargs.get('--iconWidth')
        self._iconHeight = kwargs.get('--iconHeight')
        if not self._iconWidth and not self._iconHeight:
            self._iconWidth = kwargs.get('iconWidth')
            self._iconHeight = kwargs.get('iconHeight')
        self._currentRow = 0
        self._itemDelegate = ImageItemDelegate(self, self._iconWidth,
                                               self._iconHeight)
        if self._imagePath:
            if utils.isEmImage(self._imagePath):
                self.galleryView()

    def _onGalleryViewPlaneChanged(self, index):
        """
        This Slot is executed when a new coordinate plane is selected.
        display a slices in the selected plane
        :param index: index of plane
        """
        self.fillTableGalleryView(index)
        self._onIconSizeChange()

    def _onSliceZoom(self, value):
        """
        The slices are resized taking into account the new value (in %)
        :param value: resize factor
        """
        if self._model:
            self._model.setIconSize(QSize(value+50, value+50))
        self._iconWidth = value+50
        self._iconHeight = value + 50
        self._tableSlices.setIconSize(QSize(value+50, value+50))

    def _onGotoItem(self, index):
        """
        The cell in the given index is selected
        :param row: the row
        """
        if self._tableSlices:
            if index in range(1, self._model.rowCount()+1):
                self._tableSlices.setCurrentIndex(
                    self._model.index(index-1, 0))
            self._currentRow = index

    def _onTableWidgetSliceClicked(self, index):
        """
        This methods is executes whenever a cell in the table is clicked.
        The index specified is the slice that was clicked.
        :param index: slice index
        """
        slice = index.row() + 1
        self._gotoItemSpinBox.setValue(slice)

    def _onIconSizeChange(self):
        """
        Calculate the number of columns and rows
        """
        if self._resliceComboBox.currentIndex() == 0: # Front View Slices(Z axis)
            sliceCount = self._dz
        elif self._resliceComboBox.currentIndex() == 1: # Top View Slices(Y axis)
            sliceCount = self._dy
        else:
            sliceCount = self._dx  # Right View Slices(X axis)

        cols = int((self.width() / (self._iconWidth + 8)))
        if sliceCount % cols == 0:
            rows = sliceCount / cols
        else:
            rows = sliceCount / cols + 1
        self._colsSpinBox.setValue(cols)
        self._rowsSpinBox.setValue(rows)

    def resizeEvent(self, event):
        """
        This event handler can be reimplemented in a subclass to receive widget
        resize events which are passed in the event parameter. When this method
        is called, the widget already has its new geometry.
        :param event:
        """
        if self._image:
            self._onIconSizeChange()

    def _onTableWidgetSliceDoubleClicked(self, index):
        """
        This methods is executes whenever a cell in the table is double clicked.
        The index specified is the slice that was clicked.
        This methods display the slice that was selected
        :param index: slice index
        """
        # Calculate the slice selected number
        slice = index.row()

        # Create a new Window to display the slice
        self._sliceViewDialog = QDialog()
        self._sliceViewDialog.setModal(True)

        self._sliceViewDialog.setGeometry(380, 100, 550, 550)
        self._sliceViewWidget = QWidget(self._sliceViewDialog)

        self._sliceVerticalLayout = QGridLayout(self._sliceViewWidget)
        self._sliceViewDialog.setLayout(self._sliceVerticalLayout.layout())

        # Select the plane slice
        plane = self._resliceComboBox.currentIndex()

        # Select the slice in plane
        if plane == 0:
            array = np.array(self._array3D[slice, :, :])
        elif plane == 1:
            array = np.array(self._array3D[:, slice, :])
        else:
            array = np.array(self._array3D[:, :, slice])

        self._sliceViewDialog.setWindowTitle(self._resliceComboBox.currentText()
                                             + ': Slice ' + str(slice + 1))

        # Construct an ImageView with the slice selected
        sliceSelected = pg.ImageView(view=pg.PlotItem())
        self._sliceVerticalLayout.addWidget(sliceSelected, 0, 0)
        sliceSelected.setImage(array)

        self._sliceViewDialog.show()

    def galleryView(self):
        """
        Create a window to display a Gallery View. This method show slice
        frames around the volume data in a table.
        """

        if utils.isEmImage(self._imagePath):

            # Create an image from imagePath using em-bindings
            self._image = em.Image()
            loc2 = em.ImageLocation(self._imagePath)
            self._image.read(loc2)
            # Read the dimensions of the image
            dim = self._image.getDim()

            self._dx = dim.x
            self._dy = dim.y
            self._dz = dim.z

            if self._dz > 1:  # The image has a volumes
                # Create a numpy 3D array with the image values pixel
                self._array3D = np.array(self._image, copy=False)
                self.createGalleryViewTable()
            else:
                self.createErrorTextLoadingImage()
                self._image = None

    def createErrorTextLoadingImage(self):
        """
        Create an Error Text because the image do not has a volume
        """
        self.setGeometry(400, 200, 430, 100)

        label = QLabel(self)
        label.setText(' ERROR: A valid 3D image format are required. See the '
                      'image path.')

    def createGalleryViewTable(self):
        """
        Create a main windows with the Gallery View Table
        """
        self.setWindowTitle('Gallery-View')
        # Create a main window
        self.setGeometry(300, 150, 700, 550)
        self.setMinimumWidth(515)
        self.setMinimumHeight(400)
        self._verticalLayout = QVBoxLayout(self)
        self.setLayout(self._verticalLayout.layout())

        # Create a tool bar
        self._galleryViewVerticalLayout = QVBoxLayout()

        self._optionFrame = QFrame(self)
        self._optionFrame.setFrameShape(QFrame.StyledPanel)
        self._optionFrame.setFrameShadow(QFrame.Raised)

        self._horizontalLayout = QHBoxLayout(self._optionFrame)

        self._zoomLabel = QLabel(self._optionFrame)
        self._zoomLabel.setPixmap(qta.icon('fa.search').pixmap(20, QIcon.Normal,
                                                               QIcon.On))
        self._horizontalLayout.addWidget(self._zoomLabel)

        self._zoomSpinBox = QSpinBox(self._optionFrame)
        self._zoomSpinBox.setMaximumHeight(400)
        self._zoomSpinBox.setMinimum(50)
        self._zoomSpinBox.setMaximum(200)
        self._zoomSpinBox.setValue(100)
        self._zoomSpinBox.setSingleStep(1)
        self._horizontalLayout.addWidget(self._zoomSpinBox)
        self._zoomSpinBox.valueChanged.connect(self._onSliceZoom)

        self._goToItemLabel = QLabel(self._optionFrame)
        self._goToItemLabel.setPixmap(qta.icon('fa.long-arrow-down').
                                      pixmap(20, QIcon.Normal, QIcon.On))

        self._horizontalLayout.addWidget(self._goToItemLabel)

        self._gotoItemSpinBox = QSpinBox(self._optionFrame)
        self._gotoItemSpinBox.setMinimum(1)
        self._gotoItemSpinBox.valueChanged.connect(self._onGotoItem)

        self._horizontalLayout.addWidget(self._gotoItemSpinBox)

        self._colsFormLayout = QFormLayout()
        self._colsLabel = QLabel(self._optionFrame)
        self._colsLabel.setText('Cols')
        self._colsFormLayout.setWidget(0, QFormLayout.LabelRole,
                                       self._colsLabel)

        self._colsSpinBox = QSpinBox(self._optionFrame)
        self._colsSpinBox.setEnabled(False)
        self._colsSpinBox.setMinimum(1)
        self._colsSpinBox.setValue(int(self.width() / (self._iconWidth + 10)))
        self._colsFormLayout.setWidget(0, QFormLayout.FieldRole,
                                       self._colsSpinBox)

        self._horizontalLayout.addLayout(self._colsFormLayout)

        self._rowsFormLayout = QFormLayout()
        self._rowsLabel = QLabel(self._optionFrame)
        self._rowsLabel.setText('Rows')

        self._rowsFormLayout.setWidget(0, QFormLayout.LabelRole,
                                       self._rowsLabel)

        self._rowsSpinBox = QSpinBox(self._optionFrame)
        self._rowsSpinBox.setEnabled(False)
        self._rowsSpinBox.setValue(int(self._dz / int(self.width() /
                                                      (self._iconWidth+10))))
        self._rowsSpinBox.setMinimum(1)
        self._rowsFormLayout.setWidget(0, QFormLayout.FieldRole,
                                       self._rowsSpinBox)

        self._horizontalLayout.addLayout(self._rowsFormLayout)

        self._resliceComboBox = QComboBox(self._optionFrame)
        self._resliceComboBox.insertItem(0, 'Z Axis (Front View)')
        self._resliceComboBox.insertItem(1, 'Y Axis (Top View)')
        self._resliceComboBox.insertItem(2, 'X Axis (Right View)')
        self._resliceComboBox.currentIndexChanged.connect(
            self._onGalleryViewPlaneChanged)

        self._horizontalLayout.addWidget(self._resliceComboBox)

        self.optionsHorizontalSpacer = QSpacerItem(40, 20,
                                                   QSizePolicy.Expanding,
                                                   QSizePolicy.Minimum)

        self._horizontalLayout.addItem(self.optionsHorizontalSpacer)

        self._galleryViewVerticalLayout.addWidget(self._optionFrame)

        # Create a Table View

        self._tableSlices = QListView(self)
        self._galleryViewVerticalLayout.addWidget(self._tableSlices)
        self._tableSlices.setIconSize(QSize(self._iconWidth, self._iconHeight))
        self._tableSlices.setViewMode(QListView.IconMode)
        self._tableSlices.setResizeMode(QListView.Adjust)
        self._tableSlices.setSpacing(1)

        self._tableSlices.clicked.connect(self._onTableWidgetSliceClicked)
        self._tableSlices.doubleClicked.connect(
            self._onTableWidgetSliceDoubleClicked)
        self._tableSlices.iconSizeChanged.connect(self._onIconSizeChange)

        self._verticalLayout.addLayout(self._galleryViewVerticalLayout)

        self.fillTableGalleryView(self._resliceComboBox.currentIndex())

    def setupProperties(self):
        """
        Setup all components
        """
        if self._image:
            self._image = None
            self._tableSlices.close()
            self.close()

    def fillTableGalleryView(self, plane):
        """
        Fill the Table Widget with the slices in the specified plane. The images
        displayed represent a slice.
        :param plane: dimension plane (x, y, z)
        """

        self._gotoItemSpinBox.setValue(1)

        self._model = GalleryDataModel(self, QSize(self._iconWidth,
                                                   self._iconHeight))

        if plane == 0:  # Display the slices on the Front View

            self._gotoItemSpinBox.setMaximum(self._dz)
            for sliceCount in range(0, self._dz):

                sliceZ = self._array3D[sliceCount, :, :]

                item = QStandardItem()
                self._model.appendRow(item)
                item.setData(sliceZ, Qt.UserRole)

        elif plane == 1:  # Display data slices on the Top View

                self._gotoItemSpinBox.setMaximum(self._dy)
                for sliceCount in range(0, self._dy):

                    sliceY = self._array3D[:, sliceCount, :]
                    item = QStandardItem()
                    self._model.appendRow(item)
                    item.setData(sliceY, Qt.UserRole)

        else:  # Display the slices on the Right View

            self._gotoItemSpinBox.setMaximum(self._dx)
            for sliceCount in range(0, self._dx):

                sliceX = self._array3D[:, :, sliceCount]
                item = QStandardItem()
                self._model.appendRow(item)
                item.setData(sliceX, Qt.UserRole)

        self._tableSlices.setModel(self._model)
        self._tableSlices.setModelColumn(0)
        self._tableSlices.setItemDelegate(self._itemDelegate)
        #self._tableSlices.setCurrentIndex(self._model.index(0, 0))


class ImageItemDelegate(QStyledItemDelegate):
    """
    ImageItemDelegate class provides display and editing facilities for
    image data items from a model.
    """
    def __init__(self, parent=None, iconWidth=150, iconHeight=150):
        QStyledItemDelegate.__init__(self, parent)
        self._imageView = pg.ImageView(view=pg.ViewBox())
        self._iconWidth = iconWidth
        self._iconHeight = iconHeight

    def paint(self, painter, option, index):
        """
        Reimplemented from QStyledItemDelegate
        """
        if index.isValid():
            self._setupImageView(index)

            if option.state & QStyle.State_Selected:
                if option.state & QStyle.State_HasFocus or \
                     option.state & QStyle.State_Active:
                    colorGroup = QPalette.Active
                else:
                    colorGroup = QPalette.Inactive

                painter.fillRect(option.rect,
                                 option.palette.color(colorGroup,
                                                      QPalette.Highlight))

            self._imageView.ui.graphicsView.scene().render(painter,
                                                           QRectF(option.rect))
            self._imageView.ui.graphicsView.scene().setSceneRect(
                QRectF(9, 9, option.rect.width()-17, option.rect.height()-17))

            if option.state & QStyle.State_HasFocus:
                pen = QPen(Qt.DashDotDotLine)
                pen.setColor(Qt.red)
                painter.setPen(pen)
                painter.drawRect(option.rect.x(), option.rect.y(),
                                 option.rect.width()-1, option.rect.height()-1)
            QApplication.style().drawPrimitive(
                QStyle.PE_FrameFocusRect, option, painter)

    def _setupImageView(self, index):
        """
        If the thumbnail stored in Qt.UserRole is None then create a
        thumbnail by scaling the original image according to its height and
        store the new thumbnail in Qt.DecorationRole
        :param item: the item
        :param height: height to scale the image
        :param width: width to scale the image
        """
        array = index.model().data(index, Qt.UserRole)
        size = index.model().data(index, Qt.SizeHintRole)
        self._imageView.getView().setGeometry(0, 0, size.width(),
                                    size.height())
        self._imageView.getView().resizeEvent(None)
        self._imageView.setImage(array)


class GalleryDataModel(QStandardItemModel):
    """
    Model for Gallery View
    """
    def __init__(self, parent=None, iconSize=QSize(150, 150)):
        """
        Constructs an GalleryDataModel with the given parent.
        :param parent: The parent
        :param iconSize: size of the image.
        """
        QStandardItemModel.__init__(self, parent)
        self._iconSize = iconSize

    def data(self, qModelIndex, role=Qt.UserRole):
        """
        This is an reimplemented function from QStandardItemModel.
        Reimplemented to hide the 'True' text in columns with boolean value.
        We use Qt.UserRole for store table data.
        :param qModelIndex:
        :param role:
        :return: QVariant
        """
        if not qModelIndex.isValid():
            return None
        item = self.itemFromIndex(qModelIndex)

        if role == Qt.DisplayRole:
            if self._colProperties[qModelIndex.column()].getType() == 'Bool':
                return QVariant  # hide 'True' or 'False' text

            return item.data(Qt.UserRole)  # we use Qt.UserRole for store data

        if role == Qt.SizeHintRole:
            return self._iconSize

        return QStandardItemModel.data(self, qModelIndex, role)

    def setData(self, qModelIndex, value, role=None):
        """
        Set data in the model. We use Qt.UserRole for store data
        :param qModelIndex:
        :param value:
        :param role:
        :return:
        """
        if not self.flags(qModelIndex) & Qt.ItemIsEditable:
            return False

        if role == Qt.CheckStateRole:
            return QStandardItemModel.setData(self, qModelIndex,
                                                  value, Qt.UserRole)

        if role == Qt.EditRole:
            QStandardItemModel.setData(self, qModelIndex,
                                       value, Qt.UserRole)

        return QStandardItemModel.setData(self, qModelIndex, value, role)

    def setIconSize(self, size):
        """
        Sets the size for renderable items
        :param size: QSize
        """
        self._iconSize = size

    def flags(self, qModelIndex):
        """
        Reimplemented from QStandardItemModel
        :param qModelIndex: index in the model
        :return: The flags for the item. See :  Qt.ItemDataRole
        """
        fl = Qt.ItemIsDragEnabled

        return QStandardItemModel.flags(self, qModelIndex) & \
               ~Qt.ItemIsEditable & ~fl



