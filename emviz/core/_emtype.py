
import os
import numpy as np

import emviz.models as models
import em


class EmType:
    """
    Helper class to group functions related to EM types.
    """
    TYPE_TO_MODELS = {
        em.typeBool: models.TYPE_BOOL,
        em.typeInt8: models.TYPE_INT,
        em.typeInt16: models.TYPE_INT,
        em.typeInt32: models.TYPE_INT,
        em.typeInt64: models.TYPE_INT,
        em.typeFloat: models.TYPE_FLOAT,
        em.typeDouble: models.TYPE_FLOAT,
        em.typeString: models.TYPE_STRING
    }

    TYPE_TO_NUMPY = {
        em.typeInt8: np.uint8,
        em.typeUInt8: np.uint8,
        em.typeInt16: np.uint16,
        em.typeUInt16: np.uint16,
        em.typeInt32: np.uint32,
        em.typeUInt32: np.uint32,
        em.typeInt64: np.uint64,
        em.typeUInt64: np.uint64
    }  # FIXME [hv] the others?

    @classmethod
    def toModel(cls, emType, default=None):
        """ Return an equivalent models.TYPE corresponding to this em.Type. """
        return cls.TYPE_TO_MODELS.get(emType, default)

    @classmethod
    def toNumpy(cls, emType, default=None):
        """ Return an equivalent numpy type corresponding to this em.Type. """
        return cls.TYPE_TO_NUMPY.get(emType, default)


