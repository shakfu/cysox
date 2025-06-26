#
# version of the package
#
# $Id: versioninfo.py 83 2011-03-25 21:53:45Z patrick $
#
# Copyright 2011 Patrick Atamaniuk
#
# This source code is freely redistributable and may be used for
# any purpose.  This copyright notice must be maintained.
# Patrick Atamaniuk and Contributors are not responsible for
# the consequences of using this software.
#
# idea of versioninfo stolen from lxml package
#  lxml is copyright Infrae and distributed under the BSD license
# 
from setuptools import Extension
import os, sys

INCLUDE_DIR = "/opt/homebrew/opt/sox/include"
LIB_DIR = "/opt/homebrew/opt/sox/lib"

try:
    from Cython.Distutils import build_ext as build_pyx
    import Cython.Compiler.Version
    CYTHON_INSTALLED = True
except ImportError:
    CYTHON_INSTALLED = False

__PYSOX_VERSION = None

debugflags = [] #['-g']
#debugflags = ['-g']
soxlib = ['sox']
include_dirs = [INCLUDE_DIR]
library_dirs = [LIB_DIR] #['/usr/local/libsox-dev/lib']
# extra_objects = [f'{LIB_DIR}/libsox.a']

def version():
    global __PYSOX_VERSION
    if __PYSOX_VERSION is None:
        f = open(os.path.join(get_base_dir(), 'version.txt'))
        try:
            __PYSOX_VERSION = f.read().strip()
        finally:
            f.close()
    return __PYSOX_VERSION

def dev_status():
    _version = version()
    if 'dev' in _version:
        return 'Development Status :: 3 - Alpha'
    elif 'alpha' in _version:
        return 'Development Status :: 3 - Alpha'
    elif 'beta' in _version:
        return 'Development Status :: 4 - Beta'
    else:
        return 'Development Status :: 5 - Production/Stable'

def get_base_dir():
    return os.path.join(os.getcwd(), os.path.dirname(sys.argv[0]))

def extra_setup_args():
    result = {}
    if CYTHON_INSTALLED:
        result['cmdclass'] = {'build_ext': build_pyx}

    return result

def ext_modules():
    sources = ['sox', 'customeffects', 'combiner']
    
    if CYTHON_INSTALLED:
        suffix = 'pyx'
        print("Building with Cython")
    else:
        suffix = 'c'
        print("Building without Cython")
    res = []
    for source in sources:
        res.append(
                   Extension("pysox.%s"%source, ["pysox/%s.%s"%(source,suffix)],
                             libraries=soxlib,
                             include_dirs=include_dirs,
                             library_dirs=library_dirs,
                             extra_compile_args=debugflags,
                             extra_link_args=debugflags,
                             # extra_objects=extra_objects,
                             )
                   )
    return res

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()
