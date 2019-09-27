
import datavis.models as models

from ._image_manager import ImageManager


class EmPickerDataModel(models.PickerDataModel):
    """ Em picker data model with direct access to ImageManager """

    def __init__(self, imageManager=None):
        models.PickerDataModel.__init__(self)
        self._imageManager = imageManager or ImageManager()
        self._cache = {}

    def getData(self, micId):
        """
        Return the micrograph image data
        :param micId: (int) The micrograph id
        :return: The micrograph image data
        """
        print("Loading data...micId=%s" % micId)
        if micId in self._cache:
            data = self._cache[micId]
        else:
            print("  Computing....")
            mic = self._micrographs[micId]
            from scipy.ndimage import gaussian_filter
            import numpy as np
            data = self._imageManager.getData(mic.getPath())
            gaussian_filter(data, sigma=2, output=data)
            mean = np.mean(data)
            std = 5 * np.std(data)
            print("mean: %s, std: %s" % (mean, std))
            np.clip(data, mean - std, mean + std, out=data)
            self._cache[micId] = data

        return data

    def getImageInfo(self, micId):
        """
        Return some specified info from the given image path.
        dim : Image dimensions
        ext : File extension
        data_type: Image data type

        :param micId:  (int) The micrograph Id
        :return: dict
        """
        mic = self._micrographs[micId]
        return self._imageManager.getInfo(mic.getPath())
