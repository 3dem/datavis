#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import traceback
import sys

from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

from emqt5.utils.functions import EmPath

import em

import numpy as np
import scipy.ndimage as ndimage

X_AXIS = 0
Y_AXIS = 1
Z_AXIS = 2


class ImageManager:
    """
    The image manager for centralize read/manage image operations. Contains a internal
    image cache for loaded image access and thumbnails.
    """
    DATA_TYPE_MAP = {
        em.typeInt8: np.uint8,
        em.typeUInt8: np.uint8,
        em.typeInt16: np.uint16,
        em.typeUInt16: np.uint16,
        em.typeInt32: np.uint32,
        em.typeUInt32: np.uint32,
        em.typeInt64: np.uint64,
        em.typeUInt64: np.uint64
    }  # FIXME [hv] the others?

    def __init__(self, cacheSize=50):
        self._imgData = dict()
        self._cacheSize = cacheSize

    def __createThumb(self, imgRef, **kwargs):
        """
        Return the thumbnail created for the specified image reference.
        Rescale the original image according to the param imageSize=(w, h).
        If imageSize=None then return the original image data
        """
        imgSize = kwargs.get('imgSize')
        if EmPath.isStandardImage(imgRef.path):
            pixmap = QPixmap(imgRef.path)
            if imgSize is None:
                return pixmap
            height = int(pixmap.height() * imgSize[1] / 100)
            return pixmap.scaledToHeight(height, Qt.SmoothTransformation)

        else:
            try:
                isStack = imgRef.imageType & ImageRef.STACK == ImageRef.STACK
                isVolume = imgRef.imageType & ImageRef.VOLUME == ImageRef.VOLUME

                if isVolume:
                    index = 1 if not isStack else imgRef.volumeIndex
                else:
                    index = imgRef.index

                img = self.readImage(imgRef.path, index)
            except Exception as ex:
                print(ex)
                return None
            array = self.getNumPyArray(img)

            if isVolume:
                if imgRef.axis == X_AXIS:
                    array = array[:, :, imgRef.index]
                elif imgRef.axis == Y_AXIS:
                    array = array[:, imgRef.index, :]
                elif imgRef.axis == Z_AXIS:
                    array = array[imgRef.index, :, :]

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

        return None

    def getImage(self, imgId):
        """ Return the image data for the given image id """
        return self._imgData.get(imgId)

    def createImageId(self, imageRef, imgSize=None):
        """ Create a unique image id for the given image reference. """
        if imageRef.imageType & ImageRef.SINGLE == ImageRef.SINGLE:
            imgId = imageRef.path
        elif imageRef.imageType & ImageRef.STACK == ImageRef.STACK:
            if imageRef.imageType & ImageRef.VOLUME == ImageRef.VOLUME:
                # index@axis@volIndex@img_path for image in volume stack
                imgId = '%d@%d@%d@%s' % (imageRef.index, imageRef.axis,
                                         imageRef.volumeIndex, imageRef.path)
            else:
                # index@img_path for image in stack
                imgId = '%d@%s' % (imageRef.index, imageRef.path)
        else:
            # index@axis@img_path for image in volume
            imgId = '%d@%d@%s' % (imageRef.index, imageRef.axis, imageRef.path)
        return str(imgSize) + imgId if imgSize is not None else imgId

    def addImage(self, imgRef, imgSize=None):
        """
        Adds an image data to the internal image cache.
        If imgSize is specified, then store the width x height thumbnail
        path: image path
        imgSize: (width, height) or None
        TODO: Use an ID in the future, now we use the image path
        """
        imgId = self.createImageId(imgRef, imgSize)
        ret = self._imgData.get(imgId)
        if ret is None:
            try:
                ret = self.__createThumb(imgRef, imgSize=imgSize)
                if len(self._imgData) == self._cacheSize:
                    self._imgData.popitem()
                self._imgData[imgId] = ret
            except Exception as ex:
                print(ex)
                raise ex
            except RuntimeError as ex:
                print(ex)
                raise ex
        return ret

    @classmethod
    def findImage(cls, relativePath, root=None):
        """
        Find the image path relative to the given root. Return the absolute
        image path.
        """
        if os.path.exists(relativePath):
            return relativePath
        if root is None:
            root = os.path.curdir

        ret = os.path.join(root, relativePath)

        if not os.path.exists(ret):
            ret = None

        return ret

    @classmethod
    def readImage(cls, path, index=1):
        """ Read an image from the given path and return the em.Image object """
        if not os.path.exists(path):
            raise Exception("Path does not exists: %s" % path)

        image = em.Image()
        image.read(em.ImageLocation(path, index))
        return image

    @classmethod
    def getDim(cls, path):
        """ Shortcut method to return the dimensions of the given
        image path. """
        imageIO = em.ImageIO()
        imageIO.open(path, em.File.Mode.READ_ONLY)
        dim = imageIO.getDim()
        imageIO.close()
        return dim

    @classmethod
    def getInfo(cls, path):
        """
        Return some specified info from the given image path.
        dim : Image dimensions
        ext : File extension
        data_type: Image data type
        """
        imageIO = em.ImageIO()
        imageIO.open(path, em.File.Mode.READ_ONLY)
        dim = imageIO.getDim()
        dataType = imageIO.getType()
        imageIO.close()

        return {'dim': dim,
                'ext': EmPath.getExt(path),
                'data_type': dataType}

    @classmethod
    def getNumPyArray(cls, image, copy=False):
        """
        Returns the numpy array of image data according to the image type  """
        if image is None:
            return None

        return np.array(image, copy=copy,
                        dtype=cls.DATA_TYPE_MAP.get(image.getType()))


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

    def __init__(self, path=None, index=0, volumeIndex=0, axis=-1):
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
        self.volumeIndex = volumeIndex
        self.axis = axis
        self.imageType = ImageRef.SINGLE


