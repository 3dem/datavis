# -*- coding: utf-8 -*-

from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QTransform


class ImageTransform:
    """
    Class documentation goes here.
    """
    def __init__(self, imgWidth, imgHeigth):
        self.oddFlips = False
        self.oddRotations = False
        self.transform = QTransform()
        self.imageWidth = imgWidth
        self.imageHeight = imgHeigth
        self.scale = 1.0
        self.rotationAngle = 0.0
        self.isVerticalFlip = False
        self.isHorizontalFlip = False
        
    def reset(self):
        self.oddFlips = False
        self.oddRotations = False;
        self.scale = 1.0;
        self.transform = QTransform();
        self.rotationAngle = 0.0

    def setImageWidth(self, imgWidth):
        self.imageWidth = imgWidth
        
    def imgWidth(self): 
        return self.imageWidth
        
    def setImageHeigth(self, imageHeight):    
        self.imageHeight = imageHeight
        
    def imgHeigth(self):    
        return self.imageHeight    
    
    def setScale(self,  imgScale):
        if imgScale <= 0:
            return
        self.transform.scale(1/self.scale, 1/self.scale)
        self.scale = imgScale
        self.transform.scale(imgScale, imgScale)

    def getScale(self):
        return self.scale

    def rotate(self,  angle):    
        self.oddRotations = not self.oddRotations

        # When only one of the flip is activated, we need to change
        # the rotation angle (XOR )
        if ((self.isHorizontalFlip and not self.isVerticalFlip) or
            (not self.isHorizontalFlip and self.isVerticalFlip)):
            angle *= -1

        center = QPointF(self.imageWidth/2.0, self.imageHeight/2.0)
        self.transform.translate(center.x(), center.y())
        self.transform.rotate(angle - self.rotationAngle)
        self.transform.translate(-center.x(), -center.y())
        self.rotationAngle = angle

    def transformation(self):    
        return self.transform
    
    def horizontalFlip(self):
        self.oddFlips = not self.oddFlips;
        self.isHorizontalFlip = not self.isHorizontalFlip
        if not self.oddRotations:
            self.transform.scale(-1.0, 1.0)
            self.transform.translate(-self.imageWidth, 0.0)        
        else:
            self.transform.scale(1.0, -1.0)
            self.transform.translate(0.0, -self.imageHeight)
    
    def verticalFlip(self):
        self.oddFlips = not self.oddFlips
        self.isVerticalFlip = not self.isVerticalFlip        
        if not self.oddRotations:
            self.transform.scale(1.0, -1.0)
            self.transform.translate(0.0, -self.imageHeight)        
        else:
            self.transform.scale(-1.0, 1.0);
            self.transform.translate(-self.imageWidth, 0.0);
        
    def translate(self, dx, dy):
        self.transform.translate(dx, dy)

    def mapInverse(self, point):
        return self.transform.inverted()[0].map(point)
