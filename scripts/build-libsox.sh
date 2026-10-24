#!/bin/bash
# Build a static libsox for the wheels, with codecs compiled in. mp3 decoding
# uses libmpg123 (LGPL) via scripts/patches/; sox 14.4.2 knows only libmad,
# which is GPL and cannot ship in an MIT wheel.
#
# Usage: scripts/build-libsox.sh PREFIX
set -euo pipefail

PREFIX=$(mkdir -p "${1:?usage: $0 PREFIX}" && cd "$1" && pwd)
SOX_VERSION=14.4.2
SOX_SHA256=81a6956d4330e75b5827316e44ae381e6f1e8928003c6aa45896da9041ea149c
PATCHES=$(cd "$(dirname "$0")/patches" && pwd)
SOX_URL="https://downloads.sourceforge.net/project/sox/sox/${SOX_VERSION}/sox-${SOX_VERSION}.tar.bz2"

WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

curl -fsSL -o "$WORK/sox.tar.bz2" "$SOX_URL"
if command -v sha256sum >/dev/null; then
    echo "$SOX_SHA256  $WORK/sox.tar.bz2" | sha256sum -c -
else
    echo "$SOX_SHA256  $WORK/sox.tar.bz2" | shasum -a 256 -c -
fi
tar xjf "$WORK/sox.tar.bz2" -C "$WORK"
cd "$WORK/sox-${SOX_VERSION}"

patch -p1 < "$PATCHES/sox-14.4.2-mpg123.patch"

case "$(uname -s)" in
    Darwin)
        AUDIO=(--with-coreaudio=yes)
        # Homebrew's prefix is not on the default compiler search path on arm64.
        BREW=$(brew --prefix)
        export CPPFLAGS="-I$BREW/include ${CPPFLAGS:-}"
        export LDFLAGS="-L$BREW/lib ${LDFLAGS:-}"
        ;;
    *)
        AUDIO=(--with-coreaudio=no)
        ;;
esac

# sox's configure has no mpg123 option, so define and link it by hand.
export CPPFLAGS="-DHAVE_MPG123_H ${CPPFLAGS:-}"
export LIBS="-lmpg123 ${LIBS:-}"

./configure \
    --prefix="$PREFIX" \
    --disable-shared --enable-static --with-pic \
    --disable-openmp --disable-symlinks \
    --without-libltdl --without-mad \
    --with-lame \
    --with-flac=yes --with-oggvorbis=yes --with-opus=yes \
    --with-mp3=yes --with-gsm=yes --with-lpc10=yes \
    --with-png \
    --without-id3tag --without-twolame --without-magic --without-ladspa \
    --with-sndfile=no --with-wavpack=no --with-amrwb=no --with-amrnb=no \
    --with-alsa=no --with-ao=no --with-pulseaudio=no --with-oss=no \
    --with-sndio=no --with-sunaudio=no --with-waveaudio=no \
    "${AUDIO[@]}"

# Library, header and sox.pc only. The sox binary and test programs are not
# needed, and sox_sample_test fails to compile under GCC 14.
JOBS=$(getconf _NPROCESSORS_ONLN)
make -j"$JOBS" -C libgsm
make -j"$JOBS" -C lpc10
make -j"$JOBS" -C src libsox.la
make -C src install-libLTLIBRARIES install-includeHEADERS
make install-pkgconfigDATA

# sox.pc lists only -lm in Libs.private, so a static link misses every codec.
# Take the flags configure found from the generated Makefile instead. Only
# -L from LDFLAGS: sox adds -Wl,-z,defs, which breaks a Python extension link.
LIBS_PRIVATE=$(printf 'print-libs:\n\t@echo $(filter -L%%,$(LDFLAGS)) $(FLAC_LIBS) $(OGG_VORBIS_LIBS) $(OPUS_LIBS) -lopus $(MP3_LIBS) $(PNG_LIBS) $(COREAUDIO_LIBS) $(LIBS)\n' \
    | make -s --no-print-directory -C src -f Makefile -f - print-libs)
LIBS_PRIVATE="$LIBS_PRIVATE" perl -pi -e 's|^Libs\.private:.*|Libs.private: $ENV{LIBS_PRIVATE}|' "$PREFIX/lib/pkgconfig/sox.pc"
grep '^Libs.private' "$PREFIX/lib/pkgconfig/sox.pc"
