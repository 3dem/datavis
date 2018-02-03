# -*- coding: utf-8 -*-

"""
Module implementing ImageBox.
"""

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import pyqtSlot, pyqtSignal, Qt, QPointF, QPoint, QRect
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QTransform

from .transform import ImageTransform
from .shapes import ShapeList
 

class ImageBox(QWidget): 
    """
    This Class display an image in a QWidget and implement several methods
    to perform some transformation in this image. Taking into account some
    widget events, the images can be rotated, scaled, fit to window, etc.s
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
        self.shapeList = ShapeList()
        self.autoFit = True
        
        self.setMouseTracking(True)

    def getScale(self):
        """
        Get the value of scale
        :return: value of scale
        """
        return self.imageTransform.getScale()

    def setImage(self, qimage):
        """
        Set a new image that will be displayed in the ImageBox.
        :param qimage: QImage instance
        """
        self.setupProperties()
        self.image = qimage
        if self.image:
            self.imageTransform = ImageTransform(self.image.width(),
                                                 self.image.height())

        self.update()

    def rotationAngle(self):
        """
        Get the actual rotation angle
        """
        return self.rotation

    def setAutoFit(self, autoFit):
        """
        Set the value of auto fit
        :param autoFit: new value of auto fit
        """
        self.autoFit = autoFit

    def isAutoFit(self):
        """
        Get the value of autoFit
        :return: value of autoFit
        """
        return self.autoFit

    def setupProperties(self):
        """
        Setup all properties
        """
        self.image = None #The image
        self.imgPos = QPointF() #Initial image position
        self.transformation = QTransform()        
        self.painter = QPainter()
        self.zoomStep = 0.15  # zoom step for mouse wheel

    def setupUi(self):
        """
        Create the GUI of ImageBox
        """
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

    def paintEvent(self, event):
        """
        PyQt method to implement the paint logic.
        :param event: paint event
        """

        if self.image: # Paint image
            self.painter.begin(self)
            self.painter.setTransform(self.imageTransform.transformation())
            self.painter.drawImage(0, 0, self.image)
            self.painter.end()

        if self.shapeList: # Paint all the shapes
            self.painter.begin(self)
            for s in self.shapeList.getShapes():
                s.paint(self.painter)
            self.painter.end()

    @pyqtSlot()
    def rotate(self, angle):
        """
        Rotate the image by the given angle
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


    @pyqtSlot()
    def horizontalFlip(self):
        """
        Flip horizontally the image
        """
        if self.image:
            self.imageTransform.horizontalFlip()
            self.update()

    def mousePressEvent(self, event):
        """
        This method receive mouse press events for the widget
        :param event: Mouse press event
        """
        if event.buttons() & Qt.LeftButton:
            self.mouseBtnState = self.down

        self.lastPos = event.pos()
        self.mouseBtnState = self.down

        self.onMousePressed.emit()

    def mouseMoveEvent(self, e):
        """
        This method receive mouse move events for the widget
        :param e: Mouse move event
        """
        if (e.buttons() & Qt.LeftButton) and self.mouseBtnState == self.down:
            if self.mouseBtnState == self.down:
                self.moveImage(e.pos(), self.lastPos)

        self.lastPos = e.pos()
        self.onMouseMoved.emit()

    def mouseReleaseEvent(self, event):
        """
        This method receive mouse release events for the widget
        :param event: Mouse Release event
        """
        self.mouseBtnState = self.up
        self.lastPos = event.pos()

        self.onMouseReleased.emit()

    def leaveEvent(self, event):
        """
        This method receive widget leave events which are passed in the event
        parameter. A leave event is sent to the widget when the mouse cursor
        leaves the widget
        :param event: leave event
        """
        self.onMouseLeave.emit()

    def enterEvent(self, event):
        """
        This methods receive widget enter events which are passed in the event
        parameter. An event is sent to the widget when the mouse cursor enters
        the widget
        :param event: enter event
        """
        self.onMouseEnter.emit()

    def wheelEvent(self, event):
        """
        Handle the mouse wheel event.
        From Qt Help: Returns the distance that the wheel is rotated, in eighths
                      of a degree. A positive value indicates that the wheel was
                      rotated forwards away from the user; a negative value
                      indicates that the wheel was rotated backwards toward
                      the user. Most mouse types work in steps of 15 degrees,
                      in which case the delta value is a multiple of 120; i.e.,
                      120 units * 1/8 = 15 degrees. However, some mice have
                      finer-resolution wheels and send delta values that are
                      less than 120 units (less than 15 degrees).
        :param event: enter event
        """
        if self.image:
            numPixels = event.pixelDelta()
            numDegrees = event.angleDelta() / 8

            if not numDegrees.isNull():
                numSteps = numDegrees / 15
                self.changeZoom(self.imageTransform.getScale() +
                                self.zoomStep * numSteps.y(),
                                self.lastPos)
            elif not numPixels.isNull():
                # handle with pixel calc. May be in the future
                pass

        event.accept()

    def verticalFlip(self):
        """
        Flip vertically the image
        """
        if self.image:
            self.imageTransform.verticalFlip()
            self.update()     
    
    def moveImage(self, point1,  point2):
        """
        Move the image from point1 to point2
        :param point1: actual image location point
        :param point2: future image location point
        """
        if self.image:
            origDragPoint = self.imageTransform.mapInverse(point1)
            origLastPoint = self.imageTransform.mapInverse(point2)
            dx1 = origDragPoint.x()-origLastPoint.x()
            dy1 = origDragPoint.y()-origLastPoint.y()

            self.imageTransform.translate(dx1, dy1)

            self.shapeList.makeHandlers(self.imageTransform)

            self.update()

    def preferedImageSize(self):
        """
        Get the preferred image size
        """
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
               
            wscaled = ((origW*r)-1)  # hacer casting a int
            hscaled = ((origH*r)-1)
        
        return QRect((compW-wscaled)/2, (compH-hscaled)/2, wscaled, hscaled)

    def preferedScale(self):
        """
        Get the preferred scale
        """
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
        """
        This method center the image
        """
        if not self.image:
            return
        
        origImgCenterX = self.imageTransform.getImgHeigth() / 2
        origImgCenterY = self.imageTransform.getImgHeigth() / 2
        
        cRegion = self.clipRegion()        
        compCenter = QPointF(cRegion.width() / 2, cRegion.height() / 2)
                
        compCenter = self.imageTransform.mapInverse(compCenter)
                
        dx1 = compCenter.x() - origImgCenterX
        dy1 = compCenter.y() - origImgCenterY
                
        self.imageTransform.translate(dx1, dy1)
        self.update()    
        
    def changeZoom(self, sFact, point=None):
        """
        The image is resized taking into account the value of sFact
        :param sFact: resize factor
        :param point: center of image
        """
        
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
        self.shapeList.makeHandlers(self.imageTransform)
        self.update()
        
    def fitToWindow(self):
        """
        The image is fit to window
        """
        if self.image:
            self.imageTransform.setScale(self.preferedScale())
            self.centerImage()
    
    def addShape(self, shape):
        """
        This method add a new shape to the image
        :param shape: new shape
        """
        if shape:
            self.shapeList.appendShape(shape)
            shape.makeOrigHandlers(self.imageTransform)
    
    def resizeEvent(self, resizeEvent):
        """
        This method receive widget resize events which are passed in the event
        parameter. When resizeEvent is called, the widget already has its new
        geometry and the image is automatically fit to window.
        :param resizeEvent: resize event
        """
        QWidget.resizeEvent(self, resizeEvent) 
        if self.autoFit:
            self.fitToWindow()
            

