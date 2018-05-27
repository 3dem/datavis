#!/usr/bin/python
# -*- coding: utf-8 -*-

from PyQt5.QtCore import (pyqtSlot)
from PyQt5.QtWidgets import (QMainWindow, QStatusBar, QWidget, QVBoxLayout,
                             QLabel)

from emqt5.views.table_view import TableView
from emqt5.views.model import TableDataModel


class TableViewWindow(QMainWindow):
    """
    Main window
    """

    def __init__(self, parent=None, **kwargs):
        """ Constructor
        @param parent reference to the parent widget
        @model input TableDataModel
        """
        QMainWindow.__init__(self, parent)
        self.__setupUi__(**kwargs)
        models = kwargs['models']
        if models:
            delegates = kwargs.get('delegates')
            self.tableView.setModel(models, delegates)
        else:
            self._model = TableDataModel(parent=self.tableView,
                                         emTable=kwargs['tableData'],
                                         columnProperties=kwargs[
                                             'colProperties'])
            self.tableView.setModel(self._model)

    def __setupUi__(self, **kwargs):
        self.resize(816, 517)
        self.centralWidget = QWidget(self)
        self.setCentralWidget(self.centralWidget)
        self.verticalLayout = QVBoxLayout(self.centralWidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setSpacing(0)
        self.tableView = TableView(parent=self.centralWidget, **kwargs)
        self.tableView.sigCurrentTableItemChanged.connect(
            self.__tableItemChanged)
        self.tableView.sigCurrentGalleryItemChanged.connect(
            self.__galleryItemChanged)
        self.tableView.sigGalleryItemDoubleClicked.connect(
            self.__galleryItemDoubleClicked)
        self.tableView.sigCurrentElementItemChanged.connect(
            self.__elementItemChanged)
        self.verticalLayout.addWidget(self.tableView)

        self.statusBar = QStatusBar(self)
        self.setStatusBar(self.statusBar)
        self._labelInfo = QLabel(parent=self.statusBar,
                                 text="Some information about...")
        self.statusBar.addWidget(self._labelInfo)

    @pyqtSlot(int, int)
    def __galleryItemDoubleClicked(self, row, col):
        print("-------------------")
        print("galleryItemDoubleClicked")
        print("currentRow: ", row)
        print("currentCol: ", col)
        print("-------------------")

    @pyqtSlot(int, int)
    def __tableItemChanged(self, row, col):
        print("-------------------")
        print("tableItemChanged")
        print("currentRow: ", row)
        print("currentCol: ", col)
        print("-------------------")

    @pyqtSlot(int, int)
    def __galleryItemChanged(self, row, col):
        print("-------------------")
        print("__galleryItemChanged")
        print("currentRow: ", row)
        print("currentCol: ", col)
        print("-------------------")

    @pyqtSlot(int, int)
    def __elementItemChanged(self, row, col):
        print("-------------------")
        print("__elementItemChanged")
        print("currentRow: ", row)
        print("currentCol: ", col)
        print("-------------------")
