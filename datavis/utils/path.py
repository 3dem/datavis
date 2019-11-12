# **************************************************************************
# *
# * Authors:     J.M. De la Rosa Trevin (delarosatrevin@scilifelab.se) [1]
# *
# * [1] SciLifeLab, Stockholm University
# *
# * This program is free software: you can redistribute it and/or modify
# * it under the terms of the GNU General Public License as published by
# * the Free Software Foundation, either version 3 of the License, or
# * (at your option) any later version.
# *
# * This program is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# * GNU General Public License for more details.
# *
# * You should have received a copy of the GNU General Public License
# * along with this program.  If not, see <https://www.gnu.org/licenses/>.
# *
# *  All comments concerning this program package may be sent to the
# *  e-mail address 'scipion@cnb.csic.es'
# *
# **************************************************************************
"""
This module contains the PATH related utilities
inside the utils module
"""
from __future__ import print_function
from __future__ import absolute_import

import os
import shutil
import sys
from glob import glob
import datetime


ROOT = "/"


def findFileRecursive(filename, path):
    for root, dirs, files in os.walk(path):
        if filename in files:
            return os.path.join(root, filename)
    return None   
        
        
def findFile(filename, *paths, **kwargs):
    """ Search if the file is present in some path in the *paths provided.
    Return None if not found.
    'recursive' can be passed in kwargs to iterate into subfolders.
    """
    recursive = kwargs.get('recursive', False)
    
    if filename:
        for p in paths:
            fn = os.path.join(p, filename)
            if os.path.exists(fn):
                return fn
            if recursive:
                f = findFileRecursive(filename, p)
                if f:
                    return f
    return None


def findRootFrom(referenceFile, searchFile):
    """ This method will find a path (root) from 'referenceFile'
    from which the 'searchFile' os.path.exists. 
    A practical example of 'referenceFile' is a metadata file
    and 'searchFile' is an image to be found from the metadata.
    Return None if the path is not found.
    """
    absPath = os.path.dirname(os.path.abspath(referenceFile))
    
    while absPath is not None and absPath != '/':
        if os.path.os.path.exists(os.path.join(absPath, searchFile)):
            return absPath
        absPath = os.path.dirname(absPath)
        
    return None   


def getParentFolder(path):
    """ Returns the absolute parent folder of a file or folder. Work for
    folders that ens with "/" which dirname can't"""
    return os.path.dirname(os.path.abspath(path))


def replaceExt(filename, newExt):
    """ Replace the current path extension(from last .)
    with a new one. The new one should not contains the ."""
    return os.path.splitext(filename)[0] + '.' + newExt


def replaceBaseExt(filename, newExt):
    """ Replace the current basename extension(from last .)
    with a new one. The new one should not contains the .
    """
    return replaceExt(os.path.basename(filename), newExt)


def removeBaseExt(filename):
    """Take the basename of the filename and remove extension"""
    return removeExt(os.path.basename(filename))


def removeExt(filename):
    """ Remove extension from basename """
    return os.path.splitext(filename)[0]


def joinExt(*extensions):
    """ Join several path parts with a ."""
    return '.'.join(extensions)


def getExt(filePath):
    """ Return the extesion given a file. """
    return os.path.splitext(filePath)[1]


def cleanPath(*paths):
    """ Remove a list of paths, either folders or files"""
    for p in paths:
        if os.path.exists(p):
            if os.path.isdir(p):
                if os.path.islink(p):
                    os.remove(p)
                else:
                    shutil.rmtree(p)
            else:
                os.remove(p)


def cleanPattern(pattern):
    """ Remove all files that match the pattern. """
    files = glob(pattern)
    cleanPath(*files)


def copyPattern(pattern, destFolder):
    """ Copy all files matching the pattern to the given destination folder."""
    for file in glob(pattern):
        copyFile(file, destFolder)


def makePath(*paths):
    """ Create a list of paths if they don't os.path.exists.
    Recursively create all folder needed in a path.
    If a path passed is a file, only the directory will be created.
    """
    for p in paths:
        if not os.path.exists(p) and len(p):
            os.makedirs(p)


def makeFilePath(*files):
    """ Make the path to ensure that files can be written. """
    makePath(*[os.path.dirname(f) for f in files])


def missingPaths(*paths):
    """ Check if the list of paths os.path.exists.
    Will return the list of missing files,
    if the list is empty means that all path os.path.exists
    """
    return [p for p in paths if not os.path.exists(p)]


