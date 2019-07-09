"""
Some utilities for dealing with Python 2/3 stuff.
"""

# Quick and dirty way to deal with both Python 2 and 3 basestring
# When dropped support for Python 2, we can just use str, remove py23 prefix
try:
    str = basestring
except NameError:
    str = str