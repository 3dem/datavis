
from ._constants import *


class Param:
    """
    Simple class to define properties of parameters that can
    be defined by the PickerDataModel and can be used by GUI
    components to create widgets to interact with the user.
    """
    def __init__(self, paramName, paramType, **kwargs):
        """
        Create a new PickerParam
        :param paramName: name of the param
        :param paramType: type of the param
        :param kwargs: other properties that can be defined:
            value: the initial value of the param
            range: (min, max) tuple if the type is 'int' or 'float'
            label: the label to be used for display
            help: extra help message to be shown to the user
            display: optional tip about how to display this param, options:
                - default: the default for each type, most of types is textbox
                - combo, hlist, vlist for type 'enum'
                - slider for type 'int' or 'float' if range is defined
        """
        self.name = paramName
        self.type = paramType
        # Provide default values for the following options but they will be
        # overwritten if passed in kwargs
        self.help = ''
        self.display = PARAM_DISPLAY_DEFAULT

        # Check that non-empty label is provided
        if not kwargs.get('label', ''):
            raise Exception("Non-empty label should be provided!")

        self.set(**kwargs)

    def set(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class Form:
    """
    Simple container of several Param instances that can
    be arrange into one or many rows.
    """
    def __init__(self, paramsList):
        """
        Create a new instance of Form.
        :param paramsList: the parameters list that specify how they the params
            will be arranged in the GUI.
            Each item in the list will be placed in a separated row.
            A list of params can be used to group many params in the same row.
            Example:
            f = Form([param1,
                      param2,
                      [param3, param4, param5]
                     ])
        """
        self._paramsDict = {}
        self._paramsList = []

        def __register(param):
            if not isinstance(param, Param):
                raise Exception("Invalid input, expecting Param instance!")

            self._paramsDict[param.name] = param

        for row in paramsList:
            if isinstance(row, list):
                for param in row:
                    __register(param)
                self._paramsList.append(row)
            else:
                __register(row)
                self._paramsList.append([row])

    def __iter__(self):
        """ Iterate over rows of params. """
        for row in self._paramsList:
            yield row

    def __contains__(self, paramName):
        """ Return True if there is a param with the given name. """
        return paramName in self._paramsDict

    def __getitem__(self, paramName):
        """ Return the param with this name. """
        return self._paramsDict[paramName]

