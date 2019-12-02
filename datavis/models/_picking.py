
import os
from collections import namedtuple
from itertools import chain

from ._constants import *
from ._table_models import TableModel, ColumnConfig
from ._params import Param, Form


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
    Micrograph is the base element managed by the PickerModel class
    (See PickerModel documentation).
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


class PickerModel(TableModel):
    """ Handles information about Coordinates and Micrographs.

    The PickerModel class contains a set of micrographs, where each
    micrograph contains a set of coordinates. Coordinates are essentially
    (x, y) position and can also have a given label. Labels are created by
    the PickerModel and will be used to classify different types of
    coordinates (e.g based on quality).
    """

    class Result:
        """
        Simple result object (although it might be more complex in the future)
        to notify about changes in the data model after an external action
        """
        def __init__(self,
                     currentMicChanged=False,
                     currentCoordsChanged=False,
                     tableModelChanged=False):
            """ Create a new instance with the provided values.

            This class is used as the return of many methods from the
            PickerModel to notify back the underlying data that has changed
            after the operation.

            Args:
                currentMicChanged: True if the data of the micrograph changed.
                currentCoordsChanged: True if the coordinates of the current
                    micrograph changed
                tableModelChanged: True if the whole table with micrographs
                    info changed and should be reloaded.
            """
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

    def _getCoordsList(self, micId):
        """ Return the coordinates list of a given micrograph. """
        return self.getMicrograph(micId)._coordinates

    def _nextId(self):
        """ Generates the next id. """
        self._lastId += 1
        return self._lastId

    def _initLabels(self):
        """ Initialize the labels for this PickerModel. """
        auto = self.Label(name="Auto", color="#0012FF")
        self._labels["Auto"] = auto
        self._labels["A"] = auto

        manual = self.Label(name="Manual", color="#1EFF00")
        self._labels["Manual"] = manual
        self._labels["M"] = manual

        default = self.Label(name="Default", color="#1EFF00")
        self._labels["Default"] = default
        self._labels["D"] = default

    def getMicrograph(self, micId):
        """ Returns the micrograph with the given ID. """
        return self._micDict[micId]

    def getMicrographByIndex(self, micIndex):
        """ Return the micrograph at this given index. """
        return self._micList[micIndex]

    def createCoordinate(self, x, y, label, **kwargs):
        """
        Return a Coordinate object. This is the preferred way to create
        Coordinates objects, ensuring that the object contains all
        the additional properties related to the model.
        Subclasses should implement this method
        """
        return Coordinate(x, y, 'M', **kwargs)

    def setBoxSize(self, newSizeX):
        """ Set the box size for the coordinates. """
        self._boxsize = newSizeX

    def getBoxSize(self):
        """ Return the current box size of the coordinates. """
        return self._boxsize

    def addMicrograph(self, mic):
        """ Add a new :class:`Micrograph <datavis.models.Micrograph>`
        to the model.

        Args:
            mic: Input Micrograph to be added.
                If the micrograph ID is -1 then a new ID will be assigned to
                the micrograph.

        Raises:
            Exception if the input is not an instance of Micrograph.
        """
        if not isinstance(mic, Micrograph):
            raise Exception("Invalid micrograph instance.")

        if mic.getId() is None:
            mic.setId(self._nextId())

        self._micList.append(mic)
        self._micDict[mic.getId()] = mic

    def getLabels(self):
        """ Return the existing Coordinate's labels defined by this model. """
        return self._labels

    def getLabel(self, labelName):
        """ Returns the label with this labelName. """
        return self._labels.get(labelName, self._labels['D'])

    def getData(self, micId):
        """ Return a numpy array with this micrograph binary data.

        Args:
            micId: The micrograph ID

        Returns:
            A 2D numpy array with the micrograph data.
        """
        raise Exception('Not implemented')

    def getMicrographMask(self, micId):
        """ Return the mask that should be applied to visualise the micrograph

        Args:
            micId: The micrograph ID

        Returns:
            A 2D numpy array with the micrograph mask.
        """
        return None

    def getMicrographMaskColor(self, mic):
        """ Return the color to visualise the micrograph mask

        Args:
            micId: The micrograph ID

        Returns:
            str in ARGB html format: #AARRGGBB or QColor.
            Example: '#552200FF', QColor(r=3, g=56, b=200, a=128)
        """
        return '#552200FF'


    def getParams(self):
        """ Return a :class:`Form <datavis.models.Form>`
        instance with parameters used by the picker.

        This method will be used by that can be used by the
        GUI to create widgets for each parameter. The GUI will
        then notify the model about changes in these parameters
        caused by user inputs.
        """
        return None

    def iterCoordinates(self, micId):
        """ Iterate over the micrograph coordinates.

        This iteration can yield a subset of the total coordinates depending
        on parameters such as threshold, or associate different labels
        to the coordinates.
        """
        for coord in self._getCoordsList(micId):
            yield coord

    def addCoordinates(self, micId, coords):
        """ Add coordinates to a given micrograph.

        Args:
            micId: The micrograph identifier.
            coords: An iterable with the coordinates that will be added.

        Returns:
            :class:`Result <datavis.models.PickerModel.Result>` instance
        """
        self._getCoordsList(micId).extend(coords)
        # Only notify changes in the coordinates that are not these
        # already added
        return self.Result(currentCoordsChanged=False)

    def removeCoordinates(self, micId, coords):
        """ Remove coordinates from a given micrograph.

        Args:
            micId: The micrograph ID.
            coords: An iterable over the input coordinates.

        Returns:
            :class:`Result <datavis.models.PickerModel.Result>`
            instance.
        """
        micCoords = self._getCoordsList(micId)
        for c in coords:
            if c in micCoords:
                micCoords.remove(c)
        # Only notify changes in the coordinates that are not these
        # already removed
        return self.Result(currentCoordsChanged=False)

    def clearMicrograph(self, micId):
        """ Remove all coordinates from this micrograph.

        Returns:
            :class:`Result <datavis.models.PickerModel.Result>` instance
        """
        self._getCoordsList(micId)[:] = []
        return self.Result()

    def selectMicrograph(self, newMicId):
        """ Select a new micrograph as 'active'.

        While interacting with the GUI, usually there is a micrograph
        selected. By calling this method, the GUI notifies that the
        selected micrographs was changed. The model can respond to
        this change if necessary.

        Returns:
            :class:`Result <datavis.models.PickerModel.Result>` instance
        """
        return self.Result(currentMicChanged=True,
                           currentCoordsChanged=True)

    def changeParam(self, micId, paramName, paramValue, getValuesFunc):
        """ Notify the picker model about changes in the parameters.

        By calling this method, the model is notified about changes
        in one of the parameters. This method should be re-implemented
        in subclasses that want to react to changes in parameters.

        Args:
            micId: micrograph ID
            paramName: name of the parameter that generated the change
            paramValue: current value of the parameter
            getValuesFunc: function that will return all values as dict

        Returns:
            :class:`Result <datavis.models.PickerModel.Result>` instance

        """
        return self.Result()

    def getImageInfo(self, micId):
        """
        Return some specified info from the given image path.
        dim : Image dimensions
        ext : File extension
        data_type: Image data type

        Args:
            micId:  (int) The micrograph Id

        Returns:
             dict with info
        """
        return {}

    # --------------- Methods required by TableModel ---------------------------

    def _loadTable(self, tableName):
        pass

    def iterColumns(self):
        """ Return an iterator for model columns"""
        return iter(self._columns)

    def getColumnsCount(self):
        """ Return the number of columns for displaying the micrographs table.
        """
        return len(self._columns)

    def getRowsCount(self):
        """ Return the number of rows (i.e the number of micrographs). """
        return len(self)  # Number of micrographs

    def getColumns(self):
        """ Return a Column list that will be used to display micrographs. """
        return [
            ColumnConfig('Micrograph', dataType=TYPE_STRING, editable=False),
            ColumnConfig('Coordinates', dataType=TYPE_INT, editable=False),
            ColumnConfig('Id', dataType=TYPE_INT, editable=False, visible=False)
        ]

    def getValue(self, row, col):
        """ Return the value in this (row, column) from the micrographs table.
        """
        mic = self.getMicrographByIndex(row)

        if col == 0:  # Name
            return 'Micrograph %02d' % mic.getId()
        elif col == 1:  # Coordinates
            return len(mic)
        elif col == 2:  # Id
            return mic.getId()
        else:
            raise Exception("Invalid column value '%s'" % col)


