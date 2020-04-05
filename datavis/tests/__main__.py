
import sys
import argparse
import textwrap


class TestArgsDict(dict):
    def __init__(self):
        dict.__init__(self, [('gui', False), ('name', '*')])

TRUE_VALUES = ['on', '1', 'yes', 'true']
FALSE_VALUES = ['off', '0', 'no', 'false']


class ArgDictAction(argparse.Action):
    """ Subclass of Action to implement special dict-like params
    with key=value pairs, usually with on/off boolean values.
    Example:
        --args boxsize=50 histogram=off
    """
    def __init__(self, option_strings, dest, argsDictClass=None, nargs=None,
                 **kwargs):
        if nargs != '+':
            raise Exception("Only nargs='+' are supported for ArgDictAction.")

        argparse.Action.__init__(self, option_strings, dest, nargs, **kwargs)
        self._argsDictClass = argsDictClass

    def __call__(self, parser, namespace, values, option_string=None):
        def _getValue(value):
            v = value.lower()
            if v in TRUE_VALUES:
                return True
            if v in FALSE_VALUES:
                return False
            return value  # just original string value

        argDict = self._argsDictClass()
        for pair in values:
            key, value = pair.split("=")
            argDict[key] = _getValue(value)
        setattr(namespace, self.dest, argDict)


def main(argv=None):
    argv = argv or sys.argv[1:]

    argParser = argparse.ArgumentParser(
        usage='Tool for run library tests',
        description='Runs the library tests',
        prefix_chars='--',
        argument_default=None,
        formatter_class=argparse.RawTextHelpFormatter)

    argParser.add_argument(
        '--args', nargs='+', action=ArgDictAction,
        default=TestArgsDict(),
        argsDictClass=TestArgsDict,
        help=textwrap.dedent("""
            Arguments to be passed to the tests. 
            """))

    argParser.add_argument(
        '--name', nargs='+', action=ArgDictAction,
        default='*',
        argsDictClass=TestArgsDict,
        help=textwrap.dedent("""
                Pattern to specify the test names or nothing for everyone.
                Example: test_cls_*
                """))

    args = argParser.parse_args(argv)

    print(args)

if __name__ == '__main__':
    main()