
from ._constants import *


class TableModel:
    """ Abstract base class to define the table model required by some views.
    It provides a very general interface about tabular data.
    """
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


class TableConfig:
    """
    Contains the configuration properties of each Column that will control
    how a table will be displayed by different views.
    """
    def __init__(self, *cols):
        # Store a list of ColumnConfig objects
        self._cols = cols
        self._rowIndex = True

    def addColumnConfig(self, *args, **kwargs):
        """ Add a new column config. """
        self._cols.append(ColumnConfig(*args, **kwargs))

    def hasRenderableColumn(self):
        """ Returns True if has any renderable column """
        return any(cc[RENDERABLE] for cc in self._cols)

    def isShowRowIndex(self):
        """ Returns True if the row index should be displayed.
        By default, this property is always True """
        return self._rowIndex

    def setShowRowIndex(self, s):
        self._rowIndex = s

    def getIndexes(self, propName, value):
        """ Return a indexes list having propName=value """
        return [i for i, cc in enumerate(self) if cc[propName] == value]

    def clone(self):
        tableConfig = TableConfig()
        tableConfig._cols = [colConfig.clone() for colConfig in self._cols]
        tableConfig._rowIndex = self._rowIndex
        return tableConfig

    def __iter__(self):
        """ Iterate through all the column configs. """
        return iter(self._cols)

    def __str__(self):
        s = "TableConfig columnConfigs: %d" % len(self._cols)
        for c in self._cols:
            s += '\n%s' % str(c)
        return s

    def __getitem__(self, *args, **kwargs):
        return self._cols[args[0]]

    def __len__(self):
        return len(self._cols)


class ColumnConfig:
    """
    Store properties about the visualization of a given column.
    """
    def __init__(self, name, dataType, **kwargs):
        """
        Constructor
        :param name: column name
        :param label: column label
        :param type: column type : 'Bool', 'Int', 'Float', 'Str', 'Image'
        :param kwargs:
            - visible (Bool)
            - visibleReadOnly (Bool)
            - renderable (Bool)
            - renderableReadOnly (Bool)
            - editable (Bool)
            - editableReadOnly (Bool)
            - label (Bool)
            - labelReadOnly (Bool)
        """
        self._name = name
        # FIXME: label seems duplicated here and as a property
        self._label = kwargs.get('label', name)
        self._type = dataType
        self._description = kwargs.get(DESCRIPTION, '')
        self._propertyNames = []
        self.__setProperty__(VISIBLE, True, False, **kwargs)
        self.__setProperty__(RENDERABLE, False, False, **kwargs)
        self.__setProperty__(EDITABLE, False, True, **kwargs)
        self.__setProperty__('label', False, False, **kwargs)

    def __setProperty__(self, name, default, defaultRO, **kwargs):
        """ Internal function to define a 'property' that will
        define an attribute with similar name and also a 'ReadOnly'
        flag to define when the property can be changed or not.
        :param name: the name of the property to be defined
        :param default: default value for the property
        :param defaultRO: default value for propertyReadOnly
        :param **kwargs: keyword-arguments from where to read the values
        """
        setattr(self, '__%s' % name, kwargs.get(name, default))
        self._propertyNames.append(name)
        roName = name + 'ReadOnly'
        setattr(self, '__%s' % roName, kwargs.get(roName, defaultRO))
        self._propertyNames.append(roName)

    def getName(self):
        """ Return the original name of the represented column."""
        return self._name

    def getLabel(self):
        """ Return the string that will be used to display this column. """
        return self._label

    def getType(self):
        return self._type

    def getDescrition(self):
        return self._description

    def getPropertyNames(self):
        return self._propertyNames

    def clone(self):
        copy = ColumnConfig(self._name, self._type, label=self._label,
                            description=self._description)
        for p in self._propertyNames:
            copy[p] = self[p]
        return copy

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
        s += "    desc: %s\n" % self.getDescrition()
        s += "    type: %s\n" % self.getType()
        for p in self._propertyNames:
            s += "    %s: %s\n" % (p, self[p])

        return s
