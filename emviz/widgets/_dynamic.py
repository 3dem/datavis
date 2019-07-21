
import PyQt5.QtCore as qtc
from PyQt5.QtCore import Qt, pyqtSlot
import PyQt5.QtWidgets as qtw
import PyQt5.QtGui as qtg


# TODO: Review methods, global variables, documentation, etc
# In the whole file

class OptionList(qtw.QWidget):
    """
    The OptionList provides a means of presenting a list of options to the user.
    The display param specify how the options will be displayed.
    """
    def __init__(self, parent=None, display='default', tooltip="",
                 exclusive=True, buttonsClass=qtw.QRadioButton, options=None,
                 defaultOption=0):
        """
        Construct an OptionList
        exclusive(bool): If true, the radio buttons will be exclusive
        buttonsClass:
        :param parent:       The QObject parent for this widget
        :param display:      (str) The display type for options
                             ('vlist': vertical, 'hlist': horizontal,
                             'combo': show options in combobox,
                             'slider': show options in slider)
        :param tooltip:      (str) A tooltip for this widget
        :param exclusive:    (bool) Set the options as 'exclusives' if display
                             is 'vlist' or 'hlist'
        :param buttonsClass: (QRadioButton or QCheckBox) The button class for
                             the options if display is 'vlist' or 'hlist'
        :param options:      The options. A tupple if display is 'slider' or
                             str list for other display type
        :param defaultOption: (int) The default option id (index for list)
        """
        qtw.QWidget.__init__(self, parent=parent)
        self.__buttonGroup = qtw.QButtonGroup(self)
        self.__buttonGroup.setExclusive(exclusive)
        lClass = qtw.QVBoxLayout if display == 'vlist' else qtw.QHBoxLayout
        self.__mainLayout = lClass(self)
        self.__mainLayout.setContentsMargins(0, 0, 0, 0)
        self.__singleWidget = None  # may be combobox or slider
        if display == 'combo' or display == 'default':
            self.__singleWidget = qtw.QComboBox(self)
            self.__buttonClass = None
        elif display == 'slider':
            self.__singleWidget = qtw.QSlider(Qt.Horizontal, self)
            if isinstance(options, tuple):
                self.__singleWidget.setRange(options[0], options[1])
            elif isinstance(options, list):
                self.__singleWidget.setRange(0, len(options) - 1)
        else:
            self.__buttonClass = \
                buttonsClass if buttonsClass == qtw.QRadioButton \
                                or buttonsClass == qtw.QCheckBox else None
            self.__singleWidget = qtw.QWidget(self)
            self.__groupBoxLayout = lClass(self.__singleWidget)
            self.__groupBoxLayout.setContentsMargins(3, 3, 3, 3)

        if not isinstance(self.__singleWidget, qtw.QSlider):
            for index, option in enumerate(options):
                self.addOption(option, index)

        if self.__singleWidget is not None:
            self.__singleWidget.setToolTip(tooltip)
            self.__mainLayout.addWidget(self.__singleWidget)
            self.setSelectedOption(defaultOption)

    def addOption(self, name, optionId, checked=False):
        """
        Add an option
        :param name:      (str) The option name
        :param optionId:  (int) The option id
        :param checked:   (bool) Checked value if the option list is represented
                          by a RadioButton list
        """
        if self.__buttonClass is not None \
                and isinstance(self.__singleWidget, qtw.QWidget):
            button = self.__buttonClass(self)
            button.setText(name)
            self.__buttonGroup.addButton(button, optionId)
            button.setChecked(checked)
            self.__groupBoxLayout.addWidget(button)
        elif isinstance(self.__singleWidget, qtw.QComboBox):
            self.__singleWidget.addItem(name, optionId)

    def getSelectedOptions(self):
        """ Return the selected options """
        if isinstance(self.__singleWidget, qtw.QComboBox):
            return self.__singleWidget.currentData()
        elif isinstance(self.__singleWidget, qtw.QWidget):
            if self.__buttonGroup.exclusive():
                return self.__buttonGroup.checkedId()
            else:
                options = []
                for button in self.__buttonGroup.buttons():
                    if button.isChecked():
                        options.append(self.__buttonGroup.id(button))
                return options
        elif isinstance(self.__singleWidget, qtw.QSlider):
            return self.__singleWidget.value()
        return None

    def setSelectedOption(self, optionId):
        """ Set the given option as selected """
        if isinstance(self.__singleWidget, qtw.QWidget):
            button = self.__buttonGroup.button(optionId)
            if button is not None:
                button.setChecked(True)
        elif isinstance(self.__singleWidget, qtw.QComboBox) \
                and optionId in range(self.__singleWidget.count()):
            self.__comboBox.setCurrentIndex(optionId)
        elif isinstance(self.__singleWidget, qtw.QSlider):
            self.__singleWidget.setValue(optionId)


