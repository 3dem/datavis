import os

def isEmImage(imagePath):
    """ Return True if imagePath has an extension recognized as supported
        EM-image """
    _, ext = os.path.splitext(imagePath)
    return ext in ['.mrc', '.mrcs', '.spi', '.stk', '.map', '.vol']

def isImage(imagePath):
    """ Return True if imagePath has a standard image format. """
    _, ext = os.path.splitext(imagePath)
    return ext in ['.jpg', '.jpeg', '.png', '.tif', '.bmp']