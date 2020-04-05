#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import unittest
from glob import glob
import argparse

import datavis as dv


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


class TestMatchPaths(dv.tests.TestBase):
    __title = "MatchPaths example"

    def getDataPaths(self):
        return [
            self.getPath("tmv_helix", "micrographs", 'TMV_Krios_Falcon*'),
            self.getPath("tmv_helix", "coords", 'TMV_Krios_Falcon*')
        ]

    def test_MatchPaths(self):
        argParser = argparse.ArgumentParser(usage='Tool for Viewer Apps',
                                            prefix_chars='--',
                                            argument_default=None)

        # GLOBAL PARAMETERS
        argParser.add_argument('--paths', type=str, nargs='*', default=[],
                               required=False, action=ValidateMics,
                               help='2 path pattern for micrograph and '
                                    'coordinates files.')
        a = ['--paths']
        a.extend(self.getDataPaths())
        args = argParser.parse_args(a)

        print('test_MatchPaths: OK')

if __name__ == '__main__':
    unittest.main()

