
import em
import emviz.models
import numpy as np

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
        emviz.models.TableModel.__init__(self, *cols)
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
        # FIXME [phv] removed hasColumn method from em.Table?
        #if self._table.hasColumn < 0:
        #    raise Exception("Column '%s' does not exists in the Table!"
        #                    % colName)
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


class EmSlicesModel(emviz.models.SlicesModel):
    """ SlicesModel that can be used by the SlicesView
    """
    def __init__(self, path, data=None):
        """
        Constructs an EmSlicesModel.
        You can specify the path and/or the image numpy array
        :param path : (str) The image path.
        :param data : (numpy array) The image data
        """
        emviz.models.SlicesModel.__init__(self, data)
        if path is None and data is None:
            raise Exception("Invalid initialization params. "
                            "The image path and data can not be None.")
        self._path = path
        if data is None:
            imgio = em.ImageIO()
            imgio.open(path, em.File.READ_ONLY)
            dim = imgio.getDim()
            image = em.Image()

            if dim.z > 1:
                raise Exception("No valid image type: Volume.")
            self._data = []
            self._dim = dim.x, dim.y, dim.n
            for i in range(1, dim.n + 1):
                imgio.read(i, image)
                self._data.append(np.array(image, copy=True))
            imgio.close()

    def getLocation(self):
        """ Returns the image location(the image path). """
        return self._path

    def getImageModel(self, i):
        """ Return an ImageModel for the given slice. """
        loc = (i, self._path) if self._path else None
        return emviz.models.ImageModel(data=self.getData(i), location=loc)


class EmStackModel(emviz.models.TableModel):
    """
    The EmStackModel class provides the basic functionality for image stack.
    The following methods are wrapped directly from SlicesModel:
        - getDim
        - getData
        - getLocation
        - getImageModel
    """
    def __init__(self, **kwargs):
        """
        Constructs an EmStackModel.
        Note that you can specify the path and/or image data.
        :param kwargs:
         - slicesModel : (SlicesModel) The SlicesModel from which this
                         EmStackModel will be created.
         - col         : (emviz.models.ColumnConfig) The config for image column
                         if col is None, then 'Image' will be used.
        """
        pk = emviz.models
        emviz.models.TableModel.__init__(
            self,
            kwargs.get('col',
                       pk.ColumnConfig(name='Image',
                                       dataType=pk.TYPE_STRING,
                                       **{pk.RENDERABLE: True,
                                          pk.VISIBLE: True})))
        self._slicesModel = kwargs['slicesModel']  # mandatory

    def getDim(self):
        """
        Wrapper for internal SlicesModel
        :return: SlicesModel.getDim()
        """
        return self._slicesModel.getDim()

    def getLocation(self):
        """
        Wrapper for internal SlicesModel
        :return: SlicesModel.getLocation()
        """
        return self._slicesModel.getLocation()

    def getImageModel(self, i):
        """
        Wrapper for internal SlicesModel
        :return: SlicesModel.getImageModel()
        """
        return self._slicesModel.getImageModel(i)

    def getRowsCount(self):
        """ Return the number of rows. """
        return self._slicesModel.getDim()[2]

    def getValue(self, row, col):
        """ Return the value of the item in this row, column. """
        _, _, n = self._slicesModel.getDim()
        if not 0 <= row < n:
            raise Exception("Index should be between 0 - %d" % n - 1)
        return str(row + 1) if self._path is None else "%d@%s" % (row + 1,
                                                                  self._path)

    def getData(self, row, col=0):
        """ Return the data (array like) for the item in this row, column.
         Used by rendering of images in a given cell of the table.
        """
        return self._slicesModel.getData(row)


class EmVolumeModel(emviz.models.VolumeModel):
    """
    The EmVolumeModel class provides the basic functionality for image volume
    """
    def __init__(self, path, data=None):
        """
        Constructs an EmVolumeModel.
        :param path: (str) The volume path
        :param data: (numpy array) The volume data
        """
        self._path = path
        if data is None:
            imgio = em.ImageIO()
            imgio.open(path, em.File.READ_ONLY)
            dim = imgio.getDim()
            image = em.Image()

            if dim.z <= 1:
                raise Exception("No valid image type.")
            imgio.read(1, image)
            data = np.array(image, copy=True)
            imgio.close()

        emviz.models.VolumeModel.__init__(self, data)

    def getSlicesModel(self, axis):
        """
        Creates an SlicesModel for the given axis.
        :param axis:  (int) axis should be AXIS_X, AXIS_Y or AXIS_Z
        :return:      (SlicesModel)
        """
        sModel = emviz.models.VolumeModel.getSlicesModel(self, axis)
        if sModel is None:
            return None
        return EmStackModel(slicesModel=sModel)
