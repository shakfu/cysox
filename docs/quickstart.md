# Quick Start Guide

This guide covers the basic usage of cysox for common audio processing tasks.

## High-Level API (Recommended)

The high-level API handles initialization automatically:

```python
import cysox
from cysox import fx

# Get file info
info = cysox.info('audio.wav')
print(f"Duration: {info.duration:.2f}s")

# Convert with effects
cysox.convert('input.wav', 'output.wav', effects=[
    fx.Volume(db=3),
    fx.Reverb(),
])

# Play audio
cysox.play('audio.wav')

# Stream samples
for chunk in cysox.stream('large.wav'):
    process(chunk)
```

## Low-Level API

For advanced use cases, access the full libsox bindings directly:

### Reading Audio Files

```python
from cysox import sox

sox.init()

with sox.Format('input.wav') as f:
    print(f"Filename: {f.filename}")
    print(f"Format: {f.filetype}")
    print(f"Sample rate: {f.signal.rate} Hz")
    print(f"Channels: {f.signal.channels}")
    print(f"Precision: {f.signal.precision} bits")
    print(f"Total samples: {f.signal.length}")

    samples = f.read(1024)
    print(f"Read {len(samples)} samples")

sox.quit()
```

### Zero-Copy Reading with Buffer Protocol

For better performance with large files, use the buffer protocol:

```python
import array
from cysox import sox

sox.init()

with sox.Format('input.wav') as f:
    # Option 1: Get a memoryview
    buf = f.read_buffer(1024)

    # Option 2: Read into a pre-allocated buffer
    arr = array.array('i', [0] * 1024)
    n = f.read_into(arr)
    print(f"Read {n} samples into array")

sox.quit()
```

### Writing Audio Files

```python
from cysox import sox

sox.init()

signal = sox.SignalInfo(
    rate=44100,      # 44.1 kHz
    channels=2,      # Stereo
    precision=16     # 16-bit
)

with sox.Format('output.wav', signal=signal, mode='w') as f:
    samples = [100, -100, 200, -200] * 1000
    f.write(samples)

sox.quit()
```

### Applying Effects

```python
from cysox import sox

sox.init()

input_fmt = sox.Format('input.wav')
output_fmt = sox.Format('output.wav', signal=input_fmt.signal, mode='w')

chain = sox.EffectsChain(
    in_encoding=input_fmt.encoding,
    out_encoding=output_fmt.encoding
)

# Add input effect (required first)
e = sox.Effect(sox.find_effect("input"))
e.set_options([input_fmt])
chain.add_effect(e, input_fmt.signal, input_fmt.signal)

# Add volume effect (+3dB)
e = sox.Effect(sox.find_effect("vol"))
e.set_options(["3dB"])
chain.add_effect(e, input_fmt.signal, input_fmt.signal)

# Add output effect (required last)
e = sox.Effect(sox.find_effect("output"))
e.set_options([output_fmt])
chain.add_effect(e, input_fmt.signal, input_fmt.signal)

chain.flow_effects()

input_fmt.close()
output_fmt.close()
sox.quit()
```

### Progress Callbacks

Monitor processing progress with callbacks:

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

sox.init()

# ... set up chain ...

chain.flow_effects(
    callback=progress_callback,
    client_data={'count': 0}
)

sox.quit()
```

## Error Handling

cysox uses a custom exception hierarchy:

```python
from cysox import sox

sox.init()

try:
    f = sox.Format('nonexistent.wav')
except sox.SoxFormatError as e:
    print(f"Format error: {e}")
except sox.SoxError as e:
    print(f"General error: {e}")

sox.quit()
```

Available exceptions:

- `SoxError` - Base exception for all cysox errors
- `SoxInitError` - Initialization failures
- `SoxFormatError` - File format errors
- `SoxEffectError` - Effect processing errors
- `SoxIOError` - I/O operation errors
- `SoxMemoryError` - Memory allocation errors
