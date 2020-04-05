#!/usr/bin/python
# -*- coding: utf-8 -*-

import datavis as dv


class TestParams(dv.tests.TestView):
    __title = "Params example"

    def __init__(self, methodName='runTest'):
        Param = dv.models.Param

        name = Param('name', dv.models.PARAM_TYPE_STRING, label='Name',
                     value='Pepe',
                     help='Enter your name.')

        surname = Param('surname', dv.models.PARAM_TYPE_STRING, label='Surname',
                        help='Enter your surname.')

        gender = Param('gender', dv.models.PARAM_TYPE_ENUM, label='Gender',
                       choices=['Male', 'Female'],
                       display=dv.models.PARAM_DISPLAY_HLIST)

        age = Param('age', dv.models.PARAM_TYPE_INT, label='Age')

        job = Param('job', dv.models.PARAM_TYPE_ENUM, label='Job',
                    choices=['Student', 'Unemployed', 'Academic', 'Industry',
                             'Other'])

        happy = Param('happy', dv.models.PARAM_TYPE_INT, label='Happiness',
                      range=(1, 10), value=5,
                      help='Select how happy you are in a scale from 1 to 10')

        scale = Param('scale', dv.models.PARAM_TYPE_FLOAT, value=0.5,
                      range=(0., 1),
                      label='Scale',
                      help='Just to show a float value with slider')

        hobby = Param('hobby', dv.models.PARAM_TYPE_ENUM, label='Hobby',
                      choices=['Sports', 'Paiting', 'Literature', 'Other'],
                      display=dv.models.PARAM_DISPLAY_VLIST, value=1)

        conditions = Param('conditions', dv.models.PARAM_TYPE_BOOL,
                           label='Agree on \nTerms and Conditions?',
                           value=True)

        submit = Param('submit', dv.models.PARAM_TYPE_BUTTON,
                       label='Submit')

        self.form = dv.models.Form([[name, surname],
                                    [gender, age, happy],
                                    [job, hobby, scale],
                                    [conditions, submit]
                                    ])

        dv.tests.TestView.__init__(self, methodName=methodName)

    def createView(self):
        widget = dv.widgets.FormWidget(self.form, parent=None)
        widget.sigValueChanged.connect(self.paramChanged)

        return widget

    def paramChanged(self, paramName, value):
        if paramName == 'submit':
            print("Submitting data: ")
            centralWidget = self.win.centralWidget()
            values = centralWidget.getParamValues()
            for k, v in values.items():
                print("   %s = %s" % (k, v))
        else:
            print("Changed:\n   %s = %s" % (paramName, value))

    def test_Params(self):
        print('test_Params')


if __name__ == '__main__':
    TestParams().runApp()
