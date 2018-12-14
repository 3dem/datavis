#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QAction,
                             QLineEdit, QTreeView, QVBoxLayout, QHBoxLayout,
                             QToolButton, QMenu, QSpacerItem, QSizePolicy,
                             QListView, QTableWidget, QLabel, QPushButton)

from emqt5.views.toolbar import ToolBar

import qtawesome as qta

app = QApplication(sys.argv)

win = QMainWindow()
win.resize(800, 800)

centralWidget = QWidget()
l = QHBoxLayout(centralWidget)
win.setCentralWidget(centralWidget)

toolBar = ToolBar(centralWidget, orientation=Qt.Vertical)
toolBar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
l.addWidget(toolBar)
l.addWidget(QTreeView(centralWidget))

a = QAction(None)
a.setIcon(qta.icon('fa.sliders'))
a.setText("Exclusive 1")

widgetA = QWidget()
l = QVBoxLayout(widgetA)
l.addWidget(QLineEdit("Exclusive 1", widgetA))
w1 = QWidget()
l1 = QHBoxLayout(w1)
l1.setAlignment(Qt.AlignLeft)
l1.addWidget(QLabel("Histogram"))
#l1.addWidget(QPushButton(qta.icon('fa.area-chart'), "", w1))
label = QLabel()
label.setPixmap(qta.icon('fa.area-chart').pixmap(16, 16))
l1.addWidget(label)
l.addWidget(w1)

l.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
toolBar.addAction(a, widgetA, exclusive=True)

c = QAction(None)
c.setIcon(qta.icon('fa.gift'))
c.setText("Exclusive 2")

widgetC = QWidget()
l = QVBoxLayout(widgetC)
l.addWidget(QLineEdit("Exclusive 2", widgetC))
l.addWidget(QTableWidget(widgetC))

toolBar.addAction(c, widgetC)

e = QAction(None)
e.setIcon(qta.icon('fa.flash'))
e.setText("Exclusive 3")

widgetE = QWidget()
l = QVBoxLayout(widgetE)
l.addWidget(QLineEdit("Exclusive 3", widgetE))
l.addWidget(QTableWidget(widgetE))

toolBar.addAction(e, widgetE)
toolBar.addSeparator()

e = QAction(None)
e.setIcon(qta.icon('fa.optin-monster'))
e.setText("Not Exclusive")
widgetE = QWidget()
l = QVBoxLayout(widgetE)
l.addWidget(QLineEdit("Not Exclusive", widgetE))
l.addWidget(QTableWidget(widgetE))

toolBar.addAction(e, widgetE, False)

b = QAction(None)
b.setIcon(qta.icon('fa.info-circle'))
b.setText("File Info")

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
