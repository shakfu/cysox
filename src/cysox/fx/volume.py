"""Volume and gain effects."""

from typing import List

from .base import Effect


class Volume(Effect):
    """Adjust volume level.

    Args:
        db: Volume adjustment in decibels. Positive = louder, negative = quieter.
        limiter: Apply limiter to prevent clipping (default: False).

    Example:
        >>> fx.Volume(db=3)          # Increase by 3dB
        >>> fx.Volume(db=-6)         # Decrease by 6dB
        >>> fx.Volume(db=6, limiter=True)  # Boost with limiting
    """

    def __init__(self, db: float = 0, *, limiter: bool = False):
        self.db = db
        self.limiter = limiter

    @property
    def name(self) -> str:
        return "vol"

    def to_args(self) -> List[str]:
        args = [f"{self.db}dB"]
        if self.limiter:
            args.append("limiter")
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
        balance: bool = False
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
