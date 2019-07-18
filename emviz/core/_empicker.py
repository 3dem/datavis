
import emviz.models as models

from ._image_manager import ImageManager


class EmPickerDataModel(models.PickerDataModel):
    """ Em picker data model with direct access to ImageManager """

    def __init__(self, imageManager=None):
        models.PickerDataModel.__init__(self)
        self._imageManager = imageManager or ImageManager()

    def getData(self, micId):
        """
        Return the micrograph image data
        :param micId: (int) The micrograph id
        :return: The micrograph image data
        """
        mic = self._micrographs[micId]
        return self._imageManager.getData(mic.getPath())

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