def parseImagePath(imgPath, imgRef=None, root=None):
    """
    Return the image reference, parsing the str image path.
    Find the image path beginning from the given root.
    imgPath specification:
     - some/img_path for single image
     - index@some/img_path for image in stack
     - index@axis@some/img_path for image in volume
     - index@axis@volIndex@some/img_path for image in volume stack
        axis = 0: X
        axis = 1: Y
        axis = 2: Z
        axis = -1: Undefined
    """
    if isinstance(imgPath, str) or isinstance(imgPath, unicode):
        p = imgPath.split('@')
        size = len(p)
        if imgRef is None:
            imgRef = ImageRef()
        try:
            if size == 1:  # Single image: 'image-path'
                imgRef.path = p[0]
                imgRef.index = 0
                imgRef.axis = -1
                imgRef.volumeIndex = 0
                imgRef.imageType = ImageRef.SINGLE
            elif size == 2:  # One image in stack: 'index@image-path'
                imgRef.path = p[1]
                imgRef.index = int(p[0])
                imgRef.axis = -1
                imgRef.volumeIndex = 0
                imgRef.imageType = ImageRef.STACK
            elif size == 3:  # One image in volume: 'index@axis@image-path'
                imgRef.path = p[2]
                imgRef.index = int(p[0])
                imgRef.axis = int(p[1])
                imgRef.volumeIndex = 0
                imgRef.imageType = ImageRef.VOLUME
            elif size == 4:  # One image in volume stack:
                # 'index@axis@volIndex@image-path'
                imgRef.path = p[3]
                imgRef.index = int(p[0])
                imgRef.axis = int(p[1])
                imgRef.volumeIndex = int(p[2])
                imgRef.imageType = ImageRef.STACK | ImageRef.VOLUME
            else:
                raise Exception("Invalid specification")
        except Exception:
            print("-----------------------------------------------------------")
            print("Error occurred parsing: ", imgPath)
            print("-----------------------------------------------------------")
            traceback.print_exception(*sys.exc_info())
            return None
        path = ImageManager.findImage(imgRef.path, root)
        if path is not None:
            imgRef.path = path
        return imgRef
    return None