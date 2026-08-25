"""Volume and gain effects."""

from typing import List, Optional

from .base import Effect


# sox suggests a limiter gain "much less than 1"; 0.05 is its documented example.
DEFAULT_LIMITER_GAIN = 0.05


class Volume(Effect):
    """Adjust volume level.

    Args:
        db: Volume adjustment in decibels. Positive = louder, negative = quieter.
        limiter: Apply a limiter to prevent clipping on peaks (default: False).
        limiter_gain: Limiter gain to use when ``limiter`` is set. Should be
            much less than 1; defaults to 0.05. Setting this implies
            ``limiter=True``.

    Note:
        sox's ``vol`` effect takes the gain and its unit as *separate*
        arguments (``vol 6 dB``), and the limiter as a numeric third argument
        (``vol 6 dB 0.05``). Earlier versions emitted ``vol 6dB limiter``,
        which sox rejects outright.

    Example:
        >>> fx.Volume(db=3)                # Increase by 3dB
        >>> fx.Volume(db=-6)               # Decrease by 6dB
        >>> fx.Volume(db=6, limiter=True)  # Boost with limiting
        >>> fx.Volume(db=6, limiter_gain=0.02)
    """

    def __init__(
        self,
        db: float = 0,
        *,
        limiter: bool = False,
        limiter_gain: Optional[float] = None,
    ):
        if limiter_gain is not None and not 0 < limiter_gain < 1:
            raise ValueError("limiter_gain must be between 0 and 1 (exclusive)")
        self.db = db
        self.limiter = limiter or limiter_gain is not None
        self.limiter_gain = limiter_gain

    @property
    def name(self) -> str:
        return "vol"

    def to_args(self) -> List[str]:
        args = [str(self.db), "dB"]
        if self.limiter:
            gain = (
                self.limiter_gain
                if self.limiter_gain is not None
                else DEFAULT_LIMITER_GAIN
            )
            args.append(str(gain))
        return args


class Gain(Effect):
    """Apply gain with various options.

    Args:
        db: Gain in decibels.
        normalize: Normalize to 0dBFS before applying gain.
        limiter: Apply limiter to prevent clipping.
        balance: Balance channels (for stereo).

    Example:
        >>> fx.Gain(db=-3)
        >>> fx.Gain(db=0, normalize=True)  # Normalize only
    """

    def __init__(
        self,
        db: float = 0,
        *,
        normalize: bool = False,
        limiter: bool = False,
        balance: bool = False,
    ):
        self.db = db
        self.normalize = normalize
        self.limiter = limiter
        self.balance = balance

    @property
    def name(self) -> str:
        return "gain"

    def to_args(self) -> List[str]:
        args = []
        if self.normalize:
            args.append("-n")
        if self.limiter:
            args.append("-l")
        if self.balance:
            args.append("-B")
        args.append(str(self.db))
        return args


class Normalize(Effect):
    """Normalize audio to a target level.

    Args:
        level: Target level in dB (default: -1 dBFS).

    Example:
        >>> fx.Normalize()           # Normalize to -1 dBFS
        >>> fx.Normalize(level=-3)   # Normalize to -3 dBFS
    """

    def __init__(self, level: float = -1):
        self.level = level

    @property
    def name(self) -> str:
        return "norm"

    def to_args(self) -> List[str]:
        return [str(self.level)]
