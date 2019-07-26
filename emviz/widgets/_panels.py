
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
                             QSplitter)
from PyQt5.QtCore import Qt


class ViewPanel(QWidget):
    """ The ViewPanel contains widgets organized according to the specific
    layout."""

    """ Lines up widgets horizontally """
    HORIZONTAL = 0
    """ Lines up widgets vertically """
    VERTICAL = 1
    """ Lays out widgets in a grid"""
    GRID = 2
    """ Lays out widgets in a horizontal splitter """
    HSPLITTER = 3
    """ Lays out widgets in a vertical splitter """
    VSPLITTER = 4

    def __init__(self, parent, layoutType=HORIZONTAL):
        QWidget.__init__(self, parent=parent)
        self._mainLayout = self.__createLayout(layoutType)
        if isinstance(self._mainLayout, QSplitter):
            layout = QVBoxLayout(self)
            layout.addWidget(self._mainLayout)

        self._widgets = dict()
        self._layoutType = layoutType

    def __createLayout(self, type):
        """
         Creates a layout according to the given layout type
        :param type:  (int) The layout type: HORIZONTAL, VERTICAL, HSPLITTER,
                      VSPLITTER or GRID
        :return: The layout
        """
        if type not in [ViewPanel.HORIZONTAL, ViewPanel.VERTICAL,
                        ViewPanel.GRID, ViewPanel.HSPLITTER,
                        ViewPanel.VSPLITTER]:
            raise Exception("Invalid layout type: %d. Use HORIZONTAL, "
                            "VERTICAL, HSPLITTER, VSPLITTER or GRID"
                            % type)
        if type == ViewPanel.HORIZONTAL:
            layout = QHBoxLayout(self)
        elif type == ViewPanel.VERTICAL:
            layout = QVBoxLayout(self)
        elif type == ViewPanel.GRID:
            layout = QGridLayout(self)
        else:
            h = Qt.Horizontal if type == ViewPanel.HSPLITTER else Qt.Vertical
            layout = QSplitter(orientation=h, parent=self)
        return layout

    def addWidget(self, widget, key, alignment=Qt.Alignment(), row=-1, col=-1):
        """
        Add a widget to the internal layout
        :param widget:     (QWidget) The widget
        :param key:        Unique key for the widget
        :param alignment:  (Qt.Alignment) The alignment for the widget.
                           Default value is Qt.AlignCenter
        :param row:    (int) Add the widget at row 'row' if layout is GRID
        :param col:    (int) Add the widget at column 'col' if layout is GRID
        """
        if self._layoutType in [ViewPanel.HORIZONTAL, ViewPanel.VERTICAL]:
            self._mainLayout.addWidget(widget, alignment=alignment)
        elif self._layoutType in [ViewPanel.VSPLITTER, ViewPanel.HSPLITTER]:
            self._mainLayout.addWidget(widget)
        elif row == -1 or col == -1:  # GRID
            raise Exception("Invalid (row=%d, col=%d) for the GridLayout"
                            % (row, col))
        else:  # GRID
            self._mainLayout.addWidget(widget, row, col, alignment=alignment)

        self._widgets[key] = widget

    def getWidget(self, key):
        """ Return the widget inserted with the given key """
        return self._widgets[key]
