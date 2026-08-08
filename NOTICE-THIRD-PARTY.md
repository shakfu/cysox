# Third-Party Notices

cysox itself is licensed under the MIT License (see `LICENSE`).

**Binary wheels are not pure MIT.** They bundle native libraries — statically
linked on macOS, vendored by `auditwheel` on Linux — and those libraries keep
their own licences inside the distributed artifact. This file records what is
bundled and what obligations come with it. It is shipped inside every wheel.

Building cysox from source against your own system libraries does not bundle
anything; in that case only the MIT licence applies to the code you obtained.

---

## Vendored into the source tree

| Component | Licence | Location |
|---|---|---|
| KissFFT | BSD-3-Clause | `vendor/kissfft/` (`COPYING`) |

KissFFT is compiled into the `onset` extension module on every platform,
including source builds.

---

## Bundled into binary wheels

Exact contents vary by platform. The authoritative list for any given wheel is
produced by `python scripts/check_licenses.py wheel <wheel>`, which the build
runs automatically and which fails if an unaudited library appears.

| Component | Licence | Notes |
|---|---|---|
| libsox / sox_ng | LGPL-2.1-or-later | Core audio library. Both macOS and Linux wheels bundle sox_ng 14.8.0.1 built `--without-mad` — statically on macOS, as a vendored shared object on Linux. |
| libsndfile | LGPL-2.1-or-later | Format I/O; provides mp3 decode via libmpg123. |
| libmpg123 | LGPL-2.1-only | mp3 decoding. |
| LAME (libmp3lame) | LGPL-2.0-or-later | mp3 encoding. |
| libFLAC | BSD-3-Clause | |
| libogg | BSD-3-Clause | |
| libvorbis, libvorbisenc, libvorbisfile | BSD-3-Clause | |
| libopus, libopusfile | BSD-3-Clause | |
| libsoxr | LGPL-2.1-or-later | Sample-rate conversion, when present. |
| libpng | PNG Reference Library License v2 | |
| zlib | Zlib | |
| libmagic | BSD-2-Clause | Linux only, and only when libsox is configured with file-type detection. |
| libbz2 | bzip2-1.0.6 (BSD-style) | Linux only, transitively via libmagic. |
| liblzma | 0BSD / public domain (XZ Utils) | Linux only, transitively via libmagic. |
| libltdl | LGPL-2.1-or-later | Only in wheels built against a libsox with dynamic format modules; cysox's own build uses `--without-libltdl`. |
| libgsm | Permissive (TU Berlin GSM 06.10 notice) | GSM 06.10 codec support. |
| libgomp | GPL-3.0-or-later WITH GCC-exception-3.1 | GCC OpenMP runtime; the Runtime Library Exception permits distribution with non-GPL software. |

### LGPL obligations

Several bundled components are LGPL-2.1 (or LGPL-2.0) licensed, and on macOS
they are **statically** linked. Distributing them imposes obligations on the
distributor, principally:

- this notice, which names each component and its licence;
- providing the complete corresponding source of the LGPL components, or a
  written offer for it — upstream sources are linked below;
- permitting the recipient to relink the work against a modified version of an
  LGPL component. For static linking this ordinarily means making the object
  files or an equivalent relinking mechanism available on request.

If you redistribute cysox wheels, or ship them inside your own product, these
obligations pass to you. Building against system shared libraries instead
avoids them entirely.

### What is deliberately absent

**libmad (GPL-2.0-or-later) is excluded**, along with libid3tag from the same
project. Bundling either would make the wheel GPL and contradict cysox's MIT
licence. Two mechanisms enforce this rather than one convention:

- `scripts/setup.sh` configures sox_ng `--without-mad` and aborts the macOS
  build if `HAVE_MAD` appears in `soxconfig.h` — or if `HAVE_SNDFILE` /
  `HAVE_LAME` are missing, since mp3 support would then be silently lost;
- `scripts/check_licenses.py` inspects the link graph before the build and the
  wheel contents after repair, and fails on any denylisted or unaudited native
  library on every platform.

mp3 read and write both still work: decode goes through libsndfile/libmpg123,
encode through LAME, all LGPL.

Note that on Debian/Ubuntu, the distro's sox delivers mp3 through a `dlopen`'d
plugin (`libsox_fmt_mp3.so`) that links libmad. This is why Linux wheels no
longer build against the distro's libsox at all: plugins sit outside libsox's
link graph, so `auditwheel` cannot vendor them, and a wheel built that way had
no mp3 handler while still being able to load a system plugin — and its libmad
— at runtime. cysox now builds sox_ng `--without-libltdl`, which compiles every
handler into the library and removes the dynamic-module path entirely.

---

## Upstream sources

- SoX — https://sourceforge.net/projects/sox/
- sox_ng — https://codeberg.org/sox_ng/sox_ng
- libsndfile — https://github.com/libsndfile/libsndfile
- mpg123 — https://www.mpg123.de/
- LAME — https://lame.sourceforge.io/
- FLAC — https://xiph.org/flac/
- Ogg / Vorbis / Opus — https://xiph.org/
- libsoxr — https://sourceforge.net/projects/soxr/
- libpng — http://www.libpng.org/pub/png/libpng.html
- zlib — https://zlib.net/
- file/libmagic — https://www.darwinsys.com/file/
- GNU libtool (libltdl) — https://www.gnu.org/software/libtool/
- libgsm — http://www.quut.com/gsm/
- KissFFT — https://github.com/mborgerding/kissfft
