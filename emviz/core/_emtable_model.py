
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
        raise Exception("Not implemented")


class EmStackModel(models.SlicesTableModel):
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
        models.SlicesTableModel.__init__(self, kwargs.get('slicesModel'),
                                         columnName=kwargs.get('columnName',
                                                               'Image'))
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

    def getRowsCount(self):
        if self._path is not None:
            return len(self._data)

        return models.SlicesTableModel.getRowsCount(self)

    def getData(self, row, col):
        if self._path is not None:
            return self._data[row]

        return models.SlicesTableModel.getData(self, row, col)

    def getLocation(self):
        """ Returns the image location(the image path). """
        return self._path

    def getImageModel(self, i):
        """ Return an ImageModel for the given slice. """
        loc = (i, self._path) if self._path else None
        return models.ImageModel(data=self.getData(i, 0), location=loc)


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

    # FIXME: Why the following method is re-implemented?
    # the implementation in the base class seems to work here as well

    # def getSlicesModel(self, axis):
    #     """
    #     Creates an SlicesModel for the given axis.
    #     :param axis:  (int) axis should be AXIS_X, AXIS_Y or AXIS_Z
    #     :return:      (SlicesModel)
    #     """
    #     sModel = models.VolumeModel.getSlicesModel(self, axis)
    #     if sModel is None:
    #         return None
    #     return EmStackModel(slicesModel=sModel)
