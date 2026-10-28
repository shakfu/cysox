# Third-party licences

cysox itself is MIT (`LICENSE`). The wheels also contain the code below. Each wheel ships this directory under `.dist-info/licenses/`.

| component | in the wheel as | licence | file |
|-----------|-----------------|---------|------|
| libsox 14.4.2, patched | statically linked into `cysox/sox.*.so` | LGPL-2.1-or-later, plus older notices | `sox-LGPL-2.1.txt`, `sox-NOTICES.txt` |
| libgsm (in sox) | statically linked into `cysox/sox.*.so` | TU-Berlin-1.0 | `libgsm-COPYRIGHT.txt` |
| lpc10 (in sox) | statically linked into `cysox/sox.*.so` | LGPL-2.1-or-later, as part of sox (see below) | `sox-LGPL-2.1.txt` |
| KISS FFT | statically linked into `cysox/onset.*.so` | BSD-3-Clause | `vendor/kissfft/COPYING` |
| libmpg123 | bundled shared library | LGPL-2.1 | `mpg123-COPYING.txt` |
| LAME (libmp3lame) | bundled shared library | LGPL-2.0-or-later | `lame-COPYING.txt`, `lame-LICENSE.txt` |
| libFLAC | bundled shared library | BSD-3-Clause (Xiph) | `FLAC-COPYING.Xiph.txt` |
| libogg | bundled shared library | BSD-3-Clause | `ogg-COPYING.txt` |
| libvorbis, libvorbisenc, libvorbisfile | bundled shared libraries | BSD-3-Clause | `vorbis-COPYING.txt` |
| libopus | bundled shared library | BSD-3-Clause | `opus-COPYING.txt` |
| libopusfile | bundled shared library | BSD-3-Clause | `opusfile-COPYING.txt` |
| libpng | bundled shared library | libpng licence | `libpng-LICENSE.txt` |

Bundled shared libraries are in `cysox.libs/` on Linux and `cysox/.dylibs/` on macOS. The texts were taken from the manylinux_2_28 packages that the Linux wheels bundle. The macOS wheels bundle Homebrew builds of the same libraries.

lpc10 is sox's C translation of the US DoD LPC-10 coder. Its sources carry no licence notice. It is distributed under sox's LGPL-2.1-or-later, following Debian's `sox` copyright file: https://sources.debian.org/data/main/s/sox/14.4.2+git20190427-5/debian/copyright

This product uses LAME: https://lame.sourceforge.io (formerly www.mp3dev.org).

## LGPL components

libmpg123 and LAME are separate shared libraries, so you can replace them in an installed wheel.

libsox is statically linked. To relink cysox against a modified libsox, rebuild from source:

- cysox source: https://github.com/shakfu/cysox, and the sdist on PyPI.
- libsox source: `sox-14.4.2.tar.bz2` from https://sourceforge.net/projects/sox/files/sox/14.4.2/. Its sha256 is in `scripts/build-libsox.sh`.
- The modification to libsox: `scripts/patches/sox-14.4.2-mpg123.patch`, also LGPL-2.1-or-later.
- `scripts/build-libsox.sh` builds the static libsox, and `CMakeLists.txt` links it.
