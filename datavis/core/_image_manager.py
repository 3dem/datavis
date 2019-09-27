#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import numpy as np
import scipy.ndimage as ndimage

import emcore as emc
from datavis.utils import py23
from ._empath import EmPath
from ._emtype import EmType

X_AXIS = 0
Y_AXIS = 1
Z_AXIS = 2


class ImageManager:
    """
    The image manager for centralize read/manage image operations.
    Contains a internal image cache for loaded image access and thumbnails.
    """
    def __init__(self, maxCacheSize=100, maxOpenFiles=10):
        self._imgData = dict()
        # Internally convert from Mb to bytes (default 100 Mb)
        self._maxCacheSize = maxCacheSize * 1024 * 1024
        self._maxOpenFiles = maxOpenFiles

        # FIXME: We can have many open ImageFile (until maxOpenFiles)
        # to prevent opening many times the same file
        self._imgIO = emc.ImageFile()
        self._img = emc.Image()
        self._lastOpenedFile = None

        # FIXME: Control the max size of the Cache (no limited now)
        # TODO: Maybe check LRUCache implementation here:
        # https://www.kunxi.org/2014/05/lru-cache-in-python/
        self._imageCache = {}

        # Just for debugging purposes
        self._readCount = 0
        self._cacheSize = 0

    # TODO: Review if it is better to use strings for indexes rather than tuple
    @classmethod
    def _getId(cls, imageRef):
        """ Create a unique image id for the given image reference. """
        return '%d@%s' % (imageRef.index, imageRef.path)

    @classmethod
    def findImagePrefix(cls, imageSource, rootPath):
        """
        Find the prefix path from which the imagePath value is accessible.
        A common use case is when we have a text file pointing to image paths.
        In such cases, sometimes the image path value is relative to the text
        file path (used as the rootPath here), or they are relative to a
        parent folder of the text file.

        :imagePath (str) image path value that should be searched for.
            The imagePath value should contain only the path and not other
            characters (e.g @)
        :rootPath (str) another location from which to check if the imagePath
            is valid.
        :returns The prefix that should be added to imagePath to be able to
            access the imagePath file. If it is None, it means that no prefix
            was found from where the imagePath exists. It should be noted
            that empty prefix means that imagePath already exists and
            there is no need to prepend any value.
        """
        imgRef = cls.getRef(imageSource)

        if os.path.exists(imgRef.path):
            return ''  # There is no need for any prefix

        if os.path.isdir(rootPath):
            searchPath = rootPath
        else:
            searchPath = os.path.dirname(rootPath)

        while searchPath and searchPath != '/':
            if os.path.exists(os.path.join(searchPath, imgRef.path)):
                return searchPath
            searchPath = os.path.dirname(searchPath)

        return None

    @classmethod
    def getRef(cls, imgSource):
        """ Return a ImageRef, either because imgSource is one,
        or parsing it from path. """
        if isinstance(imgSource, ImageRef):
            return imgSource

        if isinstance(imgSource, py23.str):
            return ImageRef.parsePath(imgSource)

        raise Exception('Can not get ImageRef from type %s' % type(imgSource))

    def _openRO(self, imgSource):
        """ Open image source as read-only.
        Return the imageRef and the imageIO.
        """
        imgRef = self.getRef(imgSource)
        # Let's keep open the file if possible, so we don't need
        # to re-open if in the next use it is the same file
        if self._lastOpenedFile != imgRef.path:
            self._imgIO.close()
            self._imgIO.open(imgRef.path, emc.File.READ_ONLY)
            self._lastOpenedFile = imgRef.path
        return imgRef, self._imgIO

    def getImage(self, imgSource, copy=False):
        """ Retrieve the image (from cache or from file) from the
        given imageSource.
        :param imgSource: Either ImageRef or path
        :param copy: If True, a copy of the image will be returned.
            If False, a reference to the internal buffer image will
            be returned. The internal image can be modified in further
            call to other methods from the ImageManager.
        """
        imgRef = self.getRef(imgSource)
        imgId = self._getId(imgRef)
        imgOut = self._imageCache.get(imgId, None)
        if imgOut is None:
            imgRef, imgIO = self._openRO(imgSource)
            # Create a new image if a copy is requested
            # TODO: Review this when the cache is implemented
            imgOut = emc.Image()
            self._readCount += 1
            imgIO.read(imgRef.index, imgOut)
            self._imageCache[imgId] = imgOut
            self._cacheSize += imgOut.getDataSize()
            if copy:
                imgOut = emc.Image(imgOut)
        return imgOut

    def getData(self, imgSource, copy=False):
        """ Similar to getImage, but return a numpy array instead. """
        img = self.getImage(imgSource, copy=False)
        return np.array(img, copy=copy, dtype=EmType.toNumpy(img.getType()))

    def getDim(self, imgSource):
        """ Shortcut method to return the dimensions of the given
        image source (x, y, z, n) """
        imgRef, imgIO = self._openRO(imgSource)
        dim = imgIO.getDim()
        return dim.x, dim.y, dim.z, dim.n

    def getInfo(self, imgSource):
        """
        Return some specified info from the given image path.
        dim : Image dimensions
        ext : File extension
        data_type: Image data type
        """
        imgRef, imgIO = self._openRO(imgSource)
        info = {
            'dim': imgIO.getDim(),
            'ext': EmPath.getExt(imgRef.path),
            'data_type': imgIO.getType()
        }
        return info


