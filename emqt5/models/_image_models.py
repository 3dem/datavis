

class ImageModel:
    """ Class required by some widgets that will query properties
    about the underlying image data.
    """

    def __init__(self, data=None):
        self._data = data

    def getDim(self):
        """ Return (xdim, ydim) tuple with the 2D dimensions. """
        pass

    def getData(self):
        """ Return a 2D array-like object (e.g numpy array) containing
        the image data.
        """
        return self._data

    def getLocation(self):
        """ Return the (index, path) of the image file. It can be None
        if it does contains any associated location.
        """
        return None


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
        """ Return (n, xdim, ydim) """
        return self._dim

    def getData(self, i):
        """ Return a 2D array of the slice data. i should be in (1, n). """
        if self._data is None:
            return None

        if not 0 < i <= self._dim[2]:
            raise Exception("Index should be between 1 and %d" % self._dim[2])

        return self._data[i-1]

    def getLocation(self):
        # FIXME: Check if we need this one here
        return None
