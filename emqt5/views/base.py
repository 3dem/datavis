#!/usr/bin/python
# -*- coding: utf-8 -*-

import os

from PyQt5.QtCore import Qt, pyqtSlot, pyqtSignal, QRectF, QVariant, QLocale
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QSpinBox, QLabel,
                             QStyledItemDelegate, QStyle, QHBoxLayout, QSlider,
                             QSizePolicy, QSpacerItem, QPushButton, QCheckBox,
                             QGraphicsPixmapItem, QRadioButton, QButtonGroup,
                             QComboBox, QItemDelegate, QColorDialog,
                             QTableWidget, QFormLayout, QTableWidgetItem,
                             QLineEdit, QGridLayout, QWidgetItem)
from PyQt5.QtGui import (QPixmap, QPalette, QPen, QColor, QIntValidator,
                         QDoubleValidator)

import qtawesome as qta
import pyqtgraph as pg

from emqt5.utils import ImageManager, ImageRef, parseImagePath


class EMImageItemDelegate(QStyledItemDelegate):
    """
    ImageItemDelegate class provides display and editing facilities for
    em image data items from a model.
    """
    def __init__(self, parent=None, **kwargs):
        """
        kwargs:
          - imageManager: the ImageManager for internal read/manage
                          image operations.
        """
        QStyledItemDelegate.__init__(self, parent)
        self._imageManager = kwargs.get('imageManager') or ImageManager(150)
        self._imageView = pg.ImageView(view=pg.ViewBox())
        self._imageView.getView().invertY(False)
        self._pixmapItem = None
        self._noImageItem = pg.TextItem("NO IMAGE")
        self._labelText = []
        self._imageView.getView().addItem(self._noImageItem)
        self._noImageItem.setVisible(False)
        self._imageRef = ImageRef()
        self._sBorder = 3  # selected state border (px)
        self._textHeight = 16
        self._focusPen = QPen(Qt.DotLine)
        self.__labelIndexes = []
        self._thumbSize = 64

    def paint(self, painter, option, index):
        """
        Reimplemented from QStyledItemDelegate
        """
        if index.isValid():
            x = option.rect.x()
            y = option.rect.y()
            w = option.rect.width()
            h = option.rect.height()
            rect = QRectF()
            if option.state & QStyle.State_Selected:
                if option.state & QStyle.State_HasFocus or \
                        option.state & QStyle.State_Active:
                    colorGroup = QPalette.Active
                else:
                    colorGroup = QPalette.Inactive
                painter.fillRect(option.rect,
                                 option.palette.color(colorGroup,
                                                      QPalette.Highlight))
            else:
                colorGroup = QPalette.Active
                painter.fillRect(option.rect,
                                 option.palette.color(colorGroup,
                                                      QPalette.HighlightedText))
            if self.__labelIndexes:
                h -= self._textHeight * len(self.__labelIndexes)
                self._setupText(index)
            else:
                self._labelText = []

            self._setupView(index, w, h)
            rect.setRect(self._sBorder, self._sBorder, w - 2 * self._sBorder,
                         h - 2 * self._sBorder)
            self._imageView.ui.graphicsView.scene().setSceneRect(rect)
            rect.setRect(x + self._sBorder, y + self._sBorder,
                         w - 2 * self._sBorder, h - 2 * self._sBorder)
            self._imageView.ui.graphicsView.scene().render(painter, rect)
            if option.state & QStyle.State_HasFocus:
                painter.save()
                self._focusPen.setColor(
                    option.palette.color(QPalette.Active,
                                         QPalette.Highlight))
                painter.setPen(self._focusPen)
                rect.setRect(x, y, w - 1, h - 1)
                if self._labelText:
                    rect.setHeight(
                        h + self._textHeight * len(self.__labelIndexes) - 1)
                painter.drawRect(rect)
                painter.restore()
            for i, text in enumerate(self._labelText):
                rect.setRect(x + self._sBorder, y + h + i * self._textHeight,
                             w - 2 * self._sBorder, self._textHeight)
                painter.drawText(rect, Qt.AlignLeft, text)

    def _setupText(self, index):
        """ Configure the label text """
        model = index.model()
        self._labelText = []
        if model is not None and self.__labelIndexes:
            for lIndex in self.__labelIndexes:
                value = model.data(
                    model.createIndex(index.row(), lIndex))
                if isinstance(value, QVariant):
                    value = value.value()
                self._labelText.append("%s=%s" %
                                       (model.getColumnConfig(lIndex).getName(),
                                        str(value)))

    def _setupView(self, index, width, height):
        """
        Configure the widget used as view to show the image
        """
        imgData = self._getThumb(index, self._thumbSize)

        if imgData is None:
            self._imageView.clear()
            v = self._imageView.getView()
            v.addItem(self._noImageItem)
            self._noImageItem.setVisible(True)
            v.autoRange(padding=0)
            return
        self._noImageItem.setVisible(False)
        size = index.data(Qt.SizeHintRole)
        if size is not None:
            (w, h) = (size.width(), size.height())

            v = self._imageView.getView()
            (cw, ch) = (v.width(), v.height())

            if not (w, h) == (cw, ch):
                v.setGeometry(0, 0, width, height)
                v.resizeEvent(None)

            if not isinstance(imgData, QPixmap):  # QPixmap or np.array
                if self._pixmapItem:
                    self._pixmapItem.setVisible(False)

                self._imageView.setImage(imgData)
            else:
                if not self._pixmapItem:
                    self._pixmapItem = QGraphicsPixmapItem(imgData)
                    v.addItem(self._pixmapItem)
                else:
                    self._pixmapItem.setPixmap(imgData)
                self._pixmapItem.setVisible(True)
            v.autoRange(padding=0)

    def _getThumb(self, index, height=64):
        """
        If the thumbnail stored in Image Cache
        :param index: QModelIndex
        :param height: height to scale the image
        """
        imgPath = index.data(Qt.UserRole)
        if imgPath is None:
            return None

        imgRef = parseImagePath(imgPath, self._imageRef,
                                os.path.split(index.model().getDataSource())[0])

        if imgRef is None:
            return None

        return self._imageManager.addImage(imgRef, (height, height))

    def setImageManager(self, imageManager):
        """
        Set the ImageCache object to be use for this ImageDelegate
        :param imageManager: ImageManager
        """
        self._imageManager = imageManager

    def getImageManager(self):
        """ Getter for ImageManager """
        return self._imageManager

    def setLabelIndexes(self, indexes):
        """
        Initialize the indexes of the columns that will be displayed as text
        below the images
        labels : (list)
        """
        self.__labelIndexes = indexes

    def getTextHeight(self):
        """ The height of text """
        return self._textHeight


