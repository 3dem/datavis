
import os

from ._constants import TYPE_INT, TYPE_STRING
from ._table_models import TableModel, ColumnConfig


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
        self._coordinates = []
        if coordinates:
            for c in coordinates:
                if isinstance(c, tuple):
                    size = len(c)
                    if size == 2:
                        self._coordinates.append(Coordinate(c[0], c[1],
                                                            "Default"))
                    elif size == 3:
                        self._coordinates.append(
                            Coordinate(c[0], c[1],
                                       c[2] if not c[2] == "" else "Default"))
                    elif size == 4:
                        self._coordinates.append(
                            (Coordinate(c[0], c[1], "Default"),
                             Coordinate(c[2], c[3], "Default")))
                    elif size == 5:
                        t = c[4] if not c[4] == "" else "Default"
                        self._coordinates.append((Coordinate(c[0], c[1], t),
                                                  Coordinate(c[2], c[3], t)))
                    else:
                        raise Exception(
                            "Invalid coordinate specification for :%d."
                            % str(c))
                elif isinstance(c, Coordinate):
                    self._coordinates.append(c)
                else:
                    raise Exception("Invalid coordinate type. Only tupple or "
                                    "Coordinate types are supported.")

    def __len__(self):
        """ The length of the Micrograph is the number of coordinates. """
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


class MicrographsTableModel(TableModel):
    """ Simple table model for use in PickerView """

    def __init__(self, columns=[]):
        """
        Construct an _TableModel object
        :param columns: (list) List of ColumnInfo
        """
        self._data = []
        self._colums = columns
        self._tableName = ''
        self._tableNames = []

    def _loadTable(self, tableName):
        pass

    def iterColumns(self):
        """ Return an iterator for model columns"""
        return iter(self._colums)

    def getColumnsCount(self):
        """ Return the number of columns """
        return len(self._columns)

    def getRowsCount(self):
        """ Return the number of rows """
        return len(self._data)

    def getValue(self, row, col):
        if 0 <= row < len(self._data) and 0 <= col < len(self._colums):
            return self._data[row][col]
        return 0

    def setValue(self, row, col, value):
        """
        Set the value for the given row and column
        :param row:    (int) row index.
        :param col:    (int) column index.
        :param value:  The value
        """
        self._data[row][col] = value

    def appendRow(self, row):
        """
        Append a row to the end of the model
        :param row: (list) The row values.
        """
        if isinstance(row, list) and len(row) == len(self._colums):
            self._data.append(row)
        else:
            raise Exception("Invalid row.")


class PickerDataModel:
    """
    This class stores the basic information to the particle picking data.
    It contains a list of Micrographs and each Micrograph contains a list
    of Coordinates (x, y positions in the Micrograph).
    """
    def __init__(self):
        self._micrographs = dict()
        self._labels = dict()
        self._privateLabels = dict()
        self._initLabels()
        self._boxsize = None
        self._lastId = 0

    def __len__(self):
        """ The length of the model is the number of Micrographs. """
        return len(self._micrographs)

    def __iter__(self):
        """ Iterate over all Micrographs in the model. """
        return iter(self._micrographs)

    def __getitem__(self, micId):
        return self._micrographs[micId]

    def _initLabels(self):
        """
        Initialize the labels for this PPSystem
        """
        automatic = dict()
        automatic["name"] = "Auto"
        automatic["color"] = "#0012FF"  # #AARRGGBB
        self._labels["Auto"] = automatic
        self._privateLabels["A"] = automatic

        manual = dict()
        manual["name"] = "Manual"
        manual["color"] = "#1EFF00"  # #AARRGGBB
        self._labels["Manual"] = manual
        self._privateLabels["M"] = manual

        default = dict()
        default["name"] = "Default"
        default["color"] = "#1EFF00"  # #AARRGGBB
        self._labels["Default"] = default
        self._privateLabels["D"] = default

    def setBoxSize(self, newSizeX):
        """ Set the box size for the coordinates. """
        self._boxsize = newSizeX

    def getBoxSize(self):
        """ Return the current box size of the coordinates. """
        return self._boxsize

    def addMicrograph(self, mic):
        """ Add a new micrograph to the model.
        mic:   (Micrograph) A Micrograph instance. If the micrograph ID is -1
               then a new ID will be assigned to the micrograph.
        Raise Exception if mic is not instance of Micrograph
        """
        if not isinstance(mic, Micrograph):
            raise Exception("Invalid micrograph instance.")

        if mic.getId() == -1:
            mic.setId(self.nextId())

        self._micrographs[mic.getId()] = mic

    def getLabels(self):
        """
        :return:The labels for this PPSystem
        """
        return self._labels

    def getLabel(self, labelName):
        """
        Returns the label with name=labelName in Labels list (first) or Private
        Labels list
        :param labelName: The label name
        :return: dict value
        """
        ret = self._labels.get(labelName)
        pl = self._privateLabels
        return ret if ret else pl.get(labelName, pl.get('D'))

    def nextId(self):
        """
        Generates the next id.
        """
        self._lastId += 1
        return self._lastId

    def getData(self, micId):
        """
        Return the micrograph image data
        :param micId: (int) The micrograph id
        :return: The micrograph image data
        """
        raise Exception('Not implemented')

    def getMicrographsTableModel(self):
        """ Return the TableModel that will be used to
        display the list of micrographs.
        """
        micTable = MicrographsTableModel([
            ColumnConfig('Micrograph', dataType=TYPE_STRING, editable=True),
            ColumnConfig('Coordinates', dataType=TYPE_INT, editable=True),
            ColumnConfig('Id', dataType=TYPE_INT, editable=True, visible=False)
        ])
        for micId, mic in self._micrographs.items():
            micTable.appendRow([os.path.basename(mic.getPath()),
                                len(mic), mic.getId()])

        return micTable


def parseTextCoordinates(path):
    """ Parse (x, y) coordinates from a texfile assuming
     that the first two columns on each line are x and y.
    """
    with open(path) as f:
        for line in f:
            li = line.strip()
            if li:
                parts = li.strip().split()
                size = len(parts)
                if size == 2:  # (x, y)
                    yield int(parts[0]), int(parts[1]), ''
                elif size == 3:  # (x, y, label)
                    yield int(parts[0]), int(parts[1]), str(parts[2])
                elif size == 4:  # (x1, y1, x2, y2)
                    yield int(parts[0]), int(parts[1]), \
                          int(parts[2]), int(parts[3]), ''
                elif size == 5:  # (x1, y1, x2, y2, label):
                    yield int(parts[0]), int(parts[1]), \
                          int(parts[2]), int(parts[3]), str(parts[4])
                else:
                    yield ''
