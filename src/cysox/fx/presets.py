"""Composite effect presets for common audio processing tasks.

This module provides ready-to-use composite effects that combine multiple
base effects to achieve specific audio transformations.

Example:
    >>> import cysox
    >>> from cysox.fx.presets import Telephone, VinylWarmth
    >>>
    >>> cysox.convert('input.wav', 'output.wav', effects=[Telephone()])
    >>> cysox.convert('input.wav', 'warm.wav', effects=[VinylWarmth()])

Categories:
    - Voice Effects: Transform vocal characteristics
    - Lo-Fi Effects: Degrade audio quality aesthetically
    - Spatial Effects: Add room/environment ambience
    - Broadcast Effects: Simulate transmission mediums
    - Musical Effects: Creative sound design
    - Mastering Effects: Prepare audio for final delivery
    - Cleanup Effects: Fix common audio problems
"""

from typing import List

from .base import CompositeEffect, Effect
from .eq import Bass, Treble, Equalizer
from .filter import HighPass, LowPass, BandReject
from .reverb import Reverb, Echo, Chorus, Flanger
from .volume import Volume, Normalize, Gain
from .time import Speed, Pitch, Fade, Reverse, Tempo, Trim, Repeat
from .convert import Rate


# -----------------------------------------------------------------------------
# Voice Effects
# -----------------------------------------------------------------------------


class Chipmunk(CompositeEffect):
    """High-pitched chipmunk voice effect.

    Speeds up audio to raise pitch and adds brightness.

    Args:
        intensity: Speed factor (1.5-2.5 typical). Default 1.8.
    """

    def __init__(self, intensity: float = 1.8):
        self.intensity = intensity

    @property
    def effects(self) -> List[Effect]:
        return [
            Speed(factor=self.intensity),
            Treble(gain=3),
        ]


class DeepVoice(CompositeEffect):
    """Deep, slowed-down voice effect.

    Slows audio to lower pitch and adds bass warmth.

    Args:
        intensity: Speed factor (0.5-0.8 typical). Default 0.6.
    """

    def __init__(self, intensity: float = 0.6):
        self.intensity = intensity

    @property
    def effects(self) -> List[Effect]:
        return [
            Speed(factor=self.intensity),
            Bass(gain=4),
        ]


class Robot(CompositeEffect):
    """Robotic voice effect.

    Creates a metallic, mechanical sound using flanger and EQ.

    Args:
        intensity: Effect intensity 0-100. Default 70.
    """

    def __init__(self, intensity: float = 70):
        self.intensity = intensity

    @property
    def effects(self) -> List[Effect]:
        regen = min(80, self.intensity)
        return [
            Flanger(delay=0.5, depth=2, regen=regen, width=50, speed=0.1),
            Equalizer(frequency=1500, gain=6, width=1.5),
            HighPass(frequency=200),
        ]


class HauntedVoice(CompositeEffect):
    """Spooky, ghostly voice effect.

    Lowers pitch and adds heavy reverb with echoes.

    Args:
        pitch_shift: Pitch down in semitones. Default 5.
        reverb_amount: Reverberance 0-100. Default 90.
    """

    def __init__(self, pitch_shift: float = 5, reverb_amount: float = 90):
        self.pitch_shift = pitch_shift
        self.reverb_amount = reverb_amount

    @property
    def effects(self) -> List[Effect]:
        return [
            Pitch(cents=-self.pitch_shift * 100),
            Reverb(reverberance=self.reverb_amount, room_scale=100),
            Echo(delays=[300, 600], decays=[0.4, 0.2], gain_in=0.6, gain_out=0.5),
        ]


class VocalClarity(CompositeEffect):
    """Enhance vocal clarity and presence.

    Removes mud frequencies and adds presence for clearer vocals.

    Args:
        presence_boost: Boost at 4kHz in dB. Default 4.
    """

    def __init__(self, presence_boost: float = 4):
        self.presence_boost = presence_boost

    @property
    def effects(self) -> List[Effect]:
        return [
            HighPass(frequency=80),
            Equalizer(frequency=300, gain=-3, width=1.5),  # Cut mud
            Equalizer(frequency=4000, gain=self.presence_boost, width=2.0),
            Normalize(level=-3),
        ]


