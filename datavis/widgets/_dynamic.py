
import PyQt5.QtCore as qtc
import PyQt5.QtWidgets as qtw
import PyQt5.QtGui as qtg

import datavis as dv


class ParamWidget(qtw.QWidget):
    """ ParamWidget is the base class for all Params-Widgets. A parameter is an
    abstract entity defined by a basic properties of a parameter to be used in
    different context """
    #  Signal emitted when the param value is changed.
    sigValueChanged = qtc.pyqtSignal(str, object)  # (paramName, value)

    def __init__(self, param, parent=None):
        """ Construct a ParamWidget instance

        Args:
            param:   :class:`Param <datavis.models.Param>`
            parent:  The parent widget
        """
        qtw.QWidget.__init__(self, parent=parent)
        self._param = param
        self._sizePolicy = qtw.QSizePolicy(qtw.QSizePolicy.Expanding,
                                           qtw.QSizePolicy.Minimum)
        self.setObjectName(param.name)  # the name is mandatory
        self.setToolTip(param.help)

    def set(self, value):
        """ Set the param value. Need to be reimplemented in subclasses. """
        raise Exception("Not implemented yet.")

    def get(self):
        """ Return the param value for this widget. Need to be reimplemented in
        subclasses """
        raise Exception("Not implemented yet.")

    def emitValueChanged(self, paramValue):
        """ Emits the sigValueChanged signal """
        self.sigValueChanged.emit(self._param.name, paramValue)


class OptionsWidget(ParamWidget):
    """
    The OptionsWidget provides a means of presenting a list of options
    to the user. The display param specify how the options will be displayed.
    """
    def __init__(self, param, parent=None):
        """ Construct an OptionsWidget

        Args:
            param:   :class:`Param <datavis.models.Param>`
            parent:  The parent QWidget
        """
        ParamWidget.__init__(self, param, parent=parent)
        display = param.display
        self._value = getattr(param, 'value', 0)
        layout = qtw.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        if display in [dv.models.PARAM_DISPLAY_VLIST,
                       dv.models.PARAM_DISPLAY_HLIST]:
            layout.addWidget(self.__createList(param))
        else:
            layout.addWidget(self.__createCombo(param))

        self.setLayout(layout)

    def __createList(self, param):
        """ Create the options list specified by the given
        :class:`Param <datavis.models.Param>` """
        listWidget = qtw.QWidget(self)
        group = qtw.QButtonGroup(self)
        group.setExclusive(True)

        if param.display == dv.models.PARAM_DISPLAY_HLIST:
            layout = qtw.QHBoxLayout()
        elif param.display == dv.models.PARAM_DISPLAY_VLIST:
            layout = qtw.QVBoxLayout()
        else:
            raise Exception('Unknown display %s for enum type'
                            % param.display)

        layout.setContentsMargins(3, 3, 3, 3)
        butttonList = []
        for i, opt in enumerate(param.choices):
            rb = qtw.QRadioButton(opt)
            rb.setChecked(self._value == i)
            group.addButton(rb, i)
            layout.addWidget(rb)
            butttonList.append(rb)

        listWidget.setLayout(layout)
        group.buttonClicked[int].connect(self.__onSelectionChanged)

        # Define how to set a new value for this case
        def set(value):
            butttonList[value].setChecked(True)

        self.__setValue = set

        return listWidget

    def __createCombo(self, param):
        """ Create a combobox widget containing the options specified by
        the given :class:`Param <datavis.models.Param>` """
        combo = qtw.QComboBox(self)
        for i, opt in enumerate(param.choices):
            combo.addItem(opt, i)
        combo.currentIndexChanged.connect(self.__onSelectionChanged)
        self.__buttonClass = None

        # Define how to set a new value for this case
        def set(value):
            combo.setCurrentIndex(value)
        self.__setValue = set

        return combo

    def __onSelectionChanged(self, index):
        """
        Invoked when the selected item has been changed(either in combo or list)

        Arg:
           index: (int) The new selected index
        """
        self._value = index
        self.emitValueChanged(index)

    def get(self):
        """
        Reimplemented from :class:`ParamWidget <datavis.widgets.ParamWidget>`
        """
        return self._value

    def set(self, value):
        """ Set the given option as selected.
        Reimplemented from :class:`ParamWidget <datavis.widgets.ParamWidget>`
        """
        n = len(self._param.choices)
        if value < 0 or value >= n:
            raise Exception("Invalid index '%d', value should be "
                            "between 0 and %d" % (value, n))

        self.__setValue(value)


