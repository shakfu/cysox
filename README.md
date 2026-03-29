# cysox

[![PyPI](https://img.shields.io/pypi/v/cysox)](https://pypi.org/project/cysox/)
[![Python](https://img.shields.io/pypi/pyversions/cysox)](https://pypi.org/project/cysox/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Docs](https://img.shields.io/badge/docs-online-blue)](https://shakfu.github.io/cysox/)

A Pythonic audio processing library which uses cython to wrap [libsox](https://github.com/chirlu/sox).

**[Documentation](https://shakfu.github.io/cysox/)** | **[API Reference](https://shakfu.github.io/cysox/api/effects/)** | **[Examples](https://shakfu.github.io/cysox/examples/)**

## Features

- **Simple API**: Convert, analyze, and play audio with one-liners
- **Typed Effects**: 27 base effect classes with IDE autocomplete and validation
- **53 Effect Presets**: Ready-to-use composite effects for voice, lo-fi, drums, mastering, and more
- **Sample Processing**: Auto-trim silence, split recordings into one-shots, generate chromatic pitch scales, batch process directories
- **Drum Loop Tools**: Slice loops by BPM, create stutter effects, apply beat-synced processing
- **High Performance**: Direct C bindings through Cython, KissFFT-accelerated onset detection
- **Zero Configuration**: Auto-initialization, no manual setup required
- **Cross-Platform**: macOS, Linux (Windows placeholder)

## Installation

Note that cysox only works on macOS and Linux.

```sh
pip install cysox
```

## Command Line Interface

```sh
# Show version
cysox --version

# Get audio file info
cysox info audio.wav

# Convert audio files
cysox convert input.wav output.mp3
cysox convert input.wav output.wav --rate 48000 --channels 1
cysox convert input.wav output.wav -p Telephone

# Play audio
cysox play audio.wav

# Concatenate files
cysox concat intro.wav main.wav outro.wav -o full.wav

# List available effect presets
cysox preset list
cysox preset list drums          # Filter by category

# Get preset info and parameters
cysox preset info Chipmunk

# Apply a preset to audio
cysox preset apply Telephone input.wav output.wav
cysox preset apply Chipmunk input.wav output.wav --intensity=2.0

# Slice audio into segments
cysox slice drums.wav output_dir/ -n 8
cysox slice drums.wav output_dir/ --bpm 120 --beats 1
cysox slice drums.wav output_dir/ -n 4 -p DrumPunch

# Slice at detected transients (automatic beat detection)
# -t threshold (e.g. 0.3), -s sensitivity (default 1.5), -m method (default hfc)
cysox slice drums.wav output_dir/ -t 0.3
cysox slice drums.wav output_dir/ -t 0.2 -s 1.2 -m flux

# Create stutter effects
cysox stutter drums.wav stutter.wav -d 0.125 -r 8
cysox stutter drums.wav stutter.wav -s 0.5 -d 0.25 -r 4 -p GatedReverb

# Trim silence from beginning and end of audio
cysox auto-trim raw.wav trimmed.wav
cysox auto-trim raw.wav trimmed.wav --thresh -36 --fadein 10 --fadeout 50
cysox auto-trim raw.wav trimmed.wav --speedup 2

# Split continuous recording into one-shots at silence gaps
cysox split recording.wav one_shots/
cysox split recording.wav one_shots/ --thresh -36 --min-silence 0.5

# Generate pitch-shifted copies (chromatic scale)
cysox pitch-scale sample.wav scale/                    # 12 semitones (1 octave)
cysox pitch-scale sample.wav scale/ --range 24 --offset -12

# Batch process all audio files in a directory
cysox batch raw_samples/ processed/ -p Normalize
cysox batch raw_samples/ processed/ --rate 44100 --channels 1 --format wav
cysox batch raw_samples/ processed/ --no-recursive -p DrumPunch
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

### `cysox.info(path) -> AudioInfo`

Get audio file metadata. Returns an `AudioInfo` object supporting both attribute
access and dict-style access:

```python
info = cysox.info('audio.wav')
print(info.duration)         # Attribute access
print(info['sample_rate'])   # Dict-style access (backwards compatible)
# Fields: path, format, duration, sample_rate, channels,
#         bits_per_sample, samples, encoding
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

The `cysox.fx` module provides 27 base effect classes and 53 composite presets:

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
fx.Silence(threshold=-48)          # Remove silence by amplitude
```

### Conversion

```python
fx.Rate(sample_rate=48000)         # Resample
fx.Channels(channels=1)            # Change channel count
fx.Remix(mix=["1,2"])              # Custom channel mixing
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

## Effect Presets

The library includes 54 ready-to-use composite effect presets organized by category:

### Voice Effects

```python
fx.Chipmunk(intensity=1.8)         # High-pitched voice
fx.DeepVoice(intensity=0.6)        # Low, slowed voice
fx.Robot(intensity=70)             # Metallic robotic voice
fx.HauntedVoice(pitch_shift=5)     # Spooky ghost effect
fx.VocalClarity(presence_boost=4)  # Enhanced vocal presence
fx.Whisper()                       # Intimate whisper effect
```

### Lo-Fi Effects

```python
fx.Telephone(sample_rate=8000)     # Classic telephone sound
fx.AMRadio()                       # AM radio broadcast
fx.Megaphone(volume_boost=6)       # Bullhorn effect
fx.Underwater(depth=500)           # Submerged/muffled sound
fx.VinylWarmth(bass_boost=3)       # Warm vinyl aesthetic
fx.LoFiHipHop(warmth=4)            # Lo-fi hip hop style
fx.Cassette()                      # Cassette tape degradation
```

### Spatial Effects

```python
fx.SmallRoom(wetness=30)           # Intimate room reverb
fx.LargeHall(size=100, decay=70)   # Concert hall ambience
fx.Cathedral()                     # Church reverb
fx.Bathroom()                      # Tiled room reverb
fx.Stadium()                       # Arena with echo
```

### Broadcast Effects

```python
fx.Podcast()                       # Voice cleanup + presence
fx.RadioDJ(presence=4)             # Punchy broadcast voice
fx.Voiceover()                     # Professional VO processing
fx.Intercom()                      # PA system effect
fx.WalkieTalkie()                  # Two-way radio
```

### Musical Effects

```python
fx.EightiesChorus(depth=4)         # Classic 80s chorus
fx.DreamyPad()                     # Ethereal ambient texture
fx.SlowedReverb(slow_factor=0.85)  # Slowed + reverb aesthetic
fx.SlapbackEcho(delay_ms=120)      # Rockabilly short delay
fx.DubDelay(tempo_ms=375)          # Rhythmic dub delays
fx.JetFlanger()                    # Extreme flanger sweep
fx.ShoegazeWash()                  # Heavy reverb/chorus wash
```

### Drum Loop Effects

```python
fx.HalfTime(preserve_pitch=True)   # Slow to half speed
fx.DoubleTime(preserve_pitch=True) # Speed up to double
fx.DrumPunch(punch=4, attack=3)    # Enhance punch and attack
fx.DrumCrisp(brightness=4)         # Crisp, bright drums
fx.DrumFat(fatness=5)              # Thick, heavy drums
fx.Breakbeat()                     # Classic breakbeat processing
fx.VintageBreak()                  # Lo-fi sampled break sound
fx.DrumRoom(room_size=40)          # Natural room ambience
fx.GatedReverb()                   # 80s gated reverb
fx.DrumSlice(start=0, duration=0.5)# Extract a segment
fx.ReverseCymbal(fade_duration=0.5)# Reverse riser effect
fx.LoopReady()                     # Prepare for seamless looping
```

### Mastering Effects

```python
fx.BroadcastLimiter(target_level=-1)  # Broadcast-ready limiting
fx.WarmMaster(warmth=1.5)             # Warm mastering preset
fx.BrightMaster(air=2)                # Bright/airy mastering
fx.LoudnessMaster(target_level=-0.3)  # Maximum loudness
```

### Cleanup Effects

```python
fx.RemoveRumble(cutoff=60)         # High-pass for rumble
fx.RemoveHiss(cutoff=12000)        # Low-pass for tape hiss
fx.RemoveHum(frequency=60)         # Notch filter for hum (50/60Hz)
fx.CleanVoice()                    # Basic voice cleanup
fx.TapeRestoration()               # Restore tape recordings
```

### Transition Effects

```python
fx.FadeInOut(fade_in_secs=0.3, fade_out_secs=0.3)
fx.CrossfadeReady(fade_duration=0.3)
```

### Chaining Presets

Presets can be combined with each other and base effects:

```python
cysox.convert('input.wav', 'output.wav', effects=[
    fx.RemoveRumble(),      # Cleanup first
    fx.VinylWarmth(),       # Apply lo-fi aesthetic
    fx.SmallRoom(),         # Add room ambience
    fx.WarmMaster(),        # Final mastering
])
```

## Drum Loop Slicing

cysox provides utilities for slicing drum loops and creating stutter effects.

### `cysox.slice_loop()` - Split Loops into Segments

Split an audio file into multiple segment files:

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
```

**Parameters:**

- `path`: Input audio file
- `output_dir`: Directory for slice files (created if needed)
- `slices`: Number of equal slices (default: 4)
- `bpm`: Calculate slice duration from BPM (overrides `slices`)
- `beats_per_slice`: Beats per slice when using BPM (default: 1)
- `beat_duration`: Explicit duration per slice in seconds
- `threshold`: Onset detection threshold 0.0-1.0 (enables automatic transient slicing)
- `sensitivity`: Onset detection sensitivity 1.0-3.0 (default: 1.5)
- `onset_method`: Detection method - 'hfc', 'flux', 'energy', 'complex', or 'superflux'
- `output_format`: Output format (default: "wav")
- `effects`: Effects to apply to each slice

**Returns:** List of created file paths

### Automatic Transient Slicing

Slice loops automatically at detected transients (drum hits, etc.):

```python
# Slice at detected onsets with default sensitivity
slices = cysox.slice_loop('drums.wav', 'output_dir/', threshold=0.3)

# More sensitive detection (catches subtle hits)
slices = cysox.slice_loop('drums.wav', 'output_dir/',
    threshold=0.2,
    sensitivity=1.2
)

# Use different detection method
slices = cysox.slice_loop('drums.wav', 'output_dir/',
    threshold=0.3,
    onset_method='flux'  # Good for tonal changes
)
```

### `cysox.onset` - Direct Onset Detection

For more control, use the onset detection module directly:

```python
from cysox import onset

# Detect onsets in a file
onsets = onset.detect('drums.wav', threshold=0.3)
print(f"Found {len(onsets)} transients")
for t in onsets:
    print(f"  {t:.3f}s")

# With custom parameters
onsets = onset.detect('drums.wav',
    threshold=0.3,      # Detection threshold (0.0-1.0)
    sensitivity=1.5,    # Peak picking sensitivity (1.0-3.0)
    min_spacing=0.05,   # Min time between onsets (seconds)
    method='hfc'        # 'hfc', 'flux', 'energy', 'complex', or 'superflux'
)
```

**Detection Methods:**

- **`hfc`** (default) - High-Frequency Content
  - Weights frequency bins by their index, emphasizing high frequencies
  - High frequencies are prominent in transient attacks (the "click" of a drum hit)
  - Best for: drums, percussion, plucked instruments
  - Fast and reliable for most percussive material

- **`flux`** - Spectral Flux
  - Measures the change in spectral energy between consecutive frames
  - Detects when the frequency content changes significantly
  - Best for: mixed material, melodic instruments, detecting note changes
  - Good all-around choice when HFC misses softer onsets

- **`energy`** - Energy-based
  - Simply measures the RMS energy (loudness) of each frame
  - Fastest method, minimal computation
  - Best for: very clean recordings, isolated drums, quick processing
  - May miss onsets that are spectrally distinct but similar in volume

- **`complex`** - Complex Domain
  - Analyzes both magnitude AND phase of the spectrum
  - Detects deviations from expected phase trajectories
  - Best for: maximum accuracy, subtle onsets, research applications
  - Slowest method but catches onsets other methods miss

- **`superflux`** - Superflux (Boeck & Widmer, DAFx 2013)
  - Mel-scaled spectral flux with vibrato suppression
  - Maximum filter along frequency axis to reject false onsets from frequency modulation
  - Backtracking from peaks to nearest local minimum for precise transient placement
  - Best for: polyphonic material, vibrato-heavy sources, maximum precision

**Understanding threshold vs sensitivity:**

`threshold` (0.0-1.0) and `sensitivity` (1.0-3.0) control different stages:

- **threshold** - Global minimum floor
  - Sets the absolute minimum level a peak must reach
  - Applied to the normalized detection function (0-1 scale)
  - Lower values = more sensitive, catches quieter transients
  - `threshold=0.3` means peaks must reach at least 30% of max energy
  - Think of it as: "ignore everything below this level"

- **sensitivity** - Adaptive peak picking strictness
  - Controls how much a peak must exceed the *local average*
  - Uses a moving median filter to compute the local baseline
  - Higher values = stricter, only picks prominent peaks
  - `sensitivity=1.5` means a peak must be 1.5x the local median
  - Think of it as: "how much must a peak stand out from neighbors"

**Typical combinations:**

- Drums with clear hits: `threshold=0.3, sensitivity=1.5` (defaults)
- Subtle transients: `threshold=0.2, sensitivity=1.2`
- Only loud hits: `threshold=0.5, sensitivity=2.0`

### `cysox.stutter()` - Create Stutter Effects

Extract a segment and repeat it:

```python
# Basic stutter: 8x repeat of first 1/8 note at 120 BPM
cysox.stutter('drums.wav', 'stutter.wav',
    segment_duration=0.125,  # 1/8 note at 120 BPM
    repeats=8
)

# Stutter from a specific position (e.g., the snare hit)
cysox.stutter('drums.wav', 'snare_stutter.wav',
    segment_start=0.5,       # Start at 0.5 seconds
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

**Parameters:**

- `path`: Input audio file
- `output_path`: Output file path
- `segment_start`: Start position in seconds (default: 0)
- `segment_duration`: Length of segment in seconds (default: 0.125)
- `repeats`: Total times segment plays (default: 8)
- `effects`: Effects to apply after stuttering

### Practical Examples

#### Chop an Amen Break

```python
import cysox
from cysox import fx

# Get loop info
info = cysox.info('amen.wav')
print(f"Duration: {info['duration']:.3f}s")

# Assuming 2-bar loop at 175 BPM
bpm = 175

# Slice into individual beats
slices = cysox.slice_loop('amen.wav', 'amen_beats/', bpm=bpm)
print(f"Created {len(slices)} beat slices")

# Slice into 16th notes with breakbeat processing
slices = cysox.slice_loop('amen.wav', 'amen_16ths/',
    slices=16,
    effects=[fx.Breakbeat()]
)

# Create kick stutter fill
cysox.stutter('amen.wav', 'kick_fill.wav',
    segment_start=0,
    segment_duration=info['duration'] / 16,  # First 16th note
    repeats=16
)
```

#### Process Drum Loops

```python
# Half-time for slow, heavy feel
cysox.convert('drums.wav', 'halftime.wav', effects=[fx.HalfTime()])

# Lo-fi vintage break sound
cysox.convert('drums.wav', 'vintage.wav', effects=[
    fx.VintageBreak(),
    fx.DrumRoom(wetness=20)
])

# 80s gated reverb snare
cysox.convert('drums.wav', 'gated.wav', effects=[fx.GatedReverb()])

# Full processing chain
cysox.convert('drums.wav', 'processed.wav', effects=[
    fx.RemoveRumble(cutoff=40),
    fx.DrumPunch(punch=5, attack=4),
    fx.DrumRoom(room_size=30, wetness=20),
    fx.BroadcastLimiter(),
])
```

## Sample Processing

cysox includes sample processing utilities ported from
[AudioHit](https://github.com/icaroferre/AudioHit) for preparing audio samples
for software and hardware samplers.

### `cysox.auto_trim()` - Trim Silence

Detect and remove silence from the beginning and end of audio based on
amplitude threshold:

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

**Parameters:**

- `path`: Input audio file
- `output_path`: Output audio file
- `threshold_db`: Amplitude threshold in dB (default: -48dB)
- `min_silence`: Minimum non-silence duration in seconds (default: 0.1)
- `fade_in`: Fade-in duration in milliseconds (default: 0)
- `fade_out`: Fade-out duration in milliseconds (default: 0)
- `speed_factor`: Playback speed multiplier (default: None)
- `effects`: Additional effects to apply after trimming

### `cysox.split_by_silence()` - Split at Silence Gaps

Split a continuous recording into separate one-shot samples at silence
boundaries:

```python
# Split at default threshold
segments = cysox.split_by_silence('recording.wav', 'one_shots/')

# Custom detection parameters
segments = cysox.split_by_silence('recording.wav', 'one_shots/',
    threshold_db=-36,     # Less sensitive
    min_silence=0.5,      # Require 500ms of silence to split
    min_segment=0.25,     # Discard segments shorter than 250ms
)

# With fades and effects on each segment
segments = cysox.split_by_silence('recording.wav', 'one_shots/',
    fade_in=5, fade_out=20,
    effects=[fx.Normalize()],
)
```

**Parameters:**

- `path`: Input audio file
- `output_dir`: Directory for segment files (created if needed)
- `threshold_db`: Amplitude threshold in dB (default: -48dB)
- `min_silence`: Minimum silence duration to trigger split, in seconds (default: 0.25)
- `min_segment`: Minimum segment duration, in seconds (default: 0.25)
- `fade_in`: Fade-in per segment in milliseconds (default: 0)
- `fade_out`: Fade-out per segment in milliseconds (default: 0)
- `speed_factor`: Playback speed multiplier (default: None)
- `output_format`: Output format (default: "wav")
- `effects`: Effects to apply to each segment

**Returns:** List of created file paths

### `cysox.pitch_scale()` - Generate Chromatic Pitch Variants

Create multiple pitch-shifted copies of a sample at semitone intervals,
useful for building playable melodic sample libraries:

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

**Parameters:**

- `path`: Input audio file
- `output_dir`: Directory for pitch-shifted files (created if needed)
- `semitones`: Number of copies to generate (default: 12)
- `offset`: Starting semitone offset (default: 0)
- `output_format`: Output format (default: "wav")
- `effects`: Effects to apply to each copy after pitch shifting

**Returns:** List of created file paths

### `cysox.batch()` - Batch Process Directories

Process all audio files in a directory tree:

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

**Parameters:**

- `input_dir`: Directory containing audio files
- `output_dir`: Directory for processed files (created if needed)
- `effects`: Effects to apply to each file
- `sample_rate`: Target sample rate in Hz
- `channels`: Target number of channels
- `bits`: Target bits per sample
- `recursive`: Process subdirectories (default: True)
- `output_format`: Output format (None keeps original)
- `on_file`: Callback called after each file `(input_path, output_path)`

**Returns:** List of processed output file paths

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
sudo apt-get install libsox-dev libsndfile1-dev pkg-config
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
pip install mkdocs-material
make docs          # Build static site
make docs-serve    # Live preview at http://localhost:8000
```

## License

MIT

KissFFT (vendored in `vendor/kissfft/`) is BSD-3-Clause licensed. See `vendor/kissfft/COPYING`.
