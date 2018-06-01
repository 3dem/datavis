import em

import os
import traceback
import sys


def isEmImage(imagePath):
    """ Return True if imagePath has an extension recognized as supported
        EM-image """
    if imagePath is None:
        return False
    _, ext = os.path.splitext(imagePath)
    if imagePath is None:
        return False
    return ext in ['.mrc', '.spi']


def isImage(imagePath):
    """ Return True if imagePath has a standard image format. """
    if imagePath is None:
        return False
    _, ext = os.path.splitext(imagePath)
    return ext in ['.jpg', '.jpeg', '.png', '.tif', '.bmp']


def isEMImageVolume(imagePath):
    """ Return True if imagePath has a image volume format. """
    if imagePath is None:
        return False
    _, ext = os.path.splitext(imagePath)
    return ext in ['.vol', '.map']


def isEMImageStack(imagePath):
    """ Return True if imagePath has a image stack format. """
    if imagePath is None:
        return False
    _, ext = os.path.splitext(imagePath)
    return ext in ['.mrcs', '.stk']


def isEMTable(imagePath):
    """ Return True if imagePath has a image stack format. """
    _, ext = os.path.splitext(imagePath)
    if imagePath is None:
        return False
    return ext in ['.xmd', '.star']


def loadEMImage(imagePath, index=0):
    """Return the em image at the given index"""
    try:
        image = em.Image()
        loc2 = em.ImageLocation(imagePath)
        loc2.index = index + 1
        image.read(loc2)
        return image
    except Exception:
        print("--------------------------------------------------------------")
        print("Error occurred reading: ", imagePath)
        print("--------------------------------------------------------------")
        traceback.print_exception(*sys.exc_info())
        return None


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
