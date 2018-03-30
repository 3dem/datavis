#!/usr/bin/python
# -*- coding: utf-8 -*-


class ColumnProperties:
    """
    Define the column properties for a table. The properties include:
    - name
    - label
    - visible
    - allowSetVisible
    - renderable
    - allowSetRenderable
    - editable
    - allowSetEditable
    """

    def __init__(self, name, label, dataType, **kwargs):
        """
        Constructor
        :param name: column name
        :param label: column label
        :param type: column type : 'Bool', 'Int', 'Float', 'Str', 'Image'
        :param kwargs:
                        - visible (Bool)
                        - allowSetVisible (Bool)
                        - renderable (Bool)
                        - allowSetRenderable (Bool)
                        - editable (Bool)
                        - allowSetEditable (Bool)
        """
        self._name = name
        self._label = label
        self._type = dataType
        self._visible = kwargs.get('visible', True)
        self._allowSetVisible = kwargs.get('allowSetVisible', True)
        self._renderable = kwargs.get('renderable', True)
        self._allowSetRenderable = kwargs.get('allowSetRenderable', True)
        self._editable = kwargs.get('editable', True)
        self._allowSetEditable = kwargs.get('allowSetEditable', True)

    def getName(self):
        """
        Return the column name
        """
        return self._name

    def getLabel(self):
        """
        Return the column label
        """
        return self._label

    def getType(self):
        """
        Return the data type for the column
        """
        return self._type

    def isVisible(self):
        """
        Return True if this column is visible
        """
        return self._visible

    def isAllowSetVisible(self):
        """
        Return True if this column allow set visible
        """
        return self._allowSetVisible

    def isRenderable(self):
        """
        Return True if this column is renderable.
        A column is renderable if his data type is Image, Graphic, ...
        """
        return self._renderable

    def isAllowRenderable(self):
        """
        Return True if the column allow set renderable
        """
        return self._allowSetRenderable

    def isEditable(self):
        """
        Return True if the column is editable
        """
        return self._editable

    def isAllowSetEditable(self):
        """
        Return True if the column allow set editable
        """
        return self._allowSetEditable
