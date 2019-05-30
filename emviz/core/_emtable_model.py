
import em
import emviz.models

TYPE_MAP = {
    em.typeBool: emviz.models.TYPE_BOOL,
    em.typeInt8: emviz.models.TYPE_INT,
    em.typeInt16: emviz.models.TYPE_INT,
    em.typeInt32: emviz.models.TYPE_INT,
    em.typeInt64: emviz.models.TYPE_INT,
    em.typeFloat: emviz.models.TYPE_FLOAT,
    em.typeDouble: emviz.models.TYPE_FLOAT,
    em.typeString: emviz.models.TYPE_STRING
}


class EmTableModel(emviz.models.TableModel):
    """
    Implementation of TableBase with an underlying em.Table object.
    """
    def __init__(self, emTable, *cols):
        """
        Initialization of an EmTableModel
        :param emTable: Input em.Table
        :param cols: Columns configuration objects, the name of each column
            should exist in the table.
        """
        # initialize base class with empty columns
        emviz.models.TableModel.__init__(self)
        self._table = emTable
        self._colsMap = {}  # Map between the order and the columns Id

        if cols:
            for c in cols:
                self.addColumn(c)  # To validate each column
        else:
            self._createConfigFromTable()

    def _createConfigFromTable(self):
        """ Create the columns config from the input table. """
        # TODO: Implement a binding for a proper columns iterator
        t = self._table
        for i in range(1, t.getColumnsSize() + 1):
            col = t.getColumn(i)
            cc = emviz.models.ColumnConfig(
                col.getName(), dataType=TYPE_MAP.get(col.getType()),
                editable=False, renderable=False)
            self.addColumn(cc)

    def addColumn(self, cc):
        """ Add a new ColumnConfig to the list. """
        colName = cc.getName()
        if not self._table.hasColumn(colName):
            raise Exception("Column '%s' does not exists in the Table!"
                            % colName)
        # Register the map between order and column id in the table
        self._colsMap[len(self._cols)] = self._table.getColumn(colName).getId()
        self._cols.append(cc)

    def getRowsCount(self):
        """ Return the number of rows. """
        return self._table.getSize()

    def getValue(self, row, col):
        """ Return the value of the item in this row, column. """
        return self._table[row][self._colsMap[col]]

    def getData(self, row, col):
        """ Return the data (array like) for the item in this row, column.
         Used by rendering of images in a given cell of the table.
        """
        raise Exception("Not implemented")

