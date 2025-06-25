import os
import platform
from pathlib import Path
from setuptools import setup, Extension
from Cython.Build import cythonize

PLATFORM = platform.system()
SHARED = bool(int((os.getenv("SHARED", False))))
ROOT = Path(__file__).parent
LIB_DIR = ROOT / "lib"
INCLUDE_DIR = ROOT / "include"
EXTRA_OBJECTS = [str(p) for p in LIB_DIR.glob('*.a')] if not SHARED else []
EXTRA_LINK_ARGS = []
if PLATFORM == "Darwin":
    EXTRA_LINK_ARGS.extend(['-framework', 'CoreAudio'])
LIBRARIES = ["z"]
if SHARED:
    LIBRARIES.extend([
        "sox", "sndfile", "FLAC", "opus", "mp3lame",
        "vorbis", "vorbisfile", "vorbisenc", "png16",
    ])

extensions = [
    Extension("cysox.sox", sources = [
            "src/cysox/sox.pyx",
        ],
        libraries=LIBRARIES,
        include_dirs=[str(INCLUDE_DIR)],
        library_dirs=[str(LIB_DIR)],
        extra_objects=EXTRA_OBJECTS,
        extra_link_args=EXTRA_LINK_ARGS,
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
            'overflowcheck': False,      # default: False
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
