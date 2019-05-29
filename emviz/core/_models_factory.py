
import numpy as np

import em
import emviz.models
from emviz.models import VISIBLE, EDITABLE, DESCRIPTION


class ModelsFactory:
    """ Factory class to centralize the creation of Models using the
    underlying classes from em-core.
    """
    # FIXME: This should be moved to emviz/core
    """ Basic type map between em.Type and current types. """
    TYPE_MAP = {
        em.typeBool: emviz.models.TYPE_BOOL,
        em.typeInt8: emviz.models.TYPE_INT,
        em.typeInt16: emviz.models.TYPE_INT,
        em.typeInt32: emviz.models.TYPE_INT,
        em.typeInt64: emviz.models.TYPE_INT,
        em.typeFloat: emviz.models.TYPE_FLOAT,
        em.typeDouble: emviz.models.TYPE_FLOAT,
        em.typeString: emviz.models.TYPE_STRING
    }

    @classmethod
    def createImageModel(cls, path):
        """ Create an ImageModel reading path as an em.Image. """
        image = em.Image()
        loc = em.ImageLocation(path)
        image.read(loc)
        return emviz.models.ImageModel(
            data=np.array(image, copy=False), location=loc)

    @classmethod
    def createTableConfig(cls, table, colsConfig=None):
        """
        Create a TableConfig instance from a given em.Table input.
        This function allows users to specify the minimum of properties
        and create the config from that.
        :param table: input em.Table that will be visualized
        :param colsConfig: list of elements to specify the values for each
            ColumnConfig. Each element could be either
            a single string (the column name) or a tuple (column name and
            a dict with properties). If only the column name is provided,
            the property values will be inferred from the em.Table.Column.
        :return: a new instance of TableConfig
        """
        # TODO: Implement iterColumns in table
        # tableColNames = [col.getName() for col in table.iterColumns()]
        tableColNames = [table.getColumnByIndex(i).getName()
                         for i in range(table.getColumnsSize())]

        if colsConfig is None:
            colsConfig = tableColNames

        tableConfig = emviz.models.TableConfig()
        rest = list(tableColNames)
        for item in colsConfig:
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
                cType = cls.TYPE_MAP.get(col.getType(), emviz.models.TYPE_STRING)
                if DESCRIPTION not in properties:
                    properties[DESCRIPTION] = col.getDescription()
                properties[EDITABLE] = False
                tableConfig.addColumnConfig(name, cType, **properties)
                rest.remove(name)
            else:
                raise Exception("Invalid column name: %s" % name)

        # Add the others with visible=False or True if tvConfig is empty
        visible = len(tableConfig) == 0
        for colName in rest:
            col = table.getColumn(colName)
            # Take the values from the 'properties' dict or infer from col
            cType = cls.TYPE_MAP.get(col.getType(), emviz.models.TYPE_STRING)
            properties = dict()
            properties[DESCRIPTION] = col.getDescription()
            properties[EDITABLE] = False
            properties[VISIBLE] = visible
            tableConfig.addColumnConfig(colName, cType, **properties)

        return tableConfig
