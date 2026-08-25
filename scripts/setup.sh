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

        # Check the libsox version. Two things can go wrong here and both are
        # much cheaper to catch now than as a C compile error later.
        SOX_VERSION=$(pkg-config --modversion sox 2>/dev/null)
        SOX_MAJOR=${SOX_VERSION%%.*}
        SOX_REST=${SOX_VERSION#*.}
        SOX_MINOR=${SOX_REST%%.*}

        if [ -z "$SOX_VERSION" ]; then
            echo "Warning: could not determine libsox version; continuing"
        elif [ "$SOX_MAJOR" -lt 14 ] || { [ "$SOX_MAJOR" -eq 14 ] && [ "$SOX_MINOR" -lt 4 ]; }; then
            echo "Error: libsox $SOX_VERSION is too old; cysox needs 14.4 or later"
            exit 1
        elif [ "$SOX_MAJOR" -gt 14 ] || [ "$SOX_MINOR" -ge 5 ]; then
            echo "Warning: detected libsox $SOX_VERSION (SoX_ng)."
            echo "  cysox targets the original libsox 14.4.x. It builds and"
            echo "  largely works against SoX_ng, with one known difference:"
            echo "  SoX_ng inserted values into the sox_encoding_t enum, so the"
            echo "  encoding names reported by cysox.info() are shifted (MP3"
            echo "  reads as 'amr-wb'). A few tests in tests/test_sox_encoding.py"
            echo "  and tests/test_sox_format.py fail for this reason."
        fi

        # Create placeholder for Makefile target
        touch "$LIB_DIR/libsox.a"
        echo "Setup complete - using system libsox ${SOX_VERSION:-(unknown version)} via pkg-config"
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

        DEPS=(sox flac lame mpg123 libogg libsndfile opus opusfile libvorbis libpng mad)
        for dep in "${DEPS[@]}"; do
            copy_lib "$dep"
        done

        # Build libmad from source if static library not available
        # (Homebrew's mad package only ships dynamic libraries)
        # Build libmad from source if static library not available
        # (Homebrew's mad package only ships dynamic libraries)
        if [ ! -f "$LIB_DIR/libmad.a" ]; then
            echo "libmad.a not found - building from source..."
            MAD_VERSION="0.16.4"
            MAD_BUILD_DIR=$(mktemp -d)
            curl -sL "https://codeberg.org/tenacityteam/libmad/archive/${MAD_VERSION}.tar.gz" \
                | tar xz -C "$MAD_BUILD_DIR"
            pushd "$MAD_BUILD_DIR/libmad" > /dev/null
            cmake -B build \
                -DCMAKE_BUILD_TYPE=Release \
                -DCMAKE_OSX_ARCHITECTURES="$(uname -m)" \
                -DCMAKE_POLICY_VERSION_MINIMUM=3.5 \
                -DBUILD_SHARED_LIBS=OFF
            cmake --build build
            popd > /dev/null
            cp "$MAD_BUILD_DIR/libmad/build/libmad.a" "$LIB_DIR/"
            [ ! -f "$INCLUDE_DIR/mad.h" ] && cp "$MAD_BUILD_DIR/libmad/build/mad.h" "$INCLUDE_DIR/"
            rm -rf "$MAD_BUILD_DIR"
            echo "libmad.a built successfully"
        fi

        # Remove unnecessary libraries
        rm -f \
            "$LIB_DIR/libpng.a" \
            "$LIB_DIR/libsyn123.a" \
            "$LIB_DIR/libout123.a" \
            "$LIB_DIR/libFLAC++.a" \
            "$LIB_DIR/libopusurl.a"

        echo "Setup complete - libraries copied to $LIB_DIR"
        ;;

    *)
        echo "Error: Unsupported platform: $(uname -s)"
        echo "Supported platforms: Linux, Darwin (macOS)"
        exit 1
        ;;
esac