class Whisper(CompositeEffect):
    """Intimate whisper effect.

    Reduces low frequencies and adds subtle breath-like reverb.
    """

    @property
    def effects(self) -> List[Effect]:
        return [
            HighPass(frequency=200),
            Treble(gain=2),
            Volume(db=-6),
            Reverb(reverberance=20, room_scale=20, stereo_depth=50),
        ]


# -----------------------------------------------------------------------------
# Lo-Fi Effects
# -----------------------------------------------------------------------------


class Telephone(CompositeEffect):
    """Classic telephone/landline effect.

    Bandpass filters to telephone frequency range and downsamples.

    Args:
        sample_rate: Output sample rate. Default 8000 (telephone standard).
    """

    def __init__(self, sample_rate: int = 8000):
        self.sample_rate = sample_rate

    @property
    def effects(self) -> List[Effect]:
        return [
            HighPass(frequency=300),
            LowPass(frequency=3400),
            Rate(sample_rate=self.sample_rate),
            Volume(db=-3),
        ]


class AMRadio(CompositeEffect):
    """AM radio broadcast effect.

    Restricted bandwidth with slight compression feel.
    """

    @property
    def effects(self) -> List[Effect]:
        return [
            HighPass(frequency=200),
            LowPass(frequency=5000),
            Normalize(),
            Bass(gain=-3),
        ]


class Megaphone(CompositeEffect):
    """Megaphone/bullhorn effect.

    Mid-focused frequency response with harsh presence.

    Args:
        volume_boost: Volume boost in dB. Default 6.
    """

    def __init__(self, volume_boost: float = 6):
        self.volume_boost = volume_boost

    @property
    def effects(self) -> List[Effect]:
        return [
            HighPass(frequency=800),
            LowPass(frequency=4000),
            Volume(db=self.volume_boost),
            Equalizer(frequency=2000, gain=6, width=2.0),
        ]


class Underwater(CompositeEffect):
    """Underwater/submerged muffled effect.

    Heavy low-pass filtering with reverb for submerged feel.

    Args:
        depth: Cutoff frequency (lower = deeper). Default 500.
    """

    def __init__(self, depth: float = 500):
        self.depth = depth

    @property
    def effects(self) -> List[Effect]:
        return [
            LowPass(frequency=self.depth),
            Reverb(reverberance=60, room_scale=50),
            Volume(db=-6),
        ]


class VinylWarmth(CompositeEffect):
    """Warm vinyl record aesthetic.

    Adds bass warmth and rolls off harsh highs.

    Args:
        bass_boost: Bass boost in dB. Default 3.
        treble_cut: Treble cut in dB (positive value). Default 2.
    """

    def __init__(self, bass_boost: float = 3, treble_cut: float = 2):
        self.bass_boost = bass_boost
        self.treble_cut = treble_cut

    @property
    def effects(self) -> List[Effect]:
        return [
            Bass(gain=self.bass_boost, frequency=80),
            Treble(gain=-self.treble_cut, frequency=8000),
            Reverb(reverberance=15, room_scale=20),
        ]


class LoFiHipHop(CompositeEffect):
    """Lo-fi hip hop aesthetic.

    Combines vinyl warmth with slight pitch wobble and low sample rate.

    Args:
        warmth: Bass boost amount. Default 4.
    """

    def __init__(self, warmth: float = 4):
        self.warmth = warmth

    @property
    def effects(self) -> List[Effect]:
        return [
            Rate(sample_rate=22050, quality="medium"),
            Bass(gain=self.warmth, frequency=100),
            Treble(gain=-4, frequency=6000),
            Reverb(reverberance=25, room_scale=30),
            Chorus(gain_in=0.9, gain_out=0.9, delay=20, decay=0.2, speed=0.2, depth=1),
        ]


