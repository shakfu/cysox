# cysox High-Level API

This document describes the high-level API for cysox and how to extend it.

## Overview

cysox provides two API layers:

1. **High-Level API** (recommended) - Pythonic, auto-initializing, simple
2. **Low-Level API** - Direct libsox bindings for advanced use cases

```python
# High-level API (default, recommended)
import cysox
cysox.convert('in.wav', 'out.mp3')

# Low-level API (power users)
from cysox import sox
sox.init()
f = sox.Format('audio.wav')
# ...
sox.quit()
```

## Module Structure

```text
src/cysox/
    __init__.py      # Exports high-level API as default
    audio.py         # High-level wrapper implementation
    sox.pyx          # Low-level Cython bindings
    fx/
        __init__.py  # Exports all effect classes
        base.py      # Base classes (Effect, CompositeEffect, PythonEffect)
        effects.py   # Built-in effect implementations
```

---

## Core Functions

### `info(path) -> dict`

Get audio file metadata.

```python
info = cysox.info('audio.wav')
# Returns:
# {
#     'path': 'audio.wav',
#     'format': 'wav',
#     'duration': 11.5,          # seconds
#     'sample_rate': 44100,
#     'channels': 2,
#     'bits_per_sample': 16,
#     'samples': 507150,
#     'encoding': 'signed-integer',
# }
```

### `convert(input, output, effects=None, **options)`

Convert audio files with optional effects.

```python
from cysox import fx

# Simple format conversion
cysox.convert('input.wav', 'output.mp3')

# With effects
cysox.convert('input.wav', 'output.wav', effects=[
    fx.Volume(db=3),
    fx.Bass(gain=5),
    fx.Reverb(),
])

# With output options
cysox.convert('input.wav', 'output.wav',
    sample_rate=48000,
    channels=1,
    bits=24
)
```

### `stream(path, chunk_size=8192) -> Iterator[memoryview]`

Stream audio samples for processing large files.

```python
for chunk in cysox.stream('large.wav', chunk_size=8192):
    # chunk is a memoryview - works with numpy, array.array, etc.
    arr = np.frombuffer(chunk, dtype=np.int32)
    process(arr)
```

### `play(path, effects=None)`

Play audio to the default audio device.

```python
cysox.play('audio.wav')
cysox.play('audio.wav', effects=[fx.Volume(db=-6), fx.Reverb()])
```

Uses platform-specific audio output: `coreaudio` (macOS), `alsa`/`pulseaudio` (Linux).

### `concat(inputs, output)`

Concatenate multiple audio files.

```python
cysox.concat(['intro.wav', 'main.wav', 'outro.wav'], 'full.wav')
```

All input files must have the same sample rate and channel count.

---

## Effects Module

The `cysox.fx` module provides 28 typed effect classes with IDE autocomplete and parameter validation.

### Built-in Effects

| Category | Effects |
|----------|---------|
| Volume/Dynamics | `Volume`, `Gain`, `Normalize` |
| Equalization | `Bass`, `Treble`, `Equalizer` |
| Filters | `HighPass`, `LowPass`, `BandPass`, `BandReject` |
| Spatial/Reverb | `Reverb`, `Echo`, `Chorus`, `Flanger` |
| Time-based | `Trim`, `Pad`, `Speed`, `Tempo`, `Pitch`, `Reverse`, `Fade`, `Repeat` |
| Conversion | `Rate`, `Channels`, `Remix`, `Dither` |

### Example Effect Usage

```python
from cysox import fx

cysox.convert('in.wav', 'out.wav', effects=[
    fx.Volume(db=3),
    fx.Bass(gain=5, frequency=100),
    fx.Reverb(reverberance=60),
])
```

---

## Extending the API

cysox supports multiple approaches for creating custom effects, from simple Python to high-performance C.

### Approach 1: CompositeEffect (Easiest)

Combine existing effects into reusable presets:

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


class WarmReverb(CompositeEffect):
    """Custom reverb with warmth."""

    def __init__(self, decay: float = 60, warmth: float = 2000):
        self.decay = decay
        self.warmth = warmth

    @property
    def effects(self):
        return [
            HighPass(frequency=80),
            LowPass(frequency=self.warmth),
            Reverb(reverberance=self.decay),
            Volume(db=-2),
        ]


