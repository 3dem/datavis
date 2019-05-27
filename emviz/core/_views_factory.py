
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
        imgView.setImage(imgModel.getData())

    @staticmethod
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

    @staticmethod
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

    @staticmethod
    def createDataView(table, tableViewConfig, titles, defaultView, **kwargs):
        """ Create an DataView and load the volume from the given path """
        kwargs['view'] = defaultView
        dataView = DataView(None, **kwargs)
        path = kwargs.get('dataSource')
        dataView.setModel(TableDataModel(table, titles=titles,
                                         tableViewConfig=tableViewConfig,
                                         dataSource=path))
        dataView.setView(defaultView)
        if not (path is None or EmPath.isTable(path)):
            dataView.setDataInfo(ImageManager.getInfo(path))

        return dataView