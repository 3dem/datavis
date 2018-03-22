import os

from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QFrame, QSizePolicy,
                             QVBoxLayout, QLabel, QPushButton,
                             QSpacerItem, QGridLayout, QDialog,
                             QSpinBox, QFormLayout, QComboBox,
                             QTableWidget, QItemDelegate, QTableView)
from PyQt5.QtCore import Qt, QAbstractTableModel, QModelIndex

import qtawesome as qta
import numpy as np
import pyqtgraph as pg
import em


class GalleryView(QWidget):
    """
    Declaration of Volume Slice class
    """
    def __init__(self, imagePath, parent=None, **kwargs):

        super(GalleryView, self).__init__(parent)
        self.imagePath = imagePath
        self.galleryView()

    def _onGalleryViewPlaneChanged(self, index):
        """
        This Slot is executed when a new coordinate plane is selected.
        display a slices in the selected plane
        :param index: index of plane
        """
        self.tableSlices.clearContents()
        self.fillTableGalleryView(self.rowsSpinBox.value(),
                                    self.colsSpinBox.value(),
                                    index)

    def _onSliceZoom(self, value):
        """
        The slices are resized taking into account the new value (in %)
        :param value: resize factor
        """
        for row in range(0, self.rowsSpinBox.value()):
            self.tableSlices.setRowHeight(row, 50 + value)
        for col in range(0, self.colsSpinBox.value()):
            self.tableSlices.setColumnWidth(col, 50 + value)

    def _onGotoItem(self, value):
        """
        Find an especific slice represented by a number and set the focus on this
        :param value: number of slice
        :return:
        """
        # Calculate the row and col that represent the slice value
        row = int(value/self.colsSpinBox.value())
        if int(value%self.colsSpinBox.value()) != 0:
            col = int(value%self.colsSpinBox.value()-1)
        else:
            row = row - 1
            col = self.colsSpinBox.value()-1

        # Move the focus to slice in the specified row and col
        self.tableSlices.setCurrentCell(row, col)

    def _onTableWidgetSliceClicked(self, row, col):
        """
        This methods is executes whenever a cell in the table is clicked.
        The row and column specified is the slice that was clicked.
        :param row: slice row
        :param col: slice col
        """
        self.gotoItemSpinBox.setValue(row * self.colsSpinBox.value() + col + 1)

    def __onTableWidgetSliceDoubleClicked(self, row, col):
        """
        This methods is executes whenever a cell in the table is double clicked.
        The row and column specified is the slice that was clicked.
        This methods display the slice that was selected
        :param row: slice row
        :param col: slice col
        """

        # Calculate the slice selected number
        slice = row * self.colsSpinBox.value() + col

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
            array = np.array(self.array3D[slice, :, :])
        elif plane == 1:
            array = np.array(self.array3D[:, slice, :])
        else:
            array = np.array(self.array3D[:, :, slice])

        self.sliceViewDialog.setWindowTitle(self.resliceComboBox.currentText() +
                                            ': Slice ' + str(slice + 1))

        # Contruct an ImageView with the slice selected
        v = pg.ImageView(view=pg.PlotItem())
        self.sliceVerticalLayout.addWidget(v, 0, 0)
        v.setImage(array)

        self.sliceViewDialog.show()

    def galleryView(self):
        """
        Create a window to display a Gallery View. This method show slice
        frames around the volume data in a table.
        """

        if self.isEmImage(self.imagePath):

            # Create an image from imagePath using em-bindings
            self.image = em.Image()
            loc2 = em.ImageLocation(self.imagePath)
            self.image.read(loc2)
            # Read the dimensions of the image
            dim = self.image.getDim()

            self.dx = dim.x
            self.dy = dim.y
            self.dz = dim.z

            """x1 = np.linspace(-30, 10, 128)[:, np.newaxis, np.newaxis]
            x2 = np.linspace(-20, 20, 128)[:, np.newaxis, np.newaxis]
            y = np.linspace(-30, 10, 128)[np.newaxis, :, np.newaxis]
            z = np.linspace(-20, 20, 128)[np.newaxis, np.newaxis, :]
            d1 = np.sqrt(x1 ** 2 + y ** 2 + z ** 2)
            d2 = 2 * np.sqrt(x1[::-1] ** 2 + y ** 2 + z ** 2)
            d3 = 4 * np.sqrt(x2 ** 2 + y[:, ::-1] ** 2 + z ** 2)
            data = (np.sin(d1) / d1 ** 2) + (np.sin(d2) / d2 ** 2) + (
                    np.sin(d3) / d3 ** 2)

            self.dx = 128
            self.dy = 128
            self.dz = 128

            self.array3D = np.array(data, copy=False)"""

            if self.dz > 1:  # The image has a volumes

                # Create a numpy 3D array with the image values pixel
                self.array3D = np.array(self.image, copy=False)
                self.createGalleryViewTable()

    def createGalleryViewTable(self):
        """
        Create a main windows with the Gallery View Table
        """
        # Create a main window

        self.verticalLayout = QVBoxLayout(self)
        self.setLayout(self.verticalLayout.layout())

        # Create a tool bar
        self.galleryViewVerticalLayout = QVBoxLayout(self)

        self.optionFrame = QFrame(self)
        self.optionFrame.setFrameShape(QFrame.StyledPanel)
        self.optionFrame.setFrameShadow(QFrame.Raised)

        self.horizontalLayout = QHBoxLayout(self.optionFrame)

        self.zoomPushButton = QPushButton(self.optionFrame)
        self.zoomPushButton.setEnabled(False)
        self.zoomPushButton.setIcon(qta.icon('fa.search'))

        self.horizontalLayout.addWidget(self.zoomPushButton)

        self.zoomSpinBox = QSpinBox(self.optionFrame)
        self.zoomSpinBox.setMaximumHeight(400)
        self.zoomSpinBox.setMinimum(50)
        self.zoomSpinBox.setMaximum(300)
        self.zoomSpinBox.setValue(100)
        self.zoomSpinBox.setSingleStep(1)
        self.horizontalLayout.addWidget(self.zoomSpinBox)
        self.zoomSpinBox.valueChanged.connect(self._onSliceZoom)

        self.goToItemPushButton = QPushButton(self.optionFrame)
        self.goToItemPushButton.setEnabled(False)
        self.goToItemPushButton.setIcon(qta.icon('fa.long-arrow-down'))
        self.horizontalLayout.addWidget(self.goToItemPushButton)

        self.gotoItemSpinBox = QSpinBox(self.optionFrame)
        self.gotoItemSpinBox.setMinimum(1)
        self.gotoItemSpinBox.valueChanged.connect(self._onGotoItem)

        self.horizontalLayout.addWidget(self.gotoItemSpinBox)

        self.colsFormLayout = QFormLayout()
        self.colsLabel = QLabel(self.optionFrame)
        self.colsLabel.setText('Cols')

        self.colsFormLayout.setWidget(0, QFormLayout.LabelRole, self.colsLabel)

        self.colsSpinBox = QSpinBox(self.optionFrame)
        self.colsSpinBox.setMinimum(1)
        self.colsSpinBox.setValue(int(np.sqrt(self.dz)))
        self.colsFormLayout.setWidget(0, QFormLayout.FieldRole,
                                      self.colsSpinBox)

        self.horizontalLayout.addLayout(self.colsFormLayout)

        self.rowsFormLayout = QFormLayout()
        self.rowsLabel = QLabel(self.optionFrame)
        self.rowsLabel.setText('Rows')

        self.rowsFormLayout.setWidget(0, QFormLayout.LabelRole, self.rowsLabel)

        self.rowsSpinBox = QSpinBox(self.optionFrame)
        self.rowsSpinBox.setValue(int(np.sqrt(self.dz) + 1))
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

        """self.tableWidget = QWidget()
        self._tm = TableModel(self.tableWidget,
                              50,
                              50,
                              150, 150)
        self._tv = TableView(self.tableWidget)
        self._tv.setModel(self._tm)"""

        self.tableSlices = QTableWidget()
        self.galleryViewVerticalLayout.addWidget(self.tableSlices)

        self.tableSlices.cellClicked.connect(self._onTableWidgetSliceClicked)
        self.tableSlices.cellDoubleClicked.connect(
            self.__onTableWidgetSliceDoubleClicked)

        self.verticalLayout.addLayout(self.galleryViewVerticalLayout)

        self.fillTableGalleryView(self.rowsSpinBox.value(),
                                  self.colsSpinBox.value(),
                                  self.resliceComboBox.currentIndex())

    def fillTableGalleryView(self, rowsCount, colsCount, plane):
        """
        Fill the Table Widget with the slices in the specified plane. The images
        displayed represent a slice.
        :param rowCount: count of rows that the table have
        :param colCount: count of columns that the table have
        :param plane: dimension plane (x, y, z)
        :return:
        """
        self.tableSlices.setColumnCount(colsCount)
        self.tableSlices.setRowCount(rowsCount)
        self.tableSlices.clearContents()
        self.gotoItemSpinBox.setValue(1)
        row = 0
        col = 0

        if plane == 0:  # Display the slices on the Front View

            self.gotoItemSpinBox.setMaximum(self.dz)
            for sliceCount in range(0, self.dz):

                sliceZ = self.array3D[sliceCount, :, :]

                self.itemSlice = self.createNewItemSlice(sliceZ, sliceCount+1)

                self.tableSlices.setCellWidget(row, col, self.itemSlice)
                self.tableSlices.setRowHeight(row, 150)
                self.tableSlices.setColumnWidth(col, 150)
                col = col + 1
                if col == colsCount:
                    col = 0
                    row = row + 1

        elif plane == 1:  # Display data slices on the Top View

                self.gotoItemSpinBox.setMaximum(self.dy)
                for sliceCount in range(0, self.dy):

                    sliceY = self.array3D[:, sliceCount, :]
                    self.itemSlice = self.createNewItemSlice(sliceY, sliceCount+1)
                    self.tableSlices.setCellWidget(row, col, self.itemSlice)
                    self.tableSlices.setRowHeight(row, 150)
                    self.tableSlices.setColumnWidth(col, 150)
                    col = col + 1
                    if col == colsCount:
                        col = 0
                        row = row + 1

        else:  # Display the slices on the Right View

            self.gotoItemSpinBox.setMaximum(self.dx)
            for sliceCount in range(0, self.dx):

                sliceX = self.array3D[:, :, sliceCount]
                self.itemSlice = self.createNewItemSlice(sliceX, sliceCount+1)
                self.tableSlices.setCellWidget(row, col, self.itemSlice)
                self.tableSlices.setRowHeight(row, 150)
                self.tableSlices.setColumnWidth(col, 150)
                col = col + 1
                if col == colsCount:
                    col = 0
                    row = row + 1

        self.tableSlices.setCurrentCell(0, 0)

    def createNewItemSlice(self, slice, sliceCount):
        """
        Create a new item taking into account a 2D array(slice) and put this
        into the Table Widget
        return: new item-slice
        """
        frame = QFrame()
        frame.setEnabled(False)
        widget = pg.GraphicsLayoutWidget()
        layout = QGridLayout(frame)
        frame.setLayout(layout.layout())
        layout.addWidget(widget, 0, 0)
        plotArea = widget.addPlot()
        plotArea.showAxis('bottom', False)
        plotArea.showAxis('left', False)
        imageItem = pg.ImageItem()
        plotArea.addItem(imageItem)
        imageItem.setImage(slice)
        layout.addWidget(QLabel('slice '+ str(sliceCount)), 1, 0)

        return frame

    @staticmethod
    def isEmImage(imagePath):
        """ Return True if imagePath has an extension recognized as supported
            EM-image """
        _, ext = os.path.splitext(imagePath)
        return ext in ['.mrc', '.mrcs', '.spi', '.stk', '.map']


