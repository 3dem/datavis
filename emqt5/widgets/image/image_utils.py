
from PyQt5.QtGui import QImage
import numpy as np


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
        self.max = self.maxDataValue()
        self.min = self.minDataValue()
        self.image = QImage(self.width, self.heigth, imgFormat)

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

    def convertToImage(self):
        """"
        Returns an image in the given type and format using a memory buffer.
        The image was store using an 8-bits, 16-bits or 32-bits gray scale
        format.
        :return: a 8-bits image
        """
        pixelPos = 0
        self.minPixelValue = self.buffer[pixelPos]
        self.maxPixelValue = self.buffer[pixelPos]

        #  Construct the image using a buffer data and determine the max and the
        #  min pixel value in this buffer

        dataBuffer = self.image.scanLine(0)
        pixelValuesAux = dataBuffer.asarray(self.width * self.heigth)
        pixelValues = np.array(pixelValuesAux, dtype=np.uint8, copy=False)

        for i in range(0, self.width * self.heigth):
            pixelValue = self.__toUInt8__(self.buffer[pixelPos])
            pixelValues[pixelPos] = pixelValue

            #  Compare the actual pixel with the determined minimal pixel
            if self.buffer[pixelPos] < self.minPixelValue:
                self.minPixelValue = self.buffer[pixelPos]

            #  Compare the actual pixel with the determined maximal pixel
            if self.buffer[pixelPos] > self.maxPixelValue:
                self.maxPixelValue = self.buffer[pixelPos]

            pixelPos += 1

        return self.image

    def __toUInt8__(self, value):
        """
        Creates and returns a 8-bits pixel color based on this value.
        :param value: value of pixel
        :return: a 8-bits pixel color
        """
        if self.dataType == self.UINT8:
            return value
        if self.dataType == self.UINT16:
            return round((value*255)/(2**16 - 1))
        if self.dataType == self.UINT32:
            return round((value*255)/(2**32 - 1))

        if self.dataType == self.INT8:
            return value + round(2**8/2)
        if self.dataType == self.INT16:
            value += round(2**16/2)
            return round((value * 255) / (2 ** 16 - 1))
        if self.dataType == self.INT32:
            value += round(2**32/2)
            return round((value * 255) / (2 ** 32 - 1))

    def maxDataValue(self):
        """
        Determine the maximum possible value taking into account the data type
        :return: maximal possible value
        """
        if self.dataType == self.UINT8:
            return 255
        if self.dataType == self.UINT16:
            return 2**16 - 1
        if self.dataType == self.UINT32:
            return 2**32 - 1
        if self.dataType == self.INT8:
            return 127
        if self.dataType == self.INT16:
            return round(2**16/2 - 1)
        if self.dataType == self.UINT32:
            return round(2**32/2 - 1)

    def minDataValue(self):
        """
        Determine the minimum possible value taking into account the data type
        :return: minimal possible value
        """
        if self.dataType == self.UINT8 or \
           self.dataType == self.UINT16 or \
           self.dataType == self.UINT32:
            return 0
        if self.dataType == self.INT8:
            return -128
        if self.dataType == self.INT16:
            return round(-2**16/2)
        if self.dataType == self.INT32:
            return round(-2**32/2)
        return 0

    def applyWindowLevel(self, window, level, ymin=0, ymax=255):
        print("applyWindowLevel")
        #x: output pixel value
        #ymin: minimum output pixel value
        #ymax: maximum output pixel value
        #if  (x <= c - 0.5 - (w-1)/2), then y = Ymin
        #else if (x > c - 0.5 + (w-1)/2), then y = Ymax
        #else  y = ((x - (c - 0.5)) / (w-1) + 0.5) * (Ymax - Ymin )+ Ymin

        if self.image:
            dataArray = self.image.scanLine(0)
            pixelValues = dataArray.asarray(self.width * self.heigth)

            for i in range(0, self.width * self.heigth):
                pValue = self.buffer[i]
                if pValue <= (level-0.5-(window-1)/2):
                    pixelValues[i] = ymin
                elif pValue > (level-0.5+(window-1)/2):
                    pixelValues[i] = ymax
                else:
                    pixelValues[i] = ((pValue-(level-0.5))/(window-1)+0.5)*(ymax-ymin)+ymin