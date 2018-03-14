
from PyQt5.QtCore import (QJsonDocument, QJsonParseError, QFile, QIODevice,
                          QObject, pyqtSignal)

from model import Micrograph, Coordinate

class ImageElemParser:
    """
    This class is responsible for building an ImageElem according to a specification format.
    Specification supported: JSON format. (See parseImage documentation)
    """

    def parseImage(self, jsonObj):
        """
        Parse an image specification from json object
        :param json: image specification
        :return: ImageElem

        Features:
        JSON specification for ImageElem:
        {
            "name":"image_name",
            "file":"/some/path/image_file.some",
            "box":
                  {
                    "w":20,
                    "h":20
                  }
            "coord":[
                     {
		  	          "x":20,
                      "y":20,
                      "label":"Manual"
                     },
                     {
                      "x":80,
                      "y":20,
                      "label":"Auto"
                     },
                     ...
                    ]
         }
        """
        jsonBox = jsonObj["box"].toObject()

        imageElem = Micrograph(0,
                               jsonObj["file"].toString(), [])

        self._addCoordToImage(jsonObj["coord"].toArray(), imageElem)

        return imageElem

    def _addCoordToImage(self, jsonArray, imgElem):
        """
        Add all coordinates specified in jsonArray to imgElem
        :param jsonArray: Coordinates
        :param imgElem:   Image element

        Features:
        Coordinates specification in json array format:
        [
            {
            "x":20,
            "y":20,
            "label":"Manual"
            },
            {
            "x":80,
            "y":20,
            "label":"Auto"
            },
            ...
         ]
        """

        for v in jsonArray:
            jsonC = v.toObject()
            coord = Coordinate(jsonC["x"].toInt(),
                               jsonC["y"].toInt(),
                               jsonC.get("label", "Manual"))
            imgElem.addPPCoordinate(coord)


def parseTextCoordinates(path):
    """ Parse (x, y) coordinates from a texfile assuming
     that the first two columns on each line are x and y.
    """
    with open(path) as f:
        for line in f:
            l = line.strip()
            if l:
                parts = l.strip().split()
                yield int(parts[0]), int(parts[1])
