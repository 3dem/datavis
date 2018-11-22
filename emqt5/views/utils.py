#!/usr/bin/python
# -*- coding: utf-8 -*-

import em

from .image_view import ImageView
from .slices_view import SlicesView
from .volume_view import VolumeView
from .data_view import DataView
from .model import TableDataModel

from emqt5.utils import EmImage

MOVIE_SIZE = 1000

def createImageView(path, **kwargs):
    """ Create an ImageView and load the image from the given path """
    try:
        image = em.Image()
        loc2 = em.ImageLocation(path)
        image.read(loc2)
        imgView = ImageView(None, **kwargs)
        data = EmImage.getNumPyArray(image)
        imgView.setImage(data)

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
    try:
        kwargs['view'] = defaultView
        dataView = DataView(None, **kwargs)
        dataView.setModel(TableDataModel(table, titles=titles,
                                         tableViewConfig=tableViewConfig,
                                         dataSource=kwargs.get('dataSource')))
        dataView.setView(defaultView)
        return dataView
    except Exception as ex:
        raise ex
    except RuntimeError as ex:
        raise ex
