
import PyQt5.QtCore as qtc
import PyQt5.QtGui as qtg
import PyQt5.QtWidgets as qtw


def format(color, style=''):
    """Return a QTextCharFormat with the given attributes.
    """
    _color = qtg.QColor()
    _color.setNamedColor(color)

    _format = qtg.QTextCharFormat()
    _format.setForeground(_color)
    if 'bold' in style:
        _format.setFontWeight(qtg.QFont.Bold)
    if 'italic' in style:
        _format.setFontItalic(True)

    return _format


# Syntax styles that can be shared by all languages
STYLES = {
    'keyword': format('blue'),
    'operator': format('red'),
    'brace': format('darkGray'),
    'defclass': format('black', 'bold'),
    'string': format('magenta'),
    'string2': format('darkMagenta'),
    'comment': format('darkGreen', 'italic'),
    'self': format('black', 'italic'),
    'numbers': format('brown'),
}


class PythonHighlighter (qtg.QSyntaxHighlighter):
    """Syntax highlighter for the Python language.
    """
    # Python keywords
    keywords = [
        'and', 'assert', 'break', 'class', 'continue', 'def',
        'del', 'elif', 'else', 'except', 'exec', 'finally',
        'for', 'from', 'global', 'if', 'import', 'in',
        'is', 'lambda', 'not', 'or', 'pass', 'print',
        'raise', 'return', 'try', 'while', 'yield',
        'None', 'True', 'False',
    ]

    # Python operators
    operators = [
        '=',
        # Comparison
        '==', '!=', '<', '<=', '>', '>=',
        # Arithmetic
        '\+', '-', '\*', '/', '//', '\%', '\*\*',
        # In-place
        '\+=', '-=', '\*=', '/=', '\%=',
        # Bitwise
        '\^', '\|', '\&', '\~', '>>', '<<',
    ]

    # Python braces
    braces = [
        '\{', '\}', '\(', '\)', '\[', '\]',
    ]

    def __init__(self, document):
        qtg.QSyntaxHighlighter.__init__(self, document)

        self.tri_single = (qtc.QRegExp("'''"), 1, STYLES['string2'])
        self.tri_double = (qtc.QRegExp('"""'), 2, STYLES['string2'])

        rules = []

        # Keyword, operator, and brace rules
        rules += [(r'\b%s\b' % w, 0, STYLES['keyword'])
                  for w in PythonHighlighter.keywords]
        rules += [(r'%s' % o, 0, STYLES['operator'])
                  for o in PythonHighlighter.operators]
        rules += [(r'%s' % b, 0, STYLES['brace'])
                  for b in PythonHighlighter.braces]

        # All other rules
        rules += [
            # 'self'
            (r'\bself\b', 0, STYLES['self']),

            # Double-quoted string, possibly containing escape sequences
            (r'"[^"\\]*(\\.[^"\\]*)*"', 0, STYLES['string']),
            # Single-quoted string, possibly containing escape sequences
            (r"'[^'\\]*(\\.[^'\\]*)*'", 0, STYLES['string']),

            # 'def' followed by an identifier
            (r'\bdef\b\s*(\w+)', 1, STYLES['defclass']),
            # 'class' followed by an identifier
            (r'\bclass\b\s*(\w+)', 1, STYLES['defclass']),

            # From '#' until a newline
            (r'#[^\n]*', 0, STYLES['comment']),

            # Numeric literals
            (r'\b[+-]?[0-9]+[lL]?\b', 0, STYLES['numbers']),
            (r'\b[+-]?0[xX][0-9A-Fa-f]+[lL]?\b', 0, STYLES['numbers']),
            (r'\b[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\b', 0,
             STYLES['numbers']),
        ]

        # Build a QRegExp for each pattern
        self.rules = [(qtc.QRegExp(pat), index, fmt)
                      for (pat, index, fmt) in rules]

    def highlightBlock(self, text):
        """Apply syntax highlighting to the given block of text.
        """
        # Do other syntax formatting
        for _expression, _nth, _format in self.rules:
            index = _expression.indexIn(text, 0)

            while index >= 0:
                # We actually want the index of the nth match
                index = _expression.pos(_nth)
                length = len(_expression.cap(_nth))
                self.setFormat(index, length, _format)
                index = _expression.indexIn(text, index + length)

        self.setCurrentBlockState(0)

        # Do multi-line strings
        in_multiline = self.match_multiline(text, *self.tri_single)
        if not in_multiline:
            self.match_multiline(text, *self.tri_double)

    def match_multiline(self, text, delimiter, in_state, style):
        """Do highlighting of multi-line strings. ``delimiter`` should be a
        ``QRegExp`` for triple-single-quotes or triple-double-quotes, and
        ``in_state`` should be a unique integer to represent the corresponding
        state changes when inside those strings. Returns True if we're still
        inside a multi-line string when this function is finished.
        """
        # If inside triple-single quotes, start at 0
        if self.previousBlockState() == in_state:
            start = 0
            add = 0
        # Otherwise, look for the delimiter on this line
        else:
            start = delimiter.indexIn(text)
            # Move past this match
            add = delimiter.matchedLength()

        # As long as there's a delimiter match on this line...
        while start >= 0:
            # Look for the ending delimiter
            end = delimiter.indexIn(text, start + add)
            # Ending delimiter on this line?
            if end >= add:
                length = end - start + add + delimiter.matchedLength()
                self.setCurrentBlockState(0)
            # No; multi-line string
            else:
                self.setCurrentBlockState(in_state)
                length = len(text) - start + add
            # Apply formatting
            self.setFormat(start, length, style)
            # Look for the next match
            start = delimiter.indexIn(text, start + length)

        # Return True if still inside a multi-line string, False otherwise
        if self.currentBlockState() == in_state:
            return True
        else:
            return False


