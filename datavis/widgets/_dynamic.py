
import PyQt5.QtCore as qtc
import PyQt5.QtWidgets as qtw
import PyQt5.QtGui as qtg


# TODO: Review methods, global variables, documentation, etc
# In the whole file

class ParamWidget(qtw.QWidget):
    """ Base class for all Params-Widgets """
    #  Signal emitted when the param value is changed.
    sigValueChanged = qtc.pyqtSignal(str, object)  # (paramName, value)

    def __init__(self, parent=None, specifications=dict()):
        qtw.QWidget.__init__(self, parent=parent)
        self._specifications = specifications
        self.setObjectName(specifications['name'])  # the name is mandatory
        self.setToolTip(specifications.get('help', ''))

    def setValue(self, value):
        """ Set the param value. Need to be reimplemented in subclasses. """
        raise Exception("Not implemented yet.")

    def getValue(self):
        """ Return the param value for this widget. Need to be reimplemented in
        subclasses """
        raise Exception("Not implemented yet.")

    def emitValueChanged(self, paramValue):
        self.sigValueChanged.emit(self._specifications['name'], paramValue)


class OptionList(ParamWidget):
    """
    The OptionList provides a means of presenting a list of options to the user.
    The display param specify how the options will be displayed.
    """
    def __init__(self, parent=None, exclusive=True,
                 buttonsClass=qtw.QRadioButton, specifications=dict()):
        """
        Construct an OptionList
        exclusive(bool): If true, the radio buttons will be exclusive
        buttonsClass:
        :param parent:       The QObject parent for this widget
        :param name:         (str) The param name
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
        ParamWidget.__init__(self, parent=parent, specifications=specifications)
        display = specifications.get('display', 'default')
        tooltip = specifications.get('help', "")
        options = specifications.get('choices')
        defaultOption = specifications.get('value', 0)

        self.__buttonGroup = qtw.QButtonGroup(self)
        self.__buttonGroup.setExclusive(exclusive)
        lClass = qtw.QVBoxLayout if display == 'vlist' else qtw.QHBoxLayout
        self.__mainLayout = lClass(self)
        self.__mainLayout.setContentsMargins(0, 0, 0, 0)
        self.__singleWidget = None  # may be combobox or slider
        if display == 'combo' or display == 'default':
            self.__singleWidget = qtw.QComboBox(self)
            self.__singleWidget.currentIndexChanged.connect(
                self.__onComboBoxIndexChanged)
            self.__buttonClass = None
        elif display == 'slider':
            self.__singleWidget = qtw.QSlider(qtc.Qt.Horizontal, self)
            if isinstance(options, tuple):
                self.__singleWidget.setRange(options[0], options[1])
            elif isinstance(options, list):
                self.__singleWidget.setRange(0, len(options) - 1)
            self.__singleWidget.valueChanged.connect(
                    self.__onSliderValueChanged)
        else:
            RB = qtw.QRadioButton
            CB = qtw.QCheckBox
            c = buttonsClass if (buttonsClass == RB or
                                 buttonsClass == CB) else None
            self.__buttonClass = c
            self.__singleWidget = qtw.QWidget(self)
            self.__groupBoxLayout = lClass(self.__singleWidget)
            self.__groupBoxLayout.setContentsMargins(3, 3, 3, 3)
            self.__buttonGroup.buttonClicked[int].connect(
                self.__onButtonClicked)

        if not isinstance(self.__singleWidget, qtw.QSlider):
            for index, option in enumerate(options):
                self.addOption(option, index)

        if self.__singleWidget is not None:
            self.__singleWidget.setToolTip(tooltip)
            self.__mainLayout.addWidget(self.__singleWidget)
            self.setValue(defaultOption)

        self.setLayout(self.__mainLayout)

    def __onComboBoxIndexChanged(self, index):
        """
        Invoked when the combobox current index is changed.
        :param index: (int)
        """
        self.emitValueChanged(index)

    def __onSliderValueChanged(self, value):
        """
        Invoked when the slider value is changed
        :param value: (int) The value
        """
        self.emitValueChanged(value)

    def __onButtonClicked(self, buttonId):
        """
        Invoked when the radio/check button is clicked
        :param button: (QCheckBox or QRadioButton)
        """
        self.emitValueChanged(buttonId)

    def addOption(self, name, optionId, checked=False):
        """
        Add an option
        :param name:      (str) The option name
        :param optionId:  (int) The option id
        :param checked:   (bool) Checked value if the option list is represented
                          by a RadioButton list
        """
        bc = self.__buttonClass
        if isinstance(self.__singleWidget, qtw.QComboBox):
            self.__singleWidget.addItem(name, optionId)
        elif bc is not None and isinstance(self.__singleWidget, qtw.QWidget):
            button = self.__buttonClass(self)
            button.setText(name)
            self.__buttonGroup.addButton(button, optionId)
            button.setChecked(checked)
            self.__groupBoxLayout.addWidget(button)

    def getValue(self):
        """ Return the selected options """
        if isinstance(self.__singleWidget, qtw.QComboBox):
            return self.__singleWidget.currentData()
        elif isinstance(self.__singleWidget, qtw.QSlider):
            return self.__singleWidget.value()
        elif isinstance(self.__singleWidget, qtw.QWidget):
            if self.__buttonGroup.exclusive():
                return self.__buttonGroup.checkedId()
            else:
                options = []
                for button in self.__buttonGroup.buttons():
                    if button.isChecked():
                        options.append(self.__buttonGroup.id(button))
                return options
        return None

    def setValue(self, value):
        """ Set the given option as selected """
        CB = qtw.QComboBox
        if isinstance(self.__singleWidget, qtw.QSlider):
            self.__singleWidget.setValue(value)
        elif isinstance(self.__singleWidget,
                        CB) and value in range(self.__singleWidget.count()):
            self.__singleWidget.setCurrentIndex(value)
        elif isinstance(self.__singleWidget, qtw.QWidget):
            button = self.__buttonGroup.button(value)
            if button is not None:
                button.setChecked(True)


class LineEdit(ParamWidget):
    """ """
    def __init__(self, parent=None, specifications=dict()):
        ParamWidget.__init__(self, parent=parent, specifications=specifications)
        layout = qtw.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self._lineEdit = qtw.QLineEdit(parent=self)
        t = specifications.get('type')
        if t == 'int':
            val = qtg.QIntValidator()
        elif t == 'float':
            loc = qtc.QLocale.c()
            loc.setNumberOptions(qtc.QLocale.RejectGroupSeparator)
            val = qtg.QDoubleValidator()
            val.setLocale(loc)
        else:
            val = None

        if val is not None:
            self._lineEdit.setValidator(val)
            self._lineEdit.setFixedWidth(80)

        layout.addWidget(self._lineEdit)
        self.setLayout(layout)

        self._lineEdit.returnPressed.connect(self.__onReturnPressed)

    def __onReturnPressed(self):
        self.emitValueChanged(self.getValue())

    def setValue(self, value):
        self._lineEdit.setText(str(value))

    def getValue(self):
        t = self._specifications.get('type')
        text = self._lineEdit.text()
        if t in ['float', 'int']:
            if text in ["", ".", "+", "-", '-.', '+.']:
                return 0

            return int(text) if t == 'int' else float(text)

        return text


class CheckBox(ParamWidget):
    """ """
    def __init__(self, parent=None, specifications=dict()):
        ParamWidget.__init__(self, parent=parent, specifications=specifications)
        layout = qtw.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self._checkBox = qtw.QCheckBox(parent=self)
        self._checkBox.setChecked(bool(specifications.get('value')))
        layout.addWidget(self._checkBox)
        self.setLayout(layout)

        self._checkBox.stateChanged.connect(self.__onCheckStateChanged)

    def __onCheckStateChanged(self, state):
        if state == qtc.Qt.Checked:
            self.emitValueChanged(True)
        elif state == qtc.Qt.Unchecked:
            self.emitValueChanged(False)

    def setValue(self, value):
        self._checkBox.setChecked(bool(value))

    def getValue(self):
        return self._checkBox.isChecked()


class ParamsContainer(qtw.QWidget):
    """ The base class for dynamic widgets """
    sigValueChanged = qtc.pyqtSignal(str, object)

    def __init__(self, parent=None, name='', specification=[]):
        """
        Construct an ParamsContainer object
        :param parent:  The parent widget
        :param name:    (str) The container name
        :param specifications: (dict) Params specification
        """
        qtw.QWidget.__init__(self, parent=parent)
        self.setObjectName(name)
        self.setLayout(qtw.QGridLayout())

        self.__paramsWidgets = dict()
        if isinstance(specification, list) and len(specification) > 0:
            self.__addVParamsWidgets(specification)

    def __addVParamsWidgets(self, params):
        """ Add the widgets created from params to the given QGridLayout """
        layout = self.layout()
        row = layout.rowCount()
        for param in params:
            if isinstance(param, list):
                col = 0
                row, col = self.__addHParamsWidgets(layout, param, row, col)
                row += 1
            else:
                col = 0
                widget = self.__createParamWidget(param)
                if widget is not None:
                    label = param.get('label')
                    if label is not None:
                        lab = qtw.QLabel(self)
                        lab.setText(label)
                        lab.setToolTip(param.get('help', ""))
                        layout.addWidget(lab, row, col, qtc.Qt.AlignRight)
                        col += 1
                    layout.addWidget(widget, row, col, 1, -1)
                    row += 1

    def __addHParamsWidgets(self, layout, params, row, col):
        """
        Add the params to the given layout in the row "row" from
        the column "col"
        """
        for param in params:
            if isinstance(param, list):
                row, col = self.__addHParamsWidgets(layout, param, row, col)
            elif isinstance(param, dict):
                widget = self.__createParamWidget(param)
                if widget is not None:
                    label = param.get('label')
                    if label is not None:
                        lab = qtw.QLabel(self)
                        lab.setText(label)
                        lab.setToolTip(param.get('help', ""))
                        layout.addWidget(lab, row, col, qtc.Qt.AlignRight)
                        col += 1
                    layout.addWidget(widget, row, col, 1, 1)
                    col += 1
        return row, col

    def __createParamWidget(self, param):
        """
        Creates the corresponding widget from the given param.
        """
        if not isinstance(param, dict):
            return None

        widgetName = param.get('name')
        if widgetName is None:
            return None  # rise exception??

        vType = param.get('type')
        if vType is None:
            return None  # rise exception??

        if vType == 'enum':
            widget = OptionList(parent=self,
                                exclusive=True,
                                buttonsClass=qtw.QRadioButton,
                                specifications=param)
        elif vType == 'float' or vType == 'int' or vType == 'string':
            widget = LineEdit(parent=self, specifications=param)
        elif vType == 'bool':
            widget = CheckBox(parent=self, specifications=param)

        self.setParamWidget(widgetName, param)

        if widget is not None:
            widget.sigValueChanged.connect(self._onChildChanged)

        return widget

    def __collectData(self, item):
        VBL = qtw.QVBoxLayout
        HBL = qtw.QHBoxLayout
        GL = qtw.QGridLayout
        if isinstance(item, VBL) or isinstance(item, HBL) or isinstance(item,
                                                                        GL):
            for index in range(item.count()):
                self.__collectData(item.itemAt(index))
        elif isinstance(item, qtw.QWidgetItem):
            widget = item.widget()
            param = self.__paramsWidgets.get(widget.objectName())

            if param is not None and isinstance(widget, ParamWidget):
                param['value'] = widget.getValue()

    def setParamWidget(self, name, param):
        self.__paramsWidgets[name] = param

    @qtc.pyqtSlot()
    def getParams(self):
        """ Return a dict with the current params specifications for all
        widget params. The param name will be used as key for each param. """
        self.__collectData(self.layout())
        return self.__paramsWidgets

    def _onChildChanged(self, paramName, value):
        """
         Connect this slot for child param changed notification.
         Emits sigValueChanged signal.

        :param paramName: (str) the param name
        :param value:     the data value.
        """
        self.sigValueChanged.emit(paramName, value)
