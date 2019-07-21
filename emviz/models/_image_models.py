
from ._constants import AXIS_X, AXIS_Y, AXIS_Z
import numpy as np


class ImageModel:
    """ Class required by some widgets that will query properties
    about the underlying image data.
    """

    def __init__(self, data=None, location=None):
        self._data = self._dim = self._minmax = None
        self._location = location
        self.setData(data)

    def getDim(self):
        """ Return the dimensions of the model.
            (x, y)    for 2D.
            (x, y, n) for 2D slices.
            (x, y, z) for 3D volumes.
        """
        return self._dim

    def getMinMax(self):
        """ Return the minumun and maximum value of the image data. """
        if self._data is None:
            return None

        if self._minmax is None:
            self._minmax = np.min(self._data), np.max(self._data)

        return self._minmax

    def getData(self):
        """ Return a 2D array-like object (e.g numpy array) containing
        the image data.
        """
        return self._data

    def _setDim(self):
        """ Store internal dimensions after the self._data was set. """
        self._dim = None if self._data is None else (self._data.shape[1],
                                                     self._data.shape[0])

    def setData(self, data):
        """ Setter for image data """
        self._data = data
        # Reset min-max cached value
        self._minmax = None
        self._dim = None

        if self._data is not None:
            self._setDim()

    def getLocation(self):
        """ Return the (index, path) of the image file. It can be None
        if it does contains any associated location.
        """
        return self._location


class SlicesModel(ImageModel):
    """ Model dealing with N 2D slices, usually a 3D volume or a stack
    of 2D images.
    """
    def _setDim(self):
        if self._data is not None:
            if len(self._data.shape) != 3:
                raise Exception("Data array should be three-dimensional. (%s)"
                                % str(self._data.shape))
            n, y, x = self._data.shape
            self._dim = x, y, n

    def getData(self, i=-1):
        """ Return a 2D array of the slice data. i should be in -1 or (0, n-1).
        -1 is a special case for returning the whole data array.
        """
        if i == -1 or self._data is None:
            return self._data

        if not 0 <= i < self._dim[2]:
            raise Exception("Index should be between 0 and %d"
                            % (self._dim[2]-1))

        return self._data[i]

    def getImageModel(self, i):
        """
        Creates an ImageModel for the given slice index. i should be in (1, n).
        """
        return ImageModel(data=self.getData(i))


class VolumeModel(ImageModel):
    """
    Model for volume data manipulation.
    """
    def _setDim(self):
        if self._data is not None:
            if len(self._data.shape) != 3:
                raise Exception("Data array should be three-dimensional. (%s)"
                                % str(self._data.shape))
            z, y, x = self._data.shape
            self._dim = x, y, z

    def getSlicesModel(self, axis):
        """
        Creates an SlicesModel for the given axis.
        :param axis:  (int) axis should be AXIS_X, AXIS_Y or AXIS_Z
        :return:      (SlicesModel)
        """
        if self._data is None:
            return None

        z, y, x = (0, 1, 2)
        if axis == AXIS_Z:
            data = self._data
        elif axis == AXIS_Y:
            data = np.transpose(self._data, (y, x, z))
        elif axis == AXIS_X:
            data = np.transpose(self._data, (x, z, y))
        else:
            raise Exception("Axis should be AXIS_X, AXIS_Y or AXIS_Z")

        return SlicesModel(data)

    # FIXME: I think we should go from more general to specific
    # so here I think it should be axis, i
    def getSliceData(self, i, axis):
        """ Return a 2D array of the slice data. i should be in (0, axis_n -1).
        axis should be AXIS_X, AXIS_Y or AXIS_Z
        """
        if self._data is None:
            return None

        d = self._dim[axis]
        if not 0 <= i < d:
            raise Exception("Index should be between 0 and %d" % d - 1)

        if axis == AXIS_Z:
            return self._data[i]
        elif axis == AXIS_Y:
            return self._data[:, i, :]
        elif axis == AXIS_X:
            return self._data[:, :, i]
        else:
            raise Exception("Axis should be one of: AXIS_X, AXIS_Y, AXIS_Z")

    # FIXME: I think we should go from more general to specific
    # so here I think it should be axis, i
    def getSliceImageModel(self, i, axis):
        """
        Creates an ImageModel for the given slice index and axis.
        :param i:     (int) The image index. i should be in (1, axis-n)
        :param axis:  (int) axis should be AXIS_X, AXIS_Y or AXIS_Z
        :return:      (ImageModel)
        """
        sliceData = self.getSliceData(i, axis)

        return None if sliceData is None else ImageModel(data=sliceData)


class EmptySlicesModel(SlicesModel):
    """
    The EmptySlicesModel represents an empty slices model.
    """
    def __init__(self):
        data = np.arange(8).reshape((2, 2, 2))
        SlicesModel.__init__(self, data)


class EmptyVolumeModel(VolumeModel):
    """ The EmptyVolumeModel represents an empty volume model."""
    def __init__(self):
        data = np.arange(8).reshape((2, 2, 2))
        VolumeModel.__init__(self, data)
