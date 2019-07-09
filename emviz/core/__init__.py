

# FIXME: Improve documentation of the sub-module
"""
This sub-module contains functions and classes that use em-core Python binding
and provide utility functions to create views.
"""


from .functions import EmPath, EmTable, getDim, getInfo
from ._image_manager import ImageManager, ImageRef, VolImageManager
from ._models_factory import ModelsFactory
from ._views_factory import ViewsFactory
from .utils import ImageElemParser, MOVIE_SIZE
from ._emtable_model import EmTableModel, EmStackModel, EmVolumeModel, TYPE_MAP