class Cassette(CompositeEffect):
    """Cassette tape degradation effect.

    Simulates tape hiss range and frequency limitations.
    """

    @property
    def effects(self) -> List[Effect]:
        return [
            HighPass(frequency=60),
            LowPass(frequency=12000),
            Bass(gain=2),
            Treble(gain=-3, frequency=10000),
            Chorus(gain_in=0.95, gain_out=0.95, delay=25, decay=0.1, speed=0.3, depth=0.5),
        ]


# -----------------------------------------------------------------------------
# Spatial Effects
# -----------------------------------------------------------------------------


class SmallRoom(CompositeEffect):
    """Small room ambience.

    Intimate room reverb for close-up recordings.

    Args:
        wetness: Reverberance amount 0-100. Default 30.
    """

    def __init__(self, wetness: float = 30):
        self.wetness = wetness

    @property
    def effects(self) -> List[Effect]:
        return [
            Reverb(reverberance=self.wetness, room_scale=30, hf_damping=50),
        ]


class LargeHall(CompositeEffect):
    """Large concert hall ambience.

    Spacious reverb for orchestral/live performance feel.

    Args:
        size: Room scale 0-100. Default 100.
        decay: Reverberance 0-100. Default 70.
    """

    def __init__(self, size: float = 100, decay: float = 70):
        self.size = size
        self.decay = decay

    @property
    def effects(self) -> List[Effect]:
        return [
            Reverb(reverberance=self.decay, room_scale=self.size, stereo_depth=100),
            Normalize(level=-3),
        ]


class Cathedral(CompositeEffect):
    """Cathedral/church reverb.

    Very long decay with high frequency damping.
    """

    @property
    def effects(self) -> List[Effect]:
        return [
            Reverb(reverberance=95, room_scale=100, hf_damping=70, pre_delay=40),
            Volume(db=-3),
        ]


class Bathroom(CompositeEffect):
    """Bathroom/tiled room reverb.

    Bright, reflective small-space reverb.
    """

    @property
    def effects(self) -> List[Effect]:
        return [
            Reverb(reverberance=50, room_scale=20, hf_damping=10),
            Treble(gain=2),
        ]


class Stadium(CompositeEffect):
    """Stadium/arena ambience.

    Large space with distinct echo reflections.
    """

    @property
    def effects(self) -> List[Effect]:
        return [
            Echo(delays=[150, 300], decays=[0.3, 0.15], gain_in=0.8, gain_out=0.7),
            Reverb(reverberance=60, room_scale=100, stereo_depth=80),
            Volume(db=-3),
        ]


# -----------------------------------------------------------------------------
# Broadcast Effects
# -----------------------------------------------------------------------------


class Podcast(CompositeEffect):
    """Podcast voice processing.

    Clean up voice, add presence, normalize for consistent levels.
    """

    @property
    def effects(self) -> List[Effect]:
        return [
            HighPass(frequency=80),
            Equalizer(frequency=200, gain=-2, width=1.5),  # Reduce mud
            Equalizer(frequency=3000, gain=2, width=2.0),  # Add presence
            Normalize(level=-1),
        ]


class RadioDJ(CompositeEffect):
    """Radio DJ voice processing.

    Punchy, present voice with compression-like effect.

    Args:
        presence: Presence boost at 5kHz. Default 4.
    """

    def __init__(self, presence: float = 4):
        self.presence = presence

    @property
    def effects(self) -> List[Effect]:
        return [
            HighPass(frequency=100),
            Bass(gain=3),
            Equalizer(frequency=5000, gain=self.presence, width=2.0),
            Gain(db=0, normalize=True, limiter=True),
        ]


