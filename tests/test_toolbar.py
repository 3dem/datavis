#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QAction,
                             QLineEdit, QTreeView, QVBoxLayout, QHBoxLayout,
                             QToolButton, QMenu, QSpacerItem, QSizePolicy,
                             QListView, QTableWidget)

from emqt5.views.toolbar import ToolBar

import qtawesome as qta

app = QApplication(sys.argv)

win = QMainWindow()
win.resize(800, 800)

centralWidget = QWidget(win)
l = QHBoxLayout(centralWidget)
win.setCentralWidget(centralWidget)

toolBar = ToolBar(centralWidget, orientation=Qt.Vertical)
toolBar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
l.addWidget(toolBar)
l.addWidget(QTreeView(centralWidget))

a = QAction(None)
a.setIcon(qta.icon('fa.table'))
a.setText("Action1")

widgetA = QWidget()
l = QVBoxLayout(widgetA)
l.addWidget(QLineEdit("Hello World", widgetA))
l.addWidget(QListView(widgetA))

l.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
toolBar.addAction(a, widgetA)
toolBar.addSeparator()

b = QAction(None)
b.setIcon(qta.icon('fa.th'))
b.setText("Action2")

toolBar.addAction(b)
toolBar.addSeparator()

toolButton = QToolButton(toolBar)
toolButton.setText("Configuration")
toolButton.setIcon(qta.icon('fa.gear'))

menu = QMenu(toolButton)
menu.addAction(qta.icon('fa.futbol-o'), 'Play ...')

toolButton.setMenu(menu)
toolButton.setPopupMode(QToolButton.MenuButtonPopup)

toolBar.addWidget(toolButton)
toolBar.addSeparator()

c = QAction(None)
c.setIcon(qta.icon('fa.gift'))
c.setText("Gift")

widgetC = QWidget()
l = QVBoxLayout(widgetC)
l.addWidget(QLineEdit("Gift action", widgetC))
l.addWidget(QTableWidget(widgetC))

toolBar.addAction(c, widgetC)

e = QAction(None)
e.setIcon(qta.icon('fa.flash'))
e.setText("Flash")

widgetE = QWidget()
l = QVBoxLayout(widgetE)
l.addWidget(QLineEdit("Flash action", widgetE))
l.addWidget(QTableWidget(widgetE))

toolBar.addAction(e, widgetE)

f = QAction(None)
f.setIcon(qta.icon('fa.bicycle'))
f.setText("Bicycle")
f.setCheckable(True)

toolBar.addAction(f, exclusive=True)

g = QAction(None)
g.setIcon(qta.icon('fa.bed'))
g.setText("Sleep")
g.setCheckable(True)

toolBar.addAction(g)

win.show()
win.setWindowTitle('Tool Example')

sys.exit(app.exec_())
