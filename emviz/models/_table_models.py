
from ._constants import *


class TableModel:
    """ Abstract base class to define the table model required by some views.
    It provides a very general interface about tabular data and how it will
    be displayed.
    """
    def __init__(self, *cols):
        # Store a list of ColumnConfig objects
        self._cols = cols

    def addColumn(self, columnConfig):
        """ Add a new ColumnConfig to the list. """
        self._cols.append(columnConfig)

    def hasColumn(self, **props):
        """ Returns True if has any there is any column with these properties.
        Example to check if there is a column renderable:
            hasColumn(renderable=True)
        """
        return any(c.check(props) for c in self._cols)

    def getColumn(self, col):
        return self._cols[col] if 0 <= col < len(self._cols) else None

    def getColumnsCount(self, **props):
        """ Return the number of columns that have given properties. """
        raise len(self.iterColumns(**props))

    def iterColumns(self, **props):
        return iter((i, c) for i, c in enumerate(self._cols)
                    if c.check(**props))

    # TODO: Check how this behave with subclasses
    def clone(self):
        tableConfig = TableModel()
        tableConfig._cols = [colConfig.clone() for colConfig in self._cols]
        tableConfig._rowIndex = self._rowIndex
        return tableConfig

    # ------ Abstract methods that should be implemented in subclasses ----------

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

    def __str__(self):
        s = "TableModel columnConfigs: %d" % len(self._cols)
        for c in self._cols:
            s += '\n%s' % str(c)
        return s


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
        self._label = kwargs.get('label', name)
        self._type = dataType
        self._description = kwargs.get(DESCRIPTION, '')
        self._propertyNames = []
        self.__setProperty__(VISIBLE, True, False, **kwargs)
        self.__setProperty__(RENDERABLE, False, False, **kwargs)
        self.__setProperty__(EDITABLE, False, True, **kwargs)

        # FIXME: label seems duplicated here and as a property
        #self.__setProperty__('label', False, False, **kwargs)

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

    def config(self, **props):
        """ Configure with the provided properties key=value. """
        for k, v in props.items():
            self[k] = v

    def check(self, **props):
        """ Return True if this columns have these properties values. """
        return all(self[k] == v for k, v in props.items())

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
