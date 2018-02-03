# -*- coding: utf-8 -*-

from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QTransform


class ImageTransform:
    """
    This class is used to specifies 2D images transformations. These
    transformations specifies how to translate, scale, rotate, etc. 2D images
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
        
    def getOddFlips(self):
        """
        Get the value of oddFlips
        :return: value of oddFlips
        """
        return self.oddFlips

    def setOddFlips(self, oddFlips):
        """
        Set the value of oddFlips
        :param oddFlips: new value of oddFlips
        """
        self.oddFlips = oddFlips

    def getOddRotations(self):
        """
        Get the value of oddRotations
        :return: value of oddRotations
        """
        return self.oddRotations

    def setOddRotations(self, oddRotations):
        """
        Set the value of oddRotations
        :param oddFlips: new value of oddRotations
        """
        self.oddRotations = oddRotations

    def transformation(self):
        """
        Get the value of transform
        :return: value of transform
        """
        return self.transform

    def setImageWidth(self, imgWidth):
        """
        Set the value of the image width
        :param imgWidth: new value of the image width
        """
        self.imageWidth = imgWidth

    def getImgWidth(self):
        """
        Get the value of the image width
        :return: value of image width
        """
        return self.imageWidth

    def setImageHeigth(self, imageHeight):
        """
        Set the value of image heigth
        :param imageHeight: new value of image Height
        """
        self.imageHeight = imageHeight

    def getImgHeigth(self):
        """
        Get the value of image heigth
        """
        return self.imageHeight

    def getScale(self):
        """
        Get the value of the image scale
        """
        return self.scale

    def setScale(self,  imgScale):
        """
        Transform the image with the new scale value
        :param imgScale: new value of image scale
        """
        if imgScale <= 0:
            return
        self.transform.scale(1/self.scale, 1/self.scale)
        self.scale = imgScale
        self.transform.scale(imgScale, imgScale)

    def getRotationAngle(self):
        """
        Get the rotation angle
        :return: the rotation angle
        """
        return self.rotationAngle

    def setRotationAngle(self, newRotationAngle):
        """
        Set the value of Rotation Angle
        :param newRotationAngle: new value of Rotation Angle
        """
        self.rotationAngle = newRotationAngle

    def setIsHorizontalFlips(self, isHorizFlips):
        """
        Set the value of isHorizontalFlip
        :param isHorizFlips: new value of isHorizontalFlip
        """
        self.isHorizontalFlip = isHorizFlips

    def setIsVerticalFlips(self, isVertFlips):
        """
        Set the value of isVerticalFlip
        :param isVertFlips: new value of isVerticalFlip
        """
        self.isVerticalFlip = isVertFlips

    def isVerticalFlips(self):
        """
        Get True if vertical flips has done to 2D image; otherwise return False
        :return: value of isVerticalFlips
        """
        return self.isVerticalFlips

    def isHorizontalFlips(self):
        """
        Get True if horizontal flips has done to 2D image; otherwise return False
        case
        :return: value of isVerticalFlips
        """
        return self.isHorizontalFlip

    def reset(self):
        """
        Reset the class parameters to original values(default constructor class)
        """
        self.oddFlips = False
        self.oddRotations = False;
        self.scale = 1.0;
        self.transform = QTransform();
        self.rotationAngle = 0.0

    def rotate(self,  angle):
        """
        This methods rotate 2D images in degrees
        :param angle: value of the angles (in degrees)
        """
        self.oddRotations = not self.oddRotations

        # When only one of the flip is activated, we need to change
        # the rotation angle (XOR)
        if ((self.isHorizontalFlip and not self.isVerticalFlip) or
            (not self.isHorizontalFlip and self.isVerticalFlip)):
            angle *= -1

        center = QPointF(self.imageWidth/2.0, self.imageHeight/2.0)
        self.transform.translate(center.x(), center.y())
        self.transform.rotate(angle - self.rotationAngle)
        self.transform.translate(-center.x(), -center.y())
        self.rotationAngle = angle

    def horizontalFlip(self):
        """
        This methods realize a horizontally transformation-flip to 2D image
        """
        self.oddFlips = not self.oddFlips;
        self.isHorizontalFlip = not self.isHorizontalFlip
        if not self.oddRotations:
            self.transform.scale(-1.0, 1.0)
            self.transform.translate(-self.imageWidth, 0.0)        
        else:
            self.transform.scale(1.0, -1.0)
            self.transform.translate(0.0, -self.imageHeight)
    
    def verticalFlip(self):
        """
        This methods realize a vertically transformation-flip to 2D image
        """
        self.oddFlips = not self.oddFlips
        self.isVerticalFlip = not self.isVerticalFlip        
        if not self.oddRotations:
            self.transform.scale(1.0, -1.0)
            self.transform.translate(0.0, -self.imageHeight)        
        else:
            self.transform.scale(-1.0, 1.0);
            self.transform.translate(-self.imageWidth, 0.0);
        
    def translate(self, dx, dy):
        """
        This methods moves the coordinate system dx along the x axis and dy
        along the y axis
        :param dx: variation in the x axis
        :param dy: variation in the y axis
        """
        self.transform.translate(dx, dy)

    def mapInverse(self, point):
        """
        Get an inverted copy of the map in any point
        :param point: value of the point
        """
        return self.transform.inverted()[0].map(point)

    def map(self, point):
        """
        Creates and returns a point that is a copy of the given point, mapped
        into the coordinate system defined by this trasformation
        :param point: value of the point
        :return: mapped point
        """
        return self.transform.map(point)
