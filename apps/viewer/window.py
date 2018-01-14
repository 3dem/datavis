# -*- coding: utf-8 -*-

"""
Module implementing MainWindow.
"""

from PyQt5.QtCore import pyqtSlot, QDir, QPoint
from PyQt5.QtWidgets import QMainWindow, QMessageBox,  QApplication, QFileDialog,  QSlider
from PyQt5.QtGui import QImage, QColor

from emqt5.widgets.image import ImageBox
from emqt5.widgets.image.shapes import Rectangle

from Ui_MainWindow import Ui_MainWindow


class MainWindow(QMainWindow, Ui_MainWindow):   
    """
    Class documentation goes here.
    """
    def __init__(self, parent=None, **kwargs):
        """
        Constructor
        
        @param parent reference to the parent widget
        @type QWidget
        """
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)  
        layout = (self.verticalLayout_4.layout())
        self.imageBox = ImageBox()
        layout.addWidget(self.imageBox)        
        self.scaleF = 0.25
        self.rotationStep = 10
        self.zoom = 0
        #self.tabWidget.setEnabled(False)
        imageFile = kwargs.get('imageFile', None)
        if imageFile:
            print("Loading filename:", imageFile)
            self.openImage(imageFile)
            self.imageBox.centerImage()
    
    @pyqtSlot()
    def on_actionExit_triggered(self):
        """
        Slot documentation goes here.
        """
        import sys
        sys.exit()   
        
    @pyqtSlot()
    def on_actionRigth_Rotation_triggered(self):
        """
        Slot documentation goes here.
        """
        self.changeFitToSizeCheckBoxEnable(True)
        if self.imageBox.isHorizontalFlip or self.imageBox.isVerticalFlip:
            self.imageBox.rotate(self.imageBox.rotationAngle() - self.rotationStep);   
        else:
             self.imageBox.rotate(self.imageBox.rotationAngle()+self.rotationStep);
        
    @pyqtSlot()
    def on_actionLeft_Rotation_triggered(self):
        """
        Slot documentation goes here.
        """
        self.changeFitToSizeCheckBoxEnable(True)
        if self.imageBox.isHorizontalFlip or self.imageBox.isVerticalFlip:
            self.imageBox.rotate(self.imageBox.rotationAngle()-self.rotationStep);   
        else:
             self.imageBox.rotate(self.imageBox.rotationAngle()+self.rotationStep);
    
    @pyqtSlot()
    def openImage(self,  fileName):
        if fileName==None:            
            fileName, _ = QFileDialog.getOpenFileName(self, "Open File",
                QDir.currentPath())
        if fileName:
            image = QImage(fileName)
            if image.isNull():
                QMessageBox.information(self, "Image Viewer",
                        "Cannot load %s." % fileName)
                return
            self.imageBox.setImage(image)
            self.imageBox.update()
            self.imageBox.fitToWindow()
            self.tabWidget.setEnabled(True)
    
    @pyqtSlot()
    def on_actionOpen_triggered(self):
        """
        Slot documentation goes here.
        """
        self.openImage(None)
    
    @pyqtSlot()
    def on_actionFlip_Vertical_triggered(self):
        """
        Slot documentation goes here.
        """
        self.changeFitToSizeCheckBoxEnable(True)
        self.imageBox.verticalFlip()
       
       
        
        
    @pyqtSlot()
    def on_actionFlip_Horizontal_triggered(self):
        """
        Slot documentation goes here.
        """
        self.changeFitToSizeCheckBoxEnable(True)
        self.imageBox.horizontalFlip()
        
    @pyqtSlot()
    def on_actionZoom_In_triggered(self):
        """
        Slot documentation goes here.
        """      
        self.changeFitToSizeCheckBoxEnable(True)
        self.imageBox.changeZoom(self.imageBox.getScale()+self.scaleF)
    
    @pyqtSlot()
    def on_actionZoom_Out_triggered(self):
        """
        Slot documentation goes here.
        """
        self.changeFitToSizeCheckBoxEnable(True)
        self.imageBox.changeZoom(self.imageBox.getScale()-self.scaleF)
    
    @pyqtSlot()
    def on_actionMove_triggered(self):
        """
        Slot documentation goes here.
        """
        QMessageBox.information(self, "Image Viewer","Move")
    
    @pyqtSlot()
    def on_actionFit_to_Size_triggered(self):
        """
        Slot documentation goes here.
        """
        self.changeFitToSizeCheckBoxEnable(True)
        self.imageBox.fitToWindow()
    
    @pyqtSlot(int)
    def on_horizontalSlider_valueChanged(self, value):
        """
        Slot documentation goes here.
        
        @param value DESCRIPTION
        @type int
        """      
        self.imageBox.rotate(value);
        self.changeFitToSizeCheckBoxEnable(True) 
        #self.imageBox.rotate(value);
        
            
    @pyqtSlot(int)
    def on_horizontalSlider_2_valueChanged(self, value):
        """
        Slot documentation goes here.
        
        @param value DESCRIPTION
        @type int
        """
        sign = -1 if (self.horizontalSlider_2.value() <= self.zoom) else 1
        self.imageBox.changeZoom(self.imageBox.getScale()+(sign*self.scaleF))
        self.zoom = self.horizontalSlider_2.value()
        self.changeFitToSizeCheckBoxEnable(True) 
    
    @pyqtSlot()
    def on_VerticalFlipsButton_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        self.imageBox.verticalFlip()
        self.changeFitToSizeCheckBoxEnable(True) 
    
    @pyqtSlot()
    def on_HorizontalFlipsButton_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        self.imageBox.horizontalFlip()
        self.changeFitToSizeCheckBoxEnable(True) 
        
    def changeFitToSizeCheckBoxEnable(self,  status):
          self.FitToSizeCheckBox.setChecked(not status) 
          self.FitToSizeCheckBox.setEnabled(status)   
      
    @pyqtSlot(int)
    def on_FitToSizeCheckBox_stateChanged(self, p0):
        """
        Slot documentation goes here.
        
        @param p0 DESCRIPTION
        @type int
        """
        if p0 == 2:
            self.imageBox.fitToWindow() 
            self.FitToSizeCheckBox.setEnabled(False)
            self.FitToSizeCheckBox.setChecked(True)
    
    @pyqtSlot()
    def on_pushButtonAddRect_clicked(self):
        """
        Slot documentation goes here.
        """
        self.imageBox.addShape(Rectangle(QPoint(-30, -30), 70, 100, QColor(120, 230, 30), QColor(120, 30, 30), 6, False))
        self.imageBox.update()    
