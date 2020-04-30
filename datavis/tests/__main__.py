
import sys
import argparse
import textwrap
from os.path import dirname

import datavis as dv


def main2(argv=None):
    argv = argv or sys.argv[1:]

    argParser = argparse.ArgumentParser(
        usage='Tool for run library tests',
        description='Runs the library tests',
        prefix_chars='--',
        argument_default=None,
        formatter_class=argparse.RawTextHelpFormatter)

    argParser.add_argument(
        '--type',
        default='gui',
        type=str,
        choices=['cls', 'gui'],
        help=textwrap.dedent("""
            Tests type. Choices:  cls, gui
            """))

    argParser.add_argument(
        '--pattern',
        default='*',
        type=str,
        help=textwrap.dedent("""
                A pattern to specify the test names.
                """))

    args = argParser.parse_args(argv)

    testPath = dirname(__file__)
    pattern = ('test_%s_%s' % (args.type, args.pattern))

    dv.tests.runTests(testPath, args.type, pattern)

if __name__ == '__main__':
    main2()