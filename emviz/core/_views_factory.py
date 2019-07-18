
import emviz.views

from ._models_factory import ModelsFactory


class ViewsFactory:
    """ Factory class to centralize the creation of Views, using the
    underlying classes from em-core.
    """

    @staticmethod
    def createImageView(path, **kwargs):
        """ Create an ImageView and load the image from the given path """
        imgView = emviz.views.ImageView(None, **kwargs)
        imgModel = ModelsFactory.createImageModel(path)
        imgView.setModel(imgModel)
        return imgView

    @staticmethod
    def createSlicesView(path, **kwargs):
        """ Create an SlicesView and load the slices from the given path """
        model = ModelsFactory.createStackModel(path)
        return emviz.views.SlicesView(None, sliceModel=model,  **kwargs)


    @staticmethod
    def createVolumeView(path, **kwargs):
        """ Create an VolumeView and load the volume from the given path """
        model = ModelsFactory.createVolumeModel(path)
        return emviz.views.VolumeView(None, model=model, **kwargs)

    @staticmethod
    def createDataView(path, **kwargs):
        """ Create an DataView and load the volume from the given path """
        model = ModelsFactory.createTableModel(path)
        return emviz.views.DataView(None, model=model, **kwargs)

    @staticmethod
    def createPickerView(micFiles, **kwargs):
        """
        Create an PickerView
        :param files: (list) Micrograph paths or None
        :param kwargs:
           - boxSize:  (int) The box size. Default value is 100
        """
        model = ModelsFactory.createPickerModel(micFiles,
                                                kwargs.get('boxSize', 100))
        #PickerView(None, m, sources=args.picker, **kwargs)
        return emviz.views.PickerView(None, model=model, **kwargs)
