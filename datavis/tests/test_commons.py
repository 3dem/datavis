#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import unittest
import numpy as np
from random import randrange, uniform
import pyqtgraph as pg

import PyQt5.QtWidgets as qtw

import datavis as dv


class TestData:
    """ Simple base class to define basic parameters and functions
    related to testing view examples.
    """
    __title = ''

    def _loadPaths(self):
        if not hasattr(self, '_argv'):
            return

        argv = self._argv
        self._path = None

        i = 0

        if len(argv) > 1:
            a = argv[1]
            if len(a) == 1 and a.isdigit():  # consider it as index
                i = int(a)
            else:
                self._path = argv[1]

        if not self._path:
            self._path = self.getDataPaths()[i]

    def getPath(self, *paths):
        if not hasattr(self, '_path'):
            self._loadPaths()

        testDataPath = os.environ.get("EM_TEST_DATA", None)
        joinedPath = os.path.join(*paths)

        if testDataPath is None:
            raise Exception("Define EM_TEST_DATA to run this tests."
                            "Needed for path: $EM_TEST_DATA/%s" % joinedPath)

        return os.path.join(testDataPath, joinedPath)

    def getTitle(self):
        return self.__title

    def getArgs(self):
        return self._argv

    def getDataPaths(self):
        return []


class TestBase(unittest.TestCase, TestData):
    """ Simple base class to define basic parameters and functions
    related to testing view examples.
    """
    __title = ''


class TestView(TestData):
    """ Class that will test existing Views. """

    def createView(self):
        return None

    def runApp(self, argv=None, app=None):
        self._argv = argv or sys.argv
        self._loadPaths()
        dv.views.showView(self.createView, argv=self.getArgs(),
                          title=self.getTitle())


class SimpleItemsModel(dv.models.SimpleTableModel):
    """ Example class implementing a simple items model """

    def __init__(self, columInfo):
        """
        Creates an SimpleItemsModel.
        :param columInfo: (list) The list of ColumnInfo
        """
        dv.models.SimpleTableModel.__init__(self, columInfo)

    def getData(self, row, col):
        v = self.getValue(row, col)
        if isinstance(v, np.ndarray):
            return v
        return None

    def createDefaultConfig(self):
        cols = [dv.models.ColumnConfig(c.getName(), c.getType())
                for c in self.iterColumns()]
        c = cols[1]
        c[dv.models.RENDERABLE] = True
        return dv.models.TableConfig(*cols)


class SimpleListImageModel(dv.models.ListModel):
    """ The SimpleListModel class is an example implementation of ListModel
    """
    def __init__(self, names, columnName, imgSize):
        """
        Create an SimpleListModel
        :param names: (list) A list of names
        """
        self._names = list(names)
        self._columnName = columnName or 'Image'
        self._imgSize = imgSize
        s = len(imgSize)
        if s == 2:
            self._mClass = dv.models.ImageModel
        elif s == 3:
            self._mClass = dv.models.VolumeModel
        else:
            raise Exception("Invalid image size. Supported values: 2 or 3.")

        self._imgData = dict()
        self._tableName = ''
        self._tableNames = [self._tableName]

    def iterColumns(self):
        yield dv.models.ColumnInfo(self._columnName, dv.models.TYPE_STRING)

    def getRowsCount(self):
        """ Return the number of rows. """
        return len(self._names)

    def getValue(self, row, col):
        """ Return the value of the item in this row, column. """
        return self._names[row]

    def getData(self, row, col=0):
        """ Return the data (array like) for the item in this row, column.
         Used by rendering of images in a given cell of the table.
        """
        data = self._imgData.get(row)
        if len(self._imgSize) == 2:  # 2D Image
            s = (self._imgSize[1], self._imgSize[0])
        else:  # Volume
            s = (self._imgSize[2], self._imgSize[1], self._imgSize[0])
        if data is None:
            data = pg.gaussianFilter(np.random.normal(size=s),
                                     [5 for _ in range(len(self._imgSize))])
            self._imgData[row] = data

        return data

    def getModel(self, row):
        """ Return the model for the given row """

        return self._mClass(self.getData(row))

    def createDefaultConfig(self):
        c = dv.models.ListModel.createDefaultConfig(self)
        if len(self._imgSize) == 2:
            cc = c[0]
            cc[dv.models.RENDERABLE] = True
        return c


