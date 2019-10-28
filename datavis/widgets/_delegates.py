#!/usr/bin/python
# -*- coding: utf-8 -*-

import PyQt5.QtCore as qtc
import PyQt5.QtWidgets as qtw

# Data roles for QtModels
DATA_ROLE = qtc.Qt.UserRole + 2
LABEL_ROLE = qtc.Qt.UserRole + 3


class ColorItemDelegate(qtw.QStyledItemDelegate):
    """
    ColorItemDelegate class provides display and editing facilities for
    color selections.
    """
    def createEditor(self, parent, option, index):
        return qtw.QColorDialog(parent=parent)

    def setEditorData(self, editor, index):
        color = index.data(qtc.Qt.BackgroundRole)
        if color is not None:
            editor.setCurrentColor(color)

    def setModelData(self, editor, model, index):
        color = editor.currentColor()
        model.setData(index, color, qtc.Qt.BackgroundRole)


class ComboBoxStyleItemDelegate(qtw.QStyledItemDelegate):
    """
    ComboBoxStyleItemDelegate class provides display and editing facilities for
    text list selection.
    """
    def __init__(self, parent=None, values=None):
        qtw.QStyledItemDelegate.__init__(self, parent=parent)
        self._values = []
        self.setValues(values)

    def setValues(self, values):
        if isinstance(values, list):
            index = 0
            for text in values:
                self._values.append((text, index))
                index += 1

    def createEditor(self, parent, option, index):
        return qtw.QComboBox(parent=parent)

    def setEditorData(self, editor, index):
        index = index.data(qtc.Qt.UserRole)
        for text, value in self._values:
            editor.addItem(text, qtc.QVariant(value))
        if index is not None:
            editor.setCurrentIndex(index)

    def setModelData(self, editor, model, index):
        data = editor.currentData()
        model.setData(index, data, qtc.Qt.UserRole)
        text = editor.currentText()
        model.setData(index, text, qtc.Qt.DisplayRole)


class MarkerStyleItemDelegate(qtw.QStyledItemDelegate):
    """
    MarkerStyleItemDelegate class provides display and editing facilities for
    QPen style selection.
    """
    def createEditor(self, parent, option, index):
        return qtw.QComboBox(parent=parent)

    def setEditorData(self, editor, index):
        index = index.data(qtc.Qt.UserRole)
        editor.addItem('Solid', qtc.QVariant(qtc.Qt.SolidLine))
        editor.addItem('Dashed', qtc.QVariant(qtc.Qt.DashLine))
        editor.addItem('Dotted', qtc.QVariant(qtc.Qt.DotLine))
        if index is not None:
            editor.setCurrentIndex(index)

    def setModelData(self, editor, model, index):
        data = editor.currentData()
        model.setData(index, data, qtc.Qt.UserRole)
        text = editor.currentText()
        model.setData(index, text, qtc.Qt.DisplayRole)


class ColumnPropertyItemDelegate(qtw.QItemDelegate):
    """ Class used to provide custom display features for column properties """
    def __init__(self, parent=None, checkedIcon=None, uncheckedIcon=None,
                 partiallyCheckedIcon=None):
        qtw.QItemDelegate.__init__(self, parent=parent)
        self.__checkedIcon = checkedIcon
        self.__uncheckedIcon = uncheckedIcon
        self.__partiallyCheckedIcon = partiallyCheckedIcon

    def drawCheck(self, painter, option, rect, state):
        if rect is not None and rect.isValid():
            icon = None

            if state == qtc.Qt.Checked and self.__checkedIcon is not None:
                icon = self.__checkedIcon
            elif state == qtc.Qt.Unchecked and self.__uncheckedIcon is not None:
                icon = self.__uncheckedIcon
            elif state == (qtc.Qt.PartiallyChecked
                           and self.__partiallyCheckedIcon is not None):
                icon = self.__partiallyCheckedIcon

            if icon is not None:
                painter.drawImage(rect.x(), rect.y(), icon)
            else:
                qtw.QItemDelegate.drawCheck(self, painter, option, rect, state)


