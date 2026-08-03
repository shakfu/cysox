#!/bin/bash
set -e

INCLUDE_DIR=./include
LIB_DIR=./lib

mkdir -p "$LIB_DIR" "$INCLUDE_DIR"

# Detect platform
case "$(uname -s)" in
    Linux)
        echo "Detected Linux - using system libraries"

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
            echo "libsox.a not found - building sox_ng from source..."
            SOX_NG_VERSION="14.8.0.1"
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
