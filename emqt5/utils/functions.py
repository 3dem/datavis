import os

def isEmImage(imagePath):
    """ Return True if imagePath has an extension recognized as supported
        EM-image """
    if imagePath is None:
        return False
    _, ext = os.path.splitext(imagePath)
    if imagePath is None:
        return False
    return ext in ['.mrc', '.spi', '.map', '.vol']

def isImage(imagePath):
    """ Return True if imagePath has a standard image format. """
    if imagePath is None:
        return False
    _, ext = os.path.splitext(imagePath)
    return ext in ['.jpg', '.jpeg', '.png', '.tif', '.bmp']

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

