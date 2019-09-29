#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys

import PyQt5.QtWidgets as qtw
import PyQt5.QtCore as qtc

import qtawesome as qta

import datavis as dv


app = qtw.QApplication(sys.argv)

win = qtw.QMainWindow()
win.resize(800, 800)

centralWidget = qtw.QWidget()
centralLayout = qtw.QHBoxLayout(centralWidget)
win.setCentralWidget(centralWidget)

toolBar = dv.widgets.ActionsToolBar(centralWidget, orientation=qtc.Qt.Vertical)

centralLayout.addWidget(toolBar)
centralLayout.addWidget(qtw.QTreeView(centralWidget))

a = qtw.QAction(None)
a.setIcon(qta.icon('fa.sliders'))
a.setText("Exclusive 1")

widgetA = qtw.QWidget()
layout = qtw.QVBoxLayout(widgetA)
layout.addWidget(qtw.QLineEdit("Exclusive 1", widgetA))
w1 = qtw.QWidget()
l1 = qtw.QHBoxLayout(w1)
l1.setAlignment(qtc.Qt.AlignLeft)
l1.addWidget(qtw.QLabel("Histogram"))
label = qtw.QLabel()
label.setPixmap(qta.icon('fa.area-chart').pixmap(16, 16))
l1.addWidget(label)
layout.addWidget(w1)

layout.addItem(qtw.QSpacerItem(20, 40, qtw.QSizePolicy.Minimum, qtw.QSizePolicy.Expanding))
toolBar.addAction(a, widgetA, exclusive=True)

c = qtw.QAction(None)
c.setIcon(qta.icon('fa.gift'))
c.setText("Exclusive 2")

widgetC = qtw.QWidget()
layout = qtw.QVBoxLayout(widgetC)
layout.addWidget(qtw.QLineEdit("Exclusive 2", widgetC))
layout.addWidget(qtw.QTableWidget(widgetC))

toolBar.addAction(c, widgetC)

e = qtw.QAction(None)
e.setIcon(qta.icon('fa.flash'))
e.setText("Exclusive 3")

widgetE = qtw.QWidget()
layout = qtw.QVBoxLayout(widgetE)
layout.addWidget(qtw.QLineEdit("Exclusive 3", widgetE))
layout.addWidget(qtw.QTableWidget(widgetE))

toolBar.addAction(e, widgetE)
toolBar.addSeparator()

e = qtw.QAction(None)
e.setIcon(qta.icon('fa.optin-monster'))
e.setText("Not Exclusive")
widgetE = qtw.QWidget()
layout = qtw.QVBoxLayout(widgetE)
layout.addWidget(qtw.QLineEdit("Not Exclusive", widgetE))
layout.addWidget(qtw.QTableWidget(widgetE))

toolBar.addAction(action=e, widget=widgetE, exclusive=False)

b = qtw.QAction(None)
b.setIcon(qta.icon('fa.info-circle'))
b.setText("File Info")

toolBar.addAction(b)
toolBar.addSeparator()

toolButton = qtw.QToolButton(toolBar)
toolButton.setText("Configuration")
toolButton.setIcon(qta.icon('fa.gear'))

menu = qtw.QMenu(toolButton)
menu.addAction(qta.icon('fa.futbol-o'), 'Play ...')

toolButton.setMenu(menu)
toolButton.setPopupMode(qtw.QToolButton.MenuButtonPopup)

toolBar.addWidget(toolButton)
toolBar.addSeparator()

f = qtw.QAction(None)
f.setIcon(qta.icon('fa.bicycle'))
f.setText("Bicycle")
f.setCheckable(True)

toolBar.addAction(f, exclusive=True)

g = qtw.QAction(None)
g.setIcon(qta.icon('fa.bed'))
g.setText("Sleep")
g.setCheckable(True)

toolBar.addAction(g)

win.show()
win.setWindowTitle('Tool Example')

sys.exit(app.exec_())
