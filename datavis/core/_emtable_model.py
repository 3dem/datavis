
import os
import numpy as np

import emcore as emc
import datavis.models as models
from datavis.models import TYPE_STRING
from datavis.utils import py23

from ._image_manager import ImageManager, ImageRef
from ._emtype import EmType
from ._empath import EmPath


class EmTableModel(models.TableModel):
    """
    Implementation of TableBase with an underlying emc.Table object.
    """
    def __init__(self, tableSource, **kwargs):
        """
        Initialization of an EmTableModel
        :param tableSource: Input from where table will be retrieved,
            it can be one of the following options:
            * emc.Table: just a single table that will be used, not
                other tables will be loaded in this case
            * string: This should be the path from where to read
                the table(s). The first table will be loaded by default.
            * tuple (string, string): Here you can specify the path and
                the name of the table that you want to be loaded by
                default.
        :param **kwargs: Extra arguments
            * imageManager=value Provide an ImageManager that can be used
                to read images referenced from this table.
        """
        if isinstance(tableSource, emc.Table):
            self._table = tableSource
            self._tableIO = None
            # Define only a single table name ''
            tableName = ''
            self._path = None
            self._tableNames = [tableName]
        else:  # In this variant we will create a emc.TableIO to read data
            if isinstance(tableSource, py23.str):
                self._path, tableName = tableSource, None
            elif isinstance(tableSource, tuple):
                self._path, tableName = tableSource
            else:
                raise Exception("Invalid tableSource input '%s' (type %s)"
                                % (tableSource, type(tableSource)))
            self._tableIO = emc.TableIO()
            self._tableIO.open(self._path, emc.File.Mode.READ_ONLY)
            self._table = emc.Table()
            self._tableNames = self._tableIO.getTableNames()
            # If not tableName provided, load first table
            tableName = tableName or self._tableNames[0]

        # Create an ImageManager if none is provided
        self._imageManager = kwargs.get('imageManager', ImageManager())
        # Use a dictionary for checking the prefix path of the
        # images columns data
        self._imagePrefixes = kwargs.get('imagePrefixes', {})
        self.loadTable(tableName)

    def __del__(self):
        if self._tableIO is not None:
            self._tableIO.close()

    def __updateColsMap(self):
        # TODO: Check if this is needed now, or should go to QtModel
        # Map between the order and the columns Id
        self._colsMap = {i: c.getId()
                         for i, c in enumerate(self._table.iterColumns())}

    def _loadTable(self, tableName):
        # Only really load table if we have created the emc.TableIO
        if self._tableIO is not None:
            self._tableIO.read(tableName, self._table)
        self.__updateColsMap()

    def iterColumns(self):
        for c in self._table.iterColumns():
            yield models.ColumnInfo(c.getName(), EmType.toModel(c.getType()))

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
        imgRef = self._imageManager.getRef(value)

        if col in self._imagePrefixes:
            imgPrefix = self._imagePrefixes[col]
        else:
            imgPrefix = self._imagePrefixes.get(
                col, self._imageManager.findImagePrefix(value, self._path))
            print("Finding image prefix: ", imgPrefix)
            self._imagePrefixes[col] = imgPrefix

        if imgPrefix is not None:
            imgRef.path = os.path.join(imgPrefix, imgRef.path)

        return self._imageManager.getData(imgRef)


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
         - imageManager=value Provide an ImageManager that can be used
                to read images referenced from this table.
        """
        models.SlicesModel.__init__(self, **kwargs)
        self._path = path
        self._imageManager = kwargs.get('imageManager', ImageManager())
        x, y, z, n = self._imageManager.getDim(path)
        self._dim = x, y, n

    def getData(self, i=-1):
        """ Return a 2D array of the slice data. i should be in -1 or (0, n-1).
        -1 is a special case for returning the whole data array.
        """
        if not 0 <= i < self._dim[2]:
            raise Exception("Index should be between 0 and %d, value is %d"
                            % (self._dim[2] - 1, i))

        return self._imageManager.getData(ImageRef(self._path, i+1), copy=True)

    def getLocation(self):
        """ Returns the image location(the image path). """
        return self._path


class EmVolumeModel(models.VolumeModel):
    """
    The EmVolumeModel class provides the basic functionality for image volume
    """
    def __init__(self, path, data=None, **kwargs):
        """
        Constructs an EmVolumeModel.
        :param path: (str) The volume path
        :param data: (numpy array) The volume data
        :param kwargs:
         - imageManager=value Provide an ImageManager that can be used
                to read images referenced from this table.
        """
        self._path = path

        if data is None:
            self._imageManager = kwargs.get('imageManager', ImageManager())
            info = self._imageManager.getInfo(path)
            dim = info['dim']
            imgRef = ImageRef(path, 1)

            if dim.z <= 1:
                if dim.n == dim.x and dim.n == dim.y:
                    dim.z = dim.n
                    data = np.zeros((dim.z, dim.y, dim.x),
                                    dtype=EmType.toNumpy(info['data_type']))
                    for i in range(0, dim.z):
                        imgRef.index = i + 1
                        sdata = self._imageManager.getData(imgRef, copy=False)
                        np.copyto(data[i], sdata)
                else:
                    raise Exception("No valid image type.")
            else:
                data = self._imageManager.getData(imgRef, copy=True)

            self._dim = dim.x, dim.y, dim.z

        models.VolumeModel.__init__(self, data)


class EmListModel(models.ListModel):
    """ The EmListModel class provides the basic functionality for create models
    or read data from the list of file paths
    """
    def __init__(self, files, **kwargs):
        """
        Create an EmListModel
        :param files: (list) A list of file path
        :param kwargs:
            - imageManager : (ImageManager) The ImageManager instance that can
                             be used to read images referenced from this list
            - imagePrefixes: (list) The list of image prefixes
        """
        self._files = list(files)
        self._imageManager = kwargs.get('imageManager') or ImageManager()
        self._imagePrefixes = kwargs.get('imagePrefixes') or list()
        self._columnName = kwargs.get('columnName', 'Path')

        self._tableName = ''
        self._tableNames = [self._tableName]

    def iterColumns(self):
        yield models.ColumnInfo(self._columnName, EmType.toModel(TYPE_STRING))

    def getRowsCount(self):
        """ Return the number of rows. """
        return len(self._files)

    def getValue(self, row, col):
        """ Return the value of the item in this row, column. """
        return self._files[row]

    def getData(self, row, col=0):
        """ Return the data (array like) for the item in this row, column.
         Used by rendering of images in a given cell of the table.
        """
        value = str(self._files[row])
        imgRef = self._imageManager.getRef(value)

        # FIXME[phv] need refine the image prefixes
        if self._imagePrefixes:
            imgPrefix = self._imagePrefixes[0]
        else:
            imgPrefix = self._imageManager.findImagePrefix(value, '')
            print("Finding image prefix: ", imgPrefix)
            self._imagePrefixes.append(imgPrefix)

        if imgPrefix is not None:
            imgRef.path = os.path.join(imgPrefix, imgRef.path)

        return self._imageManager.getData(imgRef)

    def getModel(self, row):
        """ Return the model for the given row """
        from ._models_factory import ModelsFactory
        path = self.getValue(row, 0)
        if EmPath.isImage(path):
            return models.ImageModel(self.getData(row))
        elif EmPath.isVolume(path):
            return ModelsFactory.createVolumeModel(path)