def getHomePath(user=''):
    """Return the home path of a give user."""
    return os.path.expanduser("~" + user)


def expandPattern(pattern, vars=True, user=True):
    """ Expand environment vars and user from a given pattern. """
    if vars:
        pattern = os.path.expandvars(pattern)
    if user:
        pattern = os.path.expanduser(pattern)
    return pattern


def getFiles(folderPath):
    """
    Gets all files of given folder and it subfolders.
    folderPath -- Folder path to get files.
    returns -- Set with all folder files.
    """
    filePaths = set()
    for path, dirs, files in os.walk(folderPath):
        for f in files:
            filePaths.add(os.path.join(path, f))
    return filePaths


def copyTree(source, dest):
    """
    Wrapper around the shutil.copytree, but allowing
    that the dest folder also os.path.exists.
    """
    if not os.path.exists(dest):
        shutil.copytree(source, dest, symlinks=True)
    else:
        for f in os.listdir(source):
            fnPath = os.path.join(source, f)
            if os.path.isfile(fnPath):
                shutil.copy(fnPath, dest)
            elif os.path.isdir(fnPath):
                copyTree(fnPath, os.path.join(dest, f))


def moveTree(src, dest):
    copyTree(src, dest)
    cleanPath(src)


def copyFile(source, dest):
    """ Shortcut to shutil.copy. """
    shutil.copy(source, dest)


def moveFile(source, dest):
    """ Move file from source to dest. """
    copyFile(source, dest)
    cleanPath(source)


def createLink(source, dest):
    """ Creates a relative link to a given file path. 
    Try to use common path for source and dest to avoid errors. 
    Different relative paths may exist since there are different valid paths
    for a file, it depends on the current working dir path"""
    if os.path.islink(dest):
        os.remove(dest)
        
    if os.path.exists(dest):
        raise Exception('Destination %s os.path.exists and is not a link'
                        % dest)
    sourcedir = os.path.dirname(source)
    destdir = os.path.dirname(dest)
    relsource = os.path.join(os.path.relpath(sourcedir, destdir),
                             os.path.basename(source))
    os.symlink(relsource, dest)


def createAbsLink(source, dest):
    """ Creates a link to a given file path"""
    if os.path.islink(dest):
        os.remove(dest)
        
    if os.path.exists(dest):
        raise Exception('Destination %s os.path.exists and is not a link' % dest)

    os.symlink(source, dest)


def getLastFile(pattern):
    """ Return the last file matching the pattern. """
    files = glob(pattern)
    if len(files):
        files.sort()
        return files[-1]
    return None


def commonPath(*paths):
    """ Return the common longest prefix path.
    It uses the python os.path.commonprefix and 
    then the direname over it since the former is
    implemented in char-by-char base.
    """
    return os.path.dirname(os.path.commonprefix(*paths))


# Console (and XMIPP) escaped colors, and the related tags that we create
# with Text.tag_config(). This dict is used in OutputText:addLine()
# See also http://www.termsys.demon.co.uk/vtansi.htm#colors
colorName = {'30': 'gray',
             '31': 'red',
             '32': 'green',
             '33': 'yellow',
             '34': 'blue',
             '35': 'magenta',
             '36': 'cyan',
             '37': 'white'}


def createUniqueFileName(fn):
    '''
    This function creates a file name that is similar to the original 
    by adding a unique numeric suffix. check   NamedTemporaryFile
    from tempfile for alternatives
    '''
    if not os.path.os.path.exists(fn):
        return fn

    path, name = os.path.split(fn)
    name, ext = os.path.splitext(name)

    make_fn = lambda i: os.path.join(path, '%s_tmp_%d_%s' % (name, i, ext))

    for i in range(2, sys.maxint):
        uni_fn = make_fn(i)
        if not os.path.os.path.exists(uni_fn):
            return uni_fn

    return None


def getFileSize(fn):
    """ Shortcut to inspect the size of a file. """
    return os.stat(fn).st_size


def getFileLastModificationDate(fn):
    """ Returns the last modification date of a file or None
    if it doesn't exist. """
    if os.path.os.path.exists(fn):
        ts = os.path.getmtime(fn)
        return datetime.datetime.fromtimestamp(ts)
    else:
        print(fn + " does not exist!!. Can't check last modification date.")
        return None



