

# FIXME: Improve documentation of the sub-module
"""
This sub-module contains functions and classes that use em-core Python binding
and provide utility functions to create views.
"""


from .functions import EmPath, EmTable
from ._image_manager import (ImageManager, ImageRef, parseImagePath,
                             VolImageManager)
from ._models_factory import ModelsFactory
from ._views_factory import ViewsFactory
from .utils import ImageElemParser
from ._emtable_model import (EmTableModel, EmStackModel, EmSlicesModel,
                             EmVolumeModel, TYPE_MAP)

