#!/usr/bin/python
# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import Qt, QVariant
from PyQt5.QtWidgets import (QWidget, QStyledItemDelegate, QVBoxLayout,
                             QToolBar, QAction, QTableView, QSpinBox, QLabel)
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QIcon
import qtawesome as qta


class TableView(QWidget):
    """
    Widget used for display table contend
    """

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.__setupUi__()

    def setModel(self, model):
        """
        Set the table model
        :param model: the model
        """
        self.tableView.setModel(model)

    def __setupUi__(self):
        self.verticalLayout = QVBoxLayout(self)
        self.toolBar = QToolBar(self)
        self.verticalLayout.addWidget(self.toolBar)
        self.tableView = QTableView(self)
        self.verticalLayout.addWidget(self.tableView)

        def _createNewAction(parent, actionName, text="", faIconName=None,
                             checkable=False):
            a = QAction(parent)
            a.setObjectName(actionName)
            if faIconName:
                a.setIcon(qta.icon(faIconName))
            a.setCheckable(checkable)
            a.setText(text)
            return a

        self._actionFirst = _createNewAction(self.toolBar, 'actionFirst',
                                             'First', 'fa.step-backward')
        self._actionPrev = _createNewAction(self.toolBar, 'actionPrev',
                                            'Previous',
                                            'fa.backward')
        self._actionNext = _createNewAction(self.toolBar, 'actionNext', 'Next',
                                            'fa.forward')
        self._actionLast = _createNewAction(self.toolBar, 'actionLast', 'Last',
                                            'fa.step-forward')
        self.toolBar.addAction(self._actionFirst)
        self.toolBar.addAction(self._actionPrev)
        self.toolBar.addAction(self._actionNext)
        self.toolBar.addAction(self._actionLast)
        self.toolBar.addSeparator()
        self.labelSearch = QLabel(self.toolBar)
        self.labelSearch.setPixmap(qta.icon('fa.search').pixmap(32,
                                                                QIcon.Normal,
                                                                QIcon.On))
        self.toolBar.addWidget(self.labelSearch)
        self._spinBoxRowHeight = QSpinBox(self.toolBar)
        self._spinBoxRowHeight.setRange(10, 256)
        self.toolBar.addWidget(self._spinBoxRowHeight)
        self.toolBar.addSeparator()


class ImageItemDelegate(QStyledItemDelegate):
    """
    ImageItemDelegate class provides display and editing facilities for
    em image data items from a model.
    """
    def __init__(self, parent=None):
        QStyledItemDelegate.__init__(self, parent)

    def paint(self, painter, option, index):
        QStyledItemDelegate.paint(self, painter, option, index)

    def sizeHint(self, option, index):
        return QStyledItemDelegate.sizeHint(option, index)
