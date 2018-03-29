import os

from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QFrame, QSizePolicy,
                             QVBoxLayout, QLabel, QApplication,
                             QSpacerItem, QGridLayout, QDialog,
                             QSpinBox, QFormLayout, QComboBox, QListView,
                             QStyledItemDelegate, QStyle)
from PyQt5.QtCore import Qt, QVariant, QSize, QRectF
from PyQt5.QtGui import QStandardItem, QStandardItemModel, QPalette, QPen, QIcon

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
            if self.isEmImage(self._imagePath):
                self.galleryView()

    def _onGalleryViewPlaneChanged(self, index):
        """
        This Slot is executed when a new coordinate plane is selected.
        display a slices in the selected plane
        :param index: index of plane
        """
        self.fillTableGalleryView(index)

    def _onSliceZoom(self, value):
        """
        The slices are resized taking into account the new value (in %)
        :param value: resize factor
        """
        if self._model:
            self._model.setIconSize(QSize(value+50, value+50))
        self._iconWidth = value+50
        self._iconHeight = value + 50
        self.tableSlices.setIconSize(QSize(value+50, value+50))

    def _onGotoItem(self, index):
        """
        The cell in the given index is selected
        :param row: the row
        """
        if self.tableSlices:
            if index in range(1, self._model.rowCount()+1):
                self.tableSlices.setCurrentIndex(
                    self._model.index(index-1, 0))
            self._currentRow = index

    def _onTableWidgetSliceClicked(self, index):
        """
        This methods is executes whenever a cell in the table is clicked.
        The index specified is the slice that was clicked.
        :param index: slice index
        """
        slice = index.row() + 1
        self.gotoItemSpinBox.setValue(slice)

    def _onIconSizeChange(self):
        """
        Calculate the number of columns and rows
        """
        if self.resliceComboBox.currentIndex() == 0: # Front View Slices(Z axis)
            sliceCount = self.dz
        elif self.resliceComboBox.currentIndex() == 1: # Top View Slices(Y axis)
            sliceCount = self.dy
        else:
            sliceCount = self.dx  # Right View Slices(X axis)

        cols = int((self.width() / (self._iconWidth + 8)))
        if sliceCount % cols == 0:
            rows = sliceCount / cols
        else:
            rows = sliceCount / cols + 1
        self.colsSpinBox.setValue(cols)
        self.rowsSpinBox.setValue(rows)

    def resizeEvent(self, event):
        """
        This event handler can be reimplemented in a subclass to receive widget
        resize events which are passed in the event parameter. When this method
        is called, the widget already has its new geometry.
        :param event:
        """
        self._onIconSizeChange()

    def __onTableWidgetSliceDoubleClicked(self, index):
        """
        This methods is executes whenever a cell in the table is double clicked.
        The index specified is the slice that was clicked.
        This methods display the slice that was selected
        :param index: slice index
        """
        # Calculate the slice selected number
        slice = index.row()

        # Create a new Window to display the slice
        self.sliceViewDialog = QDialog()
        self.sliceViewDialog.setModal(True)

        self.sliceViewDialog.setGeometry(380, 100, 550, 550)
        self.sliceViewWidget = QWidget(self.sliceViewDialog)

        self.sliceVerticalLayout = QGridLayout(self.sliceViewWidget)
        self.sliceViewDialog.setLayout(self.sliceVerticalLayout.layout())

        # Select the plane slice
        plane = self.resliceComboBox.currentIndex()

        # Select the slice in plane
        if plane == 0:
            array = np.array(self._array3D[slice, :, :])
        elif plane == 1:
            array = np.array(self._array3D[:, slice, :])
        else:
            array = np.array(self._array3D[:, :, slice])

        self.sliceViewDialog.setWindowTitle(self.resliceComboBox.currentText() +
                                            ': Slice ' + str(slice + 1))

        # Construct an ImageView with the slice selected
        v = pg.ImageView(view=pg.PlotItem())
        self.sliceVerticalLayout.addWidget(v, 0, 0)
        v.setImage(array)

        self.sliceViewDialog.show()

    def galleryView(self):
        """
        Create a window to display a Gallery View. This method show slice
        frames around the volume data in a table.
        """

        if self.isEmImage(self._imagePath):

            # Create an image from imagePath using em-bindings
            self._image = em.Image()
            loc2 = em.ImageLocation(self._imagePath)
            self._image.read(loc2)
            # Read the dimensions of the image
            dim = self._image.getDim()

            self.dx = dim.x
            self.dy = dim.y
            self.dz = dim.z

            if self.dz > 1:  # The image has a volumes
                # Create a numpy 3D array with the image values pixel
                self._array3D = np.array(self._image, copy=False)
                self.createGalleryViewTable()

    def createGalleryViewTable(self):
        """
        Create a main windows with the Gallery View Table
        """
        # Create a main window
        self.setGeometry(300, 150, 700, 550)
        self.verticalLayout = QVBoxLayout(self)
        self.setLayout(self.verticalLayout.layout())

        # Create a tool bar
        self.galleryViewVerticalLayout = QVBoxLayout()

        self.optionFrame = QFrame(self)
        self.optionFrame.setFrameShape(QFrame.StyledPanel)
        self.optionFrame.setFrameShadow(QFrame.Raised)

        self.horizontalLayout = QHBoxLayout(self.optionFrame)

        self.zoomLabel = QLabel(self.optionFrame)
        self.zoomLabel.setPixmap(qta.icon('fa.search').pixmap(20, QIcon.Normal,
                                                               QIcon.On))
        self.horizontalLayout.addWidget(self.zoomLabel)

        self.zoomSpinBox = QSpinBox(self.optionFrame)
        self.zoomSpinBox.setMaximumHeight(400)
        self.zoomSpinBox.setMinimum(50)
        self.zoomSpinBox.setMaximum(200)
        self.zoomSpinBox.setValue(100)
        self.zoomSpinBox.setSingleStep(1)
        self.horizontalLayout.addWidget(self.zoomSpinBox)
        self.zoomSpinBox.valueChanged.connect(self._onSliceZoom)

        self.goToItemLabel = QLabel(self.optionFrame)
        self.goToItemLabel.setPixmap(qta.icon('fa.long-arrow-down').pixmap(20,
                                                               QIcon.Normal,
                                                               QIcon.On))

        self.horizontalLayout.addWidget(self.goToItemLabel)

        self.gotoItemSpinBox = QSpinBox(self.optionFrame)
        self.gotoItemSpinBox.setMinimum(1)
        self.gotoItemSpinBox.valueChanged.connect(self._onGotoItem)

        self.horizontalLayout.addWidget(self.gotoItemSpinBox)

        self.colsFormLayout = QFormLayout()
        self.colsLabel = QLabel(self.optionFrame)
        self.colsLabel.setText('Cols')

        self.colsFormLayout.setWidget(0, QFormLayout.LabelRole, self.colsLabel)

        self.colsSpinBox = QSpinBox(self.optionFrame)
        self.colsSpinBox.setEnabled(False)
        self.colsSpinBox.setMinimum(1)
        self.colsSpinBox.setValue(int(self.width() / (self._iconWidth+10)))
        self.colsFormLayout.setWidget(0, QFormLayout.FieldRole,
                                      self.colsSpinBox)

        self.horizontalLayout.addLayout(self.colsFormLayout)

        self.rowsFormLayout = QFormLayout()
        self.rowsLabel = QLabel(self.optionFrame)
        self.rowsLabel.setText('Rows')

        self.rowsFormLayout.setWidget(0, QFormLayout.LabelRole, self.rowsLabel)

        self.rowsSpinBox = QSpinBox(self.optionFrame)
        self.rowsSpinBox.setEnabled(False)
        self.rowsSpinBox.setValue(int(self.dz / int(self.width() /
                                                    (self._iconWidth+10))))
        self.rowsSpinBox.setMinimum(1)
        self.rowsFormLayout.setWidget(0, QFormLayout.FieldRole,
                                      self.rowsSpinBox)

        self.horizontalLayout.addLayout(self.rowsFormLayout)

        self.resliceComboBox = QComboBox(self.optionFrame)
        self.resliceComboBox.insertItem(0, 'Z Axis (Front View)')
        self.resliceComboBox.insertItem(1, 'Y Axis (Top View)')
        self.resliceComboBox.insertItem(2, 'X Axis (Right View)')
        self.resliceComboBox.currentIndexChanged.connect(
            self._onGalleryViewPlaneChanged)

        self.horizontalLayout.addWidget(self.resliceComboBox)

        self.optionsHorizontalSpacer = QSpacerItem(40, 20,
                                                   QSizePolicy.Expanding,
                                                   QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.optionsHorizontalSpacer)

        self.galleryViewVerticalLayout.addWidget(self.optionFrame)

        # Create a Table View

        self.tableSlices = QListView(self)
        self.galleryViewVerticalLayout.addWidget(self.tableSlices)
        self.tableSlices.setIconSize(QSize(self._iconWidth, self._iconHeight))
        self.tableSlices.setViewMode(QListView.IconMode)
        self.tableSlices.setResizeMode(QListView.Adjust)

        self.tableSlices.clicked.connect(self._onTableWidgetSliceClicked)
        self.tableSlices.doubleClicked.connect(
            self.__onTableWidgetSliceDoubleClicked)
        self.tableSlices.iconSizeChanged.connect(self._onIconSizeChange)


        self.verticalLayout.addLayout(self.galleryViewVerticalLayout)

        self.fillTableGalleryView(self.resliceComboBox.currentIndex())

    def setupProperties(self):
        """
        Setup all components
        :return:
        """
        if self._image:
            self._image = None
            self.tableSlices.close()
            self.close()

    def fillTableGalleryView(self, plane):
        """
        Fill the Table Widget with the slices in the specified plane. The images
        displayed represent a slice.
        :param plane: dimension plane (x, y, z)
        """

        self.gotoItemSpinBox.setValue(1)

        self._model = GalleryDataModel(self, QSize(self._iconWidth,
                                                   self._iconHeight))

        if plane == 0:  # Display the slices on the Front View

            self.gotoItemSpinBox.setMaximum(self.dz)
            for sliceCount in range(0, self.dz):

                sliceZ = self._array3D[sliceCount, :, :]

                item = QStandardItem()
                self._model.appendRow(item)
                item.setData(sliceZ, Qt.UserRole)

        elif plane == 1:  # Display data slices on the Top View

                self.gotoItemSpinBox.setMaximum(self.dy)
                for sliceCount in range(0, self.dy):

                    sliceY = self._array3D[:, sliceCount, :]
                    item = QStandardItem()
                    self._model.appendRow(item)
                    item.setData(sliceY, Qt.UserRole)

        else:  # Display the slices on the Right View

            self.gotoItemSpinBox.setMaximum(self.dx)
            for sliceCount in range(0, self.dx):

                sliceX = self._array3D[:, :, sliceCount]
                item = QStandardItem()
                self._model.appendRow(item)
                item.setData(sliceX, Qt.UserRole)

        self.tableSlices.setModel(self._model)
        self.tableSlices.setModelColumn(0)
        self.tableSlices.setItemDelegate(self._itemDelegate)
        #self.tableSlices.setCurrentIndex(self._model.index(0, 0))


    @staticmethod
    def isEmImage(imagePath):
        """ Return True if imagePath has an extension recognized as supported
            EM-image """
        _, ext = os.path.splitext(imagePath)
        return ext in ['.mrc', '.mrcs', '.spi', '.stk', '.map']


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

    def createEditor(self, parent, option, index):
        """
        Otherwise an editor is created if the user clicks in this cell.
        """
        return None

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
                QRectF(8, 8, option.rect.width()-16, option.rect.height()-16))

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

    def flags(self, qModelIndex):
        """
        Reimplemented from QStandardItemModel
        :param qModelIndex: index in the model
        :return: The flags for the item. See :  Qt.ItemDataRole
        """
        fl = Qt.ItemIsDragEnabled

        return QStandardItemModel.flags(self, qModelIndex) & ~Qt.ItemIsEditable \
               & ~fl

    def setIconSize(self, size):
        """
        Sets the size for renderable items
        :param size: QSize
        """
        self._iconSize = size

