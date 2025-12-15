"""Time-based effects (trim, pad, speed, tempo, etc.)."""

from typing import List, Optional

from .base import Effect


class Trim(Effect):
    """Extract a portion of the audio.

    Specify either `end` or `duration`, not both.

    Args:
        start: Start time in seconds (default: 0).
        end: End time in seconds (mutually exclusive with duration).
        duration: Duration in seconds (mutually exclusive with end).

    Example:
        >>> fx.Trim(start=1.5, end=10.0)    # From 1.5s to 10s
        >>> fx.Trim(start=5.0)              # From 5s to end
        >>> fx.Trim(end=30.0)               # First 30 seconds
        >>> fx.Trim(start=0, duration=10)   # First 10 seconds
    """

    def __init__(
        self,
        start: float = 0,
        end: Optional[float] = None,
        *,
        duration: Optional[float] = None
    ):
        if end is not None and duration is not None:
            raise ValueError("Cannot specify both 'end' and 'duration'")
        self.start = start
        self.end = end
        self.duration = duration

    @property
    def name(self) -> str:
        return "trim"

    def to_args(self) -> List[str]:
        args = [str(self.start)]
        if self.duration is not None:
            args.append(str(self.duration))
        elif self.end is not None:
            args.append(f"={self.end}")
        return args


class Pad(Effect):
    """Add silence to the beginning and/or end.

    Args:
        before: Seconds of silence to add at the beginning (default: 0).
        after: Seconds of silence to add at the end (default: 0).

    Example:
        >>> fx.Pad(before=1.0)           # Add 1s silence at start
        >>> fx.Pad(after=2.0)            # Add 2s silence at end
        >>> fx.Pad(before=0.5, after=1.0)  # Add both
    """

    def __init__(self, before: float = 0, after: float = 0):
        self.before = before
        self.after = after

    @property
    def name(self) -> str:
        return "pad"

    def to_args(self) -> List[str]:
        return [str(self.before), str(self.after)]


class Speed(Effect):
    """Change playback speed (affects pitch).

    Args:
        factor: Speed multiplier. 2.0 = double speed (higher pitch),
                0.5 = half speed (lower pitch).

    Example:
        >>> fx.Speed(factor=2.0)   # Double speed, octave up
        >>> fx.Speed(factor=0.5)   # Half speed, octave down
    """

    def __init__(self, factor: float):
        if factor <= 0:
            raise ValueError("factor must be positive")
        self.factor = factor

    @property
    def name(self) -> str:
        return "speed"

    def to_args(self) -> List[str]:
        return [str(self.factor)]


class Tempo(Effect):
    """Change tempo without affecting pitch.

    Args:
        factor: Tempo multiplier. 2.0 = double tempo, 0.5 = half tempo.
        audio_type: Optimize for 'm' (music), 's' (speech), or 'l' (linear).
                   Default: None (auto-detect).
        quick: Use quicker, lower-quality algorithm (default: False).

    Example:
        >>> fx.Tempo(factor=1.5)                    # 50% faster
        >>> fx.Tempo(factor=0.8, audio_type='s')   # Slower speech
    """

    def __init__(
        self,
        factor: float,
        *,
        audio_type: Optional[str] = None,
        quick: bool = False
    ):
        if factor <= 0:
            raise ValueError("factor must be positive")
        if audio_type is not None and audio_type not in ("m", "s", "l"):
            raise ValueError("audio_type must be 'm', 's', or 'l'")
        self.factor = factor
        self.audio_type = audio_type
        self.quick = quick

    @property
    def name(self) -> str:
        return "tempo"

    def to_args(self) -> List[str]:
        args = []
        if self.quick:
            args.append("-q")
        if self.audio_type:
            args.append(f"-{self.audio_type}")
        args.append(str(self.factor))
        return args


class Pitch(Effect):
    """Change pitch without affecting tempo.

    Args:
        cents: Pitch shift in cents (100 cents = 1 semitone).
        quick: Use quicker, lower-quality algorithm (default: False).

    Example:
        >>> fx.Pitch(cents=100)    # Up one semitone
        >>> fx.Pitch(cents=-200)   # Down two semitones
    """

    def __init__(self, cents: float, *, quick: bool = False):
        self.cents = cents
        self.quick = quick

    @property
    def name(self) -> str:
        return "pitch"

    def to_args(self) -> List[str]:
        args = []
        if self.quick:
            args.append("-q")
        args.append(str(self.cents))
        return args


class Reverse(Effect):
    """Reverse the audio.

    Example:
        >>> fx.Reverse()
    """

    @property
    def name(self) -> str:
        return "reverse"

    def to_args(self) -> List[str]:
        return []


class Fade(Effect):
    """Apply fade in and/or fade out.

    Args:
        fade_in: Fade-in duration in seconds (default: 0).
        fade_out: Fade-out duration in seconds (default: 0).
        type: Fade curve type - 'q' (quarter sine), 'h' (half sine),
              't' (linear), 'l' (logarithmic), 'p' (parabola) (default: 't').

    Example:
        >>> fx.Fade(fade_in=0.5)                    # 0.5s fade in
        >>> fx.Fade(fade_out=2.0)                   # 2s fade out
        >>> fx.Fade(fade_in=1.0, fade_out=1.0, type='l')  # Log fades
    """

    def __init__(
        self,
        fade_in: float = 0,
        fade_out: float = 0,
        *,
        type: str = "t"
    ):
        if type not in ("q", "h", "t", "l", "p"):
            raise ValueError("type must be 'q', 'h', 't', 'l', or 'p'")
        self.fade_in = fade_in
        self.fade_out = fade_out
        self.type = type

    @property
    def name(self) -> str:
        return "fade"

    def to_args(self) -> List[str]:
        # sox fade type fade_in [stop_time [fade_out]]
        args = [self.type, str(self.fade_in)]
        if self.fade_out > 0:
            # Using 0 for stop_time means end of file
            args.extend(["0", str(self.fade_out)])
        return args


class Repeat(Effect):
    """Repeat the audio.

    Args:
        count: Number of times to repeat (in addition to original).

    Example:
        >>> fx.Repeat(count=2)  # Play 3 times total
    """

    def __init__(self, count: int):
        if count < 1:
            raise ValueError("count must be at least 1")
        self.count = count

    @property
    def name(self) -> str:
        return "repeat"

    def to_args(self) -> List[str]:
        return [str(self.count)]
