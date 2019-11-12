
from ._constants import *


class Param:
    """ Define basic properties of a parameter to be used in different contexts.

    This class is used by :class:`PickerModel <datavis.models.PickerModel>`
    class to define parameters that can be changed by the user in the GUI.
    """
    def __init__(self, paramName, paramType, **kwargs):
        """ Create a new instance.

        Args:
            paramName: Name of the param.
            paramType: Type of the param

        Keyword Args:
            value: the initial value of the param
            range: (min, max) tuple if the type is 'int' or 'float'
            label: the label to be used for display
            help: extra help message to be shown to the user
            display: optional tip about how to display this param, options:
                * default: the default for each type, most of types is textbox
                * combo, hlist, vlist for type 'enum'
                * slider for type 'int' or 'float' if range is defined

        Examples: ::

                # Enum param with many options, default display 'combo'
                job = Param('job', dv.models.PARAM_TYPE_ENUM, label='Job',
                            choices=['Student', 'Unemployed', 'Academic', 'Industry', 'Other'])

                # Another enum, but displayed as horizontal list (hlist)
                gender = Param('gender', dv.models.PARAM_TYPE_ENUM, label='Gender',
                               choices=['Male', 'Female'],
                               display=dv.models.PARAM_DISPLAY_HLIST)

                # Integer param with a given range, default display 'slider'
                happy = Param('happy', dv.models.PARAM_TYPE_INT, label='Happiness',
                              range=(1, 10), value=5,
                              help='Select how happy you are in a scale from 1 to 10')
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
        """ Set any of the attributes of this param. """
        for k, v in kwargs.items():
            setattr(self, k, v)

    @staticmethod
    def load(paramDict):
        """ Create a new Param from the dict description. """
        return Param(paramDict['name'], paramDict['type'], **paramDict)


class Form:
    """ Simple container of several params with a given layout. """

    def __init__(self, paramsList):
        """ Create a new Form instance.

        Args:
            paramsList: the parameters list that specify how they the params
                will be arranged in the GUI. Each item in the list will be
                placed in a separated row. A list of params can be used to
                group many params in the same row.

        Examples: ::

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

    @staticmethod
    def load(paramDictList):
        """ Creates a new Form from the description from a list of dict.

        Args:
            paramDictList: A list of dicts, describing each param.
                Each entry of the list will be a row. Multiple params can be
                grouped into the same row by using another list.

        Returns:
            A new :class:`Form <datavis.models.Form>` instance.

        Examples: ::

                pickerParams = [
                    {
                        'name': 'threshold',
                        'type': 'float',
                        'value': 0,
                        'range': (0., 1),
                        'label': 'Quality threshold',
                        'help': 'Quality threshold',
                        'display': 'slider'
                    },
                    {
                        'name': 'radius',
                        'type': 'int',
                        'value': self._radius,
                        'range': (1, int(self._imageSize[0]/3)),
                        'label': 'Radius',
                        'help': 'Radius',
                        'display': 'slider'
                    }
                ]

                form = dv.models.Form.load(pickerParams)
        """
        paramList = []

        for item in paramDictList:
            if isinstance(item, list):
                paramList.append([Param.load(d) for d in item])
            else:
                paramList.append([Param.load(item)])

        return Form(paramList)