class Voiceover(CompositeEffect):
    """Professional voiceover processing.

    Clear, warm, broadcast-ready voice.
    """

    @property
    def effects(self) -> List[Effect]:
        return [
            HighPass(frequency=80),
            Bass(gain=2, frequency=150),
            Equalizer(frequency=2500, gain=2, width=2.0),
            Equalizer(frequency=6000, gain=1, width=2.5),
            Normalize(level=-3),
        ]


class Intercom(CompositeEffect):
    """Intercom/PA system effect.

    Narrow bandwidth with harsh midrange.
    """

    @property
    def effects(self) -> List[Effect]:
        return [
            HighPass(frequency=400),
            LowPass(frequency=4000),
            Equalizer(frequency=2000, gain=8, width=1.5),
            Volume(db=3),
        ]


class WalkieTalkie(CompositeEffect):
    """Walkie-talkie/two-way radio effect.

    Very narrow bandwidth with distortion-like compression.
    """

    @property
    def effects(self) -> List[Effect]:
        return [
            HighPass(frequency=500),
            LowPass(frequency=3000),
            Rate(sample_rate=8000),
            Gain(db=6, normalize=True, limiter=True),
            Equalizer(frequency=1500, gain=6, width=2.0),
        ]


# -----------------------------------------------------------------------------
# Musical Effects
# -----------------------------------------------------------------------------


class EightiesChorus(CompositeEffect):
    """Classic 80s chorus sound.

    Lush chorus with subtle reverb, iconic of 80s production.

    Args:
        depth: Chorus depth (1-10). Default 4.
    """

    def __init__(self, depth: float = 4):
        self.depth = depth

    @property
    def effects(self) -> List[Effect]:
        return [
            Chorus(gain_in=0.5, gain_out=0.6, delay=30, decay=0.4, speed=1.5, depth=self.depth),
            Reverb(reverberance=20),
        ]


class DreamyPad(CompositeEffect):
    """Dreamy, ethereal pad effect.

    Heavy reverb and chorus for ambient textures.
    """

    @property
    def effects(self) -> List[Effect]:
        return [
            Chorus(gain_in=0.6, gain_out=0.6, delay=40, decay=0.5, speed=0.3, depth=5),
            Reverb(reverberance=85, room_scale=100, stereo_depth=100),
            LowPass(frequency=8000),
            Volume(db=-3),
        ]


class SlowedReverb(CompositeEffect):
    """Slowed + reverb aesthetic.

    Popular effect slowing audio and adding dreamy reverb.

    Args:
        slow_factor: Speed factor (0.7-0.9 typical). Default 0.85.
    """

    def __init__(self, slow_factor: float = 0.85):
        self.slow_factor = slow_factor

    @property
    def effects(self) -> List[Effect]:
        return [
            Speed(factor=self.slow_factor),
            Reverb(reverberance=60, room_scale=80, stereo_depth=80),
            Bass(gain=3),
        ]


class SlapbackEcho(CompositeEffect):
    """Classic slapback echo.

    Short delay used in rockabilly and early rock.

    Args:
        delay_ms: Delay time in milliseconds. Default 120.
    """

    def __init__(self, delay_ms: float = 120):
        self.delay_ms = delay_ms

    @property
    def effects(self) -> List[Effect]:
        return [
            Echo(delays=[self.delay_ms], decays=[0.4], gain_in=0.8, gain_out=0.8),
        ]


class DubDelay(CompositeEffect):
    """Dub-style delay effect.

    Multiple rhythmic echoes with filtering.

    Args:
        tempo_ms: Base delay time. Default 375 (160 BPM eighth note).
    """

    def __init__(self, tempo_ms: float = 375):
        self.tempo_ms = tempo_ms

    @property
    def effects(self) -> List[Effect]:
        return [
            Echo(
                delays=[self.tempo_ms, self.tempo_ms * 2, self.tempo_ms * 3],
                decays=[0.5, 0.35, 0.2],
                gain_in=0.7,
                gain_out=0.6,
            ),
            LowPass(frequency=3000),
            Bass(gain=3),
        ]


