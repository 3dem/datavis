
from collections import OrderedDict

from ._constants import *


class ColumnInfo:
    """ Basic information about a column: name and type. """
    def __init__(self, name, dataType=TYPE_STRING):
        """ Create a new instance of a ColumnInfo

        Args:
            name: The name of the column.
            dataType: The type of the column
        """
        self._name = name
        self._type = dataType

    def getName(self):
        """ Return the original name of the represented column."""
        return self._name

    def getType(self):
        return self._type


class ColumnConfig(ColumnInfo):
    """ Extend :class:`ColumnInfo <datavis.models.ColumnInfo>` class to store
    properties about the visualization of a given column.
    """
    def __init__(self, name, dataType, **kwargs):
        """ Create a new instance.

        Args:
            name: The column name.
            label: The column label
            type: column type : 'Bool', 'Int', 'Float', 'Str', 'Image'

        Keyword Args:
            label: Label that will be display as this column header.
            description: More textual information about this column.
            visible: If the columns will be shown or not.
            visibleReadOnly: If 'visible' property can be changed.
            renderable: If this columns has data that can be rendered.
            renderableReadOnly: If renderization can be turn on/off.
            editable: If the values in this columns can be edited.
            editableReadOnly: Turn on/off edition of this column.
        """
        ColumnInfo.__init__(self, name, dataType)
        self._label = kwargs.get('label', name)
        self._description = kwargs.get(DESCRIPTION, '')
        self._propertyNames = []
        self._labels = kwargs.get(LABELS) or []
        self.__setProperty__(VISIBLE, True, False, **kwargs)
        self.__setProperty__(RENDERABLE, False, False, **kwargs)
        self.__setProperty__(EDITABLE, False, True, **kwargs)

    def __setProperty__(self, name, default, defaultRO, **kwargs):
        """ Internal function to define a 'property' that will
        define an attribute with similar name and also a 'ReadOnly'
        flag to define when the property can be changed or not.

        Args:
            name: the name of the property to be defined
            default: default value for the property
            defaultRO: default value for propertyReadOnly

        Keyword Args:
            keyword-arguments from where to read the values
        """
        setattr(self, '__%s' % name, kwargs.get(name, default))
        self._propertyNames.append(name)
        roName = name + 'ReadOnly'
        setattr(self, '__%s' % roName, kwargs.get(roName, defaultRO))
        self._propertyNames.append(roName)

    def getLabel(self):
        """ Return the string that will be used to display this column. """
        return self._label

    def getDescription(self):
        """ Return the description of this column. """
        return self._description

    def getPropertyNames(self):
        return self._propertyNames

    def config(self, **props):
        """ Configure the attributes from the provided properties key=value. """
        for k, v in props.items():
            self[k] = v

    def check(self, **props):
        """ Return True if this columns have these properties values. """
        return all(self[k] == v for k, v in props.items())

    def clone(self):
        """ Return a new instance with the same values of this one. """
        copy = ColumnConfig(self._name, self._type, label=self._label,
                            description=self._description)
        for p in self._propertyNames:
            copy[p] = self[p]
        return copy

    def setLabels(self, labels):
        """ Sets the column labels """
        self._labels = labels

    def getLabels(self):
        """ Returns the column labels """
        return self._labels

    def __getitem__(self, propertyName):
        """ Return the value of a given property.
        If the property does not exits, an Exception is raised.
        """
        if propertyName not in self._propertyNames:
            raise Exception("Invalid property name: %s" % propertyName)

        return getattr(self, '__%s' % propertyName)

    def __setitem__(self, propertyName, value):
        """ Return the value of a given property.
        If the property does not exits, an Exception is raised.
        """
        if propertyName not in self._propertyNames:
            raise Exception("Invalid property name: %s" % propertyName)
        return setattr(self, '__%s' % propertyName, value)

    def __str__(self):
        """ A readable representation. """
        s = "ColumnConfig: name = %s\n" % self.getName()
        s += "   label: %s\n" % self.getLabel()
        s += "    desc: %s\n" % self.getDescription()
        s += "    type: %s\n" % self.getType()
        for p in self._propertyNames:
            s += "    %s: %s\n" % (p, self[p])

        return s


class TableModel:
    """ Abstract base class to define the table model required by some views.

    It provides a very general interface about tabular data and how it will
    be displayed. The TableModel class will be able to handle data sources
    with more than one table. The method getTableNames will return the available
    tables. Then usually the TableModel will have only one table active (or
    loaded), from where the information will be retrieved. The method loadTable
    will allow to select which is currently loaded table.
    """
    # ------ Abstract methods that should be implemented in subclasses ---------
    def getTableNames(self):
        """ Returns all available table names from the data source. """
        # Let's assume a self._tableNames property will be defined in subclasses
        # or this method will be overwritten
        return self._tableNames

    def getTableName(self):
        """ Returns the name of the table currently loaded. """
        return self._tableName

    def loadTable(self, tableName):
        """ Load the table with the given name.

        This method should not be overridden in sub-classes, instead
        _loadTable should be re-implemented.

        Raises:
            An exception if there is not table with the provided name.
        """
        if tableName not in self.getTableNames():
            raise Exception("Missing table '%s' in this data model. "
                            % tableName)
        self._tableName = tableName

        return self._loadTable(tableName)

    def _loadTable(self, tableName):
        """ Internal method that should be overwritten in subclasses to load
        the current active table.
        """
        raise Exception("Not implemented")

    def iterColumns(self):
        """ Iterated over the current ColumnInfo's of the model. """
        raise Exception("Not implemented")

    def getColumnsCount(self):
        """ Return the number of columns. """
        raise Exception("Not implemented")

    def getRowsCount(self):
        """ Return the number of rows. """
        raise Exception("Not implemented")

    def getValue(self, row, col):
        """ Return the value of the item in this row, column. """
        raise Exception("Not implemented")

    def getData(self, row, col):
        """ Return the data (array like) for the item in this row, column.
        Used by rendering of images in a given cell of the table.
        """
        raise Exception("Not implemented")

    def createDefaultConfig(self):
        """ Create the default TableConfig based on the columns on this table.
        """
        cols = [ColumnConfig(c.getName(), c.getType())
                for c in self.iterColumns()]
        return TableConfig(*cols)


