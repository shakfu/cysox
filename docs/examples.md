# Examples

## High-Level API

### Convert with effects

```python
import cysox
from cysox import fx

# Simple format conversion
cysox.convert('recording.wav', 'recording.mp3')

# Convert with effects chain
cysox.convert('vocals.wav', 'processed.wav', effects=[
    fx.HighPass(frequency=80),       # Remove rumble
    fx.Bass(gain=3),                 # Warm up the low end
    fx.Reverb(reverberance=40),      # Add some space
    fx.Normalize(level=-1),          # Normalize to -1 dBFS
])

# Resample and change channels
cysox.convert('stereo_48k.wav', 'mono_22k.wav',
    sample_rate=22050,
    channels=1,
)
```

### Apply presets

```python
import cysox
from cysox import fx

# Apply a single preset
cysox.convert('voice.wav', 'telephone.wav', effects=[fx.Telephone()])

# Combine presets with individual effects
cysox.convert('drums.wav', 'processed.wav', effects=[
    fx.DrumPunch(),
    fx.SmallRoom(),
    fx.Normalize(),
])
```

### Get file info

```python
import cysox

info = cysox.info('audio.wav')
print(f"Format:      {info.format}")
print(f"Duration:    {info.duration:.2f}s")
print(f"Sample rate: {info.sample_rate} Hz")
print(f"Channels:    {info.channels}")
print(f"Bit depth:   {info.bits_per_sample}")
print(f"Encoding:    {info.encoding}")
```

### Stream large files

Process audio in chunks without loading the entire file into memory:

```python
import cysox

for chunk in cysox.stream('large_file.wav', chunk_size=8192):
    # chunk is a memoryview of int32 samples
    # Process, analyze, or forward to another system
    rms = sum(s * s for s in chunk) / len(chunk)
```

### Progress callbacks

Monitor progress and optionally cancel long operations:

```python
import cysox
from cysox import fx

def on_progress(progress):
    """Called with progress 0.0 to 1.0. Return False to cancel."""
    print(f"\rProcessing: {progress:.0%}", end="", flush=True)
    return True  # Continue

cysox.convert('long_file.wav', 'output.wav',
    effects=[fx.Reverb()],
    on_progress=on_progress,
)
print()  # Newline after progress
```

### Concatenate files

```python
import cysox

cysox.concat(
    ['intro.wav', 'verse.wav', 'chorus.wav', 'outro.wav'],
    'full_song.wav',
)
```

### Slice audio loops

```python
import cysox

# Slice into equal parts
slices = cysox.slice_loop('drums.wav', 'slices/', slices=8)

# Slice by BPM
slices = cysox.slice_loop('drums.wav', 'slices/', bpm=120, beats_per_slice=1)

# Slice at detected transients
slices = cysox.slice_loop('drums.wav', 'slices/',
    threshold=0.3,
    onset_method='hfc',
)
print(f"Created {len(slices)} slices")
```

### Create stutter effects

```python
import cysox
from cysox import fx

# Stutter the first 125ms, 8 times
cysox.stutter('drums.wav', 'stutter.wav',
    segment_start=0,
    segment_duration=0.125,
    repeats=8,
)

# Stutter with a preset applied after
cysox.stutter('drums.wav', 'stutter_reverb.wav',
    segment_start=0.5,
    segment_duration=0.1,
    repeats=16,
    effects=[fx.SmallRoom()],
)
```

### Onset detection

```python
from cysox import onset

# Detect transients in a drum loop
times = onset.detect('drums.wav', threshold=0.3)
for i, t in enumerate(times):
    print(f"Hit {i+1}: {t:.3f}s")

# Compare detection methods
for method in ['hfc', 'flux', 'energy', 'complex', 'superflux']:
    times = onset.detect('drums.wav', method=method, threshold=0.3)
    print(f"{method:10s}: {len(times)} onsets")
```

### Auto-trim silence

```python
import cysox
from cysox import fx

# Basic silence trimming
cysox.auto_trim('raw.wav', 'trimmed.wav')

# Custom threshold with fades
cysox.auto_trim('raw.wav', 'trimmed.wav',
    threshold_db=-36,
    fade_in=10,
    fade_out=50,
)

# Trim and speed up
cysox.auto_trim('raw.wav', 'trimmed.wav',
    speed_factor=2.0,
    effects=[fx.Normalize()],
)
```

### Split recording into one-shots

```python
import cysox
from cysox import fx

# Split at silence gaps
segments = cysox.split_by_silence('recording.wav', 'one_shots/')
print(f"Created {len(segments)} one-shots")

# Custom parameters for noisy recordings
segments = cysox.split_by_silence('recording.wav', 'one_shots/',
    threshold_db=-36,
    min_silence=0.5,
    min_segment=0.25,
    effects=[fx.Normalize()],
)
```