class SimplePickerModel(dv.models.PickerModel):
    """ Simple picker data model with random images and picks """

    def __init__(self, imageSize, size, boxSize=40, picks=100, filament=False):
        dv.models.PickerModel.__init__(self)
        self._imageSize = imageSize
        self._size = size
        self._images = dict()
        self._picks = picks
        self._filament = filament
        self._cache = {}
        for i in range(size):
            mic = dv.models.Micrograph(micId=i+1, path='Micrograph %d' % (i+1))
            self.addMicrograph(mic)
            self.pickRandomly(mic.getId())
        self.setBoxSize(boxSize)

    def __getRandomCoords(self, n):
        """ Return a Micrograph object with random pick coordinates """
        w, h = self._imageSize

        def _randomCoord():
            y, x = randrange(0, h), randrange(0, w)

            kwargs = {
                'x2': randrange(0, w),
                'y2': randrange(0, h)} if self._filament else {}
            return dv.models.Coordinate(x, y, score=uniform(0, 1), **kwargs)

        return [_randomCoord() for _ in range(n)]

    def createCoordinate(self, x, y, label, **kwargs):
        if 'score' not in kwargs:
            kwargs['score'] = 1
        c = dv.models.Coordinate(x, y, label, **kwargs)
        return c

    def pickRandomly(self, micId, n=None):
        """ Pick a random number of particles just for testing. """
        n = n or randrange(0, self._picks)
        self.clearMicrograph(micId)
        self.addCoordinates(micId, self.__getRandomCoords(n))

    def getData(self, micId):
        """
        Return the micrograph image data
        :param micId: (int) The micrograph id
        :return: The micrograph image data
        """
        if micId not in self._cache:
            c, r = self._imageSize
            self._cache[micId] = pg.gaussianFilter(
                np.random.normal(size=(r, c)), (5, 5))

        return self._cache[micId]

    def getImageInfo(self, micId):
        """
        Return some specified info from the given image path.
        dim : Image dimensions
        ext : File extension
        data_type: Image data type

        :param micId:  (int) The micrograph Id
        :return: dict
        """
        return {'dim': self._imageSize}


def createPickerModel(imageSize, size, boxSize=40, picks=100,
                          filament=False):
    """
    Creates an PickerModel with random images and picks
    :param imageSize: (tupple) The image size
    :param size: (int) The number of images
    :param boxSize: (int) The box size
    :param picks: (int) The number of picks
    :param filament: (boolean) if True, generate filaments, else boxes
    :return: (PickerModel)
    """
    return SimplePickerModel(imageSize, size, boxSize, picks, filament)


def createSimplePickerModel(imageSize, size=0, boxSize=40, picks=0,
                                filament=False):
    """
    Creates an PickerModel with random images.
    :param imageSize: (tupple) The image size
    :param boxSize: (int) The box size
    :return: (PickerModel)
    """
    return SimplePickerModel(imageSize=imageSize, size=size, boxSize=boxSize,
                             picks=picks, filament=filament)


def createSlicesModel(imgSize, size):
    """
    Creates an SlicesModel, generating random images of the given image size,
    having size elements.
    :param imgSize: (tupple) The image size
    :param size: (int) The number of slices(images)
    :return: (SlicesModel)
    """
    s = size, imgSize[1], imgSize[0]
    data = pg.gaussianFilter(np.random.normal(size=s), (5, 5, 5))
    return dv.models.SlicesModel(data)


def getPythonCodeExample():
    """ Return a python code example """
    return """
    def getData(self, micId):
        if micId not in self._cache:
            self._cache[micId] = pg.gaussianFilter(
                np.random.normal(size=self._imageSize), (5, 5))
        return self._cache[micId]
    """


