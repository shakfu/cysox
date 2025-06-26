#
# $Id: setup.py 104 2011-03-30 11:31:36Z patrick $
#
# Copyright 2011 Patrick Atamaniuk
#
# This source code is freely redistributable and may be used for
# any purpose.  This copyright notice must be maintained.
# Patrick Atamaniuk and Contributors are not responsible for
# the consequences of using this software.


from setuptools import Extension, setup

import os
from versioninfo import version, dev_status, extra_setup_args, ext_modules, read

extra_options = {}
extra_options.update(extra_setup_args())

setup(
    name = "pysox",
    version = version(),
    author="Patrick Atamaniuk",
    author_email="pysox@frobs.net",
    maintainer="Patrick Atamaniuk",
    maintainer_email="pysox@frobs.net",
    url="http://foo42.de/wiki/pysox",
    download_url="http://foo42.de/devel/pysox/dist/pysox-%s.tar.gz" % version(),

    description="Python bindings for sox and libsox.",
    long_description=read('README.txt'),
    license="BSD",
    classifiers = [
    dev_status(),
    'Intended Audience :: Developers',
    'Intended Audience :: Information Technology',
    # 'License :: OSI Approved :: BSD License',
    'Programming Language :: Cython',
    'Programming Language :: Python :: 3',
    'Programming Language :: C',
    'Operating System :: OS Independent',
    'Topic :: Multimedia :: Sound/Audio',
    'Topic :: Multimedia :: Sound/Audio :: Editors',
    'Topic :: Multimedia :: Sound/Audio :: Conversion',
    'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    platforms="any",
    packages = ['pysox'],
    
    ext_modules = ext_modules(),
    package_data = {'pysox': ['*.pxd']},
    
    **extra_options
)
