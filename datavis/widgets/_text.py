
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

        # Multi-line strings (expression, flag, style)
        # FIXME: The triple-quotes in these two lines will mess up the
        # syntax highlighting from this point onward
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
                length = _expression.cap(_nth).length()
                self.setFormat(index, length, format)
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
                length = text.length() - start + add
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
    def __init__(self, parent=None):
        qtg.QSyntaxHighlighter.__init__(self, parent=parent)

        self._symbolFormat = qtg.QTextCharFormat()
        self._symbolFormat.setForeground(qtc.Qt.darkGray)
        self._symbolFormat.setFontWeight(qtg.QFont.Bold)

        self._nameFormat = qtg.QTextCharFormat()
        self._nameFormat.setForeground(qtg.QColor("#222426"))
        self._nameFormat.setFontWeight(qtg.QFont.Bold)

        self._valueFormat = qtg.QTextCharFormat()
        self._valueFormat.setForeground(qtg.QColor("#5293D8"))

    def highlightBlock(self, text):
        textBlock = text;

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
    Widget
    """