# Usage
cysox.convert('in.wav', 'out.wav', effects=[TelephoneEffect()])
cysox.convert('in.wav', 'out.wav', effects=[WarmReverb(decay=70)])
```

### Approach 2: PythonEffect (NumPy-based)

For custom DSP that sox doesn't support natively:

```python
from cysox.fx import PythonEffect
import numpy as np

class BitCrusher(PythonEffect):
    """Reduce bit depth for lo-fi effect."""

    def __init__(self, bits: int = 8):
        self.bits = bits

    def process(self, samples: np.ndarray, sample_rate: int, channels: int) -> np.ndarray:
        levels = 2 ** self.bits
        return np.round(samples * levels) / levels


class RingModulator(PythonEffect):
    """Ring modulation effect."""

    def __init__(self, frequency: float = 440):
        self.frequency = frequency

    def process(self, samples: np.ndarray, sample_rate: int, channels: int) -> np.ndarray:
        t = np.arange(len(samples)) / sample_rate
        modulator = np.sin(2 * np.pi * self.frequency * t)
        if channels > 1:
            modulator = modulator[:, np.newaxis]
        return samples * modulator


# Usage (Note: PythonEffect not yet integrated into convert())
```

**Note:** PythonEffect requires numpy and processes samples outside the sox pipeline. Currently requires manual integration with `stream()`.

### Approach 3: Wrapping Sox Effects

Create a typed wrapper for any sox effect:

```python
from cysox.fx import Effect
from typing import List

class Phaser(Effect):
    """Phaser effect wrapper."""

    def __init__(
        self,
        gain_in: float = 0.4,
        gain_out: float = 0.74,
        delay: float = 3,
        decay: float = 0.4,
        speed: float = 0.5,
    ):
        self.gain_in = gain_in
        self.gain_out = gain_out
        self.delay = delay
        self.decay = decay
        self.speed = speed

    @property
    def name(self) -> str:
        return 'phaser'

    def to_args(self) -> List[str]:
        return [
            str(self.gain_in),
            str(self.gain_out),
            str(self.delay),
            str(self.decay),
            str(self.speed),
        ]

# Usage
cysox.convert('in.wav', 'out.wav', effects=[Phaser(speed=0.8)])
```

### Approach 4: Pure C Extension (Best Performance)

For production DSP or real-time processing, write the effect in C:

```c
// my_effect.c
#include <sox.h>

typedef struct {
    double gain;
} my_effect_priv_t;

static int my_effect_getopts(sox_effect_t *effp, int argc, char *argv[]) {
    my_effect_priv_t *priv = (my_effect_priv_t *)effp->priv;
    priv->gain = argc > 0 ? atof(argv[0]) : 1.0;
    return SOX_SUCCESS;
}

static int my_effect_flow(sox_effect_t *effp,
                          const sox_sample_t *ibuf, sox_sample_t *obuf,
                          size_t *isamp, size_t *osamp) {
    my_effect_priv_t *priv = (my_effect_priv_t *)effp->priv;
    for (size_t i = 0; i < *isamp; i++) {
        obuf[i] = (sox_sample_t)(ibuf[i] * priv->gain);
    }
    *osamp = *isamp;
    return SOX_SUCCESS;
}

sox_effect_handler_t const *my_effect_handler(void) {
    static sox_effect_handler_t handler = {
        "my_effect",
        "gain",
        SOX_EFF_MCHAN | SOX_EFF_GAIN,
        my_effect_getopts,
        NULL,  // start
        my_effect_flow,
        NULL,  // drain
        NULL,  // stop
        NULL,  // kill
        sizeof(my_effect_priv_t)
    };
    return &handler;
}
```

Then wrap in Python:

```python
class MyEffect(Effect):
    """Wrapper for custom C effect."""

    def __init__(self, gain: float = 1.0):
        self.gain = gain

    @property
    def name(self) -> str:
        return 'my_effect'  # Must be registered with sox

    def to_args(self) -> list[str]:
        return [str(self.gain)]
```

### Approach 5: Cython with nogil (High Performance)

Write effect callbacks in Cython for near-C performance:

```cython
# custom_effect.pyx
from libc.stddef cimport size_t

cdef struct custom_priv_t:
    double multiplier

cdef int custom_flow(sox_effect_t *effp,
                     const sox_sample_t *ibuf, sox_sample_t *obuf,
                     size_t *isamp, size_t *osamp) noexcept nogil:
    """Process samples - runs without GIL for performance."""
    cdef custom_priv_t *priv = <custom_priv_t *>effp.priv
    cdef size_t i
    for i in range(isamp[0]):
        obuf[i] = <sox_sample_t>(ibuf[i] * priv.multiplier)
    osamp[0] = isamp[0]
    return SOX_SUCCESS
