import os
import platform
from pathlib import Path
from setuptools import setup, Extension
from Cython.Build import cythonize

PLATFORM = platform.system()

# ----------------------------------------------------------------------------
# Common

ROOT = Path(__file__).parent

LIBRARIES = ["z"]
INCLUDE_DIRS = []
LIBRARY_DIRS = []
EXTRA_OBJECTS = []
EXTRA_LINK_ARGS = []
EXTRA_COMPILE_ARGS = []

# ----------------------------------------------------------------------------
# Darwin (MacOS)

if PLATFORM == "Darwin":
    STATIC = bool(int((os.getenv("STATIC", True))))
    LIB_DIR = ROOT / "lib"
    LIBRARY_DIRS.append(str(LIB_DIR))
    INCLIDE_DIR = ROOT / "include"
    INCLUDE_DIRS.append(str(INCLIDE_DIR))
    EXTRA_LINK_ARGS.extend(['-framework', 'CoreAudio'])
    if STATIC:
        EXTRA_OBJECTS.extend([str(p) for p in LIB_DIR.glob('*.a')])
    else:
        LIBRARIES.extend([
            "sox", "sndfile", "FLAC", "opus", "mp3lame",
            "vorbis", "vorbisfile", "vorbisenc", "png16",
        ])

else:
    raise NotImplemented("other platform variants still pending")



# ----------------------------------------------------------------------------
# Extension Configuration

extensions = [
    Extension("cysox.sox", 
        sources = ["src/cysox/sox.pyx"],
        libraries=LIBRARIES,
        include_dirs=INCLUDE_DIRS,
        library_dirs=LIBRARY_DIRS,
        extra_objects=EXTRA_OBJECTS,
        extra_link_args=EXTRA_LINK_ARGS,
        extra_compile_args=EXTRA_COMPILE_ARGS,
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
            'overflowcheck': False,      # default: False
            'overflowcheck.fold': True,  # default: True
            'embedsignature': False,     # default: False
            'cdivision': False,          # default: False
            'emit_code_comments': False, # default: True
            'annotation_typing': True,   # default: True
            'warn.undeclared': False,    # default: False
            'warn.unreachable': True,    # default: True
            'warn.unused': False,        # default: False
            'warn.unused_arg': False,    # default: False
            'warn.unused_result': False, # default: False
        },
        # gdb_debug=True,
    ),
    package_dir={"": "src"},
)