class SlicesTableModel(TableModel):
    """ Simple table model based on the data from a given SlicesModel.
    """
    def __init__(self, slicesModel, columnName):
        self._slicesModel = slicesModel
        self._columnName = columnName

    def getTableNames(self):
        return ['1']  # Just name it '1' the only available table

    def getTableName(self):
        return '1'

    def iterColumns(self):
        yield ColumnInfo(self._columnName)

    def getColumnsCount(self):
        return 1

    def getRowsCount(self):
        return self._slicesModel.getDim()[2]

    def getValue(self, row, col):
        return row + 1

    def getData(self, row, col):
        return self._slicesModel.getData(row)

    def createDefaultConfig(self):
        """ Reimplement this method to make the only column renderable.
        """
        cols = [ColumnConfig(c.getName(), c.getType(), renderable=True)
                for c in self.iterColumns()]
        return TableConfig(*cols)

    def getMinMax(self):
        return self._slicesModel.getMinMax()

    def getDim(self):
        """ Return the image dimensions """
        x, y, _ = self._slicesModel.getDim()
        return x, y


class ListModel(TableModel):
    """ Abstract base class to define the list model required by some views."""
    def getColumnsCount(self):
        return 1

# ------ Abstract methods that should be implemented in subclasses ---------
    def getModel(self, row):
        """ Return the model for the given row """
        raise Exception("Not implemented")


class EmptyTableModel(TableModel):
    """
    The EmptyModel represents an empty table model.
    """
    def iterColumns(self):
        return iter(())

    def getColumnsCount(self):
        return 0

    def getRowsCount(self):
        return 0

    def getValue(self, row, col):
        """ Return the value of the item in this row, column. """
        return 0

    def getData(self, row, col):
        return None

    def getTableName(self):
        return ''

    def getTableNames(self):
        return []

    def getMinMax(self):
        return 0, 0

    def getDim(self):
        return 0, 0


class TableConfig:
    """ Contains visualization properties of the table's columns.
    """
    def __init__(self, *cols):
        # Store a list of ColumnConfig objects
        self._cols = cols or []

    def __str__(self):
        s = "TableConfig columnConfigs: %d" % len(self._cols)
        for c in self._cols:
            s += '\n%s' % str(c)
        return s

    def __getitem__(self, item):
        return self._cols[item]

    def addColumnConfig(self, columnConfig):
        """ Add a new ColumnConfig to the list. """
        self._cols.append(columnConfig)

    def hasColumnConfig(self, **props):
        """ Returns True if has any there is any column with these properties.

        Example to check if there is a column renderable::

            tableConfig.hasColumnConfig(renderable=True)
        """
        return any(c.check(**props) for c in self._cols)

    def getColumnConfig(self, col):
        """
        Returns the corresponding ColumnConfig for the given column
        :param col: (int) The column index
        """
        return self._cols[col] if 0 <= col < len(self._cols) else None

    def getColumnsCount(self, **props):
        """ Return the number of columns that have given properties. """
        return len(list(self.iterColumns(**props)))

    def iterColumns(self, **props):
        return iter((i, c) for i, c in enumerate(self._cols)
                    if c.check(**props))


class SimpleTableModel(TableModel):
    """ Implementation of TableModel using list for store data """
    def __init__(self, columnsInfo):
        """
        Create an SimpleTableModel object.
        :param columnsInfo: (list of ColumnInfo) The list of columns info
        """
        self._tableName = 'noname'
        self._columnsInfo = columnsInfo or []
        self._columns = OrderedDict()
        for i, info in enumerate(self._columnsInfo):
            self._columns[i] = []

    def getTableNames(self):
        return [self._tableName]

    def getTableName(self):
        return self._tableName

    def _loadTable(self, tableName):
        return None

    def iterColumns(self):
        """ Generate a ColumnInfo iterator over the columns of the model. """
        return iter(self._columnsInfo)

    def getColumnsCount(self):
        """ Return the number of columns. """
        return len(self._columnsInfo)

    def getRowsCount(self):
        """ Return the number of rows. """
        return len(self._columns[0]) if self._columns else 0

    def getValue(self, row, col):
        """ Return the value of the item in this row, column. """
        return self._columns[col][row]

    def getData(self, row, col):
        """ Return the data (array like) for the item in this row, column.
         Used by rendering of images in a given cell of the table.
        """
        raise Exception("Not implemented")

    def addRow(self, row):
        """
        Add a row to the end of the model
        :param row: (list of values)
        """
        if len(row) == len(self._columnsInfo):
            for i, col in self._columns.items():
                col.append(row[i])
