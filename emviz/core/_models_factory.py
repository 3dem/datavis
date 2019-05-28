
import numpy as np

import em
import emviz.models


class ModelsFactory:
    """ Factory class to centralize the creation of Models using the
    underlying classes from em-core.
    """

    @staticmethod
    def createImageModel(path):
        """ Create an ImageModel reading path as an em.Image. """
        image = em.Image()
        loc = em.ImageLocation(path)
        image.read(loc)
        return emviz.models.ImageModel(
            data=np.array(image, copy=False), location=loc)