class ColorItemDelegate(QStyledItemDelegate):
    """
    ColorItemDelegate class provides display and editing facilities for
    QColor selections.
    """
    def createEditor(self, parent, option, index):
        return QColorDialog(parent=parent)

    def setEditorData(self, editor, index):
        color = index.data(Qt.BackgroundRole)
        if color is not None:
            editor.setCurrentColor(color)

    def setModelData(self, editor, model, index):
        color = editor.currentColor()
        model.setData(index, color, Qt.BackgroundRole)


class ComboBoxStyleItemDelegate(QStyledItemDelegate):
    """
    ComboBoxStyleItemDelegate class provides display and editing facilities for
    text list selection.
    """
    def __init__(self, parent=None, values=None):
        QStyledItemDelegate.__init__(self, parent=parent)
        self._values = []
        self.setValues(values)

    def setValues(self, values):
        if isinstance(values, list):
            index = 0
            for text in values:
                self._values.append((text, index))
                index += 1

    def createEditor(self, parent, option, index):
        return QComboBox(parent=parent)

    def setEditorData(self, editor, index):
        index = index.data(Qt.UserRole)
        for text, value in self._values:
            editor.addItem(text, QVariant(value))
        if index is not None:
            editor.setCurrentIndex(index)

    def setModelData(self, editor, model, index):
        data = editor.currentData()
        model.setData(index, data, Qt.UserRole)
        text = editor.currentText()
        model.setData(index, text, Qt.DisplayRole)


class MarkerStyleItemDelegate(QStyledItemDelegate):
    """
    PenStyleItemDelegate class provides display and editing facilities for
    QPen style selection.
    """
    def createEditor(self, parent, option, index):
        return QComboBox(parent=parent)

    def setEditorData(self, editor, index):
        index = index.data(Qt.UserRole)
        editor.addItem('Solid', QVariant(Qt.SolidLine))
        editor.addItem('Dashed', QVariant(Qt.DashLine))
        editor.addItem('Dotted', QVariant(Qt.DotLine))
        if index is not None:
            editor.setCurrentIndex(index)

    def setModelData(self, editor, model, index):
        data = editor.currentData()
        model.setData(index, data, Qt.UserRole)
        text = editor.currentText()
        model.setData(index, text, Qt.DisplayRole)


