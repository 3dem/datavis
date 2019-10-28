
from ._constants import AXIS_X, AXIS_Y, AXIS_Z
import numpy as np


class ImageModel:
    """ Base model class that represents 2D or 3D image binary data.

    This model is used by several views to display 2D images such as:
    micrographs, particles, averages or volume 2D slices. It provides
    access methods to enable visualization of the underlying data.
    """

    def __init__(self, data=None, location=None):
        """ Create a new ImageModel, optionally providing data array or location.

        Args:
            data: An initial numpy array can be provided.
            location: (index, path) tuple representing the location of the data.
        """
        self._data = self._dim = self._minmax = None
        self._location = location
        self.setData(data)

    def getDim(self):
        """ Return the dimensions of the model as a tuple:

            * (x, y)    for 2D.
            * (x, y, n) for 2D slices.
            * (x, y, z) for 3D volumes.
        """
        return self._dim

    def getMinMax(self):
        """ Return the minimum and maximum values of the data (can be None). """
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
        """ Set new underlying data.

        Args:
             data: Input 2D array-like object (e.g numpy array).
        """
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
    """ This model deals with N 2D arrays, usually a 3D volume or a stack
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
        """ Return a 2D array of the slice data.

        Args:
            i: Slice index, it should be -1 or in (0, n-1) range.
               -1 is a special case for returning the whole data array.

        Returns:
            2D array of the requested slice.
        """
        if i == -1 or self._data is None:
            return self._data

        if not 0 <= i < self._dim[2]:
            raise Exception("Index should be between 0 and %d"
                            % (self._dim[2]-1))

        return self._data[i]

    def getImageModel(self, i):
        """ Creates an :class:`ImageModel <datavis.models.ImageModel>`
        representing the slice at index i.

        Args:
            i: Slice index, it should be in (0, n-1) range.

        Returns:
            A new :class:`ImageModel <datavis.models.ImageModel>` instance
            representing the given slice.
        """
        return ImageModel(data=self.getData(i))


class VolumeModel(ImageModel):
    """ Model for 3D volume data.

    Data represents a 3D array-like data array. 2D slices can be accessed
    through 3 axis: AXIS_X, AXIS_Y or AXIS_Z
    """

    def _setDim(self):
        if self._data is not None:
            if len(self._data.shape) != 3:
                raise Exception("Data array should be three-dimensional. (%s)"
                                % str(self._data.shape))
            z, y, x = self._data.shape
            self._dim = x, y, z

    def getSlicesModel(self, axis):
        """ Creates a :class:`SlicesModel <datavis.models.SlicesModel>`
        representing the data from a given axis:

        Args:
            axis: Should be AXIS_X, AXIS_Y or AXIS_Z

        Returns:
            A new :class:`SlicesModel <datavis.models.SlicesModel>` instance.
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

    def getSliceData(self, axis, i):
        """ Return a 2D array of the slice data.

        Args:
            axis: should be AXIS_X, AXIS_Y or AXIS_Z
            i: should be in (0, axis_n -1).

        Returns:
            2D array of the requested slice in the given axis.
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

    def getSliceImageModel(self, axis, i):
        """ Return an :class:`ImageModel <datavis.models.ImageModel>` for
        the requested slice in the given axis.

        Args:
            axis: should be AXIS_X, AXIS_Y or AXIS_Z
            i: should be in (0, axis_n -1).

        Returns:
            :class:`ImageModel <datavis.models.ImageModel>` instance of the
            requested slice in the given axis.
        """
        sliceData = self.getSliceData(axis, i)
        return None if sliceData is None else ImageModel(data=sliceData)


class EmptySlicesModel(SlicesModel):
    """ Represents an empty slices model. """

    def __init__(self):
        data = np.arange(8).reshape((2, 2, 2))
        SlicesModel.__init__(self, data)


class EmptyVolumeModel(VolumeModel):
    """ Represents an empty volume model."""

    def __init__(self):
        data = np.arange(8).reshape((2, 2, 2))
        VolumeModel.__init__(self, data)
