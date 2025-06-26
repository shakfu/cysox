# cysox

Towards a cython wrapper for [libsox](https://github.com/chirlu/sox)

## Overview

**cysox** is a Cython wrapper for [libsox](https://github.com/chirlu/sox), providing Python bindings to the SoX (Sound eXchange) library. SoX is a cross-platform command line utility that can convert various formats of computer audio files in to other formats.

## Features

- **Audio Processing**: Convert between different audio formats
- **Signal Manipulation**: Apply various audio effects and filters
- **Cross-platform**: Works on Windows, macOS, and Linux
- **High Performance**: Direct C bindings through Cython for optimal performance
- **Memory Efficient**: Low-level memory management for large audio files

## Building

Currently development and testing is only on MacOS. [Homebrew](https://brew.sh) is used for installing dependencies:

```sh
brew install sox libsndfile mad libpng
```

then you can build the cython extension:

```sh
make
```

build the wheel:

```sh
make wheel
```

run tests:

```sh
make test
```

## Usage Example

```python
>>> import sox
>>> f = sox.Format('tests/s00.wav')
>>> f.filetype
'wav'
>>> f.signal
<sox.SignalInfo at 0x105c754a0>
>>> f.signal.length
502840
>>> f.encoding
<sox.EncodingInfo at 0x105d4ebe0>
>>> f.encoding.bits_per_sample
16
```

## TODO

- [x] convert example0.c to test_example0.py
- [ ] pass 100% of test_example0.py
- [ ] convert example1.c to test_example1.py
- [ ] convert example2.c to test_example2.py
- [ ] convert example3.c to test_example3.py
- [ ] convert example4.c to test_example4.py
- [ ] convert example5.c to test_example5.py
- [ ] convert example6.c to test_example6.py
- [ ] test on linux
