

# FIXME: Improve documentation of the sub-module
"""
This sub-module contains functions and classes that use em-core Python binding
and provide utility functions to create views.
"""


from .functions import EmPath, EmTable
from .image_manager import (ImageManager, ImageRef, parseImagePath,
                            VolImageManager)

from .utils import (createImageView, createSlicesView, createVolumeView,
                    createDataView, createPickerModel, parseTextCoordinates,
                    ImageElemParser)
