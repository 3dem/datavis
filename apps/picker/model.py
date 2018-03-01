

class PPCoordinate:
    """
    The PPCoordinate class describes a coordinate defined in a plane
    with X and Y axes
    """
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def set(self, x, y):
        """
        Set x and y values for this coordinate
        :param x:
        :param y:
        :return:
        """
        self.x = x
        self.y = y


class PPBox:
    """
    Box for pick rect
    """
    def __init__(self, w, h):
        self.width = w
        self.height = h


class ImageElem:
    """
    ImageElem is the base element managed by the PPSystem class
    (See PPSystem documentation).
    """
    def __init__(self, name, path, box, ppCoordList=None):
        self.name = name
        self.path = path
        self.box = box
        self.ppCoordList = ppCoordList or []

    def addPPCoordinate(self, ppCoord):
        """
        Add a coordinate to the list of coordinates
        :param ppCoord: Coordinate
        """
        if ppCoord:
            self.ppCoordList.append(ppCoord)

    def setName(self, name):
        """
        Set the ImageElem name
        :param name: the new name
        """
        self.name = name

    def getName(self):
        """
        :return: The ImageElem name
        """
        return self.name

    def setPath(self, path):
        """
        Set de path to the image file
        :param path: absolute path
        """
        self.path = path

    def getPath(self):
        """
        :return: The path of the image
        """
        return self.path

    def getCoordinates(self):
        """
        :return: The coordinate list of the image
        """
        return self.ppCoordList

    def setBox(self, box):
        """
        Set the box for all coordinates
        :param box: PPBox
        """
        self.box = box

    def getBox(self):
        """
        :return: The box for all coordinates
        """
        return self.box


class PPSystem:
    """
    The PPSystem class is responsible for managing the list of images
    in particle picking operation
    """

    def __init__(self):
        self.images = []

    def addImage(self, imgElem):
        """
        Add an image
        :param imgElem: The image
        :return:
        """
        self.images.append(imgElem)
