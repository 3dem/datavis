# -*- coding: utf-8 -*-

"""
Module implementing ImageBox.
"""

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import pyqtSlot, pyqtSignal, Qt, QPointF, QPoint, QRect
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QTransform

from .transform import ImageTransform
 

class ImageBox(QWidget): 
    """
    Class documentation goes here.
    """
    onMousePressed = pyqtSignal()  
    onMouseReleased = pyqtSignal()  
    onMouseMoved = pyqtSignal()  
    onMouseLeave = pyqtSignal()  
    onMouseEnter = pyqtSignal()     
    
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget
        @type QWidget
        """
        super(ImageBox, self).__init__(parent)
        self.setupProperties()
        self.setupUi()
        self.horizontalScrollBar.setVisible(False)
        self.verticalScrollBar.setVisible(False)
        self.lastPos = QPoint        
        self.up = 1
        self.down = 2
        self.mouseBtnState = self.up
        self.isVerticalFlip = False
        self.isHorizontalFlip = False
        self.shapeList = []
        self.autoFit = True
        
        self.setMouseTracking(True)     
        
    def setupProperties(self):
        """
        Setup all properties
        """
        self.image = None #The image      
        self.imgPos = QPointF() #Initial image position
        self.transformation = QTransform()        
        self.painter = QPainter()

    def setupUi(self):
        self.resize(205, 121)
        self.gridLayout = QtWidgets.QGridLayout(self)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setSpacing(0)
        self.gridLayout.setObjectName("gridLayout")
        self.verticalScrollBar = QtWidgets.QScrollBar(self)
        self.verticalScrollBar.setOrientation(QtCore.Qt.Vertical)
        self.verticalScrollBar.setObjectName("verticalScrollBar")
        self.gridLayout.addWidget(self.verticalScrollBar, 0, 1, 1, 1)
        self.horizontalScrollBar = QtWidgets.QScrollBar(self)
        self.horizontalScrollBar.setOrientation(QtCore.Qt.Horizontal)
        self.horizontalScrollBar.setObjectName("horizontalScrollBar")
        self.gridLayout.addWidget(self.horizontalScrollBar, 1, 0, 1, 1)

        QtCore.QMetaObject.connectSlotsByName(self)

    def setImage(self, qimage):
        """
        Set a new image that will be displayed in the ImageBox.
        :param qimage: QtImage instance
        :return:
        """
        self.setupProperties()
        self.image = qimage        
        if self.image:
           self.imageTransform = ImageTransform(self.image.width(),
                                                self.image.height())
           
        self.update()
        
    def paintEvent(self, event):
        """
        PyQt method to implement the paint logic.
        :param event:
        :return:
        """
        self.painter.begin(self)

        if self.image: # Paint image
            self.painter.setTransform(self.imageTransform.transformation())
            self.painter.drawImage(0, 0, self.image)
        
        if self.shapeList: # Paint all the shapes            
            for s in self.shapeList:
                s.paint(self.painter)                

        self.painter.end()

    @pyqtSlot()
    def rotate(self, angle):
        """
        Rotate image
        @param angle The angle is specified in degrees.
        """        
        if self.image:            
            self.imageTransform.rotate(angle)
            self.update()
            
    @pyqtSlot()
    def scale(self, factor):
        """
        Scale the image
        @param factor The aspect ratio.
        """
        if self.image:
            self.imageTransform.setScale(factor)
            self.update()

    def getScale(self):
        return self.imageTransform.getScale()
    
    @pyqtSlot()
    def horizontalFlip(self):   
        if self.image:
            self.imageTransform.horizontalFlip()
            self.update()     
        
    def verticalFlip(self):
        if self.image:
            self.imageTransform.verticalFlip()
            self.update()     
    
    def rotationAngle(self):
        return self.rotation

    def moveImage(self, point1,  point2):
        if self.image:
            origDragPoint = self.imageTransform.mapInverse(point1)
            origLastPoint = self.imageTransform.mapInverse(point2)
            dx1 = origDragPoint.x()-origLastPoint.x()
            dy1 = origDragPoint.y()-origLastPoint.y()

            self.imageTransform.translate(dx1,dy1);
            self.update()

    def mousePressEvent(self, event):  
        if event.buttons() & Qt.LeftButton:
           self.mouseBtnState = self.down 
           
        self.lastPos = event.pos()
        self.mouseBtnState = self.down
            
        self.onMousePressed.emit()
        
    def mouseMoveEvent(self, event):          
        if (event.buttons() & Qt.LeftButton) and self.mouseBtnState==self.down:  
           if self.mouseBtnState==self.down:  
               self.moveImage(event.pos(), self.lastPos)
        
        self.lastPos = event.pos()
        self.onMouseMoved.emit()    
        
    def mouseReleaseEvent(self, event):
        self.mouseBtnState = self.up  
        self.lastPos = event.pos()
        
        self.onMouseReleased.emit()      
    
    def leaveEvent(self,event):                     
        self.onMouseLeave.emit() 
        
    def enterEvent(self,event):  
        self.onMouseEnter.emit()    

    def preferedImageSize(self):
        if self.image:
            compW = self.width()
            compH = self.height()
            origW = self.image.width()
            origH = self.image.height()
            
            if compW<=0 or compH<=0:
               return None
        
            rw = compW/(origW*1.0)        
            rh = compH/(origH*1.0)
            if rw<rh:
               r = rw
            else:
               r = rh 
               
            wscaled = ((origW*r)-1)#hacer casting a int
            hscaled = ((origH*r)-1)
        
        return QRect((compW-wscaled)/2, (compH-hscaled)/2, wscaled, hscaled)

    def preferedScale(self):
        if not self.image:
           return 1.0 
        
        rect = self.preferedImageSize() 
        return rect.width()/(self.image.width()*1.0)   
    
    def clipRegion(self):
        w = self.width()
        h = self.height()
        
        if self.verticalScrollBar.isVisible():
           w -= self.horizontalScrollBar.height()
        if self.horizontalScrollBar.isVisible():
           h -= self.horizontalScrollBar.height()
        
        return QRect(0, 0, w, h)
        
    def centerImage(self):    
        if not self.image:
            return
        
        origImgCenterX = self.imageTransform.imgWidth() / 2
        origImgCenterY = self.imageTransform.imgHeigth() / 2
        
        cRegion = self.clipRegion()        
        compCenter = QPointF(cRegion.width() / 2, cRegion.height() / 2)
                
        compCenter = self.imageTransform.mapInverse(compCenter)
                
        dx1 = compCenter.x() - origImgCenterX
        dy1 = compCenter.y() - origImgCenterY
                
        self.imageTransform.translate(dx1, dy1)
        self.update()    
        
    def changeZoom(self, sFact, point=None):
        
        if not self.image or sFact <= 0:
            return
        
        if not point: #zoom respect to image center
           point = QPoint(self.width()/2, self.height()/2)
           
        origMagPoint = self.imageTransform.mapInverse(point)
        self.imageTransform.setScale(sFact)
        newMagPoint = self.imageTransform.mapInverse(point)

        dx1 = (newMagPoint.x() - origMagPoint.x())
        dy1 = (newMagPoint.y() - origMagPoint.y())
        
        self.imageTransform.translate(dx1, dy1)
        self.update()
        
    def fitToWindow(self):
        if self.image:
            self.imageTransform.setScale(self.preferedScale())
            self.centerImage()
    
    def addShape(self, shape):        
        if not shape:
           return
        self.shapeList.append(shape)    
    
    def resizeEvent(self, resizeEvent):
        QWidget.resizeEvent(self, resizeEvent) 
        if self.autoFit:
            self.fitToWindow()
            
    def setAutoFit(self, autoFit):
        self.autoFit = autoFit

    def isAutoFit(self):
        return self.autoFit        
