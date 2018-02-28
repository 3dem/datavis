
from PyQt5.QtCore import (QJsonDocument, QJsonParseError, QFile, QIODevice,
                          QObject, pyqtSignal)
import sys


class PPCoordinate:

    def __init__(self, x, y, width, height):
        self.set(x, y, width, height)

    def set(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height


class Micrograph(QObject):

    def __init__(self, name, path, ppCoordList = []):
        super(Micrograph).__init__()
        self.name = name
        self.path = path
        self.ppCoordList = ppCoordList

    def addPPCoordinate(self, ppCoord):

        if ppCoord:
            self.ppCoordList.append(ppCoord)

    def setName(self, name):

        self.name = name

    def getName(self):

        return self.name

    def setPath(self, path):

        self.path = path

    def getPath(self):

        return  self.path

    def getCoordinates(self):

        return self.ppCoordList

class PPSystem:


    def __init__(self, parent=None):
        self.jsonDocument = None
        self.micrographs = []
        self.lastErrorStr = None

    def openMicrograph(self, path):

        try:
            file = QFile(path)

            if file.open(QIODevice.ReadOnly):
                error = QJsonParseError()
                json = QJsonDocument.fromJson(file.readAll(), error)

                if not error.error == QJsonParseError.NoError:
                    self.lastErrorStr = error.errorString()
                    return None

                micro = self.__parseMicrograph__(json.object())
                if micro:
                    self.micrographs.append(micro)
                    return micro
                else:
                    self.lastErrorStr = "Error parsing micrograph"
                    return None
            else:
                self.lastErrorStr = "Error reading file"
                return None

        except:
            print(sys.exc_info())
            self.lastErrorStr = sys.exc_info()
            return None

    def addMicrograph(self, micPath):
        self.micrographs.append(micPath)

    def __parseMicrograph__(self, jsonObj):

        name = jsonObj["name"].toString()
        path = jsonObj["file"].toString()

        coord = jsonObj["coord"].toArray()

        micro = Micrograph(name, path)

        self.__addCoordToMicrograph__(coord, micro)

        return micro

    def __addCoordToMicrograph__(self, jsonArray, micro):

        for v in jsonArray:
            jsonC = v.toObject()
            coord = PPCoordinate(jsonC["x"].toInt(),
                                 jsonC["y"].toInt(),
                                 jsonC["w"].toInt(),
                                 jsonC["h"].toInt())
            micro.addPPCoordinate(coord)