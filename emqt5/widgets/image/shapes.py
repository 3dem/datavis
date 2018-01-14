# -*- coding: utf-8 -*-

from PyQt5.QtCore import Qt, QPointF, QPoint, QRect
from PyQt5.QtGui import QPainter, QTransform, QColor


class Shape():
    
    ABSTRACT_SHAPE = 999
    RECTANGLE = 1000
    ELLIPSE = 1001
    SEGMENT = 1002
    POLYGONE = 1003
    POLYLINE = 1004
    
    def __init__(self, location, color):
        
        self.location = location
        self.color = color
        self.handlerColor = QColor(23,45,122)#Qt.Yellow
        self.scale = 1.0
        self.filled = False
        self.selected = False
        self.referencePoint = QPointF(0, 0)
        self.origGeomOp = None
        self.handlers = []
        self.origHandlers = []
        self.mPos = QPoint(0, 0)      
        self.hndIndex = -1
        self.HND_LENGTH = 6 #Handlers length
        
    def makeHandlers(self, newGeomOp):    
        
        if self.origHandlers!=None and newGeomOp!=None:           
           transform = newGeomOp.getTransform()                
           self.handlers.clear()         
          
           for p in self.origHandlers:
               self.handlers.append(transform.map(p))          
          
    def makeOrigHandlers(self, geomOp):
    
        if self.handlers!=None:
           self.origHandlers = []          
           for p in self.handlers:
               self.origHandlers.append(geomOp.transform.inverted()[0].map(p))
    
    def getColor(self):    
        return self.color
        
    def getHandlersColor(self):    
        return self.handlerColor
        
    def setColor(self, color):
        self.color = color    
        
    def setFilled(self, fill):
        self.filled = fill
    
    def isFilled(self):
        return self.filled
   
    def translate(self, dx, dy, moveRefPoint):   
        
        for p1 in self.handlers:
            p1.setX(p1.x()+dx)
            p1.setY(p1.y()+dy)

        if moveRefPoint and self.referencePoint!=None:
           self.referencePoint.setX(self.referencePoint.getX()+dx)
           self.referencePoint.setY(self.referencePoint.getY()+dy)
           
    def setOrigHandlers(self, handlers):
        self.origHandlers = handlers
        
    def paintHandlers(self, painter):
        painter.save()
        if self.handlers!=None:
           for h in self.handlers:
               self.paintHandler(painter, h)
        
        painter.restore()       
              
    def paintHandler(self, painter, point):    
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
    
    def getBounds(self):
        return
    
    def setLocation(self, point):
        self.location = point   
        self.updateHandlersPosition()
    
    def getType(self):
        return Shape.ABSTRACT_SHAPE
      
    def getHndIndex(self, point):
        
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
        return self.HND_LENGTH
 
    def getHandlers(self):
        return self.handlers
      
    def setSelected(self, sel):
        self.selected = sel   
    
    def isSelected(self):
        return self.selected
       
    def getReferencePoint(self):
        return self.referencePoint
    
    def seltMousePos(self, point):
        self.mPos = point    
    
    def getMousePos(self):
        return self.mPos     
    
    def getHandlerIndex(self):
        return self.hndIndex
    
    def setHandlerIndex(self, index):
        self.hndIndex = index
    
    def zoom(self, newScale):
        return 
    
    def getPerimeter(self, pixelWidth, pixelHeigth):     
        return
        
    def setScale(self, newScale):
        self.scale = newScale
    
    def getScale(self):
        return self.scale


class Rectangle(Shape):
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

    def setWidth(self, w):
        self.width = w

    def setHeight(self, h):
        self.height = h

    def updateHandlersPosition(self):

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

    def getType(self):
        return Shape.RECTANGLE

    def paint(self, painter):

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
        if newGeomOp != None:
            self.makeScaledShape(newGeomOp.transformation())

    def makeOriginalHandlers(self, geomOp):

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

    def getOrigBounds(self):

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

    def contains(self, point):

        if self.getHndIndex(point) != -1:
            return True

        return QRect(int(self.location.x()), int(self.location.y()),
                     int(self.width), int(self.height)).contains(point)

    def handle(self, hndIndex, point):

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

    def getBounds(self):
        return QRect(int(self.location.x()), int(self.location.y()),
                     int(self.width), int(self.height))

    def zoom(self, newScale):

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
