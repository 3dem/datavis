#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
from glob import glob
import argparse

if __name__ == '__main__':
    kwargs = {}

    class ValidateMics(argparse.Action):
        """
        Class that allows the validation of the values corresponding to
        the "picker" parameter
        """
        def __init__(self, option_strings, dest, **kwargs):
            argparse.Action.__init__(self, option_strings, dest, **kwargs)

        def __call__(self, parser, namespace, values, option_string=None):
            """
            Validate the maximum number of values corresponding to the
            picker parameter. Try to matching a path pattern for micrographs
            and another for coordinates.

            Return a list of tuples [mic_path, pick_path].
            """
            l = len(values)
            result = dict()
            if l > 2:
                raise ValueError("Invalid number of arguments for %s. Only 2 "
                                 "arguments are supported." % option_string)

            if l > 0:
                mics = self.__ls(values[0])
                for i in mics:
                    basename = os.path.splitext(os.path.basename(i))[0]
                    result[basename] = (i, None)

            if l > 1:
                coords = self.__ls(values[1])
                for i in coords:
                    basename = os.path.splitext(os.path.basename(i))[0]
                    t = result.get(basename)
                    if t:
                        result[basename] = (t[0], i)

            setattr(namespace, self.dest, result)

        def __ls(self, pattern):
            return glob(pattern)

    argParser = argparse.ArgumentParser(usage='Tool for Viewer Apps',
                                        description='Display the selected '
                                                    'viewer app',
                                        prefix_chars='--',
                                        argument_default=None)

    # GLOBAL PARAMETERS
    argParser.add_argument('--picker', type=str, nargs='*', default=[],
                           required=False, action=ValidateMics,
                           help='Show the Picker tool. '
                                '2 path pattern for micrograph and coordinates '
                                'files.')

    args = argParser.parse_args()
    print("Arguments: ", args.picker)
    sys.exit(0)

