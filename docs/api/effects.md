# Effects Reference

cysox provides 28 typed effect classes and 40+ composite presets. Effects are used with the high-level API:

```python
import cysox
from cysox import fx

cysox.convert('input.wav', 'output.wav', effects=[
    fx.Bass(gain=5),
    fx.Reverb(reverberance=70),
    fx.Normalize(),
])
```

Effects can also be combined into reusable presets using `CompositeEffect` (see [Presets](#presets) below).

---

## Volume and Dynamics

### Volume

Adjust volume level in decibels.

```python
fx.Volume(db=3)                  # Boost by 3dB
fx.Volume(db=-6)                 # Cut by 6dB
fx.Volume(db=6, limiter=True)    # Boost with limiter to prevent clipping
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db` | float | 0 | Volume adjustment in dB. Positive = louder. |
| `limiter` | bool | False | Apply limiter to prevent clipping. |

### Gain

Apply gain with normalization and limiting options.

```python
fx.Gain(db=-3)
fx.Gain(db=0, normalize=True)   # Normalize only
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `db` | float | 0 | Gain in decibels. |
| `normalize` | bool | False | Normalize to 0dBFS before applying gain. |
| `limiter` | bool | False | Apply limiter to prevent clipping. |
| `balance` | bool | False | Balance channels (stereo). |

### Normalize

Normalize audio to a target peak level.

```python
fx.Normalize()            # Normalize to -1 dBFS
fx.Normalize(level=-3)    # Normalize to -3 dBFS
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `level` | float | -1 | Target peak level in dBFS. |

---

## Equalization

### Bass

Boost or cut bass frequencies using a shelving filter.

```python
fx.Bass(gain=5)                      # Boost bass by 5dB
fx.Bass(gain=-3, frequency=80)       # Cut at 80Hz
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `gain` | float | *required* | Boost (positive) or cut (negative) in dB. |
| `frequency` | float | 100 | Center frequency in Hz. |
| `width` | float | 0.5 | Filter width in octaves. |

### Treble

Boost or cut treble frequencies using a shelving filter.

```python
fx.Treble(gain=3)                        # Boost treble by 3dB
fx.Treble(gain=-2, frequency=4000)       # Cut at 4kHz
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `gain` | float | *required* | Boost (positive) or cut (negative) in dB. |
| `frequency` | float | 3000 | Center frequency in Hz. |
| `width` | float | 0.5 | Filter width in octaves. |

### Equalizer

Peaking EQ filter at a specific frequency.

```python
fx.Equalizer(frequency=1000, width=1, gain=3)    # Boost 1kHz
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `frequency` | float | *required* | Center frequency in Hz. |
| `width` | float | *required* | Q factor or bandwidth. |
| `gain` | float | *required* | Boost (positive) or cut (negative) in dB. |

---

## Filters

### HighPass

High-pass filter that removes frequencies below the cutoff.

```python
fx.HighPass(frequency=80)              # Remove rumble below 80Hz
fx.HighPass(frequency=200, poles=1)    # Gentle rolloff
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `frequency` | float | *required* | Cutoff frequency in Hz. |
| `poles` | int | 2 | Filter order (1 or 2). Higher = steeper rolloff. |

### LowPass

Low-pass filter that removes frequencies above the cutoff.

```python
fx.LowPass(frequency=8000)             # Remove highs above 8kHz
fx.LowPass(frequency=4000, poles=1)    # Gentle rolloff
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `frequency` | float | *required* | Cutoff frequency in Hz. |
| `poles` | int | 2 | Filter order (1 or 2). Higher = steeper rolloff. |

### BandPass

Band-pass filter that passes frequencies within a range.

```python
fx.BandPass(frequency=1000, width=2)    # Q=2 bandpass at 1kHz
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `frequency` | float | *required* | Center frequency in Hz. |
| `width` | float | *required* | Filter width (interpretation depends on `width_type`). |
| `width_type` | str | `"q"` | `"q"` for Q-factor, `"h"` for Hz, `"o"` for octaves. |
| `constant_skirt` | bool | False | Use constant skirt gain. |

### BandReject

Band-reject (notch) filter that removes a narrow frequency range.

```python
fx.BandReject(frequency=60, width=10)    # Remove 60Hz hum
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `frequency` | float | *required* | Center frequency in Hz. |
| `width` | float | *required* | Filter width (interpretation depends on `width_type`). |
| `width_type` | str | `"q"` | `"q"` for Q-factor, `"h"` for Hz, `"o"` for octaves. |

---

## Reverb and Spatial

### Reverb

Add reverberation.

```python
fx.Reverb()                                       # Default reverb
fx.Reverb(reverberance=80)                        # Long decay
fx.Reverb(room_scale=50, pre_delay=20)            # Small room
fx.Reverb(reverberance=90, wet_only=True)         # Wet signal only
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `reverberance` | float | 50 | Reverb time, 0-100%. |
| `hf_damping` | float | 50 | High frequency damping, 0-100%. |
| `room_scale` | float | 100 | Room size, 0-100%. |
| `stereo_depth` | float | 100 | Stereo spread, 0-100%. |
| `pre_delay` | float | 0 | Pre-delay in milliseconds. |
| `wet_gain` | float | 0 | Wet signal gain in dB. |
| `wet_only` | bool | False | Output only the wet signal (no dry). |

### Echo

Add one or more echo taps.

```python
fx.Echo(delays=[100], decays=[0.5])                  # Single echo
fx.Echo(delays=[100, 200], decays=[0.6, 0.3])        # Multi-tap
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `delays` | list[float] | *required* | Delay times in milliseconds. |
| `decays` | list[float] | *required* | Decay values (0-1) for each delay. Must match length of `delays`. |
| `gain_in` | float | 0.8 | Input gain (0-1). |
| `gain_out` | float | 0.9 | Output gain (0-1). |

### Chorus

Add chorus modulation.

```python
fx.Chorus()                              # Default chorus
fx.Chorus(depth=4, speed=0.5)            # Deeper, faster
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `gain_in` | float | 0.7 | Input gain (0-1). |
| `gain_out` | float | 0.9 | Output gain (0-1). |
| `delay` | float | 55 | Base delay in ms. |
| `decay` | float | 0.4 | Decay factor. |
| `speed` | float | 0.25 | Modulation speed in Hz. |
| `depth` | float | 2 | Modulation depth in ms. |
| `shape` | str | `"s"` | `"s"` (sine) or `"t"` (triangle). |

### Flanger

Add flanging effect.

```python
fx.Flanger()                                     # Default flanger
fx.Flanger(depth=5, speed=0.3, regen=50)         # Deeper with feedback
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `delay` | float | 0 | Base delay in ms. |
| `depth` | float | 2 | Modulation depth in ms. |
| `regen` | float | 0 | Regeneration/feedback, -95 to 95%. |
| `width` | float | 71 | Wet/dry mix percentage. |
| `speed` | float | 0.5 | Modulation speed in Hz. |
| `shape` | str | `"sine"` | `"sine"` or `"triangle"`. |
| `phase` | float | 25 | Phase offset for stereo, percentage. |
| `interp` | str | `"linear"` | `"linear"` or `"quadratic"`. |

---

## Time and Pitch

### Trim

Extract a portion of the audio. Specify either `end` or `duration`, not both.

```python
fx.Trim(start=1.5, end=10.0)        # From 1.5s to 10s
fx.Trim(start=5.0)                  # From 5s to end
fx.Trim(end=30.0)                   # First 30 seconds
fx.Trim(start=0, duration=10)       # First 10 seconds
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `start` | float | 0 | Start time in seconds. |
| `end` | float | None | End time in seconds. |
| `duration` | float | None | Duration in seconds. |

### Pad

Add silence to the beginning and/or end.

```python
fx.Pad(before=1.0)                  # 1s silence at start
fx.Pad(after=2.0)                   # 2s silence at end
fx.Pad(before=0.5, after=1.0)       # Both
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `before` | float | 0 | Seconds of silence at the beginning. |
| `after` | float | 0 | Seconds of silence at the end. |

### Speed

Change playback speed. This affects pitch (higher speed = higher pitch).

```python
fx.Speed(factor=2.0)     # Double speed, octave up
fx.Speed(factor=0.5)     # Half speed, octave down
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `factor` | float | *required* | Speed multiplier (must be positive). |

### Tempo

Change tempo without affecting pitch.

```python
fx.Tempo(factor=1.5)                       # 50% faster
fx.Tempo(factor=0.8, audio_type='s')       # Slower, optimized for speech
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `factor` | float | *required* | Tempo multiplier (must be positive). |
| `audio_type` | str | None | Optimize for `"m"` (music), `"s"` (speech), or `"l"` (linear). |
| `quick` | bool | False | Use quicker, lower-quality algorithm. |

### Pitch

Change pitch without affecting tempo.

```python
fx.Pitch(cents=100)      # Up one semitone
fx.Pitch(cents=-200)     # Down two semitones
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `cents` | float | *required* | Pitch shift in cents (100 cents = 1 semitone). |
| `quick` | bool | False | Use quicker, lower-quality algorithm. |

### Reverse

Reverse the audio.

```python
fx.Reverse()
```

No parameters.

### Fade

Apply fade-in and/or fade-out.

```python
fx.Fade(fade_in=0.5)                              # 0.5s fade in
fx.Fade(fade_out=2.0)                              # 2s fade out
fx.Fade(fade_in=1.0, fade_out=1.0, type='l')       # Logarithmic fades
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `fade_in` | float | 0 | Fade-in duration in seconds. |
| `fade_out` | float | 0 | Fade-out duration in seconds. |
| `type` | str | `"t"` | Curve type: `"q"` (quarter sine), `"h"` (half sine), `"t"` (linear), `"l"` (logarithmic), `"p"` (parabola). |

### Repeat

Repeat the audio a specified number of times.

```python
fx.Repeat(count=2)     # Play 3 times total (original + 2 repeats)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `count` | int | *required* | Number of additional plays (must be >= 1). |

---

## Format Conversion

### Rate

Resample to a different sample rate.

```python
fx.Rate(sample_rate=48000)
fx.Rate(sample_rate=44100, quality='very-high')
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `sample_rate` | int | *required* | Target sample rate in Hz. |
| `quality` | str | `"high"` | `"quick"`, `"low"`, `"medium"`, `"high"`, or `"very-high"`. |

### Channels

Change the number of audio channels.

```python
fx.Channels(channels=1)     # Convert to mono
fx.Channels(channels=2)     # Convert to stereo
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `channels` | int | *required* | Target number of channels (>= 1). |

### Remix

Remix channels with custom mix specification.

```python
fx.Remix(mix=["1,2"])              # Mono mixdown
fx.Remix(mix=["2", "1"])           # Swap L/R
fx.Remix(mix=["1v0.5,2v0.5"])     # Mono with equal volume mix
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `mix` | list[str] | *required* | Channel mix specification. Each string defines one output channel. |

### Dither

Apply dithering for bit-depth reduction.

```python
fx.Dither()                         # Default shaped dither
fx.Dither(type='triangular')        # TPDF dither
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `type` | str | `"shaped"` | `"rectangular"`, `"triangular"`, `"gaussian"`, or `"shaped"`. |
| `precision` | int | None | Target precision in bits. |

---

## Presets

Presets are `CompositeEffect` subclasses that combine multiple effects into reusable chains. Use them exactly like single effects:

```python
cysox.convert('input.wav', 'output.wav', effects=[fx.Telephone()])
```

List all presets from the CLI:

```text
cysox preset list
```

### Voice

| Preset | Description |
|--------|-------------|
| `Chipmunk` | High-pitched voice via speed increase. |
| `DeepVoice` | Low-pitched voice via speed decrease. |
| `Robot` | Robotic, metallic voice with chorus and flanger. |
| `HauntedVoice` | Eerie voice with reverb and pitch shift. |
| `VocalClarity` | Enhanced voice clarity with EQ and compression. |
| `Whisper` | Soft, breathy sound with low volume and reverb. |

### Lo-Fi

| Preset | Description |
|--------|-------------|
| `Telephone` | Narrow bandwidth telephone simulation. |
| `AMRadio` | AM radio frequency response. |
| `Megaphone` | Harsh, compressed megaphone sound. |
| `Underwater` | Muffled, submerged sound. |
| `VinylWarmth` | Warm analog vinyl character. |
| `LoFiHipHop` | Lo-fi hip-hop aesthetic with warmth and slow tempo. |
| `Cassette` | Cassette tape degradation. |

### Spatial

| Preset | Description |
|--------|-------------|
| `SmallRoom` | Small room reverb. |
| `LargeHall` | Large concert hall reverb. |
| `Cathedral` | Very long cathedral reverb. |
| `Bathroom` | Small tiled bathroom reflections. |
| `Stadium` | Open stadium ambience. |

### Broadcast

| Preset | Description |
|--------|-------------|
| `Podcast` | Voice optimized for podcast production. |
| `RadioDJ` | Bright, compressed radio DJ sound. |
| `Voiceover` | Clean voiceover processing. |
| `Intercom` | Intercom/PA system simulation. |
| `WalkieTalkie` | Walkie-talkie radio effect. |

### Musical

| Preset | Description |
|--------|-------------|
| `EightiesChorus` | Classic 1980s chorus. |
| `DreamyPad` | Ethereal pad with reverb and chorus. |
| `SlowedReverb` | Slowed + reverb aesthetic. |
| `SlapbackEcho` | Short slapback delay. |
| `DubDelay` | Dub-style echo with feedback. |
| `JetFlanger` | Jet engine flanging sweep. |
| `ShoegazeWash` | Shoegaze-style reverb wash. |

### Drum Loops

| Preset | Description |
|--------|-------------|
| `HalfTime` | Half-speed for half-time feel. |
| `DoubleTime` | Double-speed for double-time feel. |
| `DrumPunch` | Punchy drums with bass boost and compression. |
| `DrumCrisp` | Crisp, bright drums with high-end boost. |
| `DrumFat` | Fat, heavy drums with low-end emphasis. |
| `Breakbeat` | Breakbeat-style processing. |
| `VintageBreak` | Vintage breakbeat character. |
| `DrumRoom` | Natural room ambience on drums. |
| `GatedReverb` | Classic gated reverb on drums. |
| `DrumSlice` | Tight, sliced drum sound. |
| `ReverseCymbal` | Reversed cymbal effect. |
| `LoopReady` | Normalized and trimmed for clean looping. |

### Mastering

| Preset | Description |
|--------|-------------|
| `BroadcastLimiter` | Broadcast-standard limiting. |
| `WarmMaster` | Warm mastering with bass and treble shaping. |
| `BrightMaster` | Bright mastering with treble lift. |
| `LoudnessMaster` | Loudness-maximized mastering. |

### Cleanup

| Preset | Description |
|--------|-------------|
| `RemoveRumble` | High-pass filter to remove low-frequency rumble. |
| `RemoveHiss` | Low-pass filter to reduce high-frequency hiss. |
| `RemoveHum` | Notch filter to remove 60Hz mains hum. |
| `CleanVoice` | Voice cleanup with rumble and hiss removal. |
| `TapeRestoration` | Restore tape recordings with EQ correction. |

### Transition

| Preset | Description |
|--------|-------------|
| `FadeInOut` | Apply fade-in and fade-out. |
| `CrossfadeReady` | Prepare audio for crossfading with fades at boundaries. |

---

## Custom Presets

Create reusable effect combinations by subclassing `CompositeEffect`:

```python
from cysox.fx import CompositeEffect, Bass, Treble, Reverb, Normalize

class MyPreset(CompositeEffect):
    """Custom processing chain."""

    def __init__(self, bass_gain=3, reverb_time=60):
        self.bass_gain = bass_gain
        self.reverb_time = reverb_time

    @property
    def name(self):
        return "my_preset"

    @property
    def effects(self):
        return [
            Bass(gain=self.bass_gain),
            Treble(gain=2),
            Reverb(reverberance=self.reverb_time),
            Normalize(),
        ]

# Use it like any other effect
cysox.convert('input.wav', 'output.wav', effects=[MyPreset(bass_gain=5)])
```