class PageBar(QWidget):

    """
    This signal is emitted when the current page change
    emit(currentPage)
    """
    sigPageChanged = pyqtSignal(int)

    """ 
    This signal is emitted when the page configuration change.
    emit(page, firstPage, lastPage, step) 
    """
    sigPageConfigChanged = pyqtSignal(int, int, int, int)

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self._page = 0
        self._firstPage = 0
        self._lastPage = 0
        self._step = 1
        self.__setupUI()

    def __setupUI(self):
        self.setMinimumHeight(40)
        self.setMaximumHeight(40)
        self._mainLayout = QHBoxLayout(self)
        self._mainLayout.setContentsMargins(1, 1, 1, 1)
        self._mainLayout.addItem(QSpacerItem(40,
                                             20,
                                             QSizePolicy.Expanding,
                                             QSizePolicy.Minimum))
        self._pushButtonPrevPage = QPushButton(self)
        self._mainLayout.addWidget(self._pushButtonPrevPage)
        self._pushButtonPrevPage.setIcon(qta.icon('fa.angle-left'))
        self._pushButtonPrevPage.clicked.connect(self._onPrevPage)
        self._spinBoxCurrentPage = QSpinBox(self)
        self._spinBoxCurrentPage.setButtonSymbols(QSpinBox.NoButtons)
        self._spinBoxCurrentPage.editingFinished.connect(
            self._onSpinBoxCurrentPageEditingFinished)
        self._spinBoxCurrentPage.setMaximumSize(50, 25)
        self._spinBoxCurrentPage.setMinimumSize(50, 25)
        self._mainLayout.addWidget(self._spinBoxCurrentPage)
        self._labelPageCount = QLabel(self)
        self._mainLayout.addWidget(self._labelPageCount)
        self._pushButtonNextPage = QPushButton(self)
        self._pushButtonNextPage.setIcon(qta.icon('fa.angle-right'))
        self._pushButtonNextPage.clicked.connect(self._onNextPage)
        self._mainLayout.addWidget(self._pushButtonNextPage)
        self._mainLayout.addItem(QSpacerItem(40,
                                             20,
                                             QSizePolicy.Expanding,
                                             QSizePolicy.Minimum))

    def __showPageCount(self):
        """ Show page count """
        t = " of %d" % (self._lastPage - self._firstPage + 1)
        self._labelPageCount.setText(t)

    @pyqtSlot()
    def _onPrevPage(self):
        self.setPage(self._page - 1)

    @pyqtSlot()
    def _onNextPage(self):
        self.setPage(self._page + 1)

    @pyqtSlot()
    def _onSpinBoxCurrentPageEditingFinished(self):
        """
        This slot is invoked when the user edit the page number and press ENTER
        """
        self.setPage(self._spinBoxCurrentPage.value() - 1)

    def setPage(self, page):
        """
        Sets page as current page.
        Emit the sigPageChanged signal
        """
        if not page == self._page and page in range(self._firstPage,
                                                    self._lastPage + 1):
            self._page = page
            self._spinBoxCurrentPage.setValue(page + 1)
            self.sigPageChanged.emit(self._page)

    def getPage(self):
        """ Return the current page """
        return self._page

    def setup(self, page, firstPage, lastPage, step=1):
        """ Setups the paging params """
        if firstPage <= lastPage and page in range(firstPage, lastPage + 1):
            self._page = page
            self._firstPage = firstPage
            self._lastPage = lastPage
            self._step = step
            self._spinBoxCurrentPage.setRange(firstPage + 1, lastPage + 1)
            self._spinBoxCurrentPage.setSingleStep(step)
            self._spinBoxCurrentPage.setValue(page + 1)
            self.__showPageCount()
            self.sigPageConfigChanged.emit(self._page, self._firstPage,
                                           self._lastPage, self._step)


