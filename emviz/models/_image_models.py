
from ._constants import AXIS_X, AXIS_Y, AXIS_Z
import numpy as np


class ImageModel:
    """ Class required by some widgets that will query properties
    about the underlying image data.
    """

    def __init__(self, data=None, location=None):
        self._data = data
        self._location = location

    def getDim(self):
        """ Return (xdim, ydim) tuple with the 2D dimensions. """

        if self._data is not None:
            return self._data.shape[1], self._data.shape[0]
        return None

    def getData(self):
        """ Return a 2D array-like object (e.g numpy array) containing
        the image data.
        """
        return self._data

    def setData(self, data):
        """ Setter for image data """
        self._data = data

    def getLocation(self):
        """ Return the (index, path) of the image file. It can be None
        if it does contains any associated location.
        """
        return self._location


class SlicesModel:
    """ Model dealing with N 2D slices, usually a 3D volume or a stack
    of 2D images.
    """

    def __init__(self, data=None):
        self._data = data
        self._dim = None

        if data is not None:
            if len(self._data.shape) != 3:
                raise Exception("Data array should be three-dimensional. (%s)"
                                % str(self._data.shape))
            n, y, x = self._data.shape
            self._dim = x, y, n

    def getDim(self):
        """ Return (xdim, ydim, n) """
        return self._dim

    def getData(self, i):
        """ Return a 2D array of the slice data. i should be in (0, n-1). """
        if self._data is None:
            return None

        if not 0 <= i < self._dim[2]:
            raise Exception("Index should be between 0 and %d" % self._dim[2]-1)

        return self._data[i]

    def getLocation(self):
        # FIXME: Check if we need this one here
        return None

    def getImageModel(self, i):
        """
        Creates an ImageModel for the given slice index. i should be in (1, n).
        """
        return ImageModel(data=self.getData(i))


class VolumeModel:
    """
    Model for volume data manipulation.
    """
    def __init__(self, data=None):
        self._data = data
        self._dim = None

        if data is not None:
            if len(self._data.shape) != 3:
                raise Exception("Data array should be three-dimensional. (%s)"
                                % str(self._data.shape))
            z, y, x = self._data.shape
            self._dim = x, y, z

    def getDim(self):
        """ Return (xdim, ydim, zdim) """
        return self._dim

    def getLocation(self):
        # FIXME: Check if we need this one here
        return None

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

    def getSliceData(self, i, axis):
        """ Return a 2D array of the slice data. i should be in (0, axis_n -1).
        axis should be AXIS_X, AXIS_Y or AXIS_Z
        """
        if self._data is None:
            return None

        d = self._dim[axis]
        if not 0 <= i < d:
            raise Exception(
                "Index should be between 0 and %d" % d - 1)

        if axis == AXIS_Z:
            return self._data[i]
        elif axis == AXIS_Y:
            return self._data[:, i, :]
        elif axis == AXIS_X:
            return self._data[:, :, i]
        else:
            raise Exception("Axis should be one of: AXIS_X, AXIS_Y, AXIS_Z")

    def getSliceImageModel(self, i, axis):
        """
        Creates an ImageModel for the given slice index and axis.
        :param i:     (int) The image index. i should be in (1, axis-n)
        :param axis:  (int) axis should be AXIS_X, AXIS_Y or AXIS_Z
        :return:      (ImageModel)
        """
        if self._data is None:
            return None

        return ImageModel(data=self.getSliceData(i, axis))


class EmptySlicesModel(SlicesModel):
    """
    The EmptySlicesModel represents an empty slices model.
    """
    def __init__(self):
        data = np.arange(1).reshape((1, 1, 1))
        SlicesModel.__init__(self, data)


class EmptyVolumeModel(VolumeModel):
    """ The EmptyVolumeModel represents an empty volume model."""
    def __init__(self):
        data = np.arange(1).reshape((1, 1, 1))
        VolumeModel.__init__(self, data)