### Generate pitch-shifted chromatic scale

```python
import cysox
from cysox import fx

# One octave up from source
files = cysox.pitch_scale('c3_piano.wav', 'scale/')

# Two octaves centered on source
files = cysox.pitch_scale('sample.wav', 'scale/',
    semitones=24, offset=-12,
    effects=[fx.Normalize()],
)
```

### Batch process a directory

```python
import cysox
from cysox import fx

# Convert all files to mono 44.1kHz
processed = cysox.batch('raw_samples/', 'processed/',
    sample_rate=44100,
    channels=1,
    effects=[fx.Normalize()],
)
print(f"Processed {len(processed)} files")

# Convert format with progress
cysox.batch('input/', 'output/',
    output_format='flac',
    on_file=lambda i, o: print(f"  {i} -> {o}"),
)
```

---

## Low-Level API

The low-level API provides direct access to libsox for cases that need full control over the processing pipeline.

### Basic effects chain

```python
from cysox import sox

def apply_effects(input_path, output_path):
    sox.init()

    try:
        input_fmt = sox.Format(input_path)
        output_fmt = sox.Format(output_path, signal=input_fmt.signal, mode='w')

        chain = sox.EffectsChain(
            in_encoding=input_fmt.encoding,
            out_encoding=output_fmt.encoding
        )

        e = sox.Effect(sox.find_effect("input"))
        e.set_options([input_fmt])
        chain.add_effect(e, input_fmt.signal, input_fmt.signal)

        e = sox.Effect(sox.find_effect("vol"))
        e.set_options(["3dB"])
        chain.add_effect(e, input_fmt.signal, input_fmt.signal)

        e = sox.Effect(sox.find_effect("flanger"))
        e.set_options([])
        chain.add_effect(e, input_fmt.signal, input_fmt.signal)

        e = sox.Effect(sox.find_effect("output"))
        e.set_options([output_fmt])
        chain.add_effect(e, input_fmt.signal, input_fmt.signal)

        chain.flow_effects()
        input_fmt.close()
        output_fmt.close()

    finally:
        sox.quit()
```

### Zero-copy reading with buffer protocol

```python
import array
from cysox import sox

sox.init()

with sox.Format('input.wav') as f:
    # Option 1: Get a memoryview
    buf = f.read_buffer(1024)

    # Option 2: Read into a pre-allocated buffer (zero-copy)
    arr = array.array('i', [0] * 1024)
    n = f.read_into(arr)
    print(f"Read {n} samples into array")

sox.quit()
```

### NumPy integration

```python
import numpy as np
from cysox import sox

def read_as_numpy(input_path):
    sox.init()

    try:
        with sox.Format(input_path) as f:
            total_samples = f.signal.length
            buf = f.read_buffer(total_samples)
            samples = np.frombuffer(buf, dtype=np.int32)

            if f.signal.channels > 1:
                samples = samples.reshape(-1, f.signal.channels)

            return samples, f.signal.rate

    finally:
        sox.quit()

samples, rate = read_as_numpy("input.wav")
print(f"Shape: {samples.shape}, Rate: {rate} Hz")
```

### Sample rate conversion

```python
from cysox import sox

def resample(input_path, output_path, target_rate):
    sox.init()

    try:
        input_fmt = sox.Format(input_path)

        out_signal = sox.SignalInfo(
            rate=target_rate,
            channels=input_fmt.signal.channels,
            precision=input_fmt.signal.precision
        )

        output_fmt = sox.Format(output_path, signal=out_signal, mode='w')

        chain = sox.EffectsChain(
            in_encoding=input_fmt.encoding,
            out_encoding=output_fmt.encoding
        )

        e = sox.Effect(sox.find_effect("input"))
        e.set_options([input_fmt])
        chain.add_effect(e, input_fmt.signal, input_fmt.signal)

        e = sox.Effect(sox.find_effect("rate"))
        e.set_options(["-v", str(target_rate)])
        chain.add_effect(e, input_fmt.signal, out_signal)

        e = sox.Effect(sox.find_effect("output"))
        e.set_options([output_fmt])
        chain.add_effect(e, out_signal, out_signal)

        chain.flow_effects()
        input_fmt.close()
        output_fmt.close()

    finally:
        sox.quit()
```

### Progress callbacks (low-level)

```python
from cysox import sox

def progress_callback(all_done, user_data):
    if all_done:
        print("Processing complete!")
    else:
        user_data['count'] += 1
        if user_data['count'] % 100 == 0:
            print(f"Processing... ({user_data['count']} buffers)")
    return True  # Continue processing

# ... set up chain ...

chain.flow_effects(
    callback=progress_callback,
    client_data={'count': 0}
)
```
