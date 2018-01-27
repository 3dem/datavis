
from PyQt5.QtGui import QImage, QColor


class ImageBuilder:
    """
    Declaration of the class ImageBuffer

    This class construct an image with the given width, height, type, and
    format, that uses an existing memory buffer, data.
    """
    # Suported Data types values
    UINT8 = 1
    UINT16 = 2
    UINT32 = 3
    INT8 = 4
    INT16 = 5
    INT32 = 6

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
        self.convertToImage()

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
        """
        Returns an image in the given type and format using a memory buffer.
        The image was store using an 8-bits, 16-bits or 32-bits gray scale
        format.
        :return: a 8-bits image
        """
        pixelPos = 0
        color = QColor(0, 0, 0)
        self.minPixelValue = self.buffer[pixelPos]
        self.maxPixelValue = self.buffer[pixelPos]

        #  Construct the image using a buffer data and determine the max and the
        #  min pixel value in this buffer

        for i in range(0, self.width):
            for j in range(0, self.heigth):
                pixelValue = self.__toUInt8__(self.buffer[pixelPos])
                color.setRgb(pixelValue, pixelValue, pixelValue)
                self.image.setPixelColor(i, j, color)

                #  Compare the actual pixel with the determined min pixel
                if self.buffer[pixelPos] < self.minPixelValue:
                    self.minPixelValue = self.buffer[pixelPos]

                #  Compare the actual pixel with the determined max pixel
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


    def maxDataValue(self):
        """
        Determine the max possible value taking into account the data type
        :return: max possible value
        """
        if self.dataType == self.UINT8:
            return 255
        if self.dataType == self.UINT16:
            return 2**16 - 1
        if self.dataType == self.UINT32:
            return 2**32 - 1

    def minDataValue(self):
        """
        Determine the min possible value taking into account the data type
        :return: min possible value
        """
        if self.dataType == self.UINT8 or \
           self.dataType == self.UINT16 or \
           self.dataType == self.UINT32:
            return 0
        return 0



