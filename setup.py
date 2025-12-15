import os
import platform
from pathlib import Path
from setuptools import setup, Extension
from Cython.Build import cythonize

def getenv(variable, default=True):
    return bool(int((os.getenv(variable, default))))

# ----------------------------------------------------------------------------
# Constants

DEBUG = getenv("DEBUG", default=False)
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
DEFINE_MACROS = []

# ----------------------------------------------------------------------------
# Darwin (MacOS)

if PLATFORM == "Darwin":
    STATIC = getenv("STATIC")
    LIB_DIR = ROOT / "lib"
    LIBRARY_DIRS.append(str(LIB_DIR))
    INCLUDE_DIR = ROOT / "include"
    INCLUDE_DIRS.append(str(INCLUDE_DIR))
    EXTRA_LINK_ARGS.extend([
        '-framework', 'CoreAudio',
    ])
    if DEBUG:
        EXTRA_COMPILE_ARGS.extend([
            '-fsanitize=address',
            '-fno-omit-frame-pointer',
        ])
    if STATIC:
        EXTRA_OBJECTS.extend([str(p) for p in LIB_DIR.glob('*.a')])
    else:
        LIBRARIES.extend([
            "sox", "sndfile", "FLAC", "opus", "mp3lame",
            "vorbis", "vorbisfile", "vorbisenc", "png16",
        ])
    if DEBUG:
        DEFINE_MACROS.extend([
            ("DEBUG", None),
            ("DEBUG_EFFECTS_CHAIN", "1"),
        ])

# ----------------------------------------------------------------------------
# Linux

elif PLATFORM == "Linux":
    import subprocess

    # Try to use pkg-config to find sox
    try:
        pkg_config_cflags = subprocess.check_output(
            ["pkg-config", "--cflags", "sox"],
            stderr=subprocess.DEVNULL
        ).decode().strip().split()

        pkg_config_libs = subprocess.check_output(
            ["pkg-config", "--libs", "sox"],
            stderr=subprocess.DEVNULL
        ).decode().strip().split()

        # Parse pkg-config output
        for flag in pkg_config_cflags:
            if flag.startswith("-I"):
                INCLUDE_DIRS.append(flag[2:])

        for flag in pkg_config_libs:
            if flag.startswith("-L"):
                LIBRARY_DIRS.append(flag[2:])
            elif flag.startswith("-l"):
                LIBRARIES.append(flag[2:])

    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback to common system paths if pkg-config fails
        INCLUDE_DIRS.extend([
            "/usr/include",
            "/usr/local/include",
        ])
        LIBRARY_DIRS.extend([
            "/usr/lib",
            "/usr/local/lib",
            "/usr/lib/x86_64-linux-gnu",
            "/usr/lib/aarch64-linux-gnu",
        ])
        LIBRARIES.extend([
            "sox", "sndfile", "FLAC", "opus", "mp3lame",
            "vorbis", "vorbisfile", "vorbisenc", "png",
        ])

    if DEBUG:
        EXTRA_COMPILE_ARGS.extend([
            '-fsanitize=address',
            '-fno-omit-frame-pointer',
        ])
        EXTRA_LINK_ARGS.extend([
            '-fsanitize=address',
        ])

# ----------------------------------------------------------------------------
# Windows

elif PLATFORM == "Windows":
    # Windows support not yet implemented
    # Users should install libsox and set environment variables:
    # - SOX_INCLUDE_DIR: path to sox headers
    # - SOX_LIB_DIR: path to sox libraries
    sox_include = os.getenv("SOX_INCLUDE_DIR")
    sox_lib = os.getenv("SOX_LIB_DIR")

    if sox_include:
        INCLUDE_DIRS.append(sox_include)
    if sox_lib:
        LIBRARY_DIRS.append(sox_lib)

    LIBRARIES.extend(["sox"])

    if not (sox_include and sox_lib):
        print("WARNING: Windows build requires SOX_INCLUDE_DIR and SOX_LIB_DIR environment variables")
        print("Please set them to the paths where libsox is installed")

else:
    raise NotImplementedError(f"Platform {PLATFORM} is not yet supported. Supported platforms: Darwin (macOS), Linux")



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
        define_macros=DEFINE_MACROS,
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
            'overflowcheck': DEBUG,      # default: False (enabled in debug mode)
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
        gdb_debug=DEBUG,
    ),
    package_dir={"": "src"},
)