class JetFlanger(CompositeEffect):
    """Extreme jet plane flanger effect.

    Dramatic sweeping flanger sound.
    """

    @property
    def effects(self) -> List[Effect]:
        return [
            Flanger(delay=0, depth=10, regen=80, width=100, speed=0.2),
        ]


class ShoegazeWash(CompositeEffect):
    """Shoegaze-style wash effect.

    Heavy reverb, chorus, and subtle pitch modulation.
    """

    @property
    def effects(self) -> List[Effect]:
        return [
            Chorus(gain_in=0.5, gain_out=0.5, delay=35, decay=0.5, speed=0.4, depth=4),
            Flanger(delay=3, depth=3, regen=30, width=60, speed=0.15),
            Reverb(reverberance=90, room_scale=100, stereo_depth=100, hf_damping=40),
            Volume(db=-3),
        ]


# -----------------------------------------------------------------------------
# Drum Loop Effects
# -----------------------------------------------------------------------------


class HalfTime(CompositeEffect):
    """Half-time drum loop effect.

    Slows the loop to half speed while preserving pitch.
    Good for creating slow, heavy beats from faster loops.

    Args:
        preserve_pitch: If True, use tempo stretch (default). If False, use
                       speed change which also lowers pitch.
    """

    def __init__(self, preserve_pitch: bool = True):
        self.preserve_pitch = preserve_pitch

    @property
    def effects(self) -> List[Effect]:
        if self.preserve_pitch:
            return [Tempo(factor=0.5, audio_type="m")]
        else:
            return [Speed(factor=0.5)]


class DoubleTime(CompositeEffect):
    """Double-time drum loop effect.

    Speeds up the loop to double speed while preserving pitch.
    Good for creating faster, energetic beats.

    Args:
        preserve_pitch: If True, use tempo stretch (default). If False, use
                       speed change which also raises pitch.
    """

    def __init__(self, preserve_pitch: bool = True):
        self.preserve_pitch = preserve_pitch

    @property
    def effects(self) -> List[Effect]:
        if self.preserve_pitch:
            return [Tempo(factor=2.0, audio_type="m")]
        else:
            return [Speed(factor=2.0)]


class DrumPunch(CompositeEffect):
    """Enhance drum punch and attack.

    Boosts low-mids and presence for punchier drums.

    Args:
        punch: Amount of low-mid boost (dB). Default 4.
        attack: Amount of presence boost (dB). Default 3.
    """

    def __init__(self, punch: float = 4, attack: float = 3):
        self.punch = punch
        self.attack = attack

    @property
    def effects(self) -> List[Effect]:
        return [
            HighPass(frequency=30),  # Remove sub-rumble
            Equalizer(frequency=100, gain=self.punch, width=1.5),  # Kick punch
            Equalizer(frequency=3500, gain=self.attack, width=2.0),  # Attack/snap
            Gain(db=0, normalize=True, limiter=True),
        ]


class DrumCrisp(CompositeEffect):
    """Crisp, bright drum sound.

    Enhances high frequencies for snappy snares and crisp hats.

    Args:
        brightness: Amount of high frequency boost (dB). Default 4.
    """

    def __init__(self, brightness: float = 4):
        self.brightness = brightness

    @property
    def effects(self) -> List[Effect]:
        return [
            HighPass(frequency=40),
            Treble(gain=self.brightness, frequency=8000),
            Equalizer(frequency=5000, gain=2, width=2.0),  # Presence
            Normalize(level=-1),
        ]


class DrumFat(CompositeEffect):
    """Fat, heavy drum sound.

    Boosts low end for thick, heavy drums.

    Args:
        fatness: Amount of bass boost (dB). Default 5.
    """

    def __init__(self, fatness: float = 5):
        self.fatness = fatness

    @property
    def effects(self) -> List[Effect]:
        return [
            Bass(gain=self.fatness, frequency=80),
            Equalizer(frequency=60, gain=3, width=1.0),  # Sub bass
            LowPass(frequency=12000),  # Slightly tame highs
            Gain(db=0, normalize=True, limiter=True),
        ]


