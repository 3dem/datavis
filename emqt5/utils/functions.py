
import os
import traceback
import sys

import em

from PIL import Image
import numpy as np


class EmPath:
    """
    Helper class to group functions related to path handling in EM.
    """
    EXT_IMAGE = 0
    EXT_VOLUME = 1
    EXT_STACK = 2
    EXT_TABLE = 3
    EXT_STD_IMAGE = 4  # Standard image extensions

    EXTESIONS_MAP = {
        EXT_IMAGE: ['.mrc', '.spi', '.xmp', '.hed', '.img'],
        EXT_VOLUME: ['.mrc', '.vol', '.map'],
        EXT_STACK: ['.mrc', '.mrcs', '.stk'],
        EXT_TABLE: ['.star', '.xmd', '.sqlite'],
        EXT_STD_IMAGE: ['.jpg', '.jpeg', '.png', '.tif', '.bmp']
    }

    @classmethod
    def __isFile(cls, path, extType):
        if not path:
            return False
        _, ext = os.path.splitext(path)
        return ext in cls.EXTESIONS_MAP[extType]

    @classmethod
    def isImage(cls, path):
        """ Return True if imagePath has an extension recognized as supported
        EM-image """
        return cls.__isFile(path, cls.EXT_IMAGE)

    @classmethod
    def isVolume(cls, path):
        return cls.__isFile(path, cls.EXT_VOLUME)

    @classmethod
    def isStack(cls, path):
        return cls.__isFile(path, cls.EXT_STACK)

    @classmethod
    def isData(cls, path):
        return cls.isImage(path) or cls.isVolume(path) or cls.isStack(path)

    @classmethod
    def isTable(cls, path):
        return cls.__isFile(path, cls.EXT_TABLE)

    @classmethod
    def isStandardImage(cls, path):
        return cls.__isFile(path, cls.EXT_STD_IMAGE)


class EmImage:
    """ Helper class around the em.Image class. """

    @classmethod
    def load(cls, path, index=1):
        """ Read an image from the path and return the object.
         Params:
         loc: can be either a path or a tuple (path, index)
        """
        if not os.path.exists(path):
            raise Exception("Path does not exists: %s" % path)

        image = em.Image()
        image.read(em.ImageLocation(path, index))
        return image

    @classmethod
    def loadStandardImage(cls, path):
        """ Read a standard image (.JPG, .PNG, etc.) """
        image = Image.open(path)
        data = np.array(image)
        return data

    @classmethod
    def getDim(cls, path):
        """ Shortcut method to return the dimensions of the given
        image path. """
        imageIO = em.ImageIO()
        imageIO.open(path, em.File.Mode.READ_ONLY)
        dim = imageIO.getDim()
        imageIO.close()
        return dim


class EmTable:
    """ Helper class around em.Table class. """
    @classmethod
    def load(cls, path, tableName=''):
        tio = em.TableIO()
        tio.open(path, em.File.Mode.READ_ONLY)
        table = em.Table()
        tio.read(tableName, table)
        return table

    @classmethod
    def fromStack(cls, path):
        """ Create a table from a given stack. """
        table = em.Table([
            em.Table.Column(1, "index", em.typeInt32, "Image index"),
            em.Table.Column(1, "path", em.typeString, "Image location")
        ])
        row = table.createRow()
        n = EmImage.getDim(path).n

        for i in range(1, n+1):
            row['index'] = i
            row['path'] = '%d@%s' % (i, path)
            table.addRow(row)

        return table


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


def parseImagePath(imgPath, imgRef=None):
    """
    Return the image reference, parsing the str image path.
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
        print("--------------------------------------------------------------")
        print("Error occurred parsing: ", imgPath)
        print("--------------------------------------------------------------")
        traceback.print_exception(*sys.exc_info())
        return None

    return imgRef
