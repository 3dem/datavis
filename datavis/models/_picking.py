
import os
from collections import namedtuple

from ._constants import *
from ._table_models import TableModel, ColumnConfig


class Coordinate:
    """
    Simple class that holds values for x and y position and a optional label.
    The label can be used to group different type of coordinates within a
    Micrograph. Other attributes can be set dynamically.
    """
    def __init__(self, x, y, label="Manual", **kwargs):
        """
        Create a new Coordinate.
        :param x: The X position
        :param y: The Y position
        :param label: A label for the coordinated, by default 'Manual'
        :param kwargs: Other properties as key=value pairs
        """
        self.x = x
        self.y = y
        self.label = label
        self.set(**kwargs)

    def __str__(self):
        return "(%f, %f)" % (self.x, self.y)

    def __eq__(self, other):
        """ Equality comparison between coordinates,
        based on x, y position only.
        """
        return other and self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash((self.x, self.y))

    def set(self, **kwargs):
        """
        Set different properties of this coordinates.
        Example:
            c = Coordinate(x, y, label='Auto')
            c.set(x=1, y=100, label='None')
            # ...
            c.set(label='Auto')
        """
        for k, v in kwargs.items():
            setattr(self, k, v)


class Micrograph:
    """
    Micrograph is the base element managed by the PickerDataModel class
    (See PickerDataModel documentation).
    """
    def __init__(self, micId=None, path=None):
        self._micId = micId
        self._path = path
        # This should be accessed only from PickerModel
        self._coordinates = []

    def __len__(self):
        """ The length of the Micrograph is the number of coordinates. """
        return len(self._coordinates)

    def __contains__(self, item):
        return any(item == c for c in self)

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


