

class Coordinate:
    """
    The PPCoordinate class describes a coordinate defined in a plane
    with X and Y axes
    """
    def __init__(self, x, y, label="Manual"):
        self.x = x
        self.y = y
        self.label = label

    def set(self, x, y):
        """
        Set x and y values for this coordinate
        :param x:
        :param y:
        :return:
        """
        self.x = x
        self.y = y

    def setLabel(self, labelName):
        """
        Sets the label name
        :param labelName: the label name
        """
        self.label = labelName

    def getLabel(self):
        """
        :return: The label name
        """
        return self.label


class Micrograph:
    """
    ImageElem is the base element managed by the PPSystem class
    (See PPSystem documentation).
    """
    def __init__(self, imgId, path, ppCoordList=None):
        self.imgId = imgId
        self.path = path
        self.ppCoordList = ppCoordList or []

    def addPPCoordinate(self, ppCoord):
        """
        Add a coordinate to the list of coordinates
        :param ppCoord: Coordinate
        """
        if ppCoord:
            self.ppCoordList.append(ppCoord)

    def setId(self, imgId):
        """
        Sets the image Id
        """
        self.imgId = imgId

    def getImageId(self):
        """
        :return: Get the image Id
        """
        return self.imgId

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

    def getPickCount(self):
        """
        :return: The picking count
        """
        return len(self.ppCoordList)

    def removeCoordinate(self, ppCoord):
        """
        Remove the coordinate from the list
        :param ppCoord:
        """
        if ppCoord and self.ppCoordList:
            self.ppCoordList.remove(ppCoord)

    def clear(self):
        """ Remove all coordinates of this micrograph. """
        self.ppCoordList = []


class PickerDataModel:
    """
    The PPSystem class is responsible for managing the list of images
    in particle picking operation
    """

    def __init__(self):
        self.images = []
        self.labels = {}
        self._initLabels()
        self._boxsize = None
        self._lastId = 0

    def setBoxSize(self, newSizeX):
        """ Set the box size for the coordinates. """
        self._boxsize = newSizeX

    def getBoxSize(self):
        """ Return the current box size of the coordinates. """
        return self._boxsize

    def addMicrograph(self, imgElem):
        """
        Add an image
        :param imgElem: The image
        :return:
        """
        if isinstance(imgElem, basestring):
            self._lastId += 1
            imgElem = Micrograph(self._lastId, imgElem)

        self.images.append(imgElem)

    def getImgCount(self):
        """
        :return: The image count
        """
        return len(self.images)

    def getLabels(self):
        """
        :return:The labels for this PPSystem
        """
        return self.labels

    def getLabel(self, labelName):
        """
        Returns the label with name=labelName in Labels List
        :param labelName: The label name
        :return: dict value
        """
        return self.labels.get(labelName)

    def _initLabels(self):
        """
        Initialize the labels for this PPSystem
        """
        automatic = {}
        automatic["name"] = "Auto"
        automatic["color"] = "#FF0004"  # #AARRGGBB
        self.labels["Auto"] = automatic

        manual = {}
        manual["name"] = "Manual"
        manual["color"] = "#1500FF"  # #AARRGGBB
        self.labels["Manual"] = manual

        default = {}
        default["name"] = "Default"
        default["color"] = "#74ea00"  # #AARRGGBB
        self.labels["Default"] = default
