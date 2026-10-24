"""Fail if an installed cysox wheel bundles a library without its licence.

Run by cibuildwheel's test-command. See licenses/README.md.
"""

import sys
from importlib.metadata import distribution

# Bundled shared library name (without version or auditwheel hash) -> licence.
SHARED = {
    "libFLAC": "FLAC-COPYING.Xiph.txt",
    "libmp3lame": "lame-COPYING.txt",
    "libmpg123": "mpg123-COPYING.txt",
    "libogg": "ogg-COPYING.txt",
    "libopus": "opus-COPYING.txt",
    "libopusfile": "opusfile-COPYING.txt",
    "libpng16": "libpng-LICENSE.txt",
    "libvorbis": "vorbis-COPYING.txt",
    "libvorbisenc": "vorbis-COPYING.txt",
    "libvorbisfile": "vorbis-COPYING.txt",
}
# Statically linked into the extensions, so always required.
STATIC = ["sox-LGPL-2.1.txt", "sox-NOTICES.txt", "libgsm-COPYRIGHT.txt", "COPYING"]

files = [str(f) for f in distribution("cysox").files]
licences = {f.rsplit("/", 1)[-1] for f in files if ".dist-info/licenses/" in f}
bundled = [
    f.rsplit("/", 1)[-1]
    for f in files
    if (f.startswith("cysox.libs/") or f.startswith("cysox/.dylibs/"))
    and (".so" in f or f.endswith(".dylib"))
]

missing = [s for s in STATIC if s not in licences]
for lib in bundled:
    name = lib.split(".")[0].split("-")[0]
    if SHARED.get(name) not in licences:
        missing.append(f"{lib} ({SHARED.get(name, 'not in SHARED')})")

print(f"{len(bundled)} bundled libraries, {len(licences)} licence files")
if missing:
    sys.exit(f"missing licences: {missing}")
