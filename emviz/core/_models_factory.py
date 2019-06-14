
import numpy as np

import em
import emviz.models
from emviz.models import VISIBLE, EDITABLE, DESCRIPTION
from .functions import EmTable
from ._emtable_model import (EmTableModel, EmSlicesModel, EmStackModel,
                             EmVolumeModel, TYPE_MAP)


class ModelsFactory:
    """ Factory class to centralize the creation of Models using the
    underlying classes from em-core.
    """
    @classmethod
    def createImageModel(cls, path):
        """ Create an ImageModel reading path as an em.Image. """
        image = em.Image()
        loc = em.ImageLocation(path)
        image.read(loc)
        return emviz.models.ImageModel(
            data=np.array(image, copy=False), location=(loc.index, loc.path))

    @classmethod
    def createTableModel(cls, path):
        """
        Creates an TableModel reading path as an em.Table
        :param path: (str) The table path
        :return:     Tuple ([table names], TableModel)
        """
        names, table = EmTable.load(path)
        return names, EmTableModel(emTable=table)

    @classmethod
    def createStackModel(cls, path):
        """
        Creates an TableModel reading stack from the given path
        :param path: (str) The stack path
        """
        return EmStackModel(slicesModel=cls.createSlicesModel(path))

    @classmethod
    def createSlicesModel(cls, path):
        """
        Creates an SlicesModel reading slices from the given path
        :param path: (str) The image path
        """
        return EmSlicesModel(path)

    @classmethod
    def createVolumeModel(cls, path):
        """
        Creates an VolumeModel reading image datas from the given path
        :param path: (str) The volume path
        """
        return EmVolumeModel(path)

    @classmethod
    def createTableConfig(cls, table, *cols):
        """
        Create a TableModel instance from a given em.Table input.
        This function allows users to specify the minimum of properties
        and create the config from that.
        :param table: input em.Table that will be visualized
        :param cols: list of elements to specify the values for each
            ColumnConfig. Each element could be either
            a single string (the column name) or a tuple (column name and
            a dict with properties). If only the column name is provided,
            the property values will be inferred from the em.Table.Column.
        :return: a new instance of TableModel
        """
        # TODO: Implement iterColumns in table
        # tableColNames = [col.getName() for col in table.iterColumns()]
        tableColNames = [table.getColumnByIndex(i).getName()
                         for i in range(table.getColumnsSize())]

        if cols is None:
            cols = tableColNames

        tableConfig = emviz.models.TableModel()
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
                cType = TYPE_MAP.get(col.getType(), emviz.models.TYPE_STRING)
                if DESCRIPTION not in properties:
                    properties[DESCRIPTION] = col.getDescription()
                properties[EDITABLE] = False
                tableConfig.addColumn(name, cType, **properties)
                rest.remove(name)
            else:
                raise Exception("Invalid column name: %s" % name)

        # Add the others with visible=False or True if tvConfig is empty
        visible = len(tableConfig) == 0
        for colName in rest:
            col = table.getColumn(colName)
            # Take the values from the 'properties' dict or infer from col
            cType = TYPE_MAP.get(col.getType(), emviz.models.TYPE_STRING)
            properties = dict()
            properties[DESCRIPTION] = col.getDescription()
            properties[EDITABLE] = False
            properties[VISIBLE] = visible
            tableConfig.addColumnConfig(colName, cType, **properties)

        return tableConfig