class Breakbeat(CompositeEffect):
    """Classic breakbeat processing.

    Gritty, punchy sound inspired by classic breakbeat samplers.
    Adds punch, slight grit, and compression-like limiting.
    """

    @property
    def effects(self) -> List[Effect]:
        return [
            HighPass(frequency=40),
            Bass(gain=3, frequency=100),
            Equalizer(frequency=200, gain=-2, width=1.5),  # Scoop mud
            Equalizer(frequency=3000, gain=4, width=2.0),  # Snap
            Gain(db=3, normalize=True, limiter=True),
            Normalize(level=-0.5),
        ]


class VintageBreak(CompositeEffect):
    """Vintage sampled break sound.

    Lo-fi, warm sound reminiscent of classic sampled breaks.
    Combines bit reduction effect with warm EQ.
    """

    @property
    def effects(self) -> List[Effect]:
        return [
            Rate(sample_rate=22050, quality="low"),  # Lo-fi sample rate
            Bass(gain=4, frequency=80),
            Treble(gain=-3, frequency=8000),
            Equalizer(frequency=2000, gain=2, width=2.0),
            Normalize(level=-1),
        ]


class DrumRoom(CompositeEffect):
    """Drum room ambience.

    Adds natural room sound to dry drums.

    Args:
        room_size: Room size 0-100. Default 40.
        wetness: Reverb amount 0-100. Default 25.
    """

    def __init__(self, room_size: float = 40, wetness: float = 25):
        self.room_size = room_size
        self.wetness = wetness

    @property
    def effects(self) -> List[Effect]:
        return [
            Reverb(
                reverberance=self.wetness,
                room_scale=self.room_size,
                hf_damping=50,
                pre_delay=5,
            ),
        ]


class GatedReverb(CompositeEffect):
    """80s gated reverb drum sound.

    Big reverb with abrupt cutoff, classic 80s snare sound.
    Simulated by using short reverb with high initial level.
    """

    @property
    def effects(self) -> List[Effect]:
        return [
            Reverb(reverberance=30, room_scale=80, stereo_depth=50, pre_delay=0),
            Equalizer(frequency=200, gain=3, width=1.5),
            Gain(db=0, normalize=True, limiter=True),
        ]


class DrumSlice(CompositeEffect):
    """Extract a slice/segment from a drum loop.

    Trims to a specific segment of the loop. Useful for isolating
    kicks, snares, or specific beats.

    Args:
        start: Start position in seconds. Default 0.
        duration: Length of segment (seconds). Default 0.5.

    Note:
        For stutter effects (repeating a slice), use slice_loop() utility
        function with repeat=True, as sox cannot chain trim+repeat.
    """

    def __init__(self, start: float = 0, duration: float = 0.5):
        self.start = start
        self.duration = duration

    @property
    def effects(self) -> List[Effect]:
        return [
            Trim(start=self.start, duration=self.duration),
        ]


class ReverseCymbal(CompositeEffect):
    """Reverse cymbal/riser effect.

    Reverses audio and adds fade-in for classic reverse cymbal sound.
    Best used on cymbal hits or noise bursts.

    Args:
        fade_duration: Fade-in duration after reverse. Default 0.5.
    """

    def __init__(self, fade_duration: float = 0.5):
        self.fade_duration = fade_duration

    @property
    def effects(self) -> List[Effect]:
        return [
            Reverse(),
            Fade(fade_in=self.fade_duration),
            Reverb(reverberance=30, room_scale=50),
        ]


class LoopReady(CompositeEffect):
    """Prepare a loop for seamless looping.

    Normalizes and adds tiny fades to prevent clicks at loop points.
    """

    @property
    def effects(self) -> List[Effect]:
        return [
            Normalize(level=-1),
            Fade(fade_in=0.005),  # 5ms fade to prevent click
            Reverse(),
            Fade(fade_in=0.005),  # 5ms fade at end
            Reverse(),
        ]


