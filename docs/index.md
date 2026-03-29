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

- **Audio Processing**: Convert between formats (WAV, MP3, FLAC, OGG, etc.) with optional effects
- **[27 Built-in Effects](api/effects.md)**: Volume, EQ, reverb, echo, chorus, flanger, pitch, tempo, trim, and more
- **[53 Presets](api/effects.md#presets)**: Ready-to-use effect chains (Telephone, Cathedral, LoFiHipHop, DrumPunch, etc.)
- **[Onset Detection](api/onset.md)**: C-optimized transient detection with 5 algorithms (HFC, flux, energy, complex, superflux)
- **[Sample Processing](api/samples.md)**: Auto-trim silence, split recordings into one-shots, generate chromatic pitch scales, batch process directories
- **[Drum Loop Tools](api/samples.md#drum-loop-slicing)**: Slice loops by BPM, create stutter effects, apply beat-synced processing
- **[CLI Tool](cli.md)**: Convert, slice, stutter, batch process, and apply presets from the command line
- **High Performance**: Direct C bindings through Cython, KissFFT-accelerated analysis
- **Buffer Protocol**: Zero-copy integration with NumPy, PyTorch, and array.array
- **Type Hints**: Full IDE autocomplete support via type stubs

## Two API Levels

**High-level API** (recommended) -- handles initialization automatically:

```python
import cysox
cysox.convert('in.wav', 'out.wav', effects=[fx.Reverb()])
```

**Low-level API** -- direct libsox bindings for full control:

```python
from cysox import sox
sox.init()
with sox.Format('audio.wav') as f:
    samples = f.read(1024)
sox.quit()
```

See the [Quick Start Guide](quickstart.md) for detailed usage of both APIs.
