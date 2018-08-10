
import os
import traceback
import sys

import em


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
        EXT_IMAGE: ['.mrc', '.spi', '.xmp'],
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
         loc: can be either a path or a tupe (path, index)
        """
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


def parseImagePath(imgPath):
    """ Return the index, the axis and the image path: [index, axis, image_path]
        If a stack index has been specified (index@some/img_path), or no index
        was specified (some/img_path) then return [0, -1, some/img_path].
        An image within a EM volume must be specified as:
         'imageIndex@axis@some_img_path'
        axis = 0: X
        axis = 1: Y
        axis = 2: Z
        axis = -1: Undefined
    """
    p = imgPath.split('@')
    size = len(p)

    try:
        if size == 1:
            return [0, -1, p[0]]
        elif size == 2:
            return [int(p[0]), -1, p[1]]
        elif size == 3:
            return [int(p[0]), int(p[1]), p[2]]
        else:
            raise Exception("Invalid specification")
    except Exception:
        print("--------------------------------------------------------------")
        print("Error occurred parsing: ", imgPath)
        print("--------------------------------------------------------------")
        traceback.print_exception(*sys.exc_info())
        return None
