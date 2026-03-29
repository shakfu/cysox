# Sample Processing

cysox includes sample processing utilities for preparing audio samples,
slicing drum loops, and batch processing directories. These are inspired
by [AudioHit](https://github.com/icaroferre/AudioHit).

## Drum Loop Slicing

### `cysox.slice_loop()`

Split an audio file into multiple segment files.

```python
import cysox
from cysox import fx

# Slice into equal parts
slices = cysox.slice_loop('drums.wav', 'output_dir/', slices=8)
# Creates: output_dir/drums_slice_000.wav through drums_slice_007.wav

# Slice by BPM (one beat per slice)
slices = cysox.slice_loop('drums.wav', 'output_dir/', bpm=120, beats_per_slice=1)

# Slice with effects applied to each segment
slices = cysox.slice_loop('drums.wav', 'output_dir/',
    slices=8,
    effects=[fx.DrumPunch()]
)

# Slice at detected transients (automatic beat detection)
slices = cysox.slice_loop('drums.wav', 'output_dir/', threshold=0.3)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `path` | str or Path | *required* | Input audio file. |
| `output_dir` | str or Path | *required* | Directory for slice files (created if needed). |
| `slices` | int | 4 | Number of equal slices. |
| `bpm` | float | None | Calculate slice duration from BPM (overrides `slices`). |
| `beats_per_slice` | int | 1 | Beats per slice when using BPM. |
| `beat_duration` | float | None | Explicit duration per slice in seconds. |
| `threshold` | float | None | Onset detection threshold 0.0-1.0 (enables automatic transient slicing). |
| `sensitivity` | float | 1.5 | Onset detection sensitivity 1.0-3.0. |
| `onset_method` | str | `"hfc"` | Detection method: `hfc`, `flux`, `energy`, `complex`, or `superflux`. |
| `output_format` | str | `"wav"` | Output format. |
| `effects` | list | None | Effects to apply to each slice. |

**Returns:** List of created file paths.

### `cysox.stutter()`

Extract a segment and repeat it to create stutter effects.

```python
# Basic stutter: 8x repeat of first 125ms
cysox.stutter('drums.wav', 'stutter.wav',
    segment_duration=0.125,
    repeats=8
)

# Stutter from a specific position
cysox.stutter('drums.wav', 'snare_stutter.wav',
    segment_start=0.5,
    segment_duration=0.125,
    repeats=4
)

# Stutter with effects
cysox.stutter('drums.wav', 'stutter_punchy.wav',
    segment_duration=0.25,
    repeats=4,
    effects=[fx.DrumPunch(), fx.DrumRoom()]
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `path` | str or Path | *required* | Input audio file. |
| `output_path` | str or Path | *required* | Output file path. |
| `segment_start` | float | 0 | Start position in seconds. |
| `segment_duration` | float | 0.125 | Length of segment in seconds. |
| `repeats` | int | 8 | Total times segment plays. |
| `effects` | list | None | Effects to apply after stuttering. |

---

## Silence Trimming and Splitting

### `cysox.auto_trim()`

Detect and remove silence from the beginning and end of audio based on amplitude threshold.

```python
# Basic silence trimming
cysox.auto_trim('raw.wav', 'trimmed.wav')

# Custom threshold (less sensitive)
cysox.auto_trim('raw.wav', 'trimmed.wav', threshold_db=-36)

# With fade in/out (milliseconds)
cysox.auto_trim('raw.wav', 'trimmed.wav', fade_in=10, fade_out=50)

# Speed up after trimming
cysox.auto_trim('raw.wav', 'trimmed.wav', speed_factor=2.0)

# With additional effects
cysox.auto_trim('raw.wav', 'trimmed.wav', effects=[fx.Normalize()])
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `path` | str or Path | *required* | Input audio file. |
| `output_path` | str or Path | *required* | Output audio file. |
| `threshold_db` | float | -48 | Amplitude threshold in dB. |
| `min_silence` | float | 0.1 | Minimum non-silence duration in seconds. |
| `fade_in` | int | 0 | Fade-in duration in milliseconds. |
| `fade_out` | int | 0 | Fade-out duration in milliseconds. |
| `speed_factor` | float | None | Playback speed multiplier. |
| `effects` | list | None | Additional effects to apply after trimming. |

### `cysox.split_by_silence()`

Split a continuous recording into separate one-shot samples at silence boundaries.

```python
# Split at default threshold
segments = cysox.split_by_silence('recording.wav', 'one_shots/')

# Custom detection parameters
segments = cysox.split_by_silence('recording.wav', 'one_shots/',
    threshold_db=-36,
    min_silence=0.5,
    min_segment=0.25,
)

# With fades and effects on each segment
segments = cysox.split_by_silence('recording.wav', 'one_shots/',
    fade_in=5, fade_out=20,
    effects=[fx.Normalize()],
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `path` | str or Path | *required* | Input audio file. |
| `output_dir` | str or Path | *required* | Directory for segment files (created if needed). |
| `threshold_db` | float | -48 | Amplitude threshold in dB. |
| `min_silence` | float | 0.25 | Minimum silence duration to trigger split, in seconds. |
| `min_segment` | float | 0.25 | Minimum segment duration, in seconds. |
| `fade_in` | int | 0 | Fade-in per segment in milliseconds. |
| `fade_out` | int | 0 | Fade-out per segment in milliseconds. |
| `speed_factor` | float | None | Playback speed multiplier. |
| `output_format` | str | `"wav"` | Output format. |
| `effects` | list | None | Effects to apply to each segment. |

**Returns:** List of created file paths.

---

## Pitch and Batch Processing

### `cysox.pitch_scale()`

Create multiple pitch-shifted copies of a sample at semitone intervals,
useful for building playable melodic sample libraries.

```python
# Generate one octave (12 semitones) of chromatic variations
files = cysox.pitch_scale('c3_piano.wav', 'scale/')
# Creates: scale/c3_piano_pitch_+0.wav through scale/c3_piano_pitch_+11.wav

# Two octaves starting from one octave below
files = cysox.pitch_scale('sample.wav', 'scale/',
    semitones=24, offset=-12)

# With effects on each copy
files = cysox.pitch_scale('sample.wav', 'scale/',
    semitones=12, effects=[fx.Normalize()])
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `path` | str or Path | *required* | Input audio file. |
| `output_dir` | str or Path | *required* | Directory for pitch-shifted files (created if needed). |
| `semitones` | int | 12 | Number of copies to generate. |
| `offset` | int | 0 | Starting semitone offset. |
| `output_format` | str | `"wav"` | Output format. |
| `effects` | list | None | Effects to apply to each copy after pitch shifting. |

**Returns:** List of created file paths.

### `cysox.batch()`

Process all audio files in a directory tree.

```python
# Convert a folder to mono 22050Hz
processed = cysox.batch('samples/', 'processed/',
    sample_rate=22050, channels=1)

# Apply effects to all files
processed = cysox.batch('raw/', 'ready/',
    effects=[fx.Normalize(), fx.Fade(fade_in=0.01)])

# Convert format, non-recursive
processed = cysox.batch('input/', 'output/',
    output_format='flac', recursive=False)

# With progress callback
cysox.batch('raw/', 'done/',
    on_file=lambda i, o: print(f"  {i} -> {o}"))
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `input_dir` | str or Path | *required* | Directory containing audio files. |
| `output_dir` | str or Path | *required* | Directory for processed files (created if needed). |
| `effects` | list | None | Effects to apply to each file. |
| `sample_rate` | int | None | Target sample rate in Hz. |
| `channels` | int | None | Target number of channels. |
| `bits` | int | None | Target bits per sample. |
| `recursive` | bool | True | Process subdirectories. |
| `output_format` | str | None | Output format (None keeps original). |
| `on_file` | callable | None | Callback called after each file `(input_path, output_path)`. |

**Returns:** List of processed output file paths.

---

## Practical Examples

### Chop an Amen Break

```python
import cysox
from cysox import fx

info = cysox.info('amen.wav')
bpm = 175

# Slice into individual beats
slices = cysox.slice_loop('amen.wav', 'amen_beats/', bpm=bpm)

# Slice into 16th notes with breakbeat processing
slices = cysox.slice_loop('amen.wav', 'amen_16ths/',
    slices=16,
    effects=[fx.Breakbeat()]
)

# Create kick stutter fill
cysox.stutter('amen.wav', 'kick_fill.wav',
    segment_start=0,
    segment_duration=info.duration / 16,
    repeats=16
)
```

### Process a Sample Library

```python
import cysox
from cysox import fx

# Trim silence from all samples
import os
for f in os.listdir('raw_samples/'):
    if f.endswith('.wav'):
        cysox.auto_trim(
            f'raw_samples/{f}',
            f'trimmed/{f}',
            threshold_db=-40,
            fade_in=5,
            fade_out=20,
        )

# Batch normalize and convert
cysox.batch('trimmed/', 'final/',
    sample_rate=44100,
    channels=1,
    effects=[fx.Normalize()],
    output_format='wav',
)
```

### Build a Chromatic Sample Pack

```python
import cysox
from cysox import fx

# Start from a C3 piano sample, generate two octaves
files = cysox.pitch_scale('c3_piano.wav', 'piano_scale/',
    semitones=24,
    offset=-12,
    effects=[fx.Normalize(), fx.Fade(fade_out=0.5)],
)
print(f"Created {len(files)} pitch variants")
```