class JsonSyntaxHighlighter(qtg.QSyntaxHighlighter):
    """
    Syntax highlighter for JSON documents
    """
    def __init__(self, document):
        """
        Construct a JsonSyntaxHighlighter instance

        Args:
            document: (QTextDocument) The document object
        """
        qtg.QSyntaxHighlighter.__init__(self, document)

        self._symbolFormat = qtg.QTextCharFormat()
        self._symbolFormat.setForeground(qtc.Qt.darkRed)
        self._symbolFormat.setFontWeight(qtg.QFont.Bold)

        self._nameFormat = qtg.QTextCharFormat()
        self._nameFormat.setForeground(qtg.QColor("#0000FF"))
        self._nameFormat.setFontWeight(qtg.QFont.Bold)

        self._valueFormat = qtg.QTextCharFormat()
        self._valueFormat.setForeground(qtg.QColor("#225655"))

    def highlightBlock(self, text):
        """ Reimplemented from QSyntaxHighlighter """
        textBlock = text

        expression = qtc.QRegExp("(\\{|\\}|\\[|\\]|\\:|\\,)")
        index = expression.indexIn(textBlock)

        while index >= 0:
            length = expression.matchedLength()
            self.setFormat(index, length, self._symbolFormat)
            index = expression.indexIn(textBlock, index + length)

        textBlock.replace("\\\"", "  ")

        expression = qtc.QRegExp("\".*\" *\\:")
        expression.setMinimal(True)
        index = expression.indexIn(textBlock)

        while index >= 0:
            length = expression.matchedLength()
            self.setFormat(index, length - 1, self._nameFormat)
            index = expression.indexIn(textBlock, index + length)

        expression = qtc.QRegExp("\\: *\".*\"")
        expression.setMinimal(True)
        index = expression.indexIn(textBlock)
        while index >= 0:
            length = expression.matchedLength();
            self.setFormat(index + 1, length - 1, self._valueFormat)
            index = expression.indexIn(textBlock, index + length)