class PickerCmpModel(PickerModel):
    """ PickerModel to handle two PickerModels """
    def __init__(self, model1, model2, boxSize=64, radius=64):
        PickerModel.__init__(self, boxSize=boxSize)
        # format RRGGBBAA
        self._labels['a'] = self.Label(name="a", color="#00ff0055")
        self._labels['b'] = self.Label(name="b", color="#00ff00")
        self._labels['c'] = self.Label(name="c", color="#0000ff55")
        self._labels['d'] = self.Label(name="d", color="#0000ff")

        self._models = (model1, model2)
        self._radius = radius
        self._union = dict()
        self.markAll()

    def __getitem__(self, micId):
        return self._models[0].getMicrograph(micId)

    def _getCoordsList(self, micId):
        """ Return the coordinates list of a given micrograph. """
        c1 = self._models[0].getMicrograph(micId)._coordinates
        c2 = self._models[1].getMicrograph(micId)._coordinates
        return chain(c1, c2)

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

    def getMicrographByIndex(self, micIndex):
        return self._models[0].getMicrographByIndex(micIndex)

    def getParams(self):
        proximityRadius = Param('proximityRadius', 'int', value=40,
                                display='slider', range=(0, 100),
                                label='Proximity radius',
                                help='Proximity radius.')

        return Form([proximityRadius])

    def changeParam(self, micId, paramName, paramValue, getValuesFunc):
        # Most cases here will modify the current coordinates
        r = self.Result(currentCoordsChanged=True, tableModelChanged=True)

        if paramName == 'proximityRadius':
            self._radius = paramValue
            self.markAll()
        else:
            r = self.Result()  # No modification

        return r

    def clearMicrograph(self, micId):
        for m in self._models:
            m.clearMicrograph(micId)

        self._union[micId] = 0
        return self.Result(currentCoordsChanged=True, tableModelChanged=True)

    def markAll(self):
        """
        Set label colors to all micrograph in the models
        """
        a, b = self._models
        for mic in a:
            micId = mic.getId()
            c = self._markCoordinates(mic._coordinates,
                                      b.getMicrograph(micId)._coordinates,
                                      self._radius)
            self._union[micId] = c

    def iterCoordinates(self, micId):
        # Re-implement this to show only these above the threshold
        # or with a different color (label)
        for coord in self._getCoordsList(micId):
            yield coord

    def getColumns(self):
        """ Return a Column list that will be used to display micrographs. """
        return [
            ColumnConfig('Micrograph', dataType=TYPE_STRING, editable=False),
            ColumnConfig('A', dataType=TYPE_INT, editable=False),
            ColumnConfig('B', dataType=TYPE_INT, editable=False),
            ColumnConfig('AnB', dataType=TYPE_INT, editable=False),
            ColumnConfig('Id', dataType=TYPE_INT, editable=False, visible=False)
        ]

    def getValue(self, row, col):
        """ Return the value of the item in this row, column. """
        mic = self.getMicrographByIndex(row)
        micId = mic.getId()

        if col == 0:  # Name
            return os.path.basename(mic.getPath())
        elif col == 1:  # 'A' coordinates
            return len(self._models[0].getMicrograph(micId))
        elif col == 2:  # 'B' coordinates
            return len(self._models[1].getMicrograph(micId))
        elif col == 3:  # 'AnB' coordinates
            return self._union.get(micId, 0)
        elif col == 4:  # 'Id'
            return mic.getId()
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