class AbstractView(QWidget):
    """ The base class for a view. AbstractView contains a paging bar """

    #  Selection Behavior
    SELECT_ROWS = 1  # Selecting single items.
    SELECT_COLUMNS = 2  # Selecting only rows.
    SELECT_ITEMS = 3  # Selecting only columns.

    #  Selection Mode
    SINGLE_SELECTION = 20  # See QAbstractItemView.SingleSelection
    EXTENDED_SELECTION = 21  # See QAbstractItemView.ExtendedSelection
    MULTI_SELECTION = 22  # See QAbstractItemView.MultiSelection
    NO_SELECTION = 23  # See QAbstractItemView.NoSelection

    """ 
        This signal is emitted when the current selection is changed
        emit(selected, deselected) 
        """
    sigSelectionChanged = pyqtSignal()

    def __init__(self, parent=None):
        QWidget.__init__(self, parent=parent)
        self._model = None
        self._selectionMode = self.NO_SELECTION
        self.__setupUI()

    def __setupUI(self):
        self._mainLayout = QVBoxLayout(self)
        self._mainLayout.setSpacing(0)
        self._mainLayout.setContentsMargins(1, 1, 1, 1)
        self._pageBar = PageBar(self)
        self._mainLayout.addWidget(self._pageBar)

    def __connectModelSignals(self, model):
        """ Connect all signals needed from the given model """
        if model:
            model.sigPageConfigChanged.connect(self.__onPageConfigChanged)
            model.sigPageChanged.connect(self.__onPageChanged)
            self._pageBar.sigPageChanged.connect(self._model.loadPage)

    def __disconnectModelSignals(self, model):
        """ Connect all signals needed from the given model """
        if model:
            model.sigPageConfigChanged.disconnect(self.__onPageConfigChanged)
            model.sigPageChanged.disconnect(self.__onPageChanged)
            self._pageBar.sigPageChanged.disconnect(self._model.loadPage)

    @pyqtSlot(int, int, int)
    def __onPageConfigChanged(self, page, pageCount, pageSize):
        """ Invoked when the model change his page configuration """
        self._pageBar.setup(page, 0, pageCount - 1, 1)

    @pyqtSlot(int)
    def __onPageChanged(self, page):
        """ Invoked when the model change his current page """
        self._pageBar.setPage(page)

    @pyqtSlot(set)
    def changeSelection(self, selection):
        """
        Invoked when the selection.
        This method must be reimplemented in inherited classes
        """
        pass

    def setModel(self, model):
        """ Sets the model for the this abstract view """
        self.__disconnectModelSignals(self._model)
        self._model = model
        self.__connectModelSignals(model)

        if model:
            self.__onPageConfigChanged(model.getPage(), model.getPageCount(),
                                       model.getPageSize())
        else:
            self.__onPageConfigChanged(0, 0, 0)

    def getModel(self):
        return self._model

    def showPageBar(self, visible):
        """ Show or hide the paging bar """
        self._pageBar.setVisible(visible)

    def getPageBar(self):
        """ Returns the page bar widget """
        return self._pageBar

    def getViewDims(self):
        """ Returns a tuple (rows, columns) with the data size """
        return 0, 0

    def setSelectionMode(self, selectionMode):
        """
        Indicates how the view responds to user selections:
        SINGLE_SELECTION, EXTENDED_SELECTION, MULTI_SELECTION.
        This method must be reimplemented in inherited classes
        """
        self._selectionMode = selectionMode

    def getSelectionMode(self):
        """ Returns the selection mode """
        return self._selectionMode

    def setSelectionBehavior(self, selectionBehavior):
        """
        This property holds which selection behavior the view uses.
        This property holds whether selections are done in terms of
        single items, rows or columns.

        Possible values:
                        SELECT_ITEMS, SELECT_ROWS, SELECT_COLUMNS
        This method must be reimplemented in inherited classes
        """
        pass

    def updateViewConfiguration(self):
        """
        It must be invoked when you need to update any change in the view
        according to modifications made to the model.
        If necessary, implement in inherited classes.
        AbstractView does not call this method.
        """
        pass


class OptionList(QWidget):
    """

    """
    def __init__(self, parent=None, display='default', tooltip="",
                 exclusive=True, buttonsClass=QRadioButton, options=None,
                 defaultOption=0):
        """
        Constructor
        parent:          The QObject parent for this widget
        display (str):   The display type for options
                         ('vlist': vertical, 'hlist': horizontal,
                         'combo': show options in combobox,
                         'slider': show options in slider)
        exclusive(bool): If true, the radio buttons will be exclusive
        buttonsClass:    The buttons class (QRadioButton or QCheckBox)
        tooltip(str):    A tooltip for this widget
        """
        QWidget.__init__(self, parent=parent)
        self.__buttonGroup = QButtonGroup(self)
        self.__buttonGroup.setExclusive(exclusive)
        lClass = QVBoxLayout if display == 'vlist' else QHBoxLayout
        self.__mainLayout = lClass(self)
        self.__mainLayout.setContentsMargins(0, 0, 0, 0)
        self.__singleWidget = None  # may be combobox or slider
        if display == 'combo' or display == 'default':
            self.__singleWidget = QComboBox(self)
            self.__buttonClass = None
        elif display == 'slider':
            self.__singleWidget = QSlider(Qt.Horizontal, self)
            if isinstance(options, tuple):
                self.__singleWidget.setRange(options[0], options[1])
            elif isinstance(options, list):
                self.__singleWidget.setRange(0, len(options) - 1)
        else:
            self.__buttonClass = \
                buttonsClass if buttonsClass == QRadioButton \
                                or buttonsClass == QCheckBox else None
            self.__singleWidget = QWidget(self)
            self.__groupBoxLayout = lClass(self.__singleWidget)
            self.__groupBoxLayout.setContentsMargins(3, 3, 3, 3)

        if not isinstance(self.__singleWidget, QSlider):
            index = 0
            for option in options:
                self.addOption(option, index)
                index += 1

        if self.__singleWidget is not None:
            self.__singleWidget.setToolTip(tooltip)
            self.__mainLayout.addWidget(self.__singleWidget)
            self.setSelectedOption(defaultOption)

    def addOption(self, name, optionId, checked=False):
        """ Add an option """

        if self.__buttonClass is not None \
                and isinstance(self.__singleWidget, QWidget):
            button = self.__buttonClass(self)
            button.setText(name)
            self.__buttonGroup.addButton(button, optionId)
            button.setChecked(checked)
            self.__groupBoxLayout.addWidget(button)
        elif isinstance(self.__singleWidget, QComboBox):
            self.__singleWidget.addItem(name, optionId)

    def getSelectedOptions(self):
        """ Return the selected options """
        if isinstance(self.__singleWidget, QComboBox):
            return self.__singleWidget.currentData()
        elif isinstance(self.__singleWidget, QWidget):
            if self.__buttonGroup.exclusive():
                return self.__buttonGroup.checkedId()
            else:
                options = []
                for button in self.__buttonGroup.buttons():
                    if button.isChecked():
                        options.append(self.__buttonGroup.id(button))
                return options
        elif isinstance(self.__singleWidget, QSlider):
            return self.__singleWidget.value()
        return None

    def setSelectedOption(self, optionId):
        """ Set the given option as selected """
        if isinstance(self.__singleWidget, QWidget):
            button = self.__buttonGroup.button(optionId)
            if button is not None:
                button.setChecked(True)
        elif isinstance(self.__singleWidget, QComboBox) \
                and optionId in range(self.__singleWidget.count()):
            self.__comboBox.setCurrentIndex(optionId)
        elif isinstance(self.__singleWidget, QSlider):
            self.__singleWidget.setValue(optionId)