class TableModel(QAbstractTableModel):
    """
    A table model to use the imageView delegate
    """

    def __init__(self, parentWidget,
                 rowsCount,
                 colsCount,
                 rowHeight,
                 colWidth):
        """
        Constructor
        :param rowsCount:
        :param colsCount:
        """
        QAbstractTableModel.__init__(self, parentWidget)
        self.rows = rowsCount
        self.cols = colsCount
        self.rowHeight = rowHeight
        self.colWidth = colWidth

    def rowCount(self, parent=QModelIndex()):
        return self.rows

    def columnCount(self, parent=QModelIndex()):
        return self.cols

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        if not role == Qt.DisplayRole:
            return None

        # If the QModelIndex is valid and the data role is DisplayRole,
        # i.e. text, then return a string of the cells position in the
        # table in the form (row,col)
        return "({0:02d},{1:02d})".format(index.row(), index.column())


class ButtonDelegate(QItemDelegate):
    """
    A delegate that places a fully functioning imageView in every
    cell of the table to which it's applied
    """

    def __init__(self, parent):
        # The parent is not an optional argument for the delegate as
        # we need to reference it in the paint method (see below)
        QItemDelegate.__init__(self, parent)
        self.v = pg.ImageView()
        self.data = np.random.normal(size=(128, 128))


    def paint(self, painter, option, index):
        # This method will be called every time a particular cell is
        # in view and that view is changed in some way. We ask the
        # delegates parent (in this case a table view) if the index
        # in question (the table cell) already has a widget associated
        # with it. If not, create one with the text for this index and
        # connect its clicked signal to a slot in the parent view so
        # we are notified when its used and can do something.
        if not self.parent().indexWidget(index):
            self.v.setImage(self.data)
            self.v.resize(50, 50)
            self.v.ui.graphicsView.render(painter)


class TableView(QTableView):
    """
    A simple table to demonstrate the button delegate.
    """

    def __init__(self, *args, **kwargs):
        QTableView.__init__(self, *args, **kwargs)

        # Set the delegate for column 0 of our table
        self.setItemDelegateForColumn(0, ButtonDelegate(self))

    def on_cellImageViewClicked(self):
        # This slot will be called when our button is clicked.
        # self.sender() returns a refence to the QPushButton created
        # by the delegate, not the delegate itself.
        print
        "Cell Button Clicked", self.sender().text()