class PickerDataModel(TableModel):
    """
    This class stores the basic information to the particle picking data.
    It contains a list of Micrographs and each Micrograph contains a list
    of Coordinates (x, y positions in the Micrograph).
    """
    class Result:
        """
        Simple result object (although it might be more complex in the future)
        to notify about changes in the data model after an external action
        """
        def __init__(self, currentMicChanged=False, currentCoordsChanged=False,
                     tableModelChanged=False):
            self.currentMicChanged = currentMicChanged
            self.currentCoordsChanged = currentCoordsChanged
            self.tableModelChanged = tableModelChanged

    def __init__(self, boxSize=64):
        # Allow access to micrographs both by id and by index
        self._micList = []
        self._micDict = {}
        self._boxsize = boxSize
        self._lastId = 0

        # Create a class for Coordinates Labels
        self.Label = namedtuple('Label', ['name', 'color'])
        self._labels = dict()
        self._initLabels()

        # Properties for TableModel
        self._columns = self.getColumns()
        self._tableName = ''
        self._tableNames = []

    def __len__(self):
        """ The length of the model is the number of Micrographs. """
        return len(self._micList)

    def __iter__(self):
        """ Iterate over all Micrographs in the model. """
        return iter(self._micList)

    def getMicrograph(self, micId):
        return self._micDict[micId]

    def getMicrographByIndex(self, micIndex):
        return self._micList[micIndex]

    def _initLabels(self):
        """
        Initialize the labels for this PickerModel
        """
        auto = self.Label(name="Auto", color="#0012FF")
        self._labels["Auto"] = auto
        self._labels["A"] = auto

        manual = self.Label(name="Manual", color="#1EFF00")
        self._labels["Manual"] = manual
        self._labels["M"] = manual

        default = self.Label(name="Default", color="#1EFF00")
        self._labels["Default"] = default
        self._labels["D"] = default

    def setBoxSize(self, newSizeX):
        """ Set the box size for the coordinates. """
        self._boxsize = newSizeX

    def getBoxSize(self):
        """ Return the current box size of the coordinates. """
        return self._boxsize

    def addMicrograph(self, mic):
        """ Add a new micrograph to the model.
        :param mic: (Micrograph) A Micrograph instance. If the micrograph ID is -1
        then a new ID will be assigned to the micrograph.
        :raise Raise Exception if mic is not instance of Micrograph
        """
        if not isinstance(mic, Micrograph):
            raise Exception("Invalid micrograph instance.")

        if mic.getId() is None:
            mic.setId(self.nextId())

        self._micList.append(mic)
        self._micDict[mic.getId()] = mic

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
        return self._labels.get(labelName, self._labels['D'])

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

    def getParams(self):
        """
        Return the parameters Form that can be used by the
        GUI to create widgets for each parameter. The GUI will
        then notify the model about changes in these parameters
        caused by user inputs.
        """
        return None

    def _getCoordsList(self, micId):
        """ Return the coordinates list of a given micrograph. """
        return self.getMicrograph(micId)._coordinates

    def iterCoordinates(self, micId):
        """ Iterate over the micrograph coordinates.
        This iteration can yield a subset of the total coordinates depending
        on parameters such as threshold, or associate different labels
        to the coordinates.
        """
        for coord in self._getCoordsList(micId):
            yield coord

    def addCoordinates(self, micId, coords):
        """
        Add coordinates to a given micrograph.

        :param micId: The micrograph identifier.
        :param coords: An iterable with the coordinates that will be added.

        :return: PickerModel.Result object with information about the changes
        in the model after this action. In subclasses this info might be
        more relevant.

        """
        self._getCoordsList(micId).extend(coords)
        # Only notify changes in the coordinates that are not these already added
        return self.Result(currentCoordsChanged=False)

    def removeCoordinates(self, micId, coords):
        """
        Remove coordinate from a given micrograph.
        :returns PickerModel.Result object with information about the changes
        in the model after this action. In subclasses this info might be
        more relevant.
        """
        micCoords = self._getCoordsList(micId)
        for c in coords:
            if c in micCoords:
                micCoords.remove(c)
        # Only notify changes in the coordinates that are not these already removed
        return self.Result(currentCoordsChanged=False)

    def clearMicrograph(self, micId):
        """ Remove all coordinates of this micrograph. """
        self._getCoordsList(micId)[:] = []
        return self.Result()

    def selectMicrograph(self, newMicId):
        """
        While interacting with the GUI, usually there is a micrograph
        selected. By calling this method, the GUI notifies that the
        selected micrographs was changed. The model can respond to
        this change if necessary.
        """
        return self.Result(currentMicChanged=True,
                           currentCoordsChanged=True)

    def changeParam(self, micId, paramName, paramValue, getValuesFunc):
        """
        By calling this method, the model is notified about changes
        in one of the parameters. This method should be re-implemented
        in subclasses that want to react to changes in parameters.
        :param paramInfo: object that contains information about
            the parameters:
            - paramInfo.name: the name of the parameter
            - paramInfo.value: the value of the parameter
            - paramInfo.getValues(): method to request all
        :returns Result instance responding back the impact of the
            changes regarding to the selected micrographs, the coordinates
            and the table with overall information.
        """
        return self.Result()

    # --------------- Methods required by TableModel ---------------------------

    def _loadTable(self, tableName):
        pass

    def iterColumns(self):
        """ Return an iterator for model columns"""
        return iter(self._columns)

    def getColumnsCount(self):
        """ Return the number of columns """
        return len(self._columns)

    def getRowsCount(self):
        """ Return the number of rows """
        return len(self)  # Number of micrographs

    def getColumns(self):
        """ Return a Column list that will be used to display micrographs. """
        return [
            ColumnConfig('Micrograph', dataType=TYPE_STRING, editable=True),
            ColumnConfig('Coordinates', dataType=TYPE_INT, editable=True),
            ColumnConfig('Id', dataType=TYPE_INT, editable=True, visible=False),
        ]

    def getValue(self, row, col):
        """ Return the value of the item in this row, column. """
        mic = self.getMicrographByIndex(row)

        if col == 0:  # Name
            return 'Micrograph %02d' % mic.getId()
        elif col == 1:  # Coordinates
            return len(mic)
        elif col == 2:  # Id
            return mic.getId()
        else:
            raise Exception("Invalid column value '%s'" % col)