class ColumnPropertyItemDelegate(QItemDelegate):
    """ Class used to provide custom display features for column properties """
    def __init__(self, parent=None, checkedIcon=None, uncheckedIcon=None,
                 partiallyCheckedIcon=None):
        QItemDelegate.__init__(self, parent=parent)
        self.__checkedIcon = checkedIcon
        self.__uncheckedIcon = uncheckedIcon
        self.__partiallyCheckedIcon = partiallyCheckedIcon

    def drawCheck(self, painter, option, rect, state):
        if rect is not None and rect.isValid():
            icon = None

            if state == Qt.Checked and self.__checkedIcon is not None:
                icon = self.__checkedIcon
            elif state == Qt.Unchecked and self.__uncheckedIcon is not None:
                icon = self.__uncheckedIcon
            elif state == Qt.PartiallyChecked and \
                    self.__partiallyCheckedIcon is not None:
                icon = self.__partiallyCheckedIcon

            if icon is not None:
                painter.drawImage(rect.x(), rect.y(), icon)
            else:
                QItemDelegate.drawCheck(self, painter, option, rect, state)


class PlotConfigWidget(QWidget):
    """ The plot configuration widget """

    """ 
    This signal is emitted when the current configuration contains errors
    emit(str:error)     
    """
    # TODO[hv] emit error code, not str message
    sigError = pyqtSignal(str)

    def __init__(self, parent=None, **kwargs):
        """
        kwargs:
          params (str list): The rows for the configuration table
          colors (str list): The initial colors for params ('#FF34AA')
          styles (str list): The styles for user selection
                             ['solid', 'dashed', 'dotted', ...]
          markers (str list): The markers for user selection
                             ['none', '.', ',', 'o', ...]
          plot-types (str list): The plot types
                                 ['Plot', 'Histogram', 'Scatter']
        """
        QWidget.__init__(self, parent=parent)
        self.__params = kwargs.get('params', [])
        self.__markers = kwargs.get('markers', ["none", ".", ",", "o", "v", "^",
                                                "<", ">", "1", "2", "3", "4",
                                                "s", "p", "h", "H", "+", "x",
                                                "D", "d", "|", "_"])
        self.__styles = kwargs.get('styles', ['solid', 'dashed', 'dotted'])
        self.__colors = kwargs.get('colors', [Qt.blue, Qt.green, Qt.red,
                                              Qt.black, Qt.darkYellow,
                                              Qt.yellow, Qt.magenta, Qt.cyan])
        self.__plotTypes = kwargs.get('plot-types',
                                      ['Plot', 'Histogram', 'Scatter'])
        self.__markerDelegate = \
            ComboBoxStyleItemDelegate(parent=self,
                                      values=self.__markers)
        self.__lineStyleDelegate = \
            ComboBoxStyleItemDelegate(
                parent=self, values=[stl.capitalize() for stl in self.__styles])
        self.__colorDelegate = ColorItemDelegate(parent=self)
        checkedIcon = qta.icon('fa5s.file-signature')
        unCheckedIcon = qta.icon('fa5s.file-signature', color='#d4d4d4')
        self.__checkDelegate = \
            ColumnPropertyItemDelegate(self, checkedIcon.pixmap(16).toImage(),
                                       unCheckedIcon.pixmap(16).toImage())
        self.__setupUi()
        self.__initPlotConfWidgets()

    def __setupUi(self):
        vLayout = QVBoxLayout(self)
        formLayout = QFormLayout()
        formLayout.setLabelAlignment(
            Qt.AlignRight | Qt.AlignTrailing | Qt.AlignVCenter)
        formLayout.setWidget(0, QFormLayout.LabelRole,
                             QLabel(text='Title: ', parent=self))
        self._lineEditPlotTitle = QLineEdit(parent=self)
        self._lineEditPlotTitle.setSizePolicy(QSizePolicy.Expanding,
                                              QSizePolicy.Preferred)
        formLayout.setWidget(0, QFormLayout.FieldRole, self._lineEditPlotTitle)
        formLayout.setWidget(1, QFormLayout.LabelRole,
                             QLabel(text='X label: ', parent=self))
        self._lineEditXlabel = QLineEdit(parent=self)
        formLayout.setWidget(1, QFormLayout.FieldRole,
                             self._lineEditXlabel)
        formLayout.setWidget(2, QFormLayout.LabelRole,
                             QLabel(text='Y label: ', parent=self))
        self._lineEditYlabel = QLineEdit(parent=self)
        formLayout.setWidget(2, QFormLayout.FieldRole, self._lineEditYlabel)
        formLayout.setWidget(3, QFormLayout.LabelRole,
                             QLabel(text='Type: ', parent=self))
        self._comboBoxPlotType = QComboBox(parent=self)
        for plotType in self.__plotTypes:
            self._comboBoxPlotType.addItem(plotType)

        self._comboBoxPlotType.currentIndexChanged.connect(
            self.__onCurrentPlotTypeChanged)

        formLayout.setWidget(3, QFormLayout.FieldRole, self._comboBoxPlotType)
        self._labelBins = QLabel(parent=self)
        self._labelBins.setText('Bins')
        self._lineEditBins = QLineEdit(self)
        self._lineEditBins.setText('50')
        formLayout.setWidget(4, QFormLayout.LabelRole, self._labelBins)
        formLayout.setWidget(4, QFormLayout.FieldRole, self._lineEditBins)
        self._labelBins.setVisible(False)
        self._lineEditBins.setVisible(False)
        self._lineEditBins.setFixedWidth(80)
        self._lineEditBins.setValidator(QIntValidator())
        formLayout.setWidget(5, QFormLayout.LabelRole, QLabel(text='X Axis: ',
                                                              parent=self))
        self._comboBoxXaxis = QComboBox(parent=self)
        self._comboBoxXaxis.currentIndexChanged.connect(
            self.__onCurrentXaxisChanged)
        formLayout.setWidget(5, QFormLayout.FieldRole, self._comboBoxXaxis)
        vLayout.addLayout(formLayout)
        label = QLabel(parent=self,
                       text="<strong>Plot columns:</strong>")
        label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        vLayout.addWidget(label, 0, Qt.AlignLeft)
        self._tablePlotConf = QTableWidget(self)
        self._tablePlotConf.setObjectName("tablePlotConf")
        self._tablePlotConf.setSelectionMode(QTableWidget.NoSelection)
        self._tablePlotConf.setSelectionBehavior(QTableWidget.SelectRows)
        self._tablePlotConf.setFocusPolicy(Qt.NoFocus)
        self._tablePlotConf.setMinimumSize(self._tablePlotConf.sizeHint())
        self._tablePlotConf.setSizePolicy(QSizePolicy.Expanding,
                                          QSizePolicy.Expanding)
        self._tablePlotConf.setColumnCount(5)
        self._tablePlotConf.setHorizontalHeaderLabels(['Label', 'Plot',
                                                       'Color', 'Line Style',
                                                       'Marker'])
        self._tablePlotConf.setItemDelegateForColumn(1, self.__checkDelegate)
        self._tablePlotConf.setItemDelegateForColumn(
            2, ColorItemDelegate(parent=self._tablePlotConf))
        self._tablePlotConf.setItemDelegateForColumn(
            3, self.__lineStyleDelegate)
        self._tablePlotConf.setItemDelegateForColumn(
            4, self.__markerDelegate)
        self._tablePlotConf.verticalHeader().setVisible(False)
        self._tablePlotConf.setEditTriggers(QTableWidget.AllEditTriggers)

        vLayout.addWidget(self._tablePlotConf)

    def __initPlotConfWidgets(self):
        """ Initialize the plot configurations widgets """
        self._comboBoxXaxis.clear()
        self._comboBoxXaxis.addItem(" ")
        self._tablePlotConf.clearContents()
        row = 0
        self._tablePlotConf.setRowCount(len(self.__params))
        nColors = len(self.__colors)

        for i, colName in enumerate(self.__params):
            self._comboBoxXaxis.addItem(colName)
            item = QTableWidgetItem(colName)
            item.setFlags(Qt.ItemIsEnabled)
            itemPlot = QTableWidgetItem("")  # for plot option
            itemPlot.setCheckState(Qt.Unchecked)
            itemColor = QTableWidgetItem("")  # for color option
            itemColor.setData(Qt.BackgroundRole,
                              QColor(self.__colors[i % nColors]))
            itemLineStye = QTableWidgetItem("")  # for line style option
            itemLineStye.setData(Qt.DisplayRole,
                                 self.__styles[0].capitalize())
            itemLineStye.setData(Qt.UserRole, 0)
            itemMarker = QTableWidgetItem("")  # for marker option
            itemMarker.setData(Qt.DisplayRole, self.__markers[0])
            itemMarker.setData(Qt.UserRole, 0)
            self._tablePlotConf.setItem(row, 0, item)
            self._tablePlotConf.setItem(row, 1, itemPlot)
            self._tablePlotConf.setItem(row, 2, itemColor)
            self._tablePlotConf.setItem(row, 3, itemLineStye)
            self._tablePlotConf.setItem(row, 4, itemMarker)
            row += 1

        self._tablePlotConf.resizeColumnsToContents()
        self._tablePlotConf.horizontalHeader().setStretchLastSection(True)

    def __getSelectedPlotProperties(self):
        """
        Return a dict with all plot properties for each row (param).
        Example:
             {
                'param1': {
                           'color': '#4565FF',
                           'line-style': 'dashed',
                           'marker':'o'
                          }
                ...
                param-n
             }
        """
        ret = dict()
        for i in range(self._tablePlotConf.rowCount()):
            if self._tablePlotConf.item(i, 1).checkState() == Qt.Checked:
                p = dict()
                p['color'] = self._tablePlotConf.item(i, 2).data(
                    Qt.BackgroundRole).name()
                p['line-style'] = self._tablePlotConf.item(i, 3).text().lower()
                p['marker'] = self._tablePlotConf.item(i, 4).text()
                ret[self.__params[i]] = p

        return ret

    @pyqtSlot()
    def __onCurrentPlotTypeChanged(self):
        """ Invoked when the current plot type is changed """
        visible = self._comboBoxPlotType.currentText() == 'Histogram'
        self._labelBins.setVisible(visible)
        self._lineEditBins.setVisible(visible)

    @pyqtSlot()
    def __onCurrentXaxisChanged(self):
        """
        Invoked when the current x axis is changed configuring the plot
        operations
        """
        self._lineEditXlabel.setText(self._comboBoxXaxis.currentText())

    def setParams(self, params=[], **kwargs):
        """ Initialize the configuration parameters """
        self.__params = params
        self.__markers = kwargs.get('markers', self.__markers)
        self.__styles = kwargs.get('styles', self.__styles)
        self.__colors = kwargs.get('colors', self.__colors)
        self.__plotTypes = kwargs.get('plot-types', self.__plotTypes)
        self.__initPlotConfWidgets()

    def setTitleText(self, text):
        """ Sets the title label text """
        self._titleLabel.setText(text)

    def getConfiguration(self):
        """
        Return a dict with the configuration parameters or None
        for invalid configuration.
        emit sigError
        dict: {
        'params': {
                    'param1': {
                               'color': '#4565FF',
                               'line-style': 'dashed',
                               'marker':'o'
                              }
                    ...
                    param-n
                  }
        'config':{
                  'title': 'Plot title',
                  'x-label': 'xlabel',
                  'y-label': 'ylabel',
                  'plot-type': 'Plot' or 'Histogram' or 'Scatter',
                  'x-axis': 'x-axis',
                  'bins': int (if type=Histogram)
                 }
        }
        """
        plotProp = self.__getSelectedPlotProperties()
        if len(plotProp) > 0:
            config = dict()
            plotType = self._comboBoxPlotType.currentText()
            config['plot-type'] = plotType

            xLabel = self._lineEditXlabel.text().strip()
            yLabel = self._lineEditYlabel.text().strip()
            title = self._lineEditPlotTitle.text().strip()
            xAxis = self._comboBoxXaxis.currentText().strip()

            if len(xAxis):
                config['x-axis'] = xAxis
            if len(title):
                config['title'] = title
            if len(xLabel):
                config['x-label'] = xLabel
            if len(yLabel):
                config['y-label'] = yLabel
            if plotType == 'Histogram':
                bins = self._lineEditBins.text().strip()
                if len(bins):
                    config['bins'] = int(self._lineEditBins.text())
                else:
                    self.sigError.emit('Invalid bins value')
                    return None
            ret = dict()
            ret['params'] = plotProp
            ret['config'] = config
            return ret
        else:
            self.sigError.emit('No columns selected for plotting')
            return None

    def sizeHint(self):
        """ Reimplemented from QWidget """
        s = QWidget.sizeHint(self)
        w = 4 * self.layout().contentsMargins().left()
        for column in range(self._tablePlotConf.columnCount()):
            w += self._tablePlotConf.columnWidth(column)
        s.setWidth(w)
        return s


