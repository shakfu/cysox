from glob import glob
from pathlib import Path
from setuptools import setup, Extension
from Cython.Build import cythonize
from os.path import join, dirname, basename

root = Path(__file__).parent

LIB_DIR = root / "lib"
INCLUDE_DIR = root / "include"
EXTRA_OBJECTS = [str(p) for p in LIB_DIR.glob('*.a')]

extensions = [
    Extension("cysox.sox", ["src/cysox/sox.pyx"],
        #libraries=LIBNAME,
        include_dirs=[str(INCLUDE_DIR)],
        library_dirs=[str(LIB_DIR)],
        extra_objects=EXTRA_OBJECTS,
        extra_link_args=['-framework', 'Foundation'],
    )
]

setup(
    name="cysox",
    ext_modules=cythonize(extensions, 
        compiler_directives={
            'language_level' : '3',
            # 'overflowcheck': True,
            # 'boundscheck': True,
            # 'wraparound': False,
            # 'cdivision': True,

        }),
    package_dir={"": "src"},
)
