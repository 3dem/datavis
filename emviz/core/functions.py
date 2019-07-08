
import os

import em


def getDim(path):
    """ Shortcut method to return the dimensions of the given
    image path. """
    imageIO = em.ImageIO()
    imageIO.open(path, em.File.Mode.READ_ONLY)
    dim = imageIO.getDim()
    imageIO.close()
    return dim


def getInfo(path):
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
        EXT_IMAGE: ['.mrc', '.spi', '.xmp', '.hed', '.img', '.dm3', '.dm4',
                    '.dat'],
        EXT_VOLUME: ['.mrc', '.vol', '.map'],
        EXT_STACK: ['.mrc', '.mrcs', '.stk', '.dm3', '.dm4', '.dat'],
        EXT_TABLE: ['.star', '.xmd', '.sqlite'],
        EXT_STD_IMAGE: ['.png', '.jpg', '.jpeg', '.tif', '.bmp']
    }

    @classmethod
    def __isFile(cls, path, extType):
        if not path:
            return False
        _, ext = os.path.splitext(path)
        return ext in cls.EXTESIONS_MAP[extType]

    @classmethod
    def getExt(cls, path):
        if not path:
            return None
        _, ext = os.path.splitext(path)
        return ext

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


class EmTable:
    """ Helper class around em.Table class. """
    @classmethod
    def load(cls, path, tableName=None, table=None):
        """
        Load the table from the specified file and return a tuple
        ([table-names], em-table).
        If the specified table is None then create new em.Table,
        otherwise the data is loaded in the specified table
        """
        tio = em.TableIO()
        tio.open(path, em.File.Mode.READ_ONLY)
        if table is None:
            table = em.Table()
        names = tio.getTableNames()
        tableName = tableName or names[0]
        tio.read(tableName, table)
        return names, table

    @classmethod
    def fromStack(cls, path):
        """ Create a table from a given stack. """
        table = em.Table([
            em.Table.Column(1, "path", em.typeString, "Image location")
        ])
        row = table.createRow()
        n = getDim(path).n

        for i in range(1, n+1):
            row['path'] = '%d@%s' % (i, path)
            table.addRow(row)

        return table