# -----------------------------------------------------------------------------
# Mastering Effects
# -----------------------------------------------------------------------------


class BroadcastLimiter(CompositeEffect):
    """Broadcast-ready limiting and normalization.

    Ensures consistent levels suitable for broadcast.

    Args:
        target_level: Target peak level in dB. Default -1.
    """

    def __init__(self, target_level: float = -1):
        self.target_level = target_level

    @property
    def effects(self) -> List[Effect]:
        return [
            Gain(db=0, normalize=True, limiter=True),
            Normalize(level=self.target_level),
        ]


class WarmMaster(CompositeEffect):
    """Warm mastering preset.

    Adds subtle warmth and presence while normalizing.

    Args:
        warmth: Bass boost amount. Default 1.5.
    """

    def __init__(self, warmth: float = 1.5):
        self.warmth = warmth

    @property
    def effects(self) -> List[Effect]:
        return [
            Bass(gain=self.warmth, frequency=100),
            Treble(gain=0.5, frequency=8000),
            Gain(db=0, normalize=True, limiter=True),
            Normalize(level=-1),
        ]


class BrightMaster(CompositeEffect):
    """Bright mastering preset.

    Adds air and clarity while normalizing.

    Args:
        air: High frequency boost amount. Default 2.
    """

    def __init__(self, air: float = 2):
        self.air = air

    @property
    def effects(self) -> List[Effect]:
        return [
            Treble(gain=self.air, frequency=10000),
            Equalizer(frequency=4000, gain=1, width=2.0),
            Gain(db=0, normalize=True, limiter=True),
            Normalize(level=-1),
        ]


class LoudnessMaster(CompositeEffect):
    """Loudness-focused mastering preset.

    Maximizes perceived loudness while preventing clipping.

    Args:
        target_level: Target peak level. Default -0.3.
    """

    def __init__(self, target_level: float = -0.3):
        self.target_level = target_level

    @property
    def effects(self) -> List[Effect]:
        return [
            Bass(gain=2, frequency=80),
            Gain(db=0, normalize=True, limiter=True),
            Normalize(level=self.target_level),
        ]


# -----------------------------------------------------------------------------
# Cleanup Effects
# -----------------------------------------------------------------------------


class RemoveRumble(CompositeEffect):
    """Remove low frequency rumble.

    High-pass filter to remove subsonic content and rumble.

    Args:
        cutoff: High-pass cutoff frequency. Default 60.
    """

    def __init__(self, cutoff: float = 60):
        self.cutoff = cutoff

    @property
    def effects(self) -> List[Effect]:
        return [
            HighPass(frequency=self.cutoff, poles=2),
        ]


class RemoveHiss(CompositeEffect):
    """Reduce high frequency hiss.

    Low-pass filter to reduce tape hiss and high frequency noise.

    Args:
        cutoff: Low-pass cutoff frequency. Default 12000.
    """

    def __init__(self, cutoff: float = 12000):
        self.cutoff = cutoff

    @property
    def effects(self) -> List[Effect]:
        return [
            LowPass(frequency=self.cutoff),
            Treble(gain=-2, frequency=8000),
        ]


class RemoveHum(CompositeEffect):
    """Remove electrical hum (50Hz or 60Hz).

    Notch filter to remove mains hum and harmonics.

    Args:
        frequency: Hum frequency (50 for EU, 60 for US). Default 60.
    """

    def __init__(self, frequency: float = 60):
        self.frequency = frequency

    @property
    def effects(self) -> List[Effect]:
        return [
            BandReject(frequency=self.frequency, width=5),
            BandReject(frequency=self.frequency * 2, width=5),  # 2nd harmonic
            BandReject(frequency=self.frequency * 3, width=5),  # 3rd harmonic
        ]


