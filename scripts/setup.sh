#!/bin/bash
set -e

INCLUDE_DIR=./include
LIB_DIR=./lib

mkdir -p "$LIB_DIR" "$INCLUDE_DIR"

# Pinned source versions, shared by the Linux SOX_NG path below and the macOS
# path further down. Bump deliberately: sox_ng is what makes mp3 work without
# libmad, and libsndfile >= 1.1 is what makes libmpg123 reachable from sox.
SOX_NG_VERSION="${SOX_NG_VERSION:-14.8.0.1}"
MPG123_VERSION="${MPG123_VERSION:-1.32.10}"
LAME_VERSION="${LAME_VERSION:-3.100}"
SNDFILE_VERSION="${SNDFILE_VERSION:-1.2.2}"

# Detect platform
case "$(uname -s)" in
    Linux)
        if [ "${SOX_NG:-0}" != "1" ]; then
            echo "Detected Linux - using system libraries"
            echo "(set SOX_NG=1 to build sox_ng from source instead - this is"
            echo " what the wheel build does; see scripts/setup.sh)"

            # Check for required dependencies
            MISSING=""
            if ! pkg-config --exists sox 2>/dev/null; then
                MISSING="$MISSING libsox-dev"
            fi

            if [ -n "$MISSING" ]; then
                echo "Error: Missing required packages:$MISSING"
                echo "Install with: sudo apt install$MISSING"
                exit 1
            fi

            # Create placeholder for Makefile target
            touch "$LIB_DIR/libsox.a"
            echo "Setup complete - system libraries will be used via pkg-config"
            exit 0
        fi

        # ------------------------------------------------------------------
        # SOX_NG=1: build sox_ng and its mp3 dependency chain from source.
        #
        # Why the wheel build does not use the distro's libsox:
        #
        #   1. On Debian/Ubuntu, sox's mp3 support lives in a dlopen'd plugin
        #      (libsox_fmt_mp3.so) that links libmad (GPL-2.0-or-later).
        #      auditwheel only follows the link graph, so the plugin is never
        #      vendored -- a repaired wheel therefore has NO mp3 handler at
        #      all. Verified by running auditwheel repair: the wheel contains
        #      libsox.so.3 and no libsox_fmt_*.
        #   2. auditwheel rewrites the vendored SONAME. If the target system
        #      does happen to have libsox-fmt-mp3 installed, the plugin
        #      declares NEEDED libsox.so.3 and drags the *system* libsox into
        #      the process alongside the vendored one -- two copies of a
        #      library with global state, and libmad arriving at runtime.
        #   3. Whatever flags a distro chose are outside our control, so the
        #      licence of the artifact would depend on the build host.
        #
        # Building sox_ng --without-mad compiles the mp3 handler INTO libsox
        # (decode via libsndfile/libmpg123, encode via LAME, all LGPL-2.1),
        # which survives auditwheel and removes the plugin mechanism entirely.
        #
        # Built SHARED, not static: auditwheel vendors the .so, which keeps
        # the LGPL relinking obligation as easy to satisfy as it is today.
        # ------------------------------------------------------------------
        SOX_NG_PREFIX="${SOX_NG_PREFIX:-/usr/local}"
        echo "Detected Linux - building sox_ng ${SOX_NG_VERSION} into ${SOX_NG_PREFIX}"

        if [ ! -w "$(dirname "$SOX_NG_PREFIX")" ] && [ ! -w "$SOX_NG_PREFIX" ]; then
            echo "Error: $SOX_NG_PREFIX is not writable."
            echo "Run as root (the wheel build does), or set SOX_NG_PREFIX to a writable path."
            exit 1
        fi

        BUILD_DIR=$(mktemp -d)
        trap 'rm -rf "$BUILD_DIR"' EXIT
        export PKG_CONFIG_PATH="$SOX_NG_PREFIX/lib/pkgconfig:$SOX_NG_PREFIX/lib64/pkgconfig:${PKG_CONFIG_PATH:-}"
        export LD_LIBRARY_PATH="$SOX_NG_PREFIX/lib:$SOX_NG_PREFIX/lib64:${LD_LIBRARY_PATH:-}"
        NPROC=$(nproc 2>/dev/null || echo 2)

        # fetch_build <name> <url> <configure-args...>
        fetch_build() {
            local name=$1 url=$2
            shift 2
            echo "--- building $name"
            local dir="$BUILD_DIR/$name"
            mkdir -p "$dir"
            curl -sSL "$url" | tar x --strip-components=1 -C "$dir"
            pushd "$dir" > /dev/null
            ./configure --prefix="$SOX_NG_PREFIX" --enable-shared --disable-static \
                --with-pic "$@"
            make -j"$NPROC"
            make install
            popd > /dev/null
        }

        # libmpg123: LGPL-2.1 mp3 decoder. libsndfile reaches mp3 through it.
        fetch_build mpg123 \
            "https://downloads.sourceforge.net/project/mpg123/mpg123/${MPG123_VERSION}/mpg123-${MPG123_VERSION}.tar.bz2"

        # LAME: LGPL mp3 encoder. sox_ng only registers the .mp3 handler when
        # MAD or LAME is present, so this is what keeps mp3 reachable at all.
        fetch_build lame \
            "https://downloads.sourceforge.net/project/lame/lame/${LAME_VERSION}/lame-${LAME_VERSION}.tar.gz" \
            --disable-frontend

        # libsndfile >= 1.1 exposes SF_FORMAT_MPEG; distro builds on the
        # manylinux base images are 1.0.x and predate it. --enable-mpeg needs
        # the mpg123 and LAME built just above.
        fetch_build libsndfile \
            "https://github.com/libsndfile/libsndfile/releases/download/${SNDFILE_VERSION}/libsndfile-${SNDFILE_VERSION}.tar.xz" \
            --enable-mpeg

        # sox_ng itself, deliberately without libmad.
        echo "--- building sox_ng"
        SOX_DIR="$BUILD_DIR/sox_ng"
        mkdir -p "$SOX_DIR"
        curl -sSL "https://codeberg.org/sox_ng/sox_ng/releases/download/sox_ng-${SOX_NG_VERSION}/sox_ng-${SOX_NG_VERSION}.tar.gz" \
            | tar xz --strip-components=1 -C "$SOX_DIR"
        pushd "$SOX_DIR" > /dev/null

        # --enable-replace installs as sox.h / libsox.so / sox.pc, so nothing
        # downstream needs to know this is sox_ng.
        ./configure \
            --prefix="$SOX_NG_PREFIX" \
            --enable-replace \
            --without-mad \
            --enable-shared \
            --disable-static \
            --with-pic \
            --without-ao \
            --without-oss \
            --without-alsa \
            --without-pulseaudio \
            --without-sndio \
            --without-ladspa \
            --without-amrnb \
            --without-amrwb \
            --without-libltdl

        # --without-libltdl is what keeps this from recreating the problem it
        # exists to solve: with the dynamic-module mechanism off, every format
        # handler is compiled into libsox and there is no dlopen path for a
        # stray system plugin (and its libmad) to arrive through at runtime.

        # Same refusal the macOS path makes: fail loudly rather than silently
        # shipping a GPL-encumbered wheel, or one that cannot handle mp3.
        if grep -q '^#define HAVE_MAD ' src/soxconfig.h; then
            echo "Error: sox_ng configured WITH libmad - refusing to build a GPL-encumbered wheel"
            exit 1
        fi
        if ! grep -q '^#define HAVE_SNDFILE ' src/soxconfig.h; then
            echo "Error: sox_ng configured without libsndfile - mp3 decoding would be unavailable"
            exit 1
        fi
        if ! grep -q '^#define HAVE_LAME ' src/soxconfig.h; then
            echo "Error: sox_ng configured without LAME - the mp3 handler would not be registered"
            exit 1
        fi

        make -j"$NPROC"
        make install
        popd > /dev/null

        ldconfig "$SOX_NG_PREFIX/lib" "$SOX_NG_PREFIX/lib64" 2>/dev/null || true

        # Verify the result rather than trusting the configure flags: no libmad
        # in the link graph, and mp3 actually decodes through the built library.
        SOX_LIB=$(ls "$SOX_NG_PREFIX"/lib*/libsox.so.* 2>/dev/null | head -1)
        if [ -z "$SOX_LIB" ]; then
            echo "Error: libsox.so not found under $SOX_NG_PREFIX after install"
            exit 1
        fi
        if ldd "$SOX_LIB" | grep -q libmad; then
            echo "Error: built libsox links libmad - refusing to continue"
            exit 1
        fi
        if [ -x "$SOX_NG_PREFIX/bin/sox" ] && [ -f tests/data/s00.mp3 ]; then
            if ! "$SOX_NG_PREFIX/bin/sox" tests/data/s00.mp3 -n stat 2>&1 | grep -q Samples; then
                echo "Error: built sox cannot decode mp3 - the whole point of this path"
                exit 1
            fi
            echo "mp3 decode verified through the built libsox"
        fi

        # Placeholder so the Makefile's lib/libsox.a target is satisfied; the
        # real library is shared and lives in $SOX_NG_PREFIX.
        touch "$LIB_DIR/libsox.a"
        echo "Setup complete - sox_ng ${SOX_NG_VERSION} (shared, without libmad) in $SOX_NG_PREFIX"
        ;;

    Darwin)
        echo "Detected macOS - copying libraries from Homebrew"

        if ! command -v brew &>/dev/null; then
            echo "Error: Homebrew is required on macOS"
            echo "Install from: https://brew.sh"
            exit 1
        fi

        copy_lib() {
            local name=$1
            local prefix
            prefix=$(brew --prefix "$name" 2>/dev/null) || {
                echo "Warning: $name not found via Homebrew, skipping"
                return 0
            }

            [ -d "$prefix/include" ] && cp -rf "$prefix/include/"* "$INCLUDE_DIR/" 2>/dev/null || true
            [ -d "$prefix/lib" ] && cp -af "$prefix/lib/"*.a "$LIB_DIR/" 2>/dev/null || true
            [ -d "$prefix/lib" ] && cp -af "$prefix/lib/"*.dylib "$LIB_DIR/" 2>/dev/null || true
        }

        # Note: `sox` and `mad` are deliberately absent.
        #
        # Homebrew's libsox is compiled against libmad, which is GPL-2.0-or-later.
        # Bundling it into a wheel would make the distributed artifact GPL and so
        # unshippable under cysox's MIT licence. Instead we build sox_ng below with
        # --without-mad; its mp3 handler then decodes through libsndfile/libmpg123
        # (LGPL-2.1) and still encodes through LAME, so mp3 read *and* write keep
        # working with nothing GPL in the wheel.
        DEPS=(flac lame mpg123 libogg libsndfile opus opusfile libvorbis libpng)
        for dep in "${DEPS[@]}"; do
            copy_lib "$dep"
        done

        # Build sox_ng from source, without libmad (see the note above).
        if [ ! -f "$LIB_DIR/libsox.a" ]; then
            echo "libsox.a not found - building sox_ng ${SOX_NG_VERSION} from source..."
            SOX_BUILD_DIR=$(mktemp -d)
            SOX_PREFIX="$SOX_BUILD_DIR/prefix"
            BREW_PREFIX=$(brew --prefix)

            # The release tarball ships a pregenerated `configure`, so autotools
            # are not needed on the build machine.
            curl -sL "https://codeberg.org/sox_ng/sox_ng/releases/download/sox_ng-${SOX_NG_VERSION}/sox_ng-${SOX_NG_VERSION}.tar.gz" \
                | tar xz -C "$SOX_BUILD_DIR"
            pushd "$SOX_BUILD_DIR/sox_ng-${SOX_NG_VERSION}" > /dev/null

            # --enable-replace installs under the traditional sox.h / libsox.a /
            # sox.pc names, so nothing downstream has to know this is sox_ng.
            PKG_CONFIG_PATH="$BREW_PREFIX/lib/pkgconfig:$PKG_CONFIG_PATH" \
            ./configure \
                --prefix="$SOX_PREFIX" \
                --enable-replace \
                --without-mad \
                --enable-static \
                --disable-shared \
                --with-pic \
                --without-ao \
                --without-oss \
                --without-alsa \
                --without-pulseaudio \
                --without-sndio \
                --without-ladspa \
                --without-amrnb \
                --without-amrwb \
                CPPFLAGS="-I$BREW_PREFIX/include" \
                LDFLAGS="-L$BREW_PREFIX/lib"

            # Fail loudly rather than silently shipping a wheel that is GPL-
            # encumbered, or one that cannot read mp3 at all. The mp3 handler is
            # only registered when MAD or LAME is present, and with MAD excluded
            # the decode path needs SNDFILE (libmpg123) to be found.
            if grep -q '^#define HAVE_MAD ' src/soxconfig.h; then
                echo "Error: sox_ng configured WITH libmad - refusing to build a GPL-encumbered wheel"
                exit 1
            fi
            if ! grep -q '^#define HAVE_SNDFILE ' src/soxconfig.h; then
                echo "Error: sox_ng configured without libsndfile - mp3 decoding would be unavailable"
                exit 1
            fi
            if ! grep -q '^#define HAVE_LAME ' src/soxconfig.h; then
                echo "Error: sox_ng configured without LAME - the mp3 handler would not be registered"
                exit 1
            fi

            make -j"$(sysctl -n hw.ncpu)"
            make install
            popd > /dev/null

            cp -L "$SOX_PREFIX/lib/libsox.a" "$LIB_DIR/"
            cp -L "$SOX_PREFIX/include/sox.h" "$INCLUDE_DIR/"
            rm -rf "$SOX_BUILD_DIR"
            echo "libsox.a (sox_ng ${SOX_NG_VERSION}, without libmad) built successfully"
        fi

        # Remove unnecessary libraries. libmad*/mad.h are cleaned up too: they are
        # left over from earlier checkouts that bundled it, and a stale libmad.a
        # in lib/ would silently be linked back into the wheel.
        rm -f \
            "$LIB_DIR/libpng.a" \
            "$LIB_DIR/libsyn123.a" \
            "$LIB_DIR/libout123.a" \
            "$LIB_DIR/libFLAC++.a" \
            "$LIB_DIR/libopusurl.a" \
            "$LIB_DIR/libmad.a" \
            "$LIB_DIR/libmad."*.dylib \
            "$LIB_DIR/libmad.dylib" \
            "$INCLUDE_DIR/mad.h"

        echo "Setup complete - libraries copied to $LIB_DIR"
        ;;

    *)
        echo "Error: Unsupported platform: $(uname -s)"
        echo "Supported platforms: Linux, Darwin (macOS)"
        exit 1
        ;;
esac
