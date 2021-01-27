from glob import glob
from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize
from os.path import join, dirname, basename

root = dirname(__file__)

LIB_DIR = 'lib-static'

INCLUDES = [join(root, "include")]
EXTRA_OBJECTS = [p for p in glob(join(LIB_DIR, '*'))]

extensions = [
    Extension("cysox", ["cysox.pyx"],
        #libraries=LIBNAME,
        include_dirs=INCLUDES,
        #library_dirs=LIBDIRS+['/usr/local/lib'],
        extra_objects=EXTRA_OBJECTS,
        extra_link_args=['-framework', 'Foundation'],
    )
]

setup(
    name="sox in cython",
    ext_modules=cythonize(extensions, 
        compiler_directives={
            'language_level' : '3',
            # 'overflowcheck': True,
            # 'boundscheck': True,
            # 'wraparound': False,
            # 'cdivision': True,

        }),
)