```

### Performance Comparison

| Approach | Performance | Complexity | Use Case |
|----------|-------------|------------|----------|
| CompositeEffect | Native sox | Trivial | Combining existing effects |
| Wrapping sox effects | Native sox | Low | Typed API for any sox effect |
| PythonEffect (NumPy) | Slow | Low | Experiments, ML integration |
| Cython `nogil` | Excellent | Medium | Custom DSP, performance-critical |
| Pure C | Best | High | Production, real-time |

### Recommendations

1. **Most users**: Use built-in `fx.*` classes or `CompositeEffect`
2. **Custom presets**: Use `CompositeEffect` to combine effects
3. **Missing sox effects**: Create a simple `Effect` subclass wrapper
4. **Custom DSP prototype**: Use `PythonEffect` with NumPy
5. **Production/real-time**: Write in C, wrap with Python class

---

## How Effects Work Internally

Effect classes are pure Python that convert named parameters to sox effect arguments:

```python
class Volume(Effect):
    def __init__(self, db: float = 0):
        self.db = db

    @property
    def name(self) -> str:
        return 'vol'

    def to_args(self) -> list[str]:
        return [f'{self.db}dB']
```

The `convert()` function bridges high-level to low-level:

```python
def convert(input_path, output_path, effects=None, **options):
    _ensure_init()

    input_fmt = sox.Format(input_path)
    output_fmt = sox.Format(output_path, signal=input_fmt.signal, mode='w')

    chain = sox.EffectsChain(input_fmt.encoding, output_fmt.encoding)

    # Add input effect
    e = sox.Effect(sox.find_effect('input'))
    e.set_options([input_fmt])
    chain.add_effect(e, input_fmt.signal, input_fmt.signal)

    # Add user effects
    if effects:
        for effect in effects:
            handler = sox.find_effect(effect.name)
            e = sox.Effect(handler)
            e.set_options(effect.to_args())
            chain.add_effect(e, input_fmt.signal, input_fmt.signal)

    # Add output effect
    e = sox.Effect(sox.find_effect('output'))
    e.set_options([output_fmt])
    chain.add_effect(e, input_fmt.signal, input_fmt.signal)

    chain.flow_effects()
    input_fmt.close()
    output_fmt.close()
```

---

## libsox Effect Handler Reference

Sox effects are defined by `sox_effect_handler_t`:

```c
struct sox_effect_handler_t {
    const char *name;
    const char *usage;
    unsigned int flags;

    // Lifecycle function pointers
    int (*getopts)(sox_effect_t *effp, int argc, char *argv[]);  // Parse options
    int (*start)(sox_effect_t *effp);                            // Initialize
    int (*flow)(sox_effect_t *effp, sox_sample_t *ibuf,          // Process samples
                sox_sample_t *obuf, size_t *isamp, size_t *osamp);
    int (*drain)(sox_effect_t *effp, sox_sample_t *obuf,         // Flush remaining
                 size_t *osamp);
    int (*stop)(sox_effect_t *effp);                             // Cleanup
    int (*kill)(sox_effect_t *effp);                             // Free resources

    size_t priv_size;  // Size of private data struct
};
```

Common effect flags:

- `SOX_EFF_MCHAN` - Effect handles multiple channels
- `SOX_EFF_GAIN` - Effect may increase signal amplitude
- `SOX_EFF_RATE` - Effect may change sample rate
- `SOX_EFF_PREC` - Effect may change sample precision

---

## Design Principles

1. **Simple types** - Functions return paths (str) or dicts, not low-level objects
2. **Typed effects** - IDE autocomplete and validation via effect classes
3. **Time in seconds** - Not samples (unless explicitly needed)
4. **Sensible defaults** - Minimal required arguments
5. **Auto resource management** - No manual init/quit or cleanup required
6. **Clear errors** - Exceptions with context, no silent failures

---

## Migration from Low-Level API

Old pattern:

```python
import cysox as sox
sox.init()
# ... operations ...
sox.quit()
```

New pattern:

```python
import cysox  # High-level API, auto-init

# Or for low-level access:
from cysox import sox
sox.init()
# ...
sox.quit()
```
