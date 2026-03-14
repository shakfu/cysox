# Onset Detection

The `cysox.onset` module provides C-optimized transient detection for locating note onsets, drum hits, and other audio events. It is implemented in Cython with KissFFT acceleration.

## Quick Start

```python
from cysox import onset

# Detect onsets in a file
times = onset.detect('drums.wav')
print(f"Found {len(times)} onsets: {times}")

# Use with slice_loop for automatic beat slicing
import cysox
cysox.slice_loop('drums.wav', 'slices/', threshold=0.3)
```

## Functions

### `onset.detect()`

Detect onsets in an audio file. This is the main entry point -- it handles file reading internally.

```python
onset.detect(
    path,
    threshold=0.3,
    sensitivity=1.5,
    min_spacing=0.05,
    method="hfc",
    frame_size=1024,
    hop_size=256,
)
```

**Returns:** List of onset times in seconds.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `path` | str or Path | *required* | Path to audio file. |
| `threshold` | float | 0.3 | Detection threshold, 0.0-1.0. Lower = more sensitive. |
| `sensitivity` | float | 1.5 | Peak picking strictness, 1.0-3.0. Higher = fewer detections. |
| `min_spacing` | float | 0.05 | Minimum time between onsets in seconds (prevents double triggers). |
| `method` | str | `"hfc"` | Detection algorithm (see [Methods](#detection-methods)). |
| `frame_size` | int | 1024 | FFT analysis frame size in samples. |
| `hop_size` | int | 256 | Hop size between analysis frames in samples. |

**Superflux-only parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `n_mels` | int | 138 | Number of mel frequency bands. |
| `fmin` | float | 27.5 | Minimum frequency in Hz. |
| `fmax` | float | 16000.0 | Maximum frequency in Hz. |
| `max_size` | int | 3 | Max-filter width along frequency axis. |
| `lag` | int | 2 | Frame lag for temporal reference comparison. |

### `onset.detect_onsets()`

Low-level onset detection on raw sample data. Use this when you already have samples in memory.

```python
onset.detect_onsets(
    samples,
    sample_rate,
    channels,
    threshold=0.3,
    sensitivity=1.5,
    min_spacing=0.05,
    method="hfc",
    frame_size=1024,
    hop_size=256,
)
```

**Returns:** List of onset times in seconds.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `samples` | list[int] | *required* | Audio samples as int32 values (sox_sample_t format). Interleaved for multi-channel: `[L, R, L, R, ...]`. |
| `sample_rate` | int | *required* | Sample rate in Hz. |
| `channels` | int | *required* | Number of audio channels. |

All other parameters are identical to `detect()`.

## Detection Methods

| Method | Best for | Description |
|--------|----------|-------------|
| `"hfc"` | Percussive transients (drums, plucks) | High-Frequency Content: weights spectral energy by frequency, emphasizing sharp attacks. Fast and accurate for rhythmic material. |
| `"flux"` | General onsets (tonal + percussive) | Spectral Flux: measures the rate of spectral change between frames. Good all-around choice. |
| `"energy"` | Loud/quiet transitions | Energy-based: detects changes in overall signal energy. Simplest and fastest, but less precise. |
| `"complex"` | Tonal onsets (pitch changes) | Complex domain: uses both phase and magnitude analysis. Most accurate for pitched instruments, but slower. |
| `"superflux"` | Vibrato-heavy material | Superflux (Boeck & Widmer, DAFx 2013): mel-scaled spectral analysis with max-filter for vibrato suppression. Best when other methods produce false positives from vibrato or tremolo. |

## Tuning Parameters

### Threshold

The `threshold` parameter (0.0-1.0) is the primary sensitivity control. It is normalized relative to the maximum onset detection function value, so the same threshold works across different recordings.

- **0.1-0.2**: Very sensitive, catches quiet onsets. May produce false positives.
- **0.3**: Good default for most drum loops and percussive material.
- **0.5-0.7**: Catches only strong, unambiguous onsets.
- **0.8+**: Only the loudest hits.

### Sensitivity

The `sensitivity` parameter (1.0-3.0) controls peak picking strictness. An onset is only reported if it exceeds `sensitivity` times the local mean of the detection function.

- **1.0**: Permissive -- most peaks are reported.
- **1.5**: Default -- good balance.
- **2.0-3.0**: Strict -- only peaks that clearly stand out.

### min_spacing

Minimum time gap (in seconds) between reported onsets. Prevents double-triggering on a single event. The default of 0.05s (50ms) works for most material. Increase to 0.1s+ for slower tempos.

## Examples

### Detect drum hits

```python
from cysox import onset

times = onset.detect('drums.wav', threshold=0.3, method='hfc')
for i, t in enumerate(times):
    print(f"Hit {i+1}: {t:.3f}s")
```

### Onset-based slicing

```python
import cysox

# Slice at every detected transient
slices = cysox.slice_loop(
    'break.wav',
    'slices/',
    threshold=0.3,
    onset_method='hfc',
    sensitivity=1.5,
)
print(f"Created {len(slices)} slices")
```

### Compare detection methods

```python
from cysox import onset

for method in ['hfc', 'flux', 'energy', 'complex', 'superflux']:
    times = onset.detect('audio.wav', method=method, threshold=0.3)
    print(f"{method:10s}: {len(times)} onsets")
```

### Low-level detection on raw samples

```python
from cysox import sox, onset

sox.init()
with sox.Format('audio.wav') as f:
    samples = f.read(f.signal.length)
    times = onset.detect_onsets(
        samples,
        sample_rate=int(f.signal.rate),
        channels=f.signal.channels,
        threshold=0.25,
    )
sox.quit()
```
