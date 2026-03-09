# cysox Documentation

**cysox** is a Cython wrapper for [libsox](https://github.com/chirlu/sox), providing
high-performance Python bindings to the SoX (Sound eXchange) audio processing library.

!!! note
    cysox requires libsox to be installed on your system. See [Installation](installation.md) for details.

## Quick Start

```python
import cysox
from cysox import fx

# Get file info
info = cysox.info('audio.wav')
print(f"Duration: {info.duration:.2f}s, Sample rate: {info.sample_rate} Hz")

# Convert with effects
cysox.convert('input.wav', 'output.mp3', effects=[
    fx.Normalize(),
    fx.Reverb(reverberance=60),
])

# Play audio
cysox.play('audio.wav')
```

## Features

- **Audio Processing**: Convert between different audio formats (WAV, MP3, FLAC, OGG, etc.)
- **Signal Manipulation**: Apply various audio effects and filters
- **High Performance**: Direct C bindings through Cython, KissFFT-accelerated onset detection
- **Buffer Protocol**: Zero-copy integration with NumPy, PyTorch, and array.array
- **Context Managers**: Automatic resource cleanup with `with` statements
- **Type Hints**: Full IDE autocomplete support via type stubs
