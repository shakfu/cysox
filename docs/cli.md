# Command Line Interface

cysox includes a CLI for common audio tasks. It is installed automatically with the package.

```text
cysox [command] [options]
```

## Global Options

| Option | Description |
|--------|-------------|
| `--version`, `-V` | Show cysox and libsox versions. |

## Commands

### info

Display audio file metadata.

```text
cysox info <file>
```

**Example:**

```text
$ cysox info drums.wav
File: drums.wav
Format: wav
Duration: 2.00s
Sample rate: 44100 Hz
Channels: 2
Bits per sample: 16
Encoding: Signed Integer PCM
```

### convert

Convert an audio file with optional format changes and effects.

```text
cysox convert <input> <output> [options]
```

| Option | Description |
|--------|-------------|
| `-r`, `--rate` | Target sample rate in Hz. |
| `-c`, `--channels` | Target number of channels. |
| `-b`, `--bits` | Target bits per sample. |
| `-p`, `--preset` | Apply a preset effect (see [preset list](#preset-list)). |

**Examples:**

```bash
# Convert WAV to MP3
cysox convert input.wav output.mp3

# Downsample to 22050 Hz mono
cysox convert input.wav output.wav -r 22050 -c 1

# Convert with a preset effect
cysox convert vocals.wav processed.wav -p Telephone
```

### play

Play an audio file to the default audio device.

```text
cysox play <file>
```

### concat

Concatenate multiple audio files into one. All input files must have matching sample rate, channels, and bit depth.

```text
cysox concat <file1> <file2> [file3 ...] -o <output>
```

**Example:**

```bash
cysox concat intro.wav verse.wav chorus.wav -o song.wav
```

!!! note
    If files have mismatched formats, convert them first with `cysox convert`.

### slice

Slice an audio file into segments. Supports three slicing modes: by count, by BPM, or by onset detection.

```text
cysox slice <input> <output_dir> [options]
```

| Option | Description |
|--------|-------------|
| `-n`, `--slices` | Number of equal slices (default: 4). |
| `--bpm` | Slice by BPM instead of count. |
| `--beats` | Beats per slice when using `--bpm` (default: 1). |
| `-t`, `--threshold` | Onset detection threshold 0.0-1.0 (enables transient-based slicing). |
| `-s`, `--sensitivity` | Onset detection sensitivity 1.0-3.0 (default: 1.5). |
| `-m`, `--method` | Onset detection method: `hfc`, `flux`, `energy`, `complex` (default: `hfc`). |
| `--min-spacing` | Minimum time between onsets in seconds (default: 0.05). |
| `-p`, `--preset` | Apply a preset to each slice. |

**Examples:**

```bash
# Slice into 8 equal parts
cysox slice drums.wav slices/ -n 8

# Slice by BPM (one slice per beat)
cysox slice drums.wav slices/ --bpm 120

# Slice at detected transients
cysox slice drums.wav slices/ -t 0.3

# Slice at transients with vintage processing
cysox slice drums.wav slices/ -t 0.3 -p VintageBreak
```

### stutter

Create a stutter/repeat effect by extracting a segment and repeating it.

```text
cysox stutter <input> <output> [options]
```

| Option | Description |
|--------|-------------|
| `-s`, `--start` | Segment start time in seconds (default: 0). |
| `-d`, `--duration` | Segment duration in seconds (default: 0.125). |
| `-r`, `--repeats` | Number of repeats (default: 8). |
| `-p`, `--preset` | Apply a preset after stuttering. |

**Example:**

```bash
# Create 8x stutter of first 125ms
cysox stutter drums.wav stutter.wav -r 8

# Stutter from 0.5s with reverb
cysox stutter drums.wav stutter.wav -s 0.5 -d 0.1 -r 16 -p SmallRoom
```

### preset

Browse and apply effect presets.

#### preset list

List available presets, optionally filtered by category.

```text
cysox preset list [category]
```

Categories: `voice`, `lofi`, `spatial`, `broadcast`, `musical`, `drums`, `mastering`, `cleanup`, `transition`.

**Example:**

```text
$ cysox preset list spatial

SPATIAL:
  SmallRoom()
  LargeHall()
  Cathedral()
  Bathroom()
  Stadium()
```

#### preset info

Show detailed information about a preset including its parameters.

```text
cysox preset info <name>
```

**Example:**

```text
$ cysox preset info Reverb

Reverb
------
Add reverberation effect.

Parameters:
  --reverberance=50
  --hf_damping=50
  --room_scale=100
  --stereo_depth=100
  --pre_delay=0
  --wet_gain=0
```

#### preset apply

Apply a preset to an audio file with optional parameter overrides.

```text
cysox preset apply <name> <input> <output> [--param=value ...]
```

**Example:**

```bash
# Apply default Cathedral preset
cysox preset apply Cathedral input.wav output.wav

# Apply with custom parameters
cysox preset apply LargeHall input.wav output.wav --reverberance=80
```
