# -*- coding: utf-8 -*-

from PyQt5.QtCore import Qt, QPointF, QPoint, QRect
from PyQt5.QtGui import QPainter, QTransform, QColor


class Shape():
    """ Declaration of the class Shape

        This class is used to define an interface for which  derived  some
        others Geometric Figures classes like Rectangle, Ellipse, etc, and
        can be used only as a base class.
        In this class we declared a set of common properties that be used by
        the derived classes """

    ABSTRACT_SHAPE = 999
    RECTANGLE = 1000
    ELLIPSE = 1001
    SEGMENT = 1002
    POLYGON = 1003
    POLYLINE = 1004

    def __init__(self, location, color):

        self.location = location
        self.color = color
        self.handlerColor = QColor(23,45,122)  # Qt.Yellow
        self.scale = 1.0
        self.filled = False
        self.selected = False
        self.referencePoint = QPointF(0, 0)
        self.origGeomOp = None
        self.handlers = []
        self.origHandlers = []
        self.mPos = QPoint(0, 0)
        self.hndIndex = -1
        self.HND_LENGTH = 6  # Handlers length

    def getLocation(self):
        """
        Get the value of location
        :return: value de location
        """
        return self.location

    def setLocation(self, point):
        """
        Set the shape location
        :param point: new value of the Shape position
        """
        self.location = point
        self.updateHandlersPosition()

    def getColor(self):
        """
        Get the color value
        :return: the color value
        """
        return self.color

    def setColor(self, color):
        """
        Set the value of color
        :param color: value of the new color
        self.color = color """

    def getHandlersColor(self):
        """
        Get the color handler
        :return: the color handler
        """
        return self.handlerColor

    def setHandlersColor(self, handlerColor):
        """
        Set de value of handlerColor
        :param handlerColor: new value of handlerColor
        :return: new value of of handlerColor
        """
        self.handlerColor = handlerColor

    def setScale(self, newScale):
        """
        Set the value of scale
        :param newScale: new value of scale
        :return: value of scale
        """
        self.scale = newScale

    def getScale(self):
        """
        Get the value of scale
        :return: value of scale
        """
        return self.scale

    def getFilled(self):
        """
        Get the value of filled
        :return: value of filled
        """
        return self.filled

    def setFilled(self, fill):
        """
        Set the value of filled (True or False)
        :param fill: new value of fill
        """
        self.filled = fill

    def getSelected(self):
        """
        Get the value of selected
        :return: value of selected
        """
        return self.selected

    def setSelected(self, sel):
        """
        Set the value of selected
        :param sel: new value of selected
        """
        self.selected = sel

    def getReferencePoint(self):
        """
        Get the value of referencePoint
        :return: value of referencePoint
        """
        return self.referencePoint

    def setReferencePoint(self, newRefPoint):
        """
        Set the value of referencePoint
        """
        self.referencePoint = newRefPoint

    def getOrigGeomOp(self):
        """
        Get the value of origGeomOp
        :return: value of origGeomOp
        """
        return self.origGeomOp

    def setOrigGeomOp(self, newOrigGeomOp):
        """
        Set the value of origGeomOp
        :param newOrigGeomOp: new value of origGeomOp
        """
        self.origGeomOp = newOrigGeomOp

    def getHandlers(self):
        """
        :return:
        """
        return self.handlers

    def setHandlers(self, newHandlers):
        """
        Set the value of handlers
        :param newHandlers: new value of handlers
        :return:
        """
        self.handlers = newHandlers

    def getOrigHandlers(self):
        """
        Get the value of origHandlers
        :return: value of origHandlers
        """
        return self.origHandlers

    def setOrigHandlers(self, handlers):
        """
        :param handlers:
        :return:
        """
        self.origHandlers = handlers

    def getMPos(self):
        """
        Get the value of mos
        :return: 
        """
        return self.mPos

    def setMPos(self, newMPos):
        """
        Set the value of mPos
        :param newMPos: new value of mPos
        :return:
        """
        self.mPos = newMPos

    def getBounds(self):
        return

    def getType(self):
        """
        Get the Shape type
        :return: the Shape type
        """
        return Shape.ABSTRACT_SHAPE

    def getHndIndex(self, point):
        """
        Get the handler index
        :param point:
        :return:
        """
        if self.handlers==None:
           return -1

        i =0
        rect = QRect()
        for ph in self.handlers:
            rect.setRect(ph.x(), ph.y(), self.HND_LENGTH, self.HND_LENGTH)
            if rect.contains(point):
               return i
            i = i+1

    def getHandlersLength(self):
        """
        :return:
        """
        return self.HND_LENGTH

    def setMousePos(self, point):
        """
        Set the value of the mouse position (QPoint)
        :param point: value of the new position
        :return: new value of mPos
        """
        self.mPos = point

    def getMousePos(self):
        """
        Get the mouse position
        :return: the mouse position
        """
        return self.mPos

    def getHandlerIndex(self):
        """
        :return:
        """
        return self.hndIndex

    def setHandlerIndex(self, index):
        """
        :param index:
        :return:
        """
        self.hndIndex = index

    def getPerimeter(self, pixelWidth, pixelHeigth):
        return

    def makeHandlers(self, newGeomOp):
        """
        :param newGeomOp:
        :return:
        """
        if self.origHandlers==None and newGeomOp==None:
           transform = newGeomOp.getTransform()
           self.handlers.clear()

           for p in self.origHandlers:
               self.handlers.append(transform.map(p))

    def makeOrigHandlers(self, geomOp):
        """
        :param self:
        :param geomOp:
        :return:
        """
        if self.handlers!=None:
           self.origHandlers = []
           for p in self.handlers:
               self.origHandlers.append(geomOp.transform.inverted()[0].map(p))

    def isFilled(self):
        """
        Return the value of parameter Filled (True or False)
        :return: value of Filled
        """
        return self.filled

    def translate(self, dx, dy, moveRefPoint):
        """
        Move a reference point to another location
        :param dx: Variation of coordinate X
        :param dy: Variation of coordinate Y
        :param moveRefPoint: Reference point
        """

        for p1 in self.handlers:
            p1.setX(p1.x()+dx)
            p1.setY(p1.y()+dy)

        if moveRefPoint and self.referencePoint!=None:
           self.referencePoint.setX(self.referencePoint.getX()+dx)
           self.referencePoint.setY(self.referencePoint.getY()+dy)

    def paintHandlers(self, painter):
        """
        :param painter:
        :return:
        """
        painter.save()
        if self.handlers!=None:
           for h in self.handlers:
               self.paintHandler(painter, h)

        painter.restore()

    def paintHandler(self, painter, point):
        """
        :param painter:
        :param point:
        :return:
        """
        painter.save()
        x = point.getX()
        y = point.getY()
        painter.setPen(self.handlerColor)
        painter.drawRect(x-self.HND_LENGTH/2,y-self.HND_LENGTH/2,self.HND_LENGTH,self.HND_LENGTH)
        painter.fillRect(x-self.HND_LENGTH/2,y-self.HND_LENGTH/2,self.HND_LENGTH,self.HND_LENGTH)
        painter.restore()

    def paint(self, painter):
        return

    def updateHandlersPosition(self):
        return

    def isSelected(self):
        """
        :return: the value of selected (True or False)
        """
        return self.selected

    def zoom(self, newScale):
        return


