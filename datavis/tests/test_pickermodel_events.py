#!/usr/bin/python
# -*- coding: utf-8 -*-

import datavis as dv
from datavis.models import ColumnConfig, TYPE_STRING, TYPE_INT

import threading

import PyQt5.QtGui as qtg
import PyQt5.QtCore as qtc


class CoordLoader(threading.Thread):
    """ The CoordLoader class provides a simple way to load coordinates for a
    Micrograph stack.
    """
    def __init__(self, model):
        threading.Thread.__init__(self)
        self._model = model
        self._maxCount = 200  # maximum coordinates count (only for test)
        self._coordBlock = 3  # coordinates block (only for test)
        self._waitTime = 1  # wait time for the next load in seconds
        self._stack = []
        self._currentMic = -1
        self._condition = threading.Condition()
        self._stopEvent = threading.Event()

    def _loadCoordinates(self):
        w, h = self._model.getImageInfo(self._currentMic)['dim']
        self._condition.wait(self._waitTime)
        return [self._model._randomCoord(w, h) for i in range(self._coordBlock)]

    def addMicrograph(self, micId):
        """ Append new micrograph to the micrograph stack """
        if self.is_alive():
            with self._condition:
                self._stack.append(micId)
                self._condition.notify()

    def run(self):
        Result = dv.models.PickerModel.Result
        with self._condition:
            while not self._stopEvent.is_set():
                if not self._stack:
                    print('ok Loader is waiting for micrograph...')
                    self._condition.wait()

                if self._stack:
                    micId = self._stack.pop()
                    self._currentMic = self._model.getMicrograph(micId)
                    cont = True
                    while cont and len(self._currentMic) < self._maxCount:
                        self._stack.append(micId)
                        coords = self._loadCoordinates()
                        self._model.addCoordinates(micId, coords)
                        self._model.notifyEvent(
                            info=Result(micId=micId, coordsAdded=True,
                                        coords=coords))
                        print('mic len= %d' % len(self._currentMic))

                        micId = self._stack.pop()
                        if not micId == self._currentMic.getId():
                            cont = False
                            self._stack.append(micId)
                        else:
                            cont = not self._stopEvent.is_set()

    def stop(self):
        self._stopEvent.set()


class MyPickerModel(dv.tests.SimplePickerModel):
    def __init__(self, *args, **kwargs):
        dv.tests.SimplePickerModel.__init__(self, *args, **kwargs)
        self._scoreThreshold = 0.5
        # Modify 'Auto' label to set red color
        self._labels['A'] = self._labels['A']._replace(color='#FF0000')
        self._showBelow = True
        self._coordLoader = CoordLoader(self)
        self._coordLoader.start()

    def __del__(self):
        self._coordLoader.stop()

    def __coordsBelow(self, micId):
        return len([c for c in self._getCoordsList(micId)
                    if c.score < self._scoreThreshold])

    def beginLoadCoordinates(self, micId):
        """ Append the given micrograph id to the loader. """
        self._coordLoader.addMicrograph(micId)

    def getParams(self):
        Param = dv.models.Param
        scoreThreshold = Param('scoreThreshold', 'float', value=0.5,
                               display='slider', range=(0, 1.0),
                               label='Score threshold',
                               help='Display coordinates with score above '
                                    'this value.')

        showBelow = Param('showBelow', 'bool', value=self._showBelow,
                          label='Show coordinates below?')

        nParam = Param('n', 'int', value=100,
                       label='Particles:',
                       help='Number of particles that you will pick randomly'
                            ' from the current micrograph.')

        clear = Param('clear', 'button', label='Clear coordinates')
        pick = Param('pick', 'button', label='Pick Again')

        return dv.models.Form([
            [scoreThreshold, showBelow],
            [pick, nParam],
            clear
        ])

    def changeParam(self, micId, paramName, paramValue, getValuesFunc):
        # Most cases here will modify the current coordinates
        r = self.Result(currentCoordsChanged=True, tableModelChanged=True)

        if paramName in ['pick', 'n']:
            values = getValuesFunc()
            self.pickRandomly(micId, n=values['n'])
        elif paramName == 'scoreThreshold':
            self._scoreThreshold = getValuesFunc()['scoreThreshold']
        elif paramName == 'clear':
            self.clearMicrograph(micId)
        elif paramName == 'showBelow':
            self._showBelow = getValuesFunc()['showBelow']
        else:
            r = self.Result()  # No modification

        return r

    def iterCoordinates(self, micId):
        # Re-implement this to show only these above the threshold
        # or with a different color (label)
        for coord in self._getCoordsList(micId):
            good = coord.score > self._scoreThreshold
            coord.label = 'M' if good else 'A'
            if good or self._showBelow:
                yield coord

    def getColumns(self):
        """ Return a Column list that will be used to display micrographs. """
        return [
            ColumnConfig('Micrograph', dataType=TYPE_STRING, editable=False),
            ColumnConfig('Coords', dataType=TYPE_INT, editable=False),
            ColumnConfig('Coords < Threshold', dataType=TYPE_INT,
                         editable=False),
            ColumnConfig('Id', dataType=TYPE_INT, editable=False, visible=False)
        ]

    def getValue(self, row, col):
        # Re-implement this to show only these above the threshold
        mic = self.getMicrographByIndex(row)
        micId = mic.getId()

        if col == 0:  # Name
            return 'Micrograph %02d' % micId
        elif col == 1:  # Coordinates
            return len(mic) - self.__coordsBelow(micId)
        elif col == 2:  # Coordinates below threshold
            return self.__coordsBelow(micId)
        elif col == 3:  # Id
            return mic.getId()
        else:
            raise Exception("Invalid column value '%s'" % col)


