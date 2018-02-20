#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys

from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QFrame, QSizePolicy,
    QSplitter, QStyleFactory, QApplication, QTreeView, QFileSystemModel)
from PyQt5.QtCore import Qt, QDir



class Example(QWidget):
    
    def __init__(self):
        QWidget.__init__(self)
        
        self.initUI()
        
        
    def initUI(self):      

        hbox = QHBoxLayout(self)
        
        sizePolicy = QSizePolicy(QSizePolicy.MinimumExpanding, 
		                         QSizePolicy.MinimumExpanding)
		# Create Top-Left panel and put the TreeView inside
        topleft = QFrame(self)
        topleft.setFrameShape(QFrame.StyledPanel)
        #topleft.setSizePolicy(sizePolicy)
        topleft.resize(640, 380)
        #p = topleft.palette()
        #p.setColor(topleft.backgroundRole(), Qt.red)
        #topleft.setPalette(p)
        # topleft.setStyleSheet("background-color:red;");
        
        tree = QTreeView(topleft)
        self.model = QFileSystemModel()
        rootPath = '/Users/josem/'
        self.model.setRootPath(rootPath)
        tree.setModel(self.model)
        tree.setRootIndex(self.model.index(rootPath))
        tree.setSortingEnabled(True)
        tree.resize(640, 380)
        
        #tree.setSizePolicy(QSizePolicy.MinimumExpanding,
		#                   QSizePolicy.MinimumExpanding)
        #tree.setSizePolicy(sizePolicy)
		    
		# Disable items to expand on double click    
        tree.setExpandsOnDoubleClick(False)
        
        tree.doubleClicked.connect(self._onPathDoubleClick)
        
        # Set more size to first column
        tree.setColumnWidth(0, 300)
 
        topright = QFrame(self)
        topright.setFrameShape(QFrame.StyledPanel)

        bottom = QFrame(self)
        bottom.setFrameShape(QFrame.StyledPanel)

        splitter1 = QSplitter(Qt.Horizontal)
        splitter1.addWidget(topleft)
        splitter1.addWidget(topright)
        splitter1.setSizes([650, 200])
        splitter1.setStretchFactor(1, 1)
        # splitter1.resized.connect()

        splitter2 = QSplitter(Qt.Vertical)
        splitter2.addWidget(splitter1)
        splitter2.addWidget(bottom)
        splitter2.setSizes([390, 100])
		
        hbox.addWidget(splitter2)
        self.setLayout(hbox)
        
        self.setGeometry(900, 600, 900, 600)
        self.setWindowTitle('EM-Browser')
        self.show()
        
    def _onPathDoubleClick(self, signal):
        file_path = self.model.filePath(signal)
        print(file_path)
        
        
if __name__ == '__main__':
    
    app = QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())