class Rectangle(Shape):
    """ Rectangle Class Declaration

        Rectangle class is used to fill areas to provide a rectangular border
        in a 2D image. This class inherit from Shape
        Constructor of Rectangle calls Shape class constructor"""

    def __init__(self, location, w, h, color, hndColor, hndLength, filled):
        Shape.__init__(self, location, color)
        self.width = w
        self.height = h
        self.filled = filled
        x = self.location.x()
        y = self.location.y()
        self.handlers.append(self.location)
        self.handlers.append(QPointF(x + w / 2.0, y))
        self.handlers.append(QPointF(x + w, y))
        self.handlers.append(QPointF(x + w, y + h / 2.0))
        self.handlers.append(QPointF(x + w, y + h))
        self.handlers.append(QPointF(x + w / 2.0, y + h))
        self.handlers.append(QPointF(x, y + h))
        self.handlers.append(QPointF(x, y + h / 2.0))

    def getWidth(self):
        """
        Get the value of width
        :return: value of width
        """
        return self.width

    def setWidth(self, w):
        """
        Set the value of the Rectangle width
        :param w: new value of width
        """
        self.width = w

    def getHeigth(self, newHeigth):
        """
        Set the value of heigth
        :param newHeigth: new value of heigth
        """
        self.height = newHeigth

    def setHeight(self, h):
        """
        Set the value of the Rectangle Heigth
        :param h: new value of heigth
        """
        self.height = h

    def getOrigBounds(self):
        """

        :return:
        """

        if len(self.origHandlers) == 0:
            return None

        p = self.origHandlers[0]
        minX = maxX = p.x()
        minY = maxY = p.y()
        for p in self.origHandlers:
            x = p.x()
            y = p.y()
            if x < minX:
                minX = x
            elif x > maxX:
                maxX = x

            if y < minY:
                minY = y
            elif y > maxY:
                maxY = y

        return QRectF(minX, minY, maxX - minX, maxY - minY)

    def getBounds(self):
        """

        :return:
        """
        return QRect(int(self.location.x()), int(self.location.y()),
                     int(self.width), int(self.height))

    def getType(self):
        """
        Get the type of Shape. In this case Rectangle
        :return: Rectangle
        """
        return Shape.RECTANGLE

    def updateHandlersPosition(self):
        """
        :return:
        """
        p = self.handlers[1]
        p.setX(self.location.x() + self.width / 2.0)
        p.setY(self.location.y())
        p = self.handlers[2]
        p.setX(self.location.x() + self.width)
        p.setY(self.location.y())
        p = self.handlers[3]
        p.setX(self.location.x() + self.width)
        p.setY(self.location.y() + self.height / 2.0)
        p = self.handlers[4]
        p.setX(self.location.x() + self.width)
        p.setY(self.location.y() + self.height)
        p = self.handlers[5]
        p.setX(self.location.x() + self.width / 2.0)
        p.setY(self.location.y() + self.height)
        p = self.handlers[6]
        p.setX(self.location.x())
        p.setY(self.location.y() + self.height)
        p = self.handlers[7]
        p.setX(self.location.x())
        p.setY(self.location.y() + self.height / 2.0)

    def paint(self, painter):
        """
        This method paint a new Rectangle
        :param painter: object painter
        """
        if painter == None:
            return

        if self.filled:
            painter.fillRect(self.location.x(), self.location.y(), self.width,
                             self.height, self.color)
        else:
            painter.setPen(self.color)
            painter.drawRect(self.location.x(), self.location.y(), self.width,
                             self.height)

        if self.selected:
            self.paintHandlers(painter)

    def makeScaledShape(self, transform):
        """
        This method scale(zoom) the rectangle when the image was scaled too
        :param transform: object QTransform
        """
        if transform != None and len(self.origHandlers) == 0:
            self.handlers.clear()

            p = self.origHandlers[0]
            minX = minY = 0
            maxX = maxY = 0

            p = transform.map(p)
            minX = maxX = p.x()
            minY = maxY = p.y()
            self.handlers.append(p)

            for p1 in self.origHandlers:
                p = transform.map(p1)
                self.handlers.append(p)
                x = p.x()
                y = p.y()

                if x < minX:
                    minX = x
                else:
                    if x > maxX:
                        maxX = x

                if y < minY:
                    minY = y
                elif y > maxY:
                    maxY = y

        p = self.handlers[0]
        p.setX(minX)
        p.setY(minY)
        self.location = p
        self.width = maxX - minX
        self.height = maxY - minY
        self.updateHandlersPosition()

    def makeHandlers(self, newGeomOp):
        """

        :param newGeomOp:
        :return:
        """
        if newGeomOp != None:
            self.makeScaledShape(newGeomOp.transformation())

    def makeOriginalHandlers(self, geomOp):
        """

        :param geomOp:
        :return:
        """

        if geomOp == None:
            return

        self.origHandlers.clear()
        t = geomOp.transformation()
        for p in self.handlers:
            self.origHandlers.append(t.inverted()[0].map(p))

        bounds = self.getOrigBounds()
        w1 = bounds.width()
        h1 = bounds.height()
        self.origHandlers.clear()
        x = bounds.x()
        y = bounds.y()
        self.origHandlers.append(QPointF(x, y))
        self.origHandlers.append(QPointF(x + w1 / 2.0, y))
        self.origHandlers.append(QPointF(x + w1, y))
        self.origHandlers.append(QPointF(x + w1, y + h1 / 2.0))
        self.origHandlers.append(QPointF(x + w1, y + h1))
        self.origHandlers.append(QPointF(x + w1 / 2.0, y + h1))
        self.origHandlers.append(QPointF(x, y + h1))
        self.origHandlers.append(QPointF(x, y + h1 / 2.0))

    def contains(self, point):
        """

        :param point:
        :return:
        """

        if self.getHndIndex(point) != -1:
            return True

        return QRect(int(self.location.x()), int(self.location.y()),
                     int(self.width), int(self.height)).contains(point)

    def handle(self, hndIndex, point):
        """
        :param hndIndex:
        :param point:
        :return:
        """

        if hndIndex <= len(self.handlers) and hndIndex >= 0:
            man = self.handlers[hndIndex]
            dx = (point.x() - man.x())
            dy = (point.y() - man.y())
            if hndIndex == 0:
                self.width += -dx
                self.height += -dy
                if self.width < 0 and self.height < 0:
                    p1 = self.handlers[3]
                    self.location.setX(p1.x())
                    self.location.setY(p1.y())
                    self.width = abs(self.width)
                    self.height = abs(self.height)
                    self.hndIndex = 4
                elif self.width < 0:
                    self.location.setX(self.location.x() + (self.width - (-dx)))
                    self.width = abs(self.width)
                    self.hndIndex = 2
                elif self.height < 0:
                    self.location.setY(
                        self.location.getY() + (self.height - (-dy)))
                    self.height = abs(self.height)
                    self.hndIndex = 6
                else:
                    man.setX(man.x() + dx)
                    man.setY(man.y() + dy)
        elif hndIndex == 1:
            self.location.setY(self.location.y() + dy)
            self.height += dy
            if self.height < 0:
                p1 = self.handlers[5]
                self.location.setY(p1.y())
                self.hndIndex = 5
                self.height = abs(self.height)
        elif hndIndex == 2:
            self.width += dx
            self.height += dy
            if self.width < 0 and self.height < 0:
                p1 = self.handlers[5]
                self.location.setX(p1.x() + self.width)
                self.location.setY(p1.y() + self.height)
                self.width = abs(self.width)
                self.height = abs(self.height)
                self.hndIndex = 6
            elif self.width < 0:
                self.width = 0
                self.hndIndex = 0
            elif self.height < 0:
                self.height = 0
                p1 = self.handlers[5]
                self.location.setY(p1.y())
                self.hndIndex = 4
            else:
                self.location.setY(self.location.y() + dy)
        elif hndIndex == 3:
            self.width += dx
            if self.width < 0:
                self.width = 0
                self.hndIndex = 7
        elif hndIndex == 4:
            self.width += dx
            self.height += dy
            if self.width < 0 and self.height < 0:
                self.width = abs(self.width)
                self.height = abs(self.height)
                self.location.setX(self.location.x() - self.width)
                self.location.setY(self.location.y() - self.height)
                self.hndIndex = 0
            elif self.width < 0:
                self.width = 0
                self.hndIndex = 6
            elif self.height < 0:
                self.height = 0
                self.hndIndex = 2
        elif hndIndex == 5:
            self.height += dy
            if self.height < 0:
                self.height = 0
                self.hndIndex = 1
        elif hndIndex == 6:
            self.width += dx
            self.height += dy
            if self.width < 0 and self.height < 0:
                self.width = abs(self.width)
                self.height = abs(self.height)
                self.hndIndex = 2
            elif self.width < 0:
                p1 = self.handlers[1]
                self.location.setX(p1.x())
                self.location.setY(p1.y())
                self.width = abs(self.width)
                self.hndIndex = 4
            elif self.height < 0:
                self.hndIndex = 0
                self.height = 0
            else:
                self.location.setX(self.location.x() + dx)
                self.location.setY(self.location.y() + dy)
        elif hndIndex == 7:
            self.width -= dx
            self.location.setX(self.location.x() + dx)
            self.location.setY(self.location.y() + dy)
            if self.width < 0:
                p1 = self.handlers[1]
                self.location.setX(p1.x())
                self.width = abs(self.width)
                self.hndIndex = 3

        self.updateHandlersPosition()

    def isFilled(self):
        """
        Return the value of parameter Filled (True or False)
        :return: value of Filled
        """
        return self.filled

    def zoom(self, newScale):
        """
        This methods scale objects type Rectangles using a new scale
        :param newScale: new scale
        """

        t = QTransform()
        t.scale(newScale)

        for i in range(0, len(self.handlers), 1):
            p = self.origHandlers[i]
            p = t.map(p)
            pScaled = self.handlers[i]
            pScaled.setX(p.x())
            pScaled.setY(p.y())

        p1 = self.handlers[2]
        p2 = self.handlers[6]
        dx = self.location.x() - p1.x()
        dy = self.location.y() - p1.y()

        self.width = int((dx ** 2 + dy ** 2) ** 0.5)

        dx = self.location.x() - p2.x()
        dy = self.location.y() - p2.y()

        self.height = int((dx ** 2 + dy ** 2) ** 0.5)

        self.setScale(newScale)