class DynamicWidget(QWidget):
    """ The base class for dynamic widgets """
    def __init__(self, parent=None, typeParams=None):
        QWidget.__init__(self, parent=parent)
        self.setLayout(QGridLayout())
        self.__paramsWidgets = dict()
        self.__typeParams = typeParams

    def __collectData(self, item):
        if isinstance(item, QVBoxLayout) or isinstance(item, QHBoxLayout) or \
                isinstance(item, QGridLayout):
            for index in range(item.count()):
                self.__collectData(item.itemAt(index))
        elif isinstance(item, QWidgetItem):
            widget = item.widget()
            param = self.__paramsWidgets.get(widget.objectName())
            if param is not None:
                t = self.__typeParams.get(param.get('type')).get('type')
                if isinstance(widget, QLineEdit):
                    if t is not None:
                        text = widget.text()
                        if text in ["", ".", "+", "-"]:
                            text = 0
                        param['value'] = t(text)
                elif isinstance(widget, QCheckBox) and t == bool:
                    # other case may be checkbox for enum: On,Off
                    param['value'] = widget.isChecked()
                elif isinstance(widget, OptionList):
                    param['value'] = widget.getSelectedOptions()

    def setParamWidget(self, name, param):
        self.__paramsWidgets[name] = param

    def getParams(self):
        """ """
        self.__collectData(self.layout())
        return self.__paramsWidgets