class PickerCmpModel(PickerDataModel):
    """ PickerModel to handle two PickerModels """
    def __init__(self, model1, model2, boxSize=64, radius=64):
        PickerDataModel.__init__(self, boxSize=boxSize)
        # format RRGGBBAA
        self._labels['a'] = self.Label(name="a", color="#00ff0055")
        self._labels['b'] = self.Label(name="b", color="#00ff00")
        self._labels['c'] = self.Label(name="c", color="#0000ff55")
        self._labels['d'] = self.Label(name="d", color="#0000ff")

        self._models = (model1, model2)
        self._radius = radius
        self._ref = dict()

    def __getitem__(self, micId):
        mic = self._micDict[micId]
        mic.clear()

        coordsA = self._models[0][micId]
        coordsB = self._models[1][micId]

        s = self._markCoordinates(coordsA,
                                  coordsB,
                                  self._radius)
        self._defaultTableModel.setValue(self._ref[micId], 3, s)
        mic.addCoordinates(coordsA)
        mic.addCoordinates(coordsB)

        return self._micDict[micId]

    def onParamChanged(self, paramName, value):
        """
         Function to be executed when a picker-param changes its value.
        :param paramName: (str) The param name.
        :param value:     The param value.

        """
        if paramName == 'radius':
            self._radius = value

    def _markCoordinates(self, listA, listB, radius):
        """
        Set the labels for the given list of Coordinates according to the
        following:
         - a) The coordinates of A and are not close to any of B
         - b) The coordinates of A and that are close to ones of B.
              (color similar to a))
         - c) Those of B that do not have close ones in A
         - d) Those of B that are close in A (color similar to c))
        :param listA: (list of Coordinate)
        :param listB: (list of Coordinate)
        :param radius: (int) Radius
        :return : (int) Number of coordinates having a) and b) conditions
        """
        c = set()
        radius *= radius

        for b in listB:
            b.set(label='c')  # case c)

        for a in listA:
            a.set(label='a')  # case a)

            for b in listB:

                d = (b.x - a.x) ** 2 + (b.y - a.y) ** 2
                if d <= radius:
                    a.set(label='b')  # case b)
                    b.set(label='d')  # case d)
                    c.add(a)
                    c.add(b)

        return len(c)

    def getColumns(self):
        """ Return a Column list that will be used to display micrographs. """
        return [
            ColumnConfig('Id', dataType=TYPE_INT, editable=True, visible=False),
            ColumnConfig('Micrograph', dataType=TYPE_STRING, editable=True),
            ColumnConfig('Coordinates', dataType=TYPE_INT, editable=True),
        ]

        if self._defaultTableModel is None:
            micTable = MicrographsTableModel([
                ColumnConfig('Micrograph', dataType=TYPE_STRING, editable=True),
                ColumnConfig('A', dataType=TYPE_INT, editable=True),
                ColumnConfig('B', dataType=TYPE_INT, editable=True),
                ColumnConfig('AnB', dataType=TYPE_INT, editable=True),
                ColumnConfig('Id', dataType=TYPE_INT, editable=True,
                             visible=False)
            ])
            m1, m2 = self._models

            for i, micId in enumerate(m1):
                mic1 = m1[micId]
                mic2 = m2[micId]

                s = self._markCoordinates(mic1, mic2, self._radius)
                micTable.appendRow([os.path.basename(mic1.getPath()), len(mic1),
                                    len(mic2), s, micId])
                self._ref[micId] = i

            self._defaultTableModel = micTable

        return self._defaultTableModel

    def getValue(self, row, col):
        """ Return the value of the item in this row, column. """
        mic = self.getMicrographByIndex(row)

        if col == 0:  # Id
            return mic.getId()
        elif col == 1:  # Name
            return os.path.basename(mic.getPath())
        elif col == 2:  # Coordinates
            return len(mic)
        else:
            raise Exception("Invalid column value '%s'" % col)


# FIXME: Check if this function is need at all and remove it from here
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
