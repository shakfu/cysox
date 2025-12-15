"""Filter effects (highpass, lowpass, bandpass, etc.)."""

from typing import List

from .base import Effect


class HighPass(Effect):
    """High-pass filter (removes low frequencies).

    Args:
        frequency: Cutoff frequency in Hz.
        poles: Filter order, 1 or 2 (default: 2). Higher = steeper rolloff.

    Example:
        >>> fx.HighPass(frequency=80)     # Remove rumble below 80Hz
        >>> fx.HighPass(frequency=200, poles=1)  # Gentle rolloff
    """

    def __init__(self, frequency: float, *, poles: int = 2):
        if poles not in (1, 2):
            raise ValueError("poles must be 1 or 2")
        self.frequency = frequency
        self.poles = poles

    @property
    def name(self) -> str:
        return "highpass"

    def to_args(self) -> List[str]:
        return [f"-{self.poles}", str(self.frequency)]


class LowPass(Effect):
    """Low-pass filter (removes high frequencies).

    Args:
        frequency: Cutoff frequency in Hz.
        poles: Filter order, 1 or 2 (default: 2). Higher = steeper rolloff.

    Example:
        >>> fx.LowPass(frequency=8000)    # Remove highs above 8kHz
        >>> fx.LowPass(frequency=4000, poles=1)  # Gentle rolloff
    """

    def __init__(self, frequency: float, *, poles: int = 2):
        if poles not in (1, 2):
            raise ValueError("poles must be 1 or 2")
        self.frequency = frequency
        self.poles = poles

    @property
    def name(self) -> str:
        return "lowpass"

    def to_args(self) -> List[str]:
        return [f"-{self.poles}", str(self.frequency)]


class BandPass(Effect):
    """Band-pass filter (passes frequencies within a range).

    Args:
        frequency: Center frequency in Hz.
        width: Filter width. Interpretation depends on width_type.
        width_type: 'q' for Q-factor, 'h' for Hz, 'o' for octaves (default: 'q').
        constant_skirt: Use constant skirt gain (default: False).

    Example:
        >>> fx.BandPass(frequency=1000, width=2)  # Q=2 bandpass at 1kHz
    """

    def __init__(
        self,
        frequency: float,
        width: float,
        *,
        width_type: str = "q",
        constant_skirt: bool = False
    ):
        if width_type not in ("q", "h", "o"):
            raise ValueError("width_type must be 'q', 'h', or 'o'")
        self.frequency = frequency
        self.width = width
        self.width_type = width_type
        self.constant_skirt = constant_skirt

    @property
    def name(self) -> str:
        return "bandpass"

    def to_args(self) -> List[str]:
        args = []
        if self.constant_skirt:
            args.append("-c")
        args.append(str(self.frequency))
        args.append(f"{self.width}{self.width_type}")
        return args


class BandReject(Effect):
    """Band-reject (notch) filter.

    Args:
        frequency: Center frequency in Hz.
        width: Filter width. Interpretation depends on width_type.
        width_type: 'q' for Q-factor, 'h' for Hz, 'o' for octaves (default: 'q').

    Example:
        >>> fx.BandReject(frequency=60, width=10)  # Remove 60Hz hum
    """

    def __init__(
        self,
        frequency: float,
        width: float,
        *,
        width_type: str = "q"
    ):
        if width_type not in ("q", "h", "o"):
            raise ValueError("width_type must be 'q', 'h', or 'o'")
        self.frequency = frequency
        self.width = width
        self.width_type = width_type

    @property
    def name(self) -> str:
        return "bandreject"

    def to_args(self) -> List[str]:
        return [str(self.frequency), f"{self.width}{self.width_type}"]