def getJsonTextExample():
    """ Return a JSON text document example """
    return """
    {   "n": "34",
        "b": "ertffgddf dfg",
        "name": "Petter HV",
        "array": [
            ["straight", 7],
            [one pair", "10"]
        ]
    }
    """""

def createTableModel(imgSize):
    """
    Creates a SimpleTableModel from a raw string
    :param imgSize:
    :return: (SimpleTableModel). The data model .
    """
    star = """1 001@../input_particles.mrcs 1 0.100 2.0 300.0 1 -39.034721 16.49 
     2 002@../input_particles.mrcs 1 0.100 2.0 300.0 1 -42.167542 81.923042  
     3 003@../input_particles.mrcs 1 0.100 2.0 300.0 1 159.489304 141.634064 
     4 004@../input_particles.mrcs 1 0.100 2.0 300.0 1 83.591354 12.817675  
     5 005@../input_particles.mrcs 1 0.100 2.0 300.0 1 -103.720657 131.01647 
     6 006@../input_particles.mrcs 1 0.100 2.0 300.0 1 -59.076363 112.342262 
     7 007@../input_particles.mrcs 1 0.100 2.0 300.0 1 -172.046432 144.34924 
     8 008@../input_particles.mrcs 1 0.100 2.0 300.0 1 140.495560 140.486542 
     9 009@../input_particles.mrcs 1 0.100 2.0 300.0 1 -77.356750 14.289002  
     10 010@../input_particles.mrcs 1 0.100 2.0 300.0 1 -20.945442 5.493235  
     11 011@../input_particles.mrcs 1 0.100 2.0 300.0 1 -65.377548 124.59455 
     12 012@../input_particles.mrcs 1 0.100 2.0 300.0 1 81.180168 36.041927  
     13 013@../input_particles.mrcs 1 0.100 2.0 300.0 1 -145.791489 144.3478 
     14 014@../input_particles.mrcs 1 0.100 2.0 300.0 1 113.191483 56.134609 
     15 015@../input_particles.mrcs 1 0.100 2.0 300.0 1 151.800842 140.09887 
     16 016@../input_particles.mrcs 1 0.100 2.0 300.0 1 151.800842 140.09887 
     17 017@../input_particles.mrcs 1 0.100 2.0 300.0 1 -106.885971 126.0560 
     18 018@../input_particles.mrcs 1 0.100 2.0 300.0 1 139.347198 153.45468 
     19 019@../input_particles.mrcs 1 0.100 2.0 300.0 1 -174.879013 143.9472 
     20 020@../input_particles.mrcs 1 0.100 2.0 300.0 1 -42.608028 13.548254 
     21 021@../input_particles.mrcs 1 0.100 2.0 300.0 1 -117.785210 22.06898 
     22 022@../input_particles.mrcs 1 0.100 2.0 300.0 1 -130.459091 18.34631 
     23 023@../input_particles.mrcs 1 0.100 2.0 300.0 1 136.737839 118.63712 
     24 024@../input_particles.mrcs 1 0.100 2.0 300.0 1 -88.254677 117.27935 
     25 025@../input_particles.mrcs 1 0.100 2.0 300.0 1 -156.224457 6.223958 
     26 026@../input_particles.mrcs 1 0.100 2.0 300.0 1 163.299591 136.57991 
     27 027@../input_particles.mrcs 1 0.100 2.0 300.0 1 -23.551188 16.126791 
     28 028@../input_particles.mrcs 1 0.100 2.0 300.0 1 -27.616928 11.341051 
     29 029@../input_particles.mrcs 1 0.100 2.0 300.0 1 -67.042992 16.500441 
     30 030@../input_particles.mrcs 1 0.100 2.0 300.0 1 -85.560081 10.980631 
     31 031@../input_particles.mrcs 1 0.100 2.0 300.0 1 126.728569 4.015432  
     32 032@../input_particles.mrcs 1 0.100 2.0 300.0 1 119.108269 44.614891 
     33 033@../input_particles.mrcs 1 0.100 2.0 300.0 1 150.178543 143.56396 
     34 034@../input_particles.mrcs 1 0.100 2.0 300.0 1 137.310287 151.57315 
     35 035@../input_particles.mrcs 1 0.100 2.0 300.0 1 -161.260162 157.9428 
     36 036@../input_particles.mrcs 1 0.100 2.0 300.0 1 141.313812 64.393486 
     37 037@../input_particles.mrcs 1 0.100 2.0 300.0 1 117.365639 45.009991 
     38 038@../input_particles.mrcs 1 0.100 2.0 300.0 1 19.277443 17.974430  
     39 039@../input_particles.mrcs 1 0.100 2.0 300.0 1 146.840744 150.42646 
     40 040@../input_particles.mrcs 1 0.100 2.0 300.0 1 143.882507 144.34771 
     41 041@../input_particles.mrcs 1 0.100 2.0 300.0 1 163.778687 152.32849 
     42 042@../input_particles.mrcs 1 0.100 2.0 300.0 1 145.590607 140.48696 
     43 043@../input_particles.mrcs 1 0.100 2.0 300.0 1 -131.518799 136.5774 
     44 044@../input_particles.mrcs 1 0.100 2.0 300.0 1 138.531738 65.039841 
     45 045@../input_particles.mrcs 1 0.100 2.0 300.0 1 119.517632 66.360832 
     46 046@../input_particles.mrcs 1 0.100 2.0 300.0 1 -159.119003 148.9276 
     47 047@../input_particles.mrcs 1 0.100 2.0 300.0 1 -10.077846 17.991758 
     48 048@../input_particles.mrcs 1 0.100 2.0 300.0 1 -8.357194 9.871947  
     49 049@../input_particles.mrcs 1 0.100 2.0 300.0 1 -79.504265 146.63566 
     50 050@../input_particles.mrcs 1 0.100 2.0 300.0 1 -31.525940 25.794075 
     51 051@../input_particles.mrcs 1 0.100 2.0 300.0 1 -65.403786 115.60958 
     52 052@../input_particles.mrcs 1 0.100 2.0 300.0 1 -69.973808 116.60721 
     53 053@../input_particles.mrcs 1 0.100 2.0 300.0 1 143.714752 141.64978 
     54 054@../input_particles.mrcs 1 0.100 2.0 300.0 1 -45.048615 10.608226 
     55 055@../input_particles.mrcs 1 0.100 2.0 300.0 1 154.190994 147.02612 
     56 056@../input_particles.mrcs 1 0.100 2.0 300.0 1 -37.301460 32.608055 
     57 057@../input_particles.mrcs 1 0.100 2.0 300.0 1 164.252548 136.16900 
     58 058@../input_particles.mrcs 1 0.100 2.0 300.0 1 144.865448 115.60527 
     59 059@../input_particles.mrcs 1 0.100 2.0 300.0 1 78.738136 58.959106  
     60 060@../input_particles.mrcs 1 0.100 2.0 300.0 1 -133.606262 125.3245 
     61 061@../input_particles.mrcs 1 0.100 2.0 300.0 1 88.229324 64.717140  
     62 062@../input_particles.mrcs 1 0.100 2.0 300.0 1 -97.273048 15.764240 
     63 063@../input_particles.mrcs 1 0.100 2.0 300.0 1 160.864700 142.40701 
     64 064@../input_particles.mrcs 1 0.100 2.0 300.0 1 -28.997452 26.920019 
     65 065@../input_particles.mrcs 1 0.100 2.0 300.0 1 -70.325310 116.94152 
     66 066@../input_particles.mrcs 1 0.100 2.0 300.0 1 86.116760 84.620056  
     67 067@../input_particles.mrcs 1 0.100 2.0 300.0 1 -178.962021 129.4593 
     68 068@../input_particles.mrcs 1 0.100 2.0 300.0 1 124.189659 46.996098 
     69 069@../input_particles.mrcs 1 0.100 2.0 300.0 1 74.521187 50.159317  
     70 070@../input_particles.mrcs 1 0.100 2.0 300.0 1 79.793495 55.769646  
     71 071@../input_particles.mrcs 1 0.100 2.0 300.0 1 124.438698 70.849754 
     72 072@../input_particles.mrcs 1 0.100 2.0 300.0 1 -164.203430 138.5403 
     73 073@../input_particles.mrcs 1 0.100 2.0 300.0 1 141.704041 131.80284 
     74 074@../input_particles.mrcs 1 0.100 2.0 300.0 1 122.550941 46.2035  
     75 075@../input_particles.mrcs 1 0.100 2.0 300.0 1 -159.013123 140.8760 
     76 076@../input_particles.mrcs 1 0.100 2.0 300.0 1 177.437515 134.19200 
     77 077@../input_particles.mrcs 1 0.100 2.0 300.0 1 115.325928 56.843040 
     78 078@../input_particles.mrcs 1 0.100 2.0 300.0 1 161.228683 148.92775 
     79 079@../input_particles.mrcs 1 0.100 2.0 300.0 1 147.987717 149.30607 
     80 080@../input_particles.mrcs 1 0.100 2.0 300.0 1 -61.858257 105.40860 
     81 081@../input_particles.mrcs 1 0.100 2.0 300.0 1 119.898422 67.325645 
     82 082@../input_particles.mrcs 1 0.100 2.0 300.0 1 -27.903179 7.673451  
     83 083@../input_particles.mrcs 1 0.100 2.0 300.0 1 173.179245 148.16873 
     84 084@../input_particles.mrcs 1 0.100 2.0 300.0 1 -141.621658 15.03443 
     85 085@../input_particles.mrcs 1 0.100 2.0 300.0 1 -23.214151 12.075578 
     86 086@../input_particles.mrcs 1 0.100 2.0 300.0 1 92.057167 40.687462  
     87 087@../input_particles.mrcs 1 0.100 2.0 300.0 1 -145.913376 112.0312 
     88 088@../input_particles.mrcs 1 0.100 2.0 300.0 1 124.882027 142.02427 
     89 089@../input_particles.mrcs 1 0.100 2.0 300.0 1 -148.724274 128.6893 
     90 090@../input_particles.mrcs 1 0.100 2.0 300.0 1 -138.499329 113.6361 
     91 091@../input_particles.mrcs 1 0.100 2.0 300.0 1 -168.667236 136.9732 
     92 092@../input_particles.mrcs 1 0.100 2.0 300.0 1 18.331707 9.872286  
     93 093@../input_particles.mrcs 1 0.100 2.0 300.0 1 142.840820 141.64970 
     94 094@../input_particles.mrcs 1 0.100 2.0 300.0 1 -41.422020 46.985058 
     95 095@../input_particles.mrcs 1 0.100 2.0 300.0 1 -159.703888 137.7575 
     96 096@../input_particles.mrcs 1 0.100 2.0 300.0 1 -112.106346 138.1443 
     97 097@../input_particles.mrcs 1 0.100 2.0 300.0 1 175.763672 152.68714 
     98 098@../input_particles.mrcs 1 0.100 2.0 300.0 1 -77.004913 116.60818 
     99 099@../input_particles.mrcs 1 0.100 2.0 300.0 1 -24.587006 50.170219 
      100 0100@../input_particles.mrcs 1 0.100 2.0 300.0 1 -50.331337 47.396 
      101 0101@../input_particles.mrcs 1 0.100 2.0 300.0 1 -158.562241 23.93 
      102 0102@../input_particles.mrcs 1 0.100 2.0 300.0 1 -140.255890 103.8 
      103 0103@../input_particles.mrcs 1 0.100 2.0 300.0 1 160.834595 154.93 
      104 0104@../input_particles.mrcs 1 0.100 2.0 300.0 1 -66.432526 125.68 
      105 0105@../input_particles.mrcs 1 0.100 2.0 300.0 1 143.528152 132.20 
      106 0106@../input_particles.mrcs 1 0.100 2.0 300.0 1 -33.064072 85.512 
      107 0107@../input_particles.mrcs 1 0.100 2.0 300.0 1 31.113691 4.76079 
      108 0108@../input_particles.mrcs 1 0.100 2.0 300.0 1 -162.789703 102.6 
      109 0109@../input_particles.mrcs 1 0.100 2.0 300.0 1 -80.521294 112.02 
      110 0110@../input_particles.mrcs 1 0.100 2.0 300.0 1 -142.749496 108.5 
      111 0111@../input_particles.mrcs 1 0.100 2.0 300.0 1 -170.234924 157.9 
      112 0112@../input_particles.mrcs 1 0.100 2.0 300.0 1 -73.839951 121.73 
      113 0113@../input_particles.mrcs 1 0.100 2.0 300.0 1 -62.210804 111.38 
      114 0114@../input_particles.mrcs 1 0.100 2.0 300.0 1 125.602005 157.18 
      115 0115@../input_particles.mrcs 1 0.100 2.0 300.0 1 131.149689 73.035 
      116 0116@../input_particles.mrcs 1 0.100 2.0 300.0 1 106.863724 55.411 
      117 0117@../input_particles.mrcs 1 0.100 2.0 300.0 1 74.870934 58.6096 
      118 0118@../input_particles.mrcs 1 0.100 2.0 300.0 1 107.563690 73.356 
      119 0119@../input_particles.mrcs 1 0.100 2.0 300.0 1 159.942474 119.32 
      120 0120@../input_particles.mrcs 1 0.100 2.0 300.0 1 -136.772949 106.3 
      121 0121@../input_particles.mrcs 1 0.100 2.0 300.0 1 -26.099846 6.9408 
      122 0122@../input_particles.mrcs 1 0.100 2.0 300.0 1 -142.449799 134.6 
      123 0123@../input_particles.mrcs 1 0.100 2.0 300.0 1 172.279190 138.54 
      124 0124@../input_particles.mrcs 1 0.100 2.0 300.0 1 62.753540 1.83183 
      125 0125@../input_particles.mrcs 1 0.100 2.0 300.0 1 -3.769190 13.1780 
      126 0126@../input_particles.mrcs 1 0.100 2.0 300.0 1 -139.930435 149.6 
      127 0127@../input_particles.mrcs 1 0.100 2.0 300.0 1 8.501844 13.54612 
      128 0128@../input_particles.mrcs 1 0.100 2.0 300.0 1 72.772171 4.75014 
      129 0129@../input_particles.mrcs 1 0.100 2.0 300.0 1 -179.467911 149.6 
      130 0130@../input_particles.mrcs 1 0.100 2.0 300.0 1 -36.540436 19.457 
      131 0131@../input_particles.mrcs 1 0.100 2.0 300.0 1 106.889290 62.381 
      132 0132@../input_particles.mrcs 1 0.100 2.0 300.0 1 -146.265274 108.5 
      133 0133@../input_particles.mrcs 1 0.100 2.0 300.0 1 -115.588860 13.55 
      134 0134@../input_particles.mrcs 1 0.100 2.0 300.0 1 -7.661511 19.4557 
      135 0135@../input_particles.mrcs 1 0.100 2.0 300.0 1 168.409668 140.87 
      136 0136@../input_particles.mrcs 1 0.100 2.0 300.0 1 170.029434 141.26 
      137 0137@../input_particles.mrcs 1 0.100 2.0 300.0 1 -11.502067 30.331 
      138 0138@../input_particles.mrcs 1 0.100 2.0 300.0 1 -168.380081 110.0 
      139 0139@../input_particles.mrcs 1 0.100 2.0 300.0 1 -1.196325 13.5639 
      140 0140@../input_particles.mrcs 1 0.100 2.0 300.0 1 -173.498993 135.7 
      141 0141@../input_particles.mrcs 1 0.100 2.0 300.0 1 68.926453 5.48775 
      142 0142@../input_particles.mrcs 1 0.100 2.0 300.0 1 -111.104210 129.0 
      143 0143@../input_particles.mrcs 1 0.100 2.0 300.0 1 -26.736540 75.822 
      144 0144@../input_particles.mrcs 1 0.100 2.0 300.0 1 -50.640484 101.71 
      145 0145@../input_particles.mrcs 1 0.100 2.0 300.0 1 -133.254959 123.5 
      146 0146@../input_particles.mrcs 1 0.100 2.0 300.0 1 15.199034 154.939 
      147 0147@../input_particles.mrcs 1 0.100 2.0 300.0 1 -41.141212 8.4073 
      148 0148@../input_particles.mrcs 1 0.100 2.0 300.0 1 121.380356 12.087 
      149 0149@../input_particles.mrcs 1 0.100 2.0 300.0 1 124.727844 12.823 
      150 0150@../input_particles.mrcs 1 0.100 2.0 300.0 1 121.980988 2.5535 
      151 0151@../input_particles.mrcs 1 0.100 2.0 300.0 1 132.167023 120.35 
      152 0152@../input_particles.mrcs 1 0.100 2.0 300.0 1 162.963867 135.39 
      153 0153@../input_particles.mrcs 1 0.100 2.0 300.0 1 -174.040161 97.79 
      154 0154@../input_particles.mrcs 1 0.100 2.0 300.0 1 -34.823460 67.968 
      155 0155@../input_particles.mrcs 1 0.100 2.0 300.0 1 -15.021922 23.175 
      156 0156@../input_particles.mrcs 1 0.100 2.0 300.0 1 150.969391 163.50 
      157 0157@../input_particles.mrcs 1 0.100 2.0 300.0 1 77.005096 56.4920 
      158 0158@../input_particles.mrcs 1 0.100 2.0 300.0 1 135.023376 8.4196 
      159 0159@../input_particles.mrcs 1 0.100 2.0 300.0 1 34.924160 3.29760 
      160 0160@../input_particles.mrcs 1 0.100 2.0 300.0 1 -43.574383 87.320 
      161 0161@../input_particles.mrcs 1 0.100 2.0 300.0 1 143.069733 82.825 
      162 0162@../input_particles.mrcs 1 0.100 2.0 300.0 1 -136.068146 120.0 
      163 0163@../input_particles.mrcs 1 0.100 2.0 300.0 1 45.002338 17.2367 
      164 0164@../input_particles.mrcs 1 0.100 2.0 300.0 1 -25.662224 31.832 
      165 0165@../input_particles.mrcs 1 0.100 2.0 300.0 1 33.393341 11.3414 
      166 0166@../input_particles.mrcs 1 0.100 2.0 300.0 1 -150.803650 117.2 
      167 0167@../input_particles.mrcs 1 0.100 2.0 300.0 1 -78.341667 18.350 
      168 0168@../input_particles.mrcs 1 0.100 2.0 300.0 1 159.590912 118.97 
      169 0169@../input_particles.mrcs 1 0.100 2.0 300.0 1 92.035309 41.4674 
      170 0170@../input_particles.mrcs 1 0.100 2.0 300.0 1 163.044098 145.49 
      171 0171@../input_particles.mrcs 1 0.100 2.0 300.0 1 159.315872 143.58 
      172 0172@../input_particles.mrcs 1 0.100 2.0 300.0 1 156.816818 12.091 
      173 0173@../input_particles.mrcs 1 0.100 2.0 300.0 1 147.417862 133.81 
      174 0174@../input_particles.mrcs 1 0.100 2.0 300.0 1 -34.472332 6.2093 
      175 0175@../input_particles.mrcs 1 0.100 2.0 300.0 1 -106.888313 113.6 
      176 0176@../input_particles.mrcs 1 0.100 2.0 300.0 1 -95.826973 136.57 
      177 0177@../input_particles.mrcs 1 0.100 2.0 300.0 1 -142.749680 106.6 
      178 0178@../input_particles.mrcs 1 0.100 2.0 300.0 1 179.566406 139.71 
      179 0179@../input_particles.mrcs 1 0.100 2.0 300.0 1 130.346222 47.395 
      180 0180@../input_particles.mrcs 1 0.100 2.0 300.0 1 124.281059 142.42 
      181 0181@../input_particles.mrcs 1 0.100 2.0 300.0 1 129.051224 5.4896 
      182 0182@../input_particles.mrcs 1 0.100 2.0 300.0 1 149.187607 144.73 
      183 0183@../input_particles.mrcs 1 0.100 2.0 300.0 1 -150.784378 143.9 
      184 0184@../input_particles.mrcs 1 0.100 2.0 300.0 1 17.321011 4.74460 
      185 0185@../input_particles.mrcs 1 0.100 2.0 300.0 1 147.988525 118.63 
      186 0186@../input_particles.mrcs 1 0.100 2.0 300.0 1 178.273865 150.82 
      187 0187@../input_particles.mrcs 1 0.100 2.0 300.0 1 128.335938 65.369 
      188 0188@../input_particles.mrcs 1 0.100 2.0 300.0 1 -174.356476 118.2 
      189 0189@../input_particles.mrcs 1 0.100 2.0 300.0 1 -156.108582 120.3 
      190 0190@../input_particles.mrcs 1 0.100 2.0 300.0 1 119.757042 153.82 
      191 0191@../input_particles.mrcs 1 0.100 2.0 300.0 1 -77.707909 117.27 
      192 0192@../input_particles.mrcs 1 0.100 2.0 300.0 1 -33.418175 57.903 
      193 0193@../input_particles.mrcs 1 0.100 2.0 300.0 1 -17.411888 16.126 
      194 0194@../input_particles.mrcs 1 0.100 2.0 300.0 1 4.641976 10.60578 
      195 0195@../input_particles.mrcs 1 0.100 2.0 300.0 1 153.728775 139.70 
      196 0196@../input_particles.mrcs 1 0.100 2.0 300.0 1 121.630112 48.593 
      197 0197@../input_particles.mrcs 1 0.100 2.0 300.0 1 -62.177063 23.179 
      198 0198@../input_particles.mrcs 1 0.100 2.0 300.0 1 -169.191223 150.8 
      199 0199@../input_particles.mrcs 1 0.100 2.0 300.0 1 -73.460724 109.47 
      200 0200@../input_particles.mrcs 1 0.100 2.0 300.0 1 165.254593 115.60 
      201 0201@../input_particles.mrcs 1 0.100 2.0 300.0 1 -84.383469 134.99 
      202 0202@../input_particles.mrcs 1 0.100 2.0 300.0 1 98.070877 77.9764 
      203 0203@../input_particles.mrcs 1 0.100 2.0 300.0 1 -60.129921 119.30 
      204 0204@../input_particles.mrcs 1 0.100 2.0 300.0 1 114.976379 67.326 
      205 0205@../input_particles.mrcs 1 0.100 2.0 300.0 1 -43.260380 76.745 
      206 0206@../input_particles.mrcs 1 0.100 2.0 300.0 1 -134.311462 110.4"""

    ColumnInfo = dv.models.ColumnInfo
    colInfo = [ColumnInfo('rlnImageId', dv.models.TYPE_INT),
               ColumnInfo('rlnImageData', dv.models.TYPE_STRING),
               ColumnInfo('rlnEnabled', dv.models.TYPE_BOOL),
               ColumnInfo('rlnAmplitudeContrast', dv.models.TYPE_FLOAT),
               ColumnInfo('rlnSphericalAberration', dv.models.TYPE_FLOAT),
               ColumnInfo('rlnVoltage', dv.models.TYPE_FLOAT),
               ColumnInfo('rlnGroupNumber', dv.models.TYPE_FLOAT),
               ColumnInfo('rlnAngleRot', dv.models.TYPE_FLOAT),
               ColumnInfo('rlnAngleTilt', dv.models.TYPE_FLOAT)]
    model = SimpleItemsModel(colInfo)
    for line in star.split('\n'):
        line = line.strip().split()
        line[1] = pg.gaussianFilter(np.random.normal(size=imgSize),
                                    (5, 5))
        model.addRow(line)

    return model


def createListImageModel(names, columnName, imgSize):
    """
     Creates an ListImageModel
    :param names: (list) The image names
    :param columnName: (str) The column name
    :param imgSize: (tupple) The images size
    :return: SimpleListImageModel
    """
    return SimpleListImageModel(names, columnName, imgSize)
