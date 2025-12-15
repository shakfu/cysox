"""Format conversion effects (rate, channels, bits)."""

from typing import List, Optional

from .base import Effect


class Rate(Effect):
    """Resample to a different sample rate.

    Args:
        sample_rate: Target sample rate in Hz.
        quality: Resampling quality - 'quick', 'low', 'medium', 'high',
                or 'very-high' (default: 'high').

    Example:
        >>> fx.Rate(sample_rate=48000)
        >>> fx.Rate(sample_rate=44100, quality='very-high')
    """

    QUALITY_FLAGS = {
        "quick": "-q",
        "low": "-l",
        "medium": "-m",
        "high": "-h",
        "very-high": "-v",
    }

    def __init__(self, sample_rate: int, *, quality: str = "high"):
        if quality not in self.QUALITY_FLAGS:
            raise ValueError(
                f"quality must be one of: {', '.join(self.QUALITY_FLAGS.keys())}"
            )
        self.sample_rate = sample_rate
        self.quality = quality

    @property
    def name(self) -> str:
        return "rate"

    def to_args(self) -> List[str]:
        return [self.QUALITY_FLAGS[self.quality], str(self.sample_rate)]


class Channels(Effect):
    """Change the number of audio channels.

    Args:
        channels: Target number of channels (1=mono, 2=stereo, etc.).

    Example:
        >>> fx.Channels(channels=1)   # Convert to mono
        >>> fx.Channels(channels=2)   # Convert to stereo
    """

    def __init__(self, channels: int):
        if channels < 1:
            raise ValueError("channels must be at least 1")
        self.channels = channels

    @property
    def name(self) -> str:
        return "channels"

    def to_args(self) -> List[str]:
        return [str(self.channels)]


class Remix(Effect):
    """Remix channels with custom mix specification.

    Args:
        mix: Channel mix specification. Each output channel is specified
             as a string like "1,2" (mix channels 1 and 2) or "1v0.5,2v0.5"
             (mix with volume adjustment). Use "-" for silence.

    Example:
        >>> fx.Remix(mix=["1,2"])           # Mono mixdown
        >>> fx.Remix(mix=["1", "2"])        # Keep stereo as-is
        >>> fx.Remix(mix=["2", "1"])        # Swap L/R
        >>> fx.Remix(mix=["1v0.5,2v0.5"])   # Mono with equal mix
    """

    def __init__(self, mix: List[str]):
        self.mix = mix

    @property
    def name(self) -> str:
        return "remix"

    def to_args(self) -> List[str]:
        return self.mix


class Dither(Effect):
    """Apply dithering for bit-depth reduction.

    Args:
        type: Dither type - 'rectangular', 'triangular', 'gaussian',
              or 'shaped' (default: 'shaped').
        precision: Target precision in bits (optional).

    Example:
        >>> fx.Dither()                      # Default shaped dither
        >>> fx.Dither(type='triangular')     # TPDF dither
    """

    def __init__(
        self,
        *,
        type: str = "shaped",
        precision: Optional[int] = None
    ):
        valid_types = ("rectangular", "triangular", "gaussian", "shaped")
        if type not in valid_types:
            raise ValueError(f"type must be one of: {', '.join(valid_types)}")
        self.type = type
        self.precision = precision

    @property
    def name(self) -> str:
        return "dither"

    def to_args(self) -> List[str]:
        args = [f"-{self.type[0]}"]  # First letter
        if self.precision is not None:
            args.extend(["-p", str(self.precision)])
        return args
