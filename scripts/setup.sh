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
        echo "Detected macOS - building libsox from source against Homebrew codecs"

        if ! command -v brew &>/dev/null; then
            echo "Error: Homebrew is required on macOS"
            echo "Install from: https://brew.sh"
            exit 1
        fi

        DEPS=(flac lame mpg123 libogg libvorbis opus opusfile libpng pkg-config)
        MISSING=""
        for dep in "${DEPS[@]}"; do
            brew list --versions "$dep" &>/dev/null || MISSING="$MISSING $dep"
        done
        if [ -n "$MISSING" ]; then
            echo "Error: Missing Homebrew packages:$MISSING"
            echo "Install with: brew install$MISSING"
            exit 1
        fi

        "$(dirname "$0")/build-libsox.sh" .
        echo "Setup complete - static libsox installed to $LIB_DIR"
        ;;

    *)
        echo "Error: Unsupported platform: $(uname -s)"
        echo "Supported platforms: Linux, Darwin (macOS)"
        exit 1
        ;;
esac