class PickerEvent(qtc.QEvent):
    def __init__(self, type, info):
        qtc.QEvent.__init__(self, type)
        self.info = info


class MyPickerView(dv.views.PickerView):
    def __init__(self, model, **kwargs):
        dv.views.PickerView.__init__(self, model, **kwargs)
        model.registerObserver(self._handleModelEvents)
        self._cvImages.sigCurrentRowChanged.connect(self._onCurrentRowChanged)
        self.installEventFilter(self)

    def _onCurrentRowChanged(self, row):
        mic = self._model.getMicrographByIndex(row)
        if mic is not None and mic == self._currentMic:
            print('beginLoadCoordinates')
            self._model.beginLoadCoordinates(mic.getId())
        print('_onCurrentRowChanged exit')

    def _handleModelEvents(self, event):
        """ Refresh different components depending on the model event """
        print('Processing event: micId= %s' % event.info.micId)
        qtg.QApplication.postEvent(self, PickerEvent(qtc.QEvent.User,
                                                     event.info))
        print('New PickerEvent was sent to event queue')

    def _handleGUIEvent(self, result):

        micId = result.micId
        print('_handleGUIEvent: ', micId)

        if result.tableModelChanged:
            self._cvImages.updatePage()

        if result.currentMicChanged:
            self._showMicrograph()  # This already update coordiantes

        elif result.coordsAdded:
            self._cvImages.updatePage()
            if (self._currentMic is not None and
                    self._currentMic.getId() == micId):
                self._createRoiHandlers(coords=result.coords, clear=False)

    def eventFilter(self, obj, event):
        if event.type() == qtc.QEvent.User:
            self._handleGUIEvent(event.info)
            return True
        else:
            #  standard event processing
            return dv.views.PickerView.eventFilter(self, obj, event)


class TestPickerViewEvents(dv.tests.TestView):
    __title = "TestPickerViewEvents Example"

    def __init__(self, methodName='runTest'):
        dv.tests.TestView.__init__(self, methodName=methodName)

    def getDataPaths(self):
        return ['']

    def createView(self):
        kwargs = dict()
        kwargs['selectionMode'] = dv.views.PagingView.SINGLE_SELECTION
        kwargs['boxSize'] = 64
        kwargs['pickerMode'] = dv.views.DEFAULT_MODE
        kwargs['shape'] = dv.views.SHAPE_CIRCLE
        kwargs['removeRois'] = True
        kwargs['roiAspectLocked'] = True
        kwargs['roiCentered'] = True

        model = MyPickerModel((512, 512), 10, 64, 150, False)
        print('============= ok.. creating the pickerview ==================')
        return MyPickerView(model, **kwargs)

    def test_PickingViewDefault(self):
        print('test_PickingViewMask')


if __name__ == '__main__':
    TestPickerViewEvents().runApp()
