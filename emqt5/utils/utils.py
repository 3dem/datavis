#!/usr/bin/python
# -*- coding: utf-8 -*-

import os

import em
from emqt5.models import Coordinate, Micrograph, PickerDataModel
from emqt5.views import (ImageView, SlicesView, VolumeView, DataView,
                         TableDataModel)
from .functions import EmPath
from .image_manager import ImageManager

MOVIE_SIZE = 1000


def createImageView(path, **kwargs):
    """ Create an ImageView and load the image from the given path """
    try:
        image = em.Image()
        loc2 = em.ImageLocation(path)
        image.read(loc2)
        imgView = ImageView(None, **kwargs)
        data = ImageManager.getNumPyArray(image)
        imgView.setImage(data)
        imgView.setImageInfo(path=path, format=EmPath.getExt(path),
                             data_type=str(image.getType()))

        return imgView
    except Exception as ex:
        raise ex
    except RuntimeError as ex:
        raise ex


def createSlicesView(path, **kwargs):
    """ Create an SlicesView and load the slices from the given path """
    try:
        kwargs['path'] = path
        slicesView = SlicesView(None, **kwargs)

        return slicesView
    except Exception as ex:
        raise ex
    except RuntimeError as ex:
        raise ex


def createVolumeView(path, **kwargs):
    """ Create an VolumeView and load the volume from the given path """
    try:
        kwargs['path'] = path
        volumeView = VolumeView(None, **kwargs)

        return volumeView
    except Exception as ex:
        raise ex
    except RuntimeError as ex:
        raise ex


def createDataView(table, tableViewConfig, titles, defaultView, **kwargs):
    """ Create an DataView and load the volume from the given path """
    kwargs['view'] = defaultView
    dataView = DataView(None, **kwargs)
    path = kwargs.get('dataSource')
    dataView.setModel(TableDataModel(table, titles=titles,
                                     tableViewConfig=tableViewConfig,
                                     dataSource=path))
    dataView.setView(defaultView)
    if not (path is None or EmPath.isTable(path)):
        dataView.setDataInfo(ImageManager.getInfo(path))

    return dataView


# FIXME: Check if this classes is needed?
# FIXME: If yes, maybe moved to models._picking?
class ImageElemParser:
    """
    This class is responsible for building an ImageElem according to a specification format.
    Specification supported: JSON format. (See parseImage documentation)
    """

    def parseImage(self, jsonObj):
        """
        Parse an image specification from json object
        :param json: image specification
        :return: ImageElem

        Features:
        JSON specification for ImageElem:
        {
            "name":"image_name",
            "file":"/some/path/image_file.some",
            "box":
                  {
                    "w":20,
                    "h":20
                  }
            "coord":[
                     {
		  	          "x":20,
                      "y":20,
                      "label":"Manual"
                     },
                     {
                      "x":80,
                      "y":20,
                      "label":"Auto"
                     },
                     ...
                    ]
         }
        """
        jsonBox = jsonObj["box"].toObject()

        imageElem = Micrograph(0,
                               jsonObj["file"].toString(), [])

        self._addCoordToImage(jsonObj["coord"].toArray(), imageElem)

        return imageElem

    def _addCoordToImage(self, jsonArray, imgElem):
        """
        Add all coordinates specified in jsonArray to imgElem
        :param jsonArray: Coordinates
        :param imgElem:   Image element

        Features:
        Coordinates specification in json array format:
        [
            {
            "x":20,
            "y":20,
            "label":"Manual"
            },
            {
            "x":80,
            "y":20,
            "label":"Auto"
            },
            ...
         ]
        """
        for v in jsonArray:
            jsonC = v.toObject()
            coord = Coordinate(jsonC["x"].toInt(),
                               jsonC["y"].toInt(),
                               jsonC.get("label", "Manual"))
            imgElem.addCoordinate(coord)


def parseTextCoordinates(path):
    """ Parse (x, y) coordinates from a texfile assuming
     that the first two columns on each line are x and y.
    """
    with open(path) as f:
        for line in f:
            li = line.strip()
            if li:
                parts = li.strip().split()
                size = len(parts)
                if size == 2:  # (x, y)
                    yield int(parts[0]), int(parts[1]), ""
                elif size == 3:  # (x, y, label)
                    yield int(parts[0]), int(parts[1]), str(parts[2])
                elif size == 4:  # (x1, y1, x2, y2)
                    yield int(parts[0]), int(parts[1]), \
                          int(parts[2]), int(parts[3]), ""
                elif size == 5:  # (x1, y1, x2, y2, label):
                    yield int(parts[0]), int(parts[1]), \
                          int(parts[2]), int(parts[3]), str(parts[4])
                else:
                    yield ""


def createPickerModel(files, boxsize):
    """ Create the PickerDataModel from the given files """
    model = PickerDataModel()

    if isinstance(files, list):
        for f in files:
            if not os.path.exists(f):
                raise Exception("Input file '%s' does not exists. " % f)
            if not os.path.isdir(f):
                model.addMicrograph(f)
            else:
                raise Exception('Directories are not supported for '
                                'picker model.')

    model.setBoxSize(boxsize)
    return model
