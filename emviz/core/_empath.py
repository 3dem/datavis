
import os


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

