# Installation

## Requirements

cysox requires:

- Python 3.9 or later
- libsox development libraries
- A C compiler (for building from source)

## Installing libsox

### macOS (Homebrew)

```bash
brew install sox libsndfile mad libpng flac lame mpg123 libogg opus libvorbis
```

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
