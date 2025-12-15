"""Equalization effects (bass, treble, equalizer)."""

from typing import List

from .base import Effect


class Bass(Effect):
    """Boost or cut bass frequencies.

    Args:
        gain: Amount to boost (positive) or cut (negative) in dB.
        frequency: Center frequency in Hz (default: 100).
        width: Filter width in octaves (default: 0.5).

    Example:
        >>> fx.Bass(gain=5)              # Boost bass by 5dB
        >>> fx.Bass(gain=-3, frequency=80)  # Cut at 80Hz
    """

    def __init__(
        self,
        gain: float,
        *,
        frequency: float = 100,
        width: float = 0.5
    ):
        self.gain = gain
        self.frequency = frequency
        self.width = width

    @property
    def name(self) -> str:
        return "bass"

    def to_args(self) -> List[str]:
        return [str(self.gain), str(self.frequency), str(self.width)]


class Treble(Effect):
    """Boost or cut treble frequencies.

    Args:
        gain: Amount to boost (positive) or cut (negative) in dB.
        frequency: Center frequency in Hz (default: 3000).
        width: Filter width in octaves (default: 0.5).

    Example:
        >>> fx.Treble(gain=3)             # Boost treble by 3dB
        >>> fx.Treble(gain=-2, frequency=4000)  # Cut at 4kHz
    """

    def __init__(
        self,
        gain: float,
        *,
        frequency: float = 3000,
        width: float = 0.5
    ):
        self.gain = gain
        self.frequency = frequency
        self.width = width

    @property
    def name(self) -> str:
        return "treble"

    def to_args(self) -> List[str]:
        return [str(self.gain), str(self.frequency), str(self.width)]


class Equalizer(Effect):
    """Peaking EQ filter at a specific frequency.

    Args:
        frequency: Center frequency in Hz.
        width: Filter width (Q factor or bandwidth in Hz).
        gain: Amount to boost (positive) or cut (negative) in dB.

    Example:
        >>> fx.Equalizer(frequency=1000, width=1, gain=3)  # Boost 1kHz
    """

    def __init__(self, frequency: float, width: float, gain: float):
        self.frequency = frequency
        self.width = width
        self.gain = gain

    @property
    def name(self) -> str:
        return "equalizer"

    def to_args(self) -> List[str]:
        return [str(self.frequency), str(self.width), str(self.gain)]
