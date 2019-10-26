#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys

import PyQt5.QtWidgets as qtw
import PyQt5.QtCore as qtc

import qtawesome as qta

import datavis as dv


app = qtw.QApplication(sys.argv)

win = qtw.QMainWindow()
win.resize(500, 300)

Param = dv.models.Param

name = Param('name', dv.models.PARAM_TYPE_STRING, label='Name',
             value='Pepe',
             help='Enter your name.')

surname = Param('surname', dv.models.PARAM_TYPE_STRING, label='Surname',
                help='Enter your surname.')

gender = Param('gender', dv.models.PARAM_TYPE_ENUM, label='Gender',
               choices=['Male', 'Female'], display=dv.models.PARAM_DISPLAY_HLIST)

age = Param('age', dv.models.PARAM_TYPE_INT, label='Age')

job = Param('job', dv.models.PARAM_TYPE_ENUM, label='Job',
            choices=['Student', 'Unemployed', 'Academic', 'Industry', 'Other'])

happy = Param('happy', dv.models.PARAM_TYPE_INT, label='Happiness',
              range=(1, 10), value=5,
              help='Select how happy you are in a scale from 1 to 10')

scale = Param('scale', dv.models.PARAM_TYPE_FLOAT, value=0.5, range=(0., 1),
              label='Scale', help='Just to show a float value with slider')

hobby = Param('hobby', dv.models.PARAM_TYPE_ENUM, label='Hobby',
              choices=['Sports', 'Paiting', 'Literature', 'Other'],
              display=dv.models.PARAM_DISPLAY_VLIST, value=1)


conditions = Param('conditions', dv.models.PARAM_TYPE_BOOL,
                   label='Agree on \nTerms and Conditions?',
                   value=True)

submit = Param('submit', dv.models.PARAM_TYPE_BUTTON,
               label='Submit')

form = dv.models.Form([[name, surname],
                       [gender, age, happy],
                       [job, hobby, scale],
                       [conditions, submit]
                       ])

centralWidget = dv.widgets.FormWidget(form, parent=None)


def paramChanged(paramName, value):
    if paramName == 'submit':
        print("Submitting data: ")
        values = centralWidget.getParamValues()
        for k, v in values.items():
            print("   %s = %s" % (k, v))
    else:
        print("Changed:\n   %s = %s" % (paramName, value))

centralWidget.sigValueChanged.connect(paramChanged)

centralLayout = qtw.QHBoxLayout(centralWidget)
win.setCentralWidget(centralWidget)
win.show()
win.setWindowTitle('Params Example')

sys.exit(app.exec_())
