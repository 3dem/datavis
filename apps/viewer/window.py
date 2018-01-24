# -*- coding: utf-8 -*-

"""
Module implementing MainWindow.
"""

from PyQt5.QtCore import pyqtSlot, QDir, QPoint
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QApplication, QFileDialog, QSlider
from PyQt5.QtGui import QImage, QColor

from emqt5.widgets.image import ImageBox
from emqt5.widgets.image.shapes import Rectangle
from emqt5.widgets.image.adjust_widgets import WindowLevels, BrightnessContrast, HistogramData

from Ui_MainWindow import Ui_MainWindow


class MainWindow(QMainWindow, Ui_MainWindow):
    """
    MainWindow class is used to display and interact with a 2D image.
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

        self.__insertAdjustWidgets__()
        imageFile = kwargs.get('imageFile', None)
        if imageFile:
            print("Loading filename:", imageFile)
            self.openImage(imageFile)
            self.imageBox.centerImage()

    def __insertAdjustWidgets__(self):
        """
        """
        self.windowLevels = WindowLevels(self.tab)
        self.brightnessContrast = BrightnessContrast(self.tab)
        histoData = HistogramData()
        pixelValues = [1, 3, 5, 7, 34, 45, 47, 30, 56, 70, 78, 78, 89, 80, 100,
                       40, 57, 61, 40, 20, 100, 120, 180, 60, 23, 24, 230, 200,
                       100, 78, 77, 40, 15, 30, 100, 30, 50, 55, 80, 85, 150,
                       180, 170, 170, 5, 5, 30,
                       1, 3, 5, 7, 34, 45, 47, 30, 56, 70, 78, 78, 89, 80, 100,
                       40, 57, 61, 40, 20,
                       100, 120, 180, 60, 23, 24, 230, 200, 100, 78, 77, 40, 15,
                       30, 100, 30, 50, 55,
                       80, 85, 150, 180, 170, 170, 5, 5, 30, 30, 100, 30, 50,
                       55, 80, 85, 150, 180, 170, 170, 5, 5, 30,
                       1, 3, 5, 7, 34, 45, 47, 30, 56, 70, 78, 78, 89, 80, 100,
                       40, 57, 61, 40, 20,
                       100, 120, 180, 60, 23, 24, 230, 200, 100, 78, 77, 40, 15,
                       30, 100, 30, 50,
                       45, 47, 30, 56, 70, 78, 78, 89, 80, 100, 40, 57, 61, 40,
                       20, 55, 77, 89, 0, 23,
                       100, 120, 180, 60, 23, 24, 230, 200, 100, 78, 77, 40, 15,
                       30, 100, 30, 50, 55,
                       80, 85, 150, 180, 170, 170, 5, 5, 30, 30, 100, 30, 50,
                       55, 80, 85, 150, 180, 170, 170, 5, 5, 30,
                       1, 3, 5, 7, 34, 45, 47, 30, 56, 70, 78, 78, 89, 80, 100,
                       40, 57, 61, 40, 20,
                       100, 120, 180, 60, 23, 24, 230, 200, 100, 78, 77, 40, 15,
                       30, 100, 30, 50,
                       45, 47, 30, 56, 70, 78, 78, 89, 80, 100, 40, 57]
        print("cantidad=%i", len(pixelValues))
        histoData.setData(pixelValues)
        histoData.setMin(0)
        histoData.setMax(255)

        histogramWidget = self.windowLevels.getHistogramWidget()
        histogramWidget.setData(histoData)
        layout = self.verticalLayout_8.layout()
        layout.addWidget(self.windowLevels)
        layout.addWidget(self.brightnessContrast)
        self.windowLevels.autoWindowLevels.connect(self.autoWindowLevelsHandler)
        self.windowLevels.resetWindowLevels.connect(self.resetWindowLevelsHandler)
        self.windowLevels.configNewWindowLevels.connect(self.setWindowLevelsHandler)

    @pyqtSlot()
    def autoWindowLevelsHandler(self):
        QMessageBox.information(self, "Image Viewer",
                                "Button Auto clicked. Add code please")

    @pyqtSlot()
    def resetWindowLevelsHandler(self):
        QMessageBox.information(self, "Image Viewer",
                                "Button Reset clicked. Add code please")

    @pyqtSlot()
    def setWindowLevelsHandler(self):
        QMessageBox.information(self, "Image Viewer",
                                "Button Set clicked. Add code please")

    @pyqtSlot()
    def on_actionExit_triggered(self):
        """
        Tells the application to exit with a return code
        """
        import sys
        sys.exit()   
        
    @pyqtSlot()
    def on_actionRigth_Rotation_triggered(self):
        """
        Rotate the image towards to right side
        """
        self.changeFitToSizeCheckBoxEnable(True)
        if self.imageBox.isHorizontalFlip or self.imageBox.isVerticalFlip:
            self.imageBox.rotate(self.imageBox.rotationAngle() -
                                 self.rotationStep);
        else:
             self.imageBox.rotate(self.imageBox.rotationAngle() +
                                  self.rotationStep);
        
    @pyqtSlot()
    def on_actionLeft_Rotation_triggered(self):
        """
        Rotate the image towards to left side
        """
        self.changeFitToSizeCheckBoxEnable(True)
        if self.imageBox.isHorizontalFlip or self.imageBox.isVerticalFlip:
            self.imageBox.rotate(self.imageBox.rotationAngle()-self.rotationStep);   
        else:
             self.imageBox.rotate(self.imageBox.rotationAngle()+self.rotationStep);
    
    @pyqtSlot()
    def openImage(self,  fileName):
        """
        Loads an image from the file with the given fileName.
        :param fileName: image file name
        :return: return false if the image was unsuccessfully loaded
        """
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
        This Slot communicate the action to open an image with openImage method.
        """
        self.openImage(None)
    
    @pyqtSlot()
    def on_actionFlip_Vertical_triggered(self):
        """
        This slot communicate the action to flip vertically an image with
        verticalFlip method.
        Flip vertically an image.
        """
        self.changeFitToSizeCheckBoxEnable(True)
        self.imageBox.verticalFlip()
       
    @pyqtSlot()
    def on_actionFlip_Horizontal_triggered(self):
        """
        This slot communicate the action to flip horizontally an image with
        verticalFlip method in ImageBox class.
        Flip horizontally an image.
        """
        self.changeFitToSizeCheckBoxEnable(True)
        self.imageBox.horizontalFlip()
        
    @pyqtSlot()
    def on_actionZoom_In_triggered(self):
        """
        This slot communicate the action to zoom_in an image with
        changeZoom method in ImageBox class.
        Reduce the image.
        """      
        self.changeFitToSizeCheckBoxEnable(True)
        self.imageBox.changeZoom(self.imageBox.getScale()+self.scaleF)
    
    @pyqtSlot()
    def on_actionZoom_Out_triggered(self):
        """
        This slot communicate the action to zoom_out an image with
        changeZoom method in ImageBox class.
        Enlarge the image.
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
        This slot communicate the action to fit to size an image with
        fitToWindow method in ImageBox class.
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
        self.imageBox.addShape(Rectangle(QPoint(-30, -30), 70, 100,
                                         QColor(120, 230, 30), QColor(120, 30,
                                                                      30), 6,
                                         False))
        self.imageBox.update()    
