
import sys
import argparse
import textwrap

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
        default='cls',
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

    pattern = ('test_%s_%s' % (args.type, args.pattern))

    if args.type == 'cls':
        dv.tests.runTests(pattern)
    else:
        ColInfo = dv.models.ColumnInfo
        TYPE_STR = dv.models.TYPE_STRING
        model = dv.models.SimpleTableModel([ColInfo('Test', dataType=TYPE_STR),
                                            ColInfo('Class',
                                                    dataType=TYPE_STR)])

        tests = dv.tests.getTests(pattern)

        for path, t in tests:
            model.addRow([dv.tests.TestFilePath(path, t.getTestMethodName()),
                          t])

        win = dv.tests.ExampleWindow(model)
        win.runApp()

if __name__ == '__main__':
    main2()