class TextWidget(ParamWidget):
    """ The TextWidget is a one-line text editor. """

    def __init__(self, param, parent=None):
        """ Construct an TextWidget instance.

        Args:
            param:   :class:`Param <datavis.models.Param>`
            parent:  The parent widget
        """
        ParamWidget.__init__(self, param, parent=parent)
        layout = qtw.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self._lineEdit = qtw.QLineEdit(parent=self)
        layout.addWidget(self._lineEdit)
        self.setLayout(layout)
        value = getattr(param, 'value', None)
        if value is not None:
            self.set(value)
        self._lineEdit.returnPressed.connect(self.__onReturnPressed)

    def __onReturnPressed(self):
        """ Invoked when the user press Enter """
        self.emitValueChanged(self.get())

    def set(self, value):
        """
        Reimplemented from :class:`ParamWidget <datavis.widgets.ParamWidget>`.
        Set the given value as the current text.
        """
        self._lineEdit.setText(str(value))

    def get(self):
        """
        Reimplemented from :class:`ParamWidget <datavis.widgets.ParamWidget>`.

        Returns:
            The current text
        """
        return self._lineEdit.text()


class NumericWidget(ParamWidget):
    """ The NumericWidget is a one-line numbers editor.
    It supports the following types: integer, float """
    def __init__(self, param, parent=None):
        ParamWidget.__init__(self, param, parent=parent)
        layout = qtw.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        pType = param.type

        if pType == dv.models.PARAM_TYPE_INT:
            val = qtg.QIntValidator()
            self._type = int
        elif pType == dv.models.PARAM_TYPE_FLOAT:
            loc = qtc.QLocale.c()
            loc.setNumberOptions(qtc.QLocale.RejectGroupSeparator)
            val = qtg.QDoubleValidator()
            val.setLocale(loc)
            self._type = float
        else:
            raise Exception('Invalid type %s' % pType)

        range = getattr(param, 'range', None)

        if range is not None:
            minValue, maxValue = range
            value = getattr(param, 'value', minValue)
            widget = dv.widgets.SpinSlider(parent=self, currentValue=value,
                                           minValue=range[0], maxValue=range[1])
            widget.setValue(value)
            widget.sigValueChanged.connect(self.__onValueChanged)
            self.get = lambda: widget.getValue()
            self.set = lambda value: widget.setValue(value)
        else:
            widget = qtw.QLineEdit(parent=self)
            widget.setValidator(val)
            widget.setFixedWidth(80)
            value = getattr(param, 'value', None)
            if value is not None:
                widget.setText(str(value))
            widget.returnPressed.connect(self.__onReturnPressed)
            self.get = lambda : self.__getNumeric(widget.text())
            self.set = lambda value: widget.setValue(str(value))

        layout.addWidget(widget)
        self.setLayout(layout)

    def __onReturnPressed(self):
        self.emitValueChanged(self.get())

    def __onValueChanged(self, value):
        self.emitValueChanged(value)

    def __getNumeric(self, value):
         #FIXME: What is the purpose of this validation?
         invalid = ["", ".", "+", "-", '-.', '+.']
         return None if value in invalid else self._type(value)


class BoolWidget(ParamWidget):
    """ ParamWidget subclass that wraps a Param with 'bool' type. """
    def __init__(self, param, parent=None):
        """
        Construct an BoolWidget instance.
        Args:
            param:   :class:`Param <datavis.models.Param>`
            parent:  The parent widget
        """
        ParamWidget.__init__(self, param, parent=parent)
        layout = qtw.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self._checkBox = qtw.QCheckBox(parent=self)
        self._checkBox.setChecked(bool(getattr(param, 'value', False)))
        layout.addWidget(self._checkBox)
        self.setLayout(layout)

        self._checkBox.stateChanged.connect(self.__onCheckStateChanged)

    def __onCheckStateChanged(self, state):
        """ Invoked when the current state has been changed """
        self.emitValueChanged(state == qtc.Qt.Checked)

    def set(self, value):
        """
        Reimplemented from :class:`ParamWidget <datavis.widgets.ParamWidget>`
        """
        self._checkBox.setChecked(bool(value))

    def get(self):
        """
        Reimplemented from :class:`ParamWidget <datavis.widgets.ParamWidget>`
        """
        return self._checkBox.isChecked()