class CleanVoice(CompositeEffect):
    """Clean up voice recording.

    Removes rumble, reduces mud, and normalizes.
    """

    @property
    def effects(self) -> List[Effect]:
        return [
            HighPass(frequency=80),
            Equalizer(frequency=250, gain=-2, width=1.5),  # Reduce mud
            Normalize(level=-3),
        ]


class TapeRestoration(CompositeEffect):
    """Basic tape restoration.

    Reduces hiss and rumble from tape recordings.
    """

    @property
    def effects(self) -> List[Effect]:
        return [
            HighPass(frequency=40),
            LowPass(frequency=14000),
            Treble(gain=-2, frequency=10000),
            Normalize(level=-3),
        ]


# -----------------------------------------------------------------------------
# Transition Effects
# -----------------------------------------------------------------------------


class FadeInOut(CompositeEffect):
    """Fade in and fade out.

    Applies fade in at start and fade out at end.

    Args:
        fade_in_secs: Fade in duration in seconds. Default 0.3.
        fade_out_secs: Fade out duration in seconds. Default 0.3.

    Note:
        Uses reverse trick for fade_out since sox fade_out is unreliable.
    """

    def __init__(self, fade_in_secs: float = 0.3, fade_out_secs: float = 0.3):
        self.fade_in_secs = fade_in_secs
        self.fade_out_secs = fade_out_secs

    @property
    def effects(self) -> List[Effect]:
        effects = []
        if self.fade_in_secs > 0:
            effects.append(Fade(fade_in=self.fade_in_secs))
        if self.fade_out_secs > 0:
            # Workaround: reverse, fade_in (which becomes fade_out), reverse back
            effects.extend([
                Reverse(),
                Fade(fade_in=self.fade_out_secs),
                Reverse(),
            ])
        return effects if effects else [Fade(fade_in=0.3)]


class CrossfadeReady(CompositeEffect):
    """Prepare audio for crossfading.

    Adds fade in/out and normalizes for consistent mixing.

    Args:
        fade_duration: Duration of both fades in seconds. Default 0.3.

    Note:
        Uses reverse trick for fade_out since sox fade_out is unreliable.
    """

    def __init__(self, fade_duration: float = 0.3):
        self.fade_duration = fade_duration

    @property
    def effects(self) -> List[Effect]:
        return [
            Normalize(level=-3),
            Fade(fade_in=self.fade_duration),
            # Workaround: reverse, fade_in, reverse for fade_out
            Reverse(),
            Fade(fade_in=self.fade_duration),
            Reverse(),
        ]


# Export all presets
__all__ = [
    # Voice
    "Chipmunk",
    "DeepVoice",
    "Robot",
    "HauntedVoice",
    "VocalClarity",
    "Whisper",
    # Lo-Fi
    "Telephone",
    "AMRadio",
    "Megaphone",
    "Underwater",
    "VinylWarmth",
    "LoFiHipHop",
    "Cassette",
    # Spatial
    "SmallRoom",
    "LargeHall",
    "Cathedral",
    "Bathroom",
    "Stadium",
    # Broadcast
    "Podcast",
    "RadioDJ",
    "Voiceover",
    "Intercom",
    "WalkieTalkie",
    # Musical
    "EightiesChorus",
    "DreamyPad",
    "SlowedReverb",
    "SlapbackEcho",
    "DubDelay",
    "JetFlanger",
    "ShoegazeWash",
    # Drum Loops
    "HalfTime",
    "DoubleTime",
    "DrumPunch",
    "DrumCrisp",
    "DrumFat",
    "Breakbeat",
    "VintageBreak",
    "DrumRoom",
    "GatedReverb",
    "DrumSlice",
    "ReverseCymbal",
    "LoopReady",
    # Mastering
    "BroadcastLimiter",
    "WarmMaster",
    "BrightMaster",
    "LoudnessMaster",
    # Cleanup
    "RemoveRumble",
    "RemoveHiss",
    "RemoveHum",
    "CleanVoice",
    "TapeRestoration",
    # Transition
    "FadeInOut",
    "CrossfadeReady",
]
