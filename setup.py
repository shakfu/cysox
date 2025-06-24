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
    Extension("cysox.sox", sources = [
            "src/cysox/sox.pyx",
        ],
        libraries=["z"],
        include_dirs=[str(INCLUDE_DIR)],
        library_dirs=[str(LIB_DIR)],
        extra_objects=EXTRA_OBJECTS,
        extra_link_args=['-framework', 'CoreAudio'],
        extra_compile_args=[],
    )
]

setup(
    name="cysox",
    ext_modules=cythonize(extensions, 
        compiler_directives={
            'language_level' : '3',
            'binding': True,             # default: True
            'boundscheck': True,         # default: True
            'wraparound': True,          # default: True
            'initializedcheck': True,    # default: True
            'nonecheck': False,          # default: False
            'overflowcheck': True,       # default: False
            'overflowcheck.fold': True,  # default: True
            'embedsignature': False,     # default: False
            'cdivision': False,          # default: False
            'emit_code_comments': False, # default: True
            'annotation_typing': True,   # default: True
            'warn.undeclared': True,     # default: False
            'warn.unreachable': True,    # default: True
            'warn.unused': True,         # default: False
            'warn.unused_arg': True,     # default: False
            'warn.unused_result': True,  # default: False
        }),
    package_dir={"": "src"},
)
