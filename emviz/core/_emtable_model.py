
import em
import emviz.models as models
import numpy as np

TYPE_MAP = {
    em.typeBool: models.TYPE_BOOL,
    em.typeInt8: models.TYPE_INT,
    em.typeInt16: models.TYPE_INT,
    em.typeInt32: models.TYPE_INT,
    em.typeInt64: models.TYPE_INT,
    em.typeFloat: models.TYPE_FLOAT,
    em.typeDouble: models.TYPE_FLOAT,
    em.typeString: models.TYPE_STRING
}


class EmTableModel(models.TableModel):
    """
    Implementation of TableBase with an underlying em.Table object.
    """
    def __init__(self, emTable):
        """
        Initialization of an EmTableModel
        :param emTable: Input em.Table
        :param cols: Columns configuration objects, the name of each column
            should exist in the table.
        """
        self._table = emTable
        # TODO: Check if this is needed now, or should go to QtModel
        # Map between the order and the columns Id
        self._colsMap = {i: c.getId()
                         for i, c in enumerate(emTable.iterColumns())}

    def iterColumns(self):
        for c in self._table.iterColumns():
            yield models.ColumnInfo(c.getName(), TYPE_MAP[c.getType()])

    def getColumnsCount(self):
        """ Return the number of columns. """
        return self._table.getColumnsSize()

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
        value = str(self._table[row][self._colsMap[col]])
        l = value.split('@')
        if len(l) == 2:
            index, path = int(l[0]), l[1]
            imgio = em.ImageIO()
            image = em.Image()
            imgio.open(path, em.File.READ_ONLY)
            imgio.read(index, image)
            return np.array(image, copy=False)
        return None


class EmStackModel(models.SlicesModel):
    """
    The EmStackModel class provides the basic functionality for image stack.
    The following methods are wrapped directly from SlicesModel:
        - getDim
        - getData
        - getLocation
        - getImageModel
    """
    def __init__(self, path, **kwargs):
        """
        Constructs an EmStackModel.
        Note that you can specify the path and/or SlicesModel.
        :param path:     (str) The image path
        :param kwargs:
         - slicesModel : (SlicesModel) The SlicesModel from which this
                         EmStackModel will be created.
         - columnName  : (str) The column name for image column.
                         if columnName is None, then 'Image' will be used.
        """
        models.SlicesModel.__init__(self, **kwargs)
        self._path = path
        if path is not None:
            imgio = em.ImageIO()
            imgio.open(path, em.File.READ_ONLY)
            dim = imgio.getDim()
            image = em.Image()

            if dim.z > 1:
                raise Exception("No valid image type: Volume.")
            self._data = []
            self._dim = dim.x, dim.y, dim.n
            # FIXME: Implement read on-demand, we can't have all stacks
            # in memory always
            for i in range(1, dim.n + 1):
                imgio.read(i, image)
                self._data.append(np.array(image, copy=True))
            imgio.close()

    def getLocation(self):
        """ Returns the image location(the image path). """
        return self._path

    # TODO: Maybe we will need to implement the getData in
    # the case that we don't want to store the whole stack in memory


class EmVolumeModel(models.VolumeModel):
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

        models.VolumeModel.__init__(self, data)