class DynamicWidgetsFactory:
    """ A dynamic widgets factory """

    def __init__(self):
        self.__typeParams = {
            'float': {
                'type': float,
                'display': {
                    'default': QLineEdit
                },
                'validator': QDoubleValidator
            },
            'int': {
                'type': int,
                'display': {
                    'default': QLineEdit
                },
                'validator': QIntValidator
            },
            'string': {
                'type': str,
                'display': {
                    'default': QLineEdit
                }
            },
            'bool': {
                'type': bool,
                'display': {
                    'default': QCheckBox
                }
            },
            'enum': {
                'display': {
                    'default': OptionList,
                    'vlist': OptionList,
                    'hlist': OptionList,
                    'slider': QSlider,
                    'combo': OptionList
                }
            }
        }

    def createWidget(self, specification):
        """ Creates the widget for de given specification """
        widget = DynamicWidget(typeParams=self.__typeParams)
        self.__addVParamsWidgets(widget, specification)
        return widget

    def __addVParamsWidgets(self, mainWidget, params):
        """ Add the widgets created from params to the given QGridLayout """
        layout = mainWidget.layout()
        row = layout.rowCount()
        for param in params:
            if isinstance(param, list):
                col = 0
                row, col = self.__addHParamsWidgets(mainWidget, layout, param,
                                                    row, col)
                row += 1
            else:
                col = 0
                widget = self.__createParamWidget(mainWidget, param)
                if widget is not None:
                    label = param.get('label')
                    if label is not None:
                        lab = QLabel(mainWidget)
                        lab.setText(label)
                        lab.setToolTip(param.get('help', ""))
                        layout.addWidget(lab, row, col, Qt.AlignRight)
                        col += 1
                    layout.addWidget(widget, row, col, 1, -1)
                    row += 1

    def __addHParamsWidgets(self, mainWidget, layout, params, row, col):
        """
        Add the params to the given layout in the row "row" from
        the column "col"
        """
        for param in params:
            if isinstance(param, list):
                row, col = self.__addHParamsWidgets(layout, param, row, col)
            elif isinstance(param, dict):
                widget = self.__createParamWidget(mainWidget, param)
                if widget is not None:
                    label = param.get('label')
                    if label is not None:
                        lab = QLabel(mainWidget)
                        lab.setText(label)
                        lab.setToolTip(param.get('help', ""))
                        layout.addWidget(lab, row, col, Qt.AlignRight)
                        col += 1
                    layout.addWidget(widget, row, col, 1, 1)
                    col += 1
        return row, col

    def __createParamWidget(self, mainWidget, param):
        """
        Creates the corresponding widget from the given param.
        """
        if not isinstance(param, dict):
            return None

        widgetName = param.get('name')
        if widgetName is None:
            return None  # rise exception??

        valueType = param.get('type')
        if valueType is None:
            return None  # rise exception??

        paramDef = self.__typeParams.get(valueType)

        if paramDef is None:
            return None  # rise exception??

        display = paramDef.get('display')
        widgetClass = display.get(param.get('display', 'default'))

        if widgetClass is None:
            return None  # rise exception??

        if valueType == 'enum':
            widget = OptionList(parent=mainWidget,
                                display=param.get('display', 'default'),
                                tooltip=param.get('help', ""), exclusive=True,
                                buttonsClass=QRadioButton,
                                options=param.get('choices'),
                                defaultOption=param.get('value', 0))
        else:
            widget = widgetClass(mainWidget)
            widget.setToolTip(param.get('help', ''))
            self.__setParamValue(widget, param.get('value'))

        widget.setObjectName(widgetName)

        mainWidget.setParamWidget(widgetName, param)

        if widgetClass == QLineEdit:
            # widget.setClearButtonEnabled(True)
            validatorClass = paramDef.get('validator')
            if validatorClass is not None:
                val = validatorClass()
                if validatorClass == QDoubleValidator:
                    loc = QLocale.c()
                    loc.setNumberOptions(QLocale.RejectGroupSeparator)
                    val.setLocale(loc)
                widget.setValidator(val)
            if valueType == 'float' or valueType == 'int':
                widget.setFixedWidth(80)

        return widget

    def __setParamValue(self, widget, value):
        """ Set the widget value"""
        if isinstance(widget, QLineEdit):
            widget.setText(str(value))
        elif isinstance(widget, QCheckBox) and isinstance(value, bool):
            widget.setChecked(value)