class VolImageManager(ImageManager):
    """ ImageManager for Volume images """
    def __init__(self, volData):
        self._volData = volData

    def addImage(self, imgRef, imgSize=None):
        return self.__createThumb(imgRef, imgSize=imgSize)

    def __createThumb(self, imgRef, **kwargs):
        """
        Return the thumbnail created for the specified image reference.
        Rescale the original image according to the param imageSize=(w, h).
        If imageSize=None then return the original image data
        """
        imgSize = kwargs.get('imgSize')

        if imgRef.axis == X_AXIS:
            array = self._volData[:, :, imgRef.index]
        elif imgRef.axis == Y_AXIS:
            array = self._volData[:, imgRef.index, :]
        else:  # Z
            array = self._volData[imgRef.index, :, :]

        if imgSize is None:
            return array

        # preserve aspect ratio
        x, y = array.shape[0], array.shape[1]
        if x > imgSize[0]:
            y = int(max(y * imgSize[0] / x, 1))
            x = int(imgSize[0])
        if y > imgSize[1]:
            x = int(max(x * imgSize[1] / y, 1))
            y = int(imgSize[1])

        if x >= array.shape[0] and y >= array.shape[1]:
            return array

        return ndimage.zoom(array, x / float(array.shape[0]), order=1)


class ImageRef:
    """
    The ImageRef class is used to describe the referenced image in a stack
    or volume. For performance reasons, the access to the member variables
    is direct.
    """
    SINGLE = 1
    STACK = 2
    VOLUME = 4

    def __init__(self, path=None, index=0, slice=0):
        """
        Constructor:
        path (str): the image path
        index (int): the image index in the stack
        volumeIndex (int): volume index in the volume stack
        axis (int): the axis
        axis = 0: X
        axis = 1: Y
        axis = 2: Z
        axis = -1: Undefined
        """
        self.path = path
        self.index = index
        self.slice = slice
        self.imageType = ImageRef.SINGLE

    @classmethod
    def parsePath(cls, path):
        """ Parse the path to return a ImageRef instance.
        """
        parts = path.split('@')
        n = len(parts)
        imgRef = ImageRef()

        if n == 1:
            imgRef.path = path
        elif n == 2:
            imgRef.path, imgRef.index = parts[1], int(parts[0])
        elif n == 3:
            imgRef.path, imgRef.index = parts[2], int(parts[1])
            imgRef.slice = int(parts[0])
        else:
            raise Exception("Invalid number of @ in the image path: %s" % path)

        return imgRef

