
import os.path as Path
import numpy as np

import emcore as emc
import datavis.models as models
from ._empath import EmPath
from ._emtype import EmType
from ._emtable_model import (EmTableModel, EmStackModel, EmVolumeModel,
                             EmListModel)
from ._empicker import EmPickerDataModel


class ModelsFactory:
    """ Factory class to centralize the creation of Models using the
    underlying classes from em-core.
    """
    @classmethod
    def createImageModel(cls, path):
        """ Create an ImageModel reading path as an emc.Image. """
        image = emc.Image()
        loc = emc.ImageLocation(path)
        image.read(loc)
        return models.ImageModel(
            data=np.array(image, copy=False), location=(loc.index, loc.path))

    @classmethod
    def createTableModel(cls, path):
        """
        Creates an TableModel reading path as an emc.Table
        :param path: (str) The table path
        :return:     TableModel
        """
        if EmPath.isTable(path):
            model = EmTableModel(path)
        elif EmPath.isStack(path):
            model = models.SlicesTableModel(EmStackModel(path), 'Index')
        elif EmPath.isVolume(path):
            slicesModel = EmVolumeModel(path).getSlicesModel(models.AXIS_Z)
            model = models.SlicesTableModel(slicesModel, 'Slice')
        else:
            raise Exception("Unknown file type: %s" % path)

        return model

    @classmethod
    def createPickerModel(cls, files, boxsize):
        """ Create the PickerDataModel from the given list of files
         files:    (list) The list of files
         boxsize:  (int) The box size
         """
        model = EmPickerDataModel()

        if isinstance(files, list):
            for f in files:
                if not Path.exists(f):
                    raise Exception("Input file '%s' does not exists. " % f)
                if not Path.isdir(f):
                    model.addMicrograph(models.Micrograph(-1, f))
                else:
                    raise Exception('Directories are not supported for '
                                    'picker model.')

        model.setBoxSize(boxsize)
        return model

    @classmethod
    def createEmptyTableModel(cls, columns=[]):
        """
        Creates an TableModel, initializing the table header from the given
        ColumnInfo list
        :param columns:  (list) List of ColumnInfo for table header
                                initialization
        :return: TableModel
        """
        Column = emc.Table.Column
        cols = []
        for i, info in enumerate(columns):
            if isinstance(info, models.ColumnInfo):
                cols.append(Column(i + 1, info.getName(),
                                   EmType.toModel(info.getType())))
            else:
                raise Exception("Invalid ColumnInfo.")

        return EmTableModel(emc.Table(cols))

    @classmethod
    def createStackModel(cls, path):
        """
        Creates an TableModel reading stack from the given path
        :param path: (str) The stack path
        """
        return EmStackModel(path)

    @classmethod
    def createVolumeModel(cls, path):
        """
        Creates an VolumeModel reading image data from the given path
        :param path: (str) The volume path
        """
        return EmVolumeModel(path)

    @classmethod
    def createListModel(cls, files):
        """ Creates an ListModel from the given file path list """
        return EmListModel(files)

    # FIXME: This method is duplicated with the one in TableModel
    # here seems a good place to have it
    @classmethod
    def createTableConfig(cls, table, *cols):
        """
        Create a TableModel instance from a given emc.Table input.
        This function allows users to specify the minimum of properties
        and create the config from that.
        :param table: input emc.Table that will be visualized
        :param cols: list of elements to specify the values for each
            ColumnConfig. Each element could be either
            a single string (the column name) or a tuple (column name and
            a dict with properties). If only the column name is provided,
            the property values will be inferred from the emc.Table.Column.
        :return: a new instance of TableModel
        """
        # TODO: Implement iterColumns in table
        # tableColNames = [col.getName() for col in table.iterColumns()]
        tableColNames = [table.getColumnByIndex(i).getName()
                         for i in range(table.getColumnsSize())]

        if cols is None:
            cols = tableColNames

        tableConfig = models.TableConfig()
        rest = list(tableColNames)
        for item in cols:
            if isinstance(item, str) or isinstance(item, unicode):
                name = item
                properties = {}
            elif isinstance(item, tuple):
                name, properties = item
            else:
                raise Exception("Invalid item type: %s" % type(item))

            # Only consider names that are present in the table ignore others
            if name in tableColNames and name in rest:
                col = table.getColumn(name)
                # Take the values from the 'properties' dict or infer from col
                cType = EmType.toModel(col.getType(),
                                       default=models.TYPE_STRING)
                if models.DESCRIPTION not in properties:
                    properties[models.DESCRIPTION] = col.getDescription()
                properties[models.EDITABLE] = False
                tableConfig.addColumnConfig(name, cType, **properties)
                rest.remove(name)
            else:
                raise Exception("Invalid column name: %s" % name)

        # Add the others with visible=False or True if tvConfig is empty
        visible = len(tableConfig) == 0
        for colName in rest:
            col = table.getColumn(colName)
            # Take the values from the 'properties' dict or infer from col
            cType = EmType.toModel(col.getType(),
                                   default=models.TYPE_STRING)
            properties = dict()
            properties[models.DESCRIPTION] = col.getDescription()
            properties[models.EDITABLE] = False
            properties[models.VISIBLE] = visible
            tableConfig.addColumnConfig(colName, cType, **properties)

        return tableConfig
