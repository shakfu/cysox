"""Typed audio effect classes for cysox.

This module provides typed effect classes that can be used with
cysox.convert() and other high-level functions.

Example:
    >>> import cysox
    >>> from cysox import fx
    >>>
    >>> cysox.convert('input.wav', 'output.mp3', effects=[
    ...     fx.Volume(db=3),
    ...     fx.Bass(gain=5),
    ...     fx.Reverb(),
    ... ])
"""

# Base classes
from .base import (
    Effect,
    CompositeEffect,
    PythonEffect,
    CEffect,
)

# Volume and gain effects
from .volume import (
    Volume,
    Gain,
    Normalize,
)

# Equalization effects
from .eq import (
    Bass,
    Treble,
    Equalizer,
)

# Filter effects
from .filter import (
    HighPass,
    LowPass,
    BandPass,
    BandReject,
)

# Reverb and spatial effects
from .reverb import (
    Reverb,
    Echo,
    Chorus,
    Flanger,
)

# Time-based effects
from .time import (
    Trim,
    Pad,
    Speed,
    Tempo,
    Pitch,
    Reverse,
    Fade,
    Repeat,
)

# Conversion effects
from .convert import (
    Rate,
    Channels,
    Remix,
    Dither,
)

# Composite presets
from .presets import (
    # Voice
    Chipmunk,
    DeepVoice,
    Robot,
    HauntedVoice,
    VocalClarity,
    Whisper,
    # Lo-Fi
    Telephone,
    AMRadio,
    Megaphone,
    Underwater,
    VinylWarmth,
    LoFiHipHop,
    Cassette,
    # Spatial
    SmallRoom,
    LargeHall,
    Cathedral,
    Bathroom,
    Stadium,
    # Broadcast
    Podcast,
    RadioDJ,
    Voiceover,
    Intercom,
    WalkieTalkie,
    # Musical
    EightiesChorus,
    DreamyPad,
    SlowedReverb,
    SlapbackEcho,
    DubDelay,
    JetFlanger,
    ShoegazeWash,
    # Drum Loops
    HalfTime,
    DoubleTime,
    DrumPunch,
    DrumCrisp,
    DrumFat,
    Breakbeat,
    VintageBreak,
    DrumRoom,
    GatedReverb,
    DrumSlice,
    ReverseCymbal,
    LoopReady,
    # Mastering
    BroadcastLimiter,
    WarmMaster,
    BrightMaster,
    LoudnessMaster,
    # Cleanup
    RemoveRumble,
    RemoveHiss,
    RemoveHum,
    CleanVoice,
    TapeRestoration,
    # Transition
    FadeInOut,
    CrossfadeReady,
)

__all__ = [
    # Base
    "Effect",
    "CompositeEffect",
    "PythonEffect",
    "CEffect",
    # Volume
    "Volume",
    "Gain",
    "Normalize",
    # EQ
    "Bass",
    "Treble",
    "Equalizer",
    # Filter
    "HighPass",
    "LowPass",
    "BandPass",
    "BandReject",
    # Reverb/Spatial
    "Reverb",
    "Echo",
    "Chorus",
    "Flanger",
    # Time
    "Trim",
    "Pad",
    "Speed",
    "Tempo",
    "Pitch",
    "Reverse",
    "Fade",
    "Repeat",
    # Convert
    "Rate",
    "Channels",
    "Remix",
    "Dither",
    # Presets - Voice
    "Chipmunk",
    "DeepVoice",
    "Robot",
    "HauntedVoice",
    "VocalClarity",
    "Whisper",
    # Presets - Lo-Fi
    "Telephone",
    "AMRadio",
    "Megaphone",
    "Underwater",
    "VinylWarmth",
    "LoFiHipHop",
    "Cassette",
    # Presets - Spatial
    "SmallRoom",
    "LargeHall",
    "Cathedral",
    "Bathroom",
    "Stadium",
    # Presets - Broadcast
    "Podcast",
    "RadioDJ",
    "Voiceover",
    "Intercom",
    "WalkieTalkie",
    # Presets - Musical
    "EightiesChorus",
    "DreamyPad",
    "SlowedReverb",
    "SlapbackEcho",
    "DubDelay",
    "JetFlanger",
    "ShoegazeWash",
    # Presets - Drum Loops
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
    # Presets - Mastering
    "BroadcastLimiter",
    "WarmMaster",
    "BrightMaster",
    "LoudnessMaster",
    # Presets - Cleanup
    "RemoveRumble",
    "RemoveHiss",
    "RemoveHum",
    "CleanVoice",
    "TapeRestoration",
    # Presets - Transition
    "FadeInOut",
    "CrossfadeReady",
]
