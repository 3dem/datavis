
import datavis as dv


class TestTextView(dv.tests.TestView):
    __title = "TextView example"

    def __init__(self, methodName='runTest'):
        self.textView = dv.widgets.TextView()
        dv.tests.TestView.__init__(self, methodName=methodName)

    def createView(self):
        Param = dv.models.Param
        fileTypes = Param('fileType', dv.models.PARAM_TYPE_ENUM,
                          label='File types',
                          choices=['.py', '.json', 'text', '20 lines'],
                          display=dv.models.PARAM_DISPLAY_HLIST, value=0)

        form = dv.models.Form([fileTypes])
        centralWidget = dv.widgets.ViewPanel(None,
                                             dv.widgets.ViewPanel.VERTICAL)
        selectionWidget = dv.widgets.FormWidget(form, parent=centralWidget)
        selectionWidget.sigValueChanged.connect(self.paramChanged)
        self.textView.setParent(centralWidget)
        self.textView.setReadOnly(True)
        self.textView.setLinesWrap(False)

        centralWidget.addWidget(selectionWidget, 'selectionWidget')
        centralWidget.addWidget(self.textView, 'textView')
        self.paramChanged('fileType', 0)
        return centralWidget

    def paramChanged(self, paramName, value):

        if paramName == 'fileType':
            if value == 0:  # python code example
                text = dv.tests.getPythonCodeExample()
                self.textView.setHighlighter(dv.widgets.PythonHighlighter(None))
                self.textView.setText(text)
            elif value == 1:  # json example
                text = dv.tests.getJsonTextExample()
                self.textView.setHighlighter(
                    dv.widgets.JsonSyntaxHighlighter(None))
                self.textView.setText(text)
            elif value == 3:  # text file
                self.textView.setHighlighter(dv.widgets.PythonHighlighter(None))
                from os import path
                fpath = path.abspath(__file__)

                with open(fpath) as f:
                    self.textView.readText(f, 20, 20, '...')
            else:
                self.textView.setHighlighter(None)
                self.textView.setText("""This is a text example.
                                      The Highlighter works very well.""")
        else:
            print("Oh!! wrong param.")

    def test_TextView(self):
        print('test_TextView')


if __name__ == '__main__':
    TestTextView().runApp()
