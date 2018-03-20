#!/usr/bin/python
# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import (QMainWindow, QStatusBar, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel)

from table_view import TableView
from model import TableDataModel


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
        self.__setupUi__()
        self.model = TableDataModel(kwargs['tableData'])
        self.tableView.setModel(self.model)

    def __setupUi__(self):
        self.resize(816, 517)
        self.centralWidget = QWidget(self)
        self.setCentralWidget(self.centralWidget)
        self.verticalLayout = QVBoxLayout(self.centralWidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setSpacing(0)
        self.tableView = TableView(self.centralWidget)
        self.verticalLayout.addWidget(self.tableView)

        self.statusBar = QStatusBar(self)
        self.setStatusBar(self.statusBar)
        self._labelInfo = QLabel(parent=self.statusBar,
                                 text="Some information about...")
        self.statusBar.addWidget(self._labelInfo)

