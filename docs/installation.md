# Installation

## Requirements

cysox requires:

- Python 3.9 or later
- libsox development libraries
- A C compiler (for building from source)

## Installing libsox

### macOS (Homebrew)

```bash
brew install flac lame mpg123 libogg libvorbis opus opusfile libpng pkg-config
```

`scripts/setup.sh` then builds libsox from source against these.

### Linux (Ubuntu/Debian)

```bash
sudo apt-get install libsox-dev libsndfile1-dev libflac-dev \
    libmp3lame-dev libvorbis-dev libopus-dev pkg-config
```

### Linux (Fedora/RHEL)

```bash
sudo dnf install sox-devel libsndfile-devel flac-devel \
    lame-devel libvorbis-devel opus-devel pkg-config
```

### Windows

Windows support is experimental. You need to:

1. Install libsox (e.g., via vcpkg or manual build)
2. Set environment variables:
   - `SOX_INCLUDE_DIR`: Path to sox headers
   - `SOX_LIB_DIR`: Path to sox libraries

## Installing cysox

### From PyPI

```bash
pip install cysox
```

The wheels need no system libsox. Their format support:

| Format | Read | Write |
|--------|------|-------|
| wav, aiff, au, raw, gsm | yes | yes |
| flac, ogg/vorbis | yes | yes |
| opus | yes | no |
| mp3 | yes | yes |

The wheels decode mp3 with libmpg123 rather than sox's usual libmad, which is GPL. Decoding is gapless: when a file carries a LAME tag, the encoder's delay and padding are trimmed, so lengths can differ from a libmad-based sox by up to a few thousand samples. See [mp3 decoding](dev/mp3_decoding.md).

The wheels have no audio device drivers on Linux, so `cysox.play()` works only on macOS.

The bundled libraries' licences ship in the wheel's `.dist-info/licenses/`; `licenses/README.md` in the repository lists them.

### From Source

```bash
git clone https://github.com/shakfu/cysox.git
cd cysox
pip install -e .
```

### Building a Wheel

```bash
make wheel
pip install dist/cysox-*.whl
```

### Development Installation

```bash
# Install with development dependencies
pip install -e ".[dev]"

# Run tests
make test
```

## Verifying Installation

```python
import cysox
print(f"cysox version: {cysox.__version__}")
```

## Platform Support

| Platform | Status  | Notes                        |
|----------|---------|------------------------------|
| macOS    | Full    | Primary development platform |
| Linux    | Full    | Tested on Ubuntu, Fedora     |
| Windows  | Partial | Requires manual libsox setup |