class DynamicWidget(qtw.QWidget):
    """ The base class for dynamic widgets """
    def __init__(self, parent=None, typeParams=None):
        qtw.QWidget.__init__(self, parent=parent)
        self.setLayout(qtw.QGridLayout())
        self.__paramsWidgets = dict()
        self.__typeParams = typeParams

    def __collectData(self, item):
        if isinstance(item, qtw.QVBoxLayout) \
                or isinstance(item, qtw.QHBoxLayout) \
                or isinstance(item, qtw.QGridLayout):
            for index in range(item.count()):
                self.__collectData(item.itemAt(index))
        elif isinstance(item, qtw.QWidgetItem):
            widget = item.widget()
            param = self.__paramsWidgets.get(widget.objectName())
            if param is not None:
                t = self.__typeParams.get(param.get('type')).get('type')
                if isinstance(widget, qtw.QLineEdit):
                    if t is not None:
                        text = widget.text()
                        if text in ["", ".", "+", "-"]:
                            text = 0
                        param['value'] = t(text)
                elif isinstance(widget, qtw.QCheckBox) and t == bool:
                    # other case may be checkbox for enum: On,Off
                    param['value'] = widget.isChecked()
                elif isinstance(widget, OptionList):
                    param['value'] = widget.getSelectedOptions()

    def setParamWidget(self, name, param):
        self.__paramsWidgets[name] = param

    @pyqtSlot()
    def getParams(self):
        """ Return a dict with the current params specifications for all
        widget params. The param name will be used as key for each param. """
        self.__collectData(self.layout())
        return self.__paramsWidgets


class DynamicWidgetsFactory:
    """ Factory class to centralize the creation of widgets, using a dynamic
    widget specification.
     """

    def __init__(self):
        self.__typeParams = {
            'float': {
                'type': float,
                'display': {
                    'default': qtw.QLineEdit
                },
                'validator': qtg.QDoubleValidator
            },
            'int': {
                'type': int,
                'display': {
                    'default': qtw.QLineEdit
                },
                'validator': qtg.QIntValidator
            },
            'string': {
                'type': str,
                'display': {
                    'default': qtw.QLineEdit
                }
            },
            'bool': {
                'type': bool,
                'display': {
                    'default': qtw.QCheckBox
                }
            },
            'enum': {
                'display': {
                    'default': OptionList,
                    'vlist': OptionList,
                    'hlist': OptionList,
                    'slider': qtw.QSlider,
                    'combo': OptionList
                }
            }
        }

    def __addVParamsWidgets(self, mainWidget, params):
        """ Add the widgets created from params to the given QGridLayout """
        layout = mainWidget.layout()
        row = layout.rowCount()
        for param in params:
            if isinstance(param, list):
                col = 0
                row, col = self.__addHParamsWidgets(mainWidget, layout, param,
                                                    row, col)
                row += 1
            else:
                col = 0
                widget = self.__createParamWidget(mainWidget, param)
                if widget is not None:
                    label = param.get('label')
                    if label is not None:
                        lab = qtw.QLabel(mainWidget)
                        lab.setText(label)
                        lab.setToolTip(param.get('help', ""))
                        layout.addWidget(lab, row, col, Qt.AlignRight)
                        col += 1
                    layout.addWidget(widget, row, col, 1, -1)
                    row += 1

    def __addHParamsWidgets(self, mainWidget, layout, params, row, col):
        """
        Add the params to the given layout in the row "row" from
        the column "col"
        """
        for param in params:
            if isinstance(param, list):
                row, col = self.__addHParamsWidgets(layout, param, row, col)
            elif isinstance(param, dict):
                widget = self.__createParamWidget(mainWidget, param)
                if widget is not None:
                    label = param.get('label')
                    if label is not None:
                        lab = qtw.QLabel(mainWidget)
                        lab.setText(label)
                        lab.setToolTip(param.get('help', ""))
                        layout.addWidget(lab, row, col, Qt.AlignRight)
                        col += 1
                    layout.addWidget(widget, row, col, 1, 1)
                    col += 1
        return row, col

    def __createParamWidget(self, mainWidget, param):
        """
        Creates the corresponding widget from the given param.
        """
        if not isinstance(param, dict):
            return None

        widgetName = param.get('name')
        if widgetName is None:
            return None  # rise exception??

        valueType = param.get('type')
        if valueType is None:
            return None  # rise exception??

        paramDef = self.__typeParams.get(valueType)

        if paramDef is None:
            return None  # rise exception??

        display = paramDef.get('display')
        widgetClass = display.get(param.get('display', 'default'))

        if widgetClass is None:
            return None  # rise exception??

        if valueType == 'enum':
            widget = OptionList(parent=mainWidget,
                                display=param.get('display', 'default'),
                                tooltip=param.get('help', ""), exclusive=True,
                                buttonsClass=qtw.QRadioButton,
                                options=param.get('choices'),
                                defaultOption=param.get('value', 0))
        else:
            widget = widgetClass(mainWidget)
            widget.setToolTip(param.get('help', ''))
            self.__setParamValue(widget, param.get('value'))

        widget.setObjectName(widgetName)

        mainWidget.setParamWidget(widgetName, param)

        if widgetClass == qtw.QLineEdit:
            # widget.setClearButtonEnabled(True)
            validatorClass = paramDef.get('validator')
            if validatorClass is not None:
                val = validatorClass()
                if validatorClass == qtg.QDoubleValidator:
                    loc = qtc.QLocale.c()
                    loc.setNumberOptions(qtc.QLocale.RejectGroupSeparator)
                    val.setLocale(loc)
                widget.setValidator(val)
            if valueType == 'float' or valueType == 'int':
                widget.setFixedWidth(80)

        return widget

    def __setParamValue(self, widget, value):
        """ Set the widget value"""
        if isinstance(widget, qtw.QLineEdit):
            widget.setText(str(value))
        elif isinstance(widget, qtw.QCheckBox) and isinstance(value, bool):
            widget.setChecked(value)

    def createWidget(self, specification):
        """ Creates the widget for de given specification """
        if isinstance(specification, list) and len(specification) > 0:
            widget = DynamicWidget(typeParams=self.__typeParams)
            self.__addVParamsWidgets(widget, specification)
            return widget
        return None
