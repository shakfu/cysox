# cysox

[![PyPI](https://img.shields.io/pypi/v/cysox)](https://pypi.org/project/cysox/)
[![Python](https://img.shields.io/pypi/pyversions/cysox)](https://pypi.org/project/cysox/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

A Pythonic audio processing library which uses cython to wrap [libsox](https://github.com/chirlu/sox).

## Features

- **Simple API**: Convert, analyze, and play audio with one-liners
- **Typed Effects**: 28 effect classes with IDE autocomplete and validation
- **High Performance**: Direct C bindings through Cython
- **Zero Configuration**: Auto-initialization, no manual setup required
- **Cross-Platform**: macOS, Linux (Windows placeholder)

## Installation

Note that cysox only works on macOS and Linux.

```sh
pip install cysox
```

## Quick Start

```python
import cysox
from cysox import fx

# Get audio file info
info = cysox.info('audio.wav')
print(f"Duration: {info['duration']:.2f}s, Sample rate: {info['sample_rate']} Hz")

# Convert with effects
cysox.convert('input.wav', 'output.mp3', effects=[
    fx.Normalize(),
    fx.Reverb(reverberance=60),
    fx.Fade(fade_in=0.5, fade_out=1.0),
])

# Play audio (macOS/Linux)
cysox.play('audio.wav')

# Play with effects
cysox.play('audio.wav', effects=[fx.Volume(db=-6)])
```

## Core Functions

### `cysox.info(path) -> dict`

Get audio file metadata:

```python
info = cysox.info('audio.wav')
# Returns: {
#     'path': 'audio.wav',
#     'format': 'wav',
#     'duration': 11.5,
#     'sample_rate': 44100,
#     'channels': 2,
#     'bits_per_sample': 16,
#     'samples': 507150,
#     'encoding': 'signed-integer',
# }
```

### `cysox.convert(input, output, effects=[], **options)`

Convert audio files with optional effects and format options:

```python
# Simple format conversion
cysox.convert('input.wav', 'output.mp3')

# With effects
cysox.convert('input.wav', 'output.wav', effects=[
    fx.Volume(db=3),
    fx.Bass(gain=5),
    fx.Reverb(),
])

# With format options
cysox.convert('input.wav', 'output.wav',
    sample_rate=48000,
    channels=1,
    bits=24,
)
```

### `cysox.stream(path, chunk_size=8192) -> Iterator[memoryview]`

Stream audio samples for processing:

```python
import numpy as np

for chunk in cysox.stream('large.wav', chunk_size=8192):
    arr = np.frombuffer(chunk, dtype=np.int32)
    process(arr)
```

### `cysox.play(path, effects=[])`

Play audio to the default audio device:

```python
cysox.play('audio.wav')
cysox.play('audio.wav', effects=[fx.Volume(db=-6), fx.Reverb()])
```

### `cysox.concat(inputs, output)`

Concatenate multiple audio files:

```python
cysox.concat(['intro.wav', 'main.wav', 'outro.wav'], 'full.wav')
```

All input files must have the same sample rate and channel count.

## Effects Module

The `cysox.fx` module provides 28 typed effect classes:

### Volume & Dynamics
```python
fx.Volume(db=3)                    # Adjust volume in dB
fx.Gain(db=6)                      # Apply gain
fx.Normalize(level=-3)             # Normalize to target level
```

### Equalization
```python
fx.Bass(gain=5, frequency=100)     # Boost/cut bass
fx.Treble(gain=-2, frequency=3000) # Boost/cut treble
fx.Equalizer(frequency=1000, width=1.0, gain=3)
```

### Filters
```python
fx.HighPass(frequency=200)         # Remove low frequencies
fx.LowPass(frequency=8000)         # Remove high frequencies
fx.BandPass(frequency=1000, width=100)
fx.BandReject(frequency=60, width=10)  # Notch filter
```

### Spatial & Reverb
```python
fx.Reverb(reverberance=50, room_scale=100)
fx.Echo(gain_in=0.8, gain_out=0.9, delays=[100], decays=[0.5])
fx.Chorus()
fx.Flanger()
```

### Time-Based
```python
fx.Trim(start=1.0, end=5.0)        # Extract portion
fx.Pad(before=0.5, after=1.0)      # Add silence
fx.Speed(factor=1.5)               # Change speed (affects pitch)
fx.Tempo(factor=1.5)               # Change tempo (preserves pitch)
fx.Pitch(cents=100)                # Shift pitch (preserves tempo)
fx.Reverse()                       # Reverse audio
fx.Fade(fade_in=0.5, fade_out=1.0) # Fade in/out
fx.Repeat(count=3)                 # Repeat audio
```

### Conversion
```python
fx.Rate(sample_rate=48000)         # Resample
fx.Channels(channels=1)            # Change channel count
fx.Remix(out_spec=[[1, 2]])        # Custom channel mixing
fx.Dither()                        # Add dither
```

### Composite Effects

Create reusable effect combinations:

```python
from cysox.fx import CompositeEffect, HighPass, LowPass, Reverb, Volume

class TelephoneEffect(CompositeEffect):
    """Simulate telephone audio quality."""

    @property
    def effects(self):
        return [
            HighPass(frequency=300),
            LowPass(frequency=3400),
            Volume(db=-3),
        ]

# Use like any other effect
cysox.convert('input.wav', 'output.wav', effects=[TelephoneEffect()])
```

## Low-Level API

For advanced use cases, access the full libsox bindings:

```python
from cysox import sox

# Manual initialization (high-level API handles this automatically)
sox.init()

# Open files
input_fmt = sox.Format('input.wav')
output_fmt = sox.Format('output.wav', signal=input_fmt.signal, mode='w')

# Build effects chain
chain = sox.EffectsChain(input_fmt.encoding, output_fmt.encoding)

e = sox.Effect(sox.find_effect("input"))
e.set_options([input_fmt])
chain.add_effect(e, input_fmt.signal, input_fmt.signal)

e = sox.Effect(sox.find_effect("vol"))
e.set_options(["3dB"])
chain.add_effect(e, input_fmt.signal, input_fmt.signal)

e = sox.Effect(sox.find_effect("output"))
e.set_options([output_fmt])
chain.add_effect(e, input_fmt.signal, input_fmt.signal)

# Process
chain.flow_effects()

# Cleanup
input_fmt.close()
output_fmt.close()
sox.quit()
```

## Building from Source

### macOS

```sh
brew install sox libsndfile mad libpng flac lame mpg123 libogg opus opusfile libvorbis
make
make test
```

### Linux

```sh
apt-get install libsox-dev libsndfile1-dev
make
make test
```

## Status

Comprehensive test suite covering all functionality. All libsox C examples ported to Python (effects chains, waveform analysis, trim, concatenation, format conversion).

## Known Issues

- **Memory I/O**: libsox memory I/O functions have platform issues (tests skipped)
- **Init/Quit Cycles**: Use high-level API to avoid init/quit issues (handled automatically)

See [KNOWN_LIMITATIONS.md](https://github.com/shakfu/cysox/blob/main/KNOWN_LIMITATIONS.md) for details.

## Platform Support

- **macOS**: Full support
- **Linux**: Full support
- **Windows**: Placeholder (contributions welcome)

## Building Documentation

```sh
pip install sphinx furo myst-parser
make docs
make docs-serve  # http://localhost:8000
```

## License

MIT
