
from PyQt5.QtGui import QImage
import numpy as np
import sys
import em


class ImageBuilder:
    """
    Declaration of the class ImageBuffer

    This class construct an image with the given width, height, type, and
    format, that uses an existing memory buffer, data.
    """
    # Supported Data types values
    UINT8 = 1
    UINT16 = 2
    UINT32 = 3
    INT8 = 4
    INT16 = 5
    INT32 = 6
    FLOAT = 7
    DOUBLE = 8

    def __init__(self, dataArray, imgWidth, imgHeigth, dataType, imgFormat):

        self.width = imgWidth
        self.heigth = imgHeigth
        self.buffer = dataArray
        self.dataType = dataType
        self.maxPixelValue = 0
        self.minPixelValue = 0
        self.image = QImage(self.width, self.heigth, imgFormat)

    def getImage(self):
        """
        Get the image
        :return: the image
        """
        return self.image

    def getBuffer(self):
        """
        Get the buffer data
        :return: the buffer data
        """
        return self.buffer

    def getMaxPixelValue(self):
        """
        Get the maximal pixel value from the buffer data
        :return: maximal pixel value
        """
        return self.maxPixelValue

    def getMinPixelValue(self):
        """
        Get the minimal pixel value from the buffer data
        :return: minimal pixel value
        """
        return self.minPixelValue

    def computeMinMaxPixelValues(self):
        """
        Calculate the minimum and maximum pixels in the buffer array
        :return:
        """
        self.minPixelValue = self.buffer.min()
        self.maxPixelValue = self.buffer.max()


    def getPixelValue(self, x, y):
        """
        Get the pixel value from the buffer data in (x, y) position. This method
        fire an IndexError exception if (x, y) are out of range
        :param x: value in [0..width]
        :param y: value in [0..heigth]
        :return: the pixel value from the buffer data
        """
        if self.isValidPos(x, y):
            return self.dataArray[x + y*self.heigth]
        raise IndexError("Index out of range")


    def isValidPos(self, x, y):
        """
        Determine if (x, y) is a valid position in the buffer data
        :param x: value in [0..width]
        :param y: value in [0..heigth]
        :return:
        """
        return x >=0 and x < self.width and y >= 0 and y < self.heigth

    def applyWindowLevel(self, window, level, ymin=0, ymax=255):

        #x: output pixel value
        #ymin: minimum output pixel value
        #ymax: maximum output pixel value
        #if  (x <= c - 0.5 - (w-1)/2), then y = Ymin
        #else if (x > c - 0.5 + (w-1)/2), then y = Ymax
        #else  y = ((x - (c - 0.5)) / (w-1) + 0.5) * (Ymax - Ymin )+ Ymin

        if self.image:
            dataArray = self.image.scanLine(0)
            pixelValues = dataArray.asarray(self.width * self.heigth)
            x = np.array(pixelValues, copy=False)
            buff = np.array(self.buffer, copy=False)
            try:
                x[:] = np.piecewise(buff,
                                    [buff[:] <= (level - 0.5 - (window - 1) / 2),
                                     buff[:] > (level - 0.5 + (window - 1) / 2)],
                                    [ymin, ymax, lambda x:
                                    ((x[:] - (level - 0.5)) / (window-1) + 0.5)*
                                    (ymax - ymin)])

            except:
                print(sys.exc_info())
