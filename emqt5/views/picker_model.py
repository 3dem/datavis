

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
    Micrograph is the base element managed by the PickerDataModel class
    (See PickerDataModel documentation).
    """
    def __init__(self, micId, path, coordinates=None):
        self._micId = micId
        self._path = path
        self._coordinates = coordinates or []

    def __len__(self):
        """ The lenght of the Micrograph is the number of coordinates. """
        return len(self._coordinates)

    def __iter__(self):
        """ Iterates over all coordinates in the micrograph. """
        return iter(self._coordinates)

    def setId(self, micId):
        """ Set the micrograph Id. """
        self._micId = micId

    def getId(self):
        """ Returns the micrograph Id. """
        return self._micId

    def setPath(self, path):
        """ Set the micrograph path. """
        self._path = path

    def getPath(self):
        """ Returns the path of the micrograph. """
        return self._path

    def addCoordinate(self, coord):
        """ Add a new coordinate to this micrograph. """
        self._coordinates.append(coord)

    def removeCoordinate(self, ppCoord):
        """ Remove the coordinate from the list. """
        if ppCoord and self._coordinates:
            self._coordinates.remove(ppCoord)

    def clear(self):
        """ Remove all coordinates of this micrograph. """
        self._coordinates = []


class PickerDataModel:
    """
    This class stores the basic information to the particle picking data.
    It contains a list of Micrographs and each Micrograph contains a list
    of Coordinates (x, y positions in the Micrograph).
    """
    def __init__(self):
        self._micrographs = []
        self._labels = {}
        self._initLabels()
        self._boxsize = None
        self._lastId = 0

    def __len__(self):
        """ The lenght of the model is the number of Micrographs. """
        return len(self._micrographs)

    def __iter__(self):
        """ Iterate over all Micrographs in the model. """
        return iter(self._micrographs)

    def _initLabels(self):
        """
        Initialize the labels for this PPSystem
        """
        automatic = dict()
        automatic["name"] = "Auto"
        automatic["color"] = "#FF0004"  # #AARRGGBB
        self._labels["Auto"] = automatic

        manual = dict()
        manual["name"] = "Manual"
        manual["color"] = "#1500FF"  # #AARRGGBB
        self._labels["Manual"] = manual

        default = dict()
        default["name"] = "Default"
        default["color"] = "#74ea00"  # #AARRGGBB
        self._labels["Default"] = default

    def setBoxSize(self, newSizeX):
        """ Set the box size for the coordinates. """
        self._boxsize = newSizeX

    def getBoxSize(self):
        """ Return the current box size of the coordinates. """
        return self._boxsize

    def addMicrograph(self, mic):
        """ Add a new micrograph to the model.
        Params:
            mic: could be Micrograph instance or a path.
        """
        if isinstance(mic, str) or isinstance(mic, unicode):
            self._lastId += 1
            mic = Micrograph(self._lastId, mic)

        self._micrographs.append(mic)

    def getLabels(self):
        """
        :return:The labels for this PPSystem
        """
        return self._labels

    def getLabel(self, labelName):
        """
        Returns the label with name=labelName in Labels List
        :param labelName: The label name
        :return: dict value
        """
        return self._labels.get(labelName)