class ButtonWidget(ParamWidget):
    """ ParamWidget subclass that wraps a Param with 'button' type. """
    def __init__(self, param, parent=None):
        """
        Construct an BoolWidget instance.
        Args:
            param:   :class:`Param <datavis.models.Param>`
            parent:  The parent widget
        """
        ParamWidget.__init__(self, param, parent=parent)
        layout = qtw.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        btn = qtw.QPushButton(param.label, parent=self)
        if param.help:
            btn.setToolTip(param.help)

        layout.addWidget(btn)
        self.setLayout(layout)
        btn.clicked.connect(self.__onClicked)

    def __onClicked(self):
        """ Invoked when the button has been clicked """
        self.emitValueChanged(True)  # just to notify

    def set(self, value):
        pass

    def get(self):
        return False


class FormWidget(qtw.QWidget):
    """ The FormWidget is the container widget for a ordered
    group of :class:`Params <datavis.models.Param>`"""
    sigValueChanged = qtc.pyqtSignal(str, object)

    # Map between the Param type and the associated Widget class
    CLASSES_DICT = {
        dv.models.PARAM_TYPE_ENUM: OptionsWidget,
        dv.models.PARAM_TYPE_BOOL: BoolWidget,
        dv.models.PARAM_TYPE_INT: NumericWidget,
        dv.models.PARAM_TYPE_FLOAT: NumericWidget,
        dv.models.PARAM_TYPE_BUTTON: ButtonWidget,
    }

    def __init__(self, form, parent=None, name=''):
        """ Construct an FormWidget instance

        Args:
            form: :class:`Form <datavis.models.Form>` instance with
                the definition of the params.
            parent: The parent widget
            name: (str) The container name
        """
        # FIXME: Is the name useful?
        qtw.QWidget.__init__(self, parent=parent)
        self.setObjectName(name)
        self.setLayout(qtw.QGridLayout())
        self._widgetsDict = dict()
        self.__createFormWidgets(form)

    def __createFormWidgets(self, form):
        """ Add the widgets created from params to the given QGridLayout """
        layout = self.layout()
        row = layout.rowCount()
        for r, params in enumerate(form):
            for col, param in enumerate(params):
                # Only the special case of button does not require extra label
                if param.type != dv.models.PARAM_TYPE_BUTTON:
                    label = qtw.QLabel(param.label, parent=self)
                    layout.addWidget(label, row+r, 2*col, qtc.Qt.AlignRight)
                widget = self.__createParamWidget(param)
                layout.addWidget(widget, row+r, 2*col+1) #, 1, -1)
                if param.help:
                    label.setToolTip(param.help)
                    widget.setToolTip(param.help)

    def __createParamWidget(self, param):
        """ Creates the corresponding widget from the given param. """
        if not param.name or not param.type or not param.label:
            raise Exception("Invalid param, empty name, type or label!")

        # Get the widget class associated to the given Param type
        # by default create a NumericWidget
        WidgetClass = self.CLASSES_DICT.get(param.type, TextWidget)
        widget = WidgetClass(param, parent=self)
        self._widgetsDict[param.name] = widget
        widget.sigValueChanged.connect(self._onChildChanged)
        return widget

    def getParamValues(self):
        """ Return a dict with the value of each of the input params.
         The key of each item will be the param's name and the value
         the current value from the GUI.
        """
        values = {}
        for key, widget in self._widgetsDict.items():
            values[key] = widget.get()
        return values

    def _onChildChanged(self, paramName, value):
        """
        Connect this slot for child param changed notification.
        Emits sigValueChanged signal.

        Args:
            paramName: (str) the param name
            value:     the data value.
        """
        self.sigValueChanged.emit(paramName, value)