class _LineNumberArea(qtw.QWidget):
    """
    Widget for line number display
    """
    def __init__(self, textView, backgroundColor=qtc.Qt.lightGray):
        qtw.QWidget.__init__(self, textView)
        """
        Construct a _LineNumberArea
        Args:
            codeEditor: the code editor
        """
        self._textView = textView
        self._backgroundColor = backgroundColor

    def getBackgrountColor(self):
        return self._backgroundColor

    def sizeHint(self):
        return qtc.QSize(self._textView.lineNumberAreaWidth(), 0)

    def paintEvent(self, event):
        self._textView.lineNumberAreaPaintEvent(event)


class _PlainTextEdit(qtw.QPlainTextEdit):
    """
    TextView class provides a widget that is used to edit and display plain text
    """
    def __init__(self, parent=None, showLineNumber=True, linesDict=None):
        """
        Construct a TextView instance:

        Args:
            parent: The parent widget.
            showLineNumber: If True, then show the line numbers
            linesDict: dict for lines number mapping.
        """
        qtw.QPlainTextEdit.__init__(self, parent=parent)
        self._showLineNumber = showLineNumber
        self._linesDict = linesDict

        self._lineNumberArea = _LineNumberArea(self)
        self._lineNumberArea.setVisible(showLineNumber)
        self._lineColor = qtg.QColor(qtc.Qt.yellow).lighter(160)
        self._highlighter = None

        self.blockCountChanged.connect(self.updateLineNumberAreaWidth)
        self.updateRequest.connect(self.updateLineNumberArea)
        self.cursorPositionChanged.connect(self.highlightCurrentLine)

        self.updateLineNumberAreaWidth(0)
        self.highlightCurrentLine()

    def setLinesDict(self, d):
        """
        Set the lines dict for lines number mapping. Each line number will be
        mapping in the given dict.

        Args:
            d:  (dict) A dict with the line number map.
                Example:
                    { 1: 4, 2: 5, 3: 6}
        """
        self._linesDict = d

    def setHighlighter(self, highlighter):
        """ Set the document highlighter """
        if self._highlighter is not None:
            self._highlighter.setDocument(None)

        self._highlighter = highlighter
        if highlighter is not None:
            self._highlighter.setDocument(self.document())

    def lineNumberAreaPaintEvent(self, event):
        """ Paint the line number area """
        painter = qtg.QPainter(self._lineNumberArea)
        painter.fillRect(event.rect(),
                         self._lineNumberArea.getBackgrountColor())

        block = self.firstVisibleBlock()
        blockNumber = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(
            self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                if self._linesDict is None:
                    number = str(blockNumber + 1)
                else:
                    number = str(self._linesDict.get(blockNumber + 1, ''))

                painter.setPen(qtc.Qt.black)
                painter.drawText(0, top, self._lineNumberArea.width(),
                                 self.fontMetrics().height(), qtc.Qt.AlignRight,
                                 number)
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            blockNumber += 1

    def lineNumberAreaWidth(self):
        """ Returns the width of the line number area according to the number
        of lines. """
        if not self._showLineNumber:
            return 0

        digits = 1
        m = max(self._linesDict.values()) if self._linesDict else 1
        m = max(m, self.blockCount())

        while m >= 10:
            m /= 10
            digits += 1

        space = 3 + self.fontMetrics().width('9') * digits

        return space

    def updateLineNumberAreaWidth(self, newBlockCount):
        """ Update the width of the line number area. """
        self.setViewportMargins(self.lineNumberAreaWidth(), 0, 0, 0)

    def highlightCurrentLine(self):
        """ Highlight the current line """
        extraSelections = []

        selection = qtw.QTextEdit.ExtraSelection()
        selection.format.setBackground(self._lineColor)
        selection.format.setProperty(qtg.QTextFormat.FullWidthSelection,
                                     True)
        selection.cursor = self.textCursor()
        selection.cursor.clearSelection()
        extraSelections.append(selection)

        self.setExtraSelections(extraSelections)

    def updateLineNumberArea(self, rect, dy):
        """ Update the line number area """
        if dy:
            self._lineNumberArea.scroll(0, dy)
        else:
            self._lineNumberArea.update(0, rect.y(),
                                        self._lineNumberArea.width(),
                                        rect.height())

        if rect.contains(self.viewport().rect()):
            self.updateLineNumberAreaWidth(0)

    def resizeEvent(self, event):
        """ Reimplemented from QPlainTextEdit.
        Updates the line number area """
        qtw.QPlainTextEdit.resizeEvent(self, event)

        cr = self.contentsRect()
        self._lineNumberArea.setGeometry(qtc.QRect(cr.left(), cr.top(),
                                                   self.lineNumberAreaWidth(),
                                                   cr.height()))


class TextView(qtw.QWidget):
    """ Provides a widget that is used to edit and display plain
    text. TextView can read the text lines from a file input stream and show
    only the first and last lines specified.
    """
    def __init__(self, parent=None, showLines=True):
        qtw.QWidget.__init__(self, parent=parent)
        layout = qtw.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._textEdit = _PlainTextEdit(self, showLines)
        layout.addWidget(self._textEdit)

    def __readLinesFromFile(self, inputStream, fi, la):
        """
        Read the first fi lines and last la lines from the given file input
        stream

        Args:
            inputStream: The input stream
            fi:    (int) The first lines to be read
            la:    (int) The last lines to be read

        Returns:
             A tupple with two list: first and last lines,
             and the number of lines
        """

        lines = []
        for _ in range(fi):
            line = inputStream.readline()
            if line is not None:
                lines.append(line)
            else:
                break

        s = inputStream.tell()
        size = len(lines)
        for _ in inputStream:
            size += 1

        fsize = inputStream.tell()
        inputStream.seek(s)

        if s < fsize:
            i = 0
            bufsize = 8192
            if bufsize > fsize:
                bufsize = fsize - 1

            data = []
            while True:
                i += 1
                seek = fsize - bufsize * i
                if seek < s:
                    seek = s

                inputStream.seek(seek)

                data.extend(inputStream.readlines())
                if len(data) >= la or seek == s:
                    return lines, data[-la:], size
        else:
            return lines, [], size

    def setHighlighter(self, highlighter):
        """ Set the document highlighter """
        self._textEdit.setHighlighter(highlighter)

    def setText(self, text):
        """ Sets the plain text editor's contents

        Args:
            text: (str) The text
        """
        self._textEdit.setLinesDict({})
        self._textEdit.setPlainText(text)

    def readText(self, inputStream, firstLines, lastLines, separator='.'):
        """
        Read text lines from the given input stream and show the first
        'firstLines' lines and the last 'lastLines' using a separator between
        the text blocks.
        Args:
            inputStream: A file input stream
            firstLines: The number of first lines to be shown
            lastLines: The number of last lines to be shown
            separator: The lines range separator
        """
        fl, ll, size = self.__readLinesFromFile(inputStream, firstLines,
                                                lastLines)
        d = {i + 1: i + 1 for i in range(len(fl))}
        self._textEdit.setLinesDict(d)

        self._textEdit.setPlainText("".join(fl))
        if ll:
            for _ in range(3):
                self._textEdit.appendPlainText(separator)
            self._textEdit.appendPlainText('')

            for i in range(len(ll)):
                d[firstLines + i + 6] = size - lastLines + i + 1

            self._textEdit.appendPlainText("".join(ll))

    def setReadOnly(self, ro):
        """ Set the text edition as read-only if ro is True. """
        self._textEdit.setReadOnly(ro)

    def isReadOnly(self):
        """ Return True if the text edition is in read-only mode """
        return self._textEdit.isReadOnly()

    def clear(self):
        """ Deletes all the text in the text edit. """
        self._textEdit.setLinesDict(None)
        self._textEdit.clear()

    def setLinesWrap(self, w):
        """
        Enable/disable the lines wrap mode
        Args:
            w: (bool) The lines wrap
        """
        TE = qtw.QPlainTextEdit
        self._textEdit.setLineWrapMode(TE.WidgetWidth if w else TE.NoWrap)
