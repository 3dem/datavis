
import os
import numpy as np

import datavis.models as models
import emcore as emc


class EmType:
    """
    Helper class to group functions related to EM types.
    """
    TYPE_TO_MODELS = {
        emc.typeBool: models.TYPE_BOOL,
        emc.typeInt8: models.TYPE_INT,
        emc.typeInt16: models.TYPE_INT,
        emc.typeInt32: models.TYPE_INT,
        emc.typeInt64: models.TYPE_INT,
        emc.typeFloat: models.TYPE_FLOAT,
        emc.typeDouble: models.TYPE_FLOAT,
        emc.typeString: models.TYPE_STRING
    }

    TYPE_TO_NUMPY = {
        emc.typeInt8: np.uint8,
        emc.typeUInt8: np.uint8,
        emc.typeInt16: np.uint16,
        emc.typeUInt16: np.uint16,
        emc.typeInt32: np.uint32,
        emc.typeUInt32: np.uint32,
        emc.typeInt64: np.uint64,
        emc.typeUInt64: np.uint64
    }  # FIXME [hv] the others?

    MODELS_TYPE_TO_EM_TYPE = {
        models.TYPE_BOOL: emc.typeBool,
        models.TYPE_INT: emc.typeInt32,
        models.TYPE_FLOAT: emc.typeFloat,
        models.TYPE_STRING: emc.typeString
    }

    @classmethod
    def toModel(cls, emType, default=None):
        """ Return an equivalent models.TYPE corresponding to this emc.Type. """
        return cls.TYPE_TO_MODELS.get(emType, default)

    @classmethod
    def toNumpy(cls, emType, default=None):
        """ Return an equivalent numpy type corresponding to this emc.Type. """
        return cls.TYPE_TO_NUMPY.get(emType, default)

    @classmethod
    def toEmType(cls, mType, default=None):
        """ Return an equivalent emc.TYPE corresponding to this models.Type. """
        return cls.MODELS_TYPE_TO_EM_TYPE.get(mType, default)
