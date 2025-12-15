"""Reverb and spatial effects."""

from typing import List

from .base import Effect


class Reverb(Effect):
    """Add reverberation effect.

    Args:
        reverberance: Reverb time as percentage 0-100 (default: 50).
        hf_damping: High frequency damping percentage 0-100 (default: 50).
        room_scale: Room size percentage 0-100 (default: 100).
        stereo_depth: Stereo spread percentage 0-100 (default: 100).
        pre_delay: Pre-delay in milliseconds (default: 0).
        wet_gain: Wet signal gain in dB (default: 0).
        wet_only: Output only wet signal, no dry (default: False).

    Example:
        >>> fx.Reverb()                           # Default reverb
        >>> fx.Reverb(reverberance=80)            # Long reverb
        >>> fx.Reverb(room_scale=50, pre_delay=20)  # Small room with pre-delay
    """

    def __init__(
        self,
        reverberance: float = 50,
        hf_damping: float = 50,
        room_scale: float = 100,
        stereo_depth: float = 100,
        pre_delay: float = 0,
        wet_gain: float = 0,
        *,
        wet_only: bool = False
    ):
        self.reverberance = reverberance
        self.hf_damping = hf_damping
        self.room_scale = room_scale
        self.stereo_depth = stereo_depth
        self.pre_delay = pre_delay
        self.wet_gain = wet_gain
        self.wet_only = wet_only

    @property
    def name(self) -> str:
        return "reverb"

    def to_args(self) -> List[str]:
        args = []
        if self.wet_only:
            args.append("-w")
        args.extend([
            str(self.reverberance),
            str(self.hf_damping),
            str(self.room_scale),
            str(self.stereo_depth),
            str(self.pre_delay),
            str(self.wet_gain),
        ])
        return args


class Echo(Effect):
    """Add echo effect.

    Args:
        gain_in: Input gain (0-1, default: 0.8).
        gain_out: Output gain (0-1, default: 0.9).
        delays: List of delay times in milliseconds.
        decays: List of decay values (0-1) for each delay.

    Example:
        >>> fx.Echo(delays=[100], decays=[0.5])  # Single echo
        >>> fx.Echo(delays=[100, 200], decays=[0.6, 0.3])  # Multi-tap
    """

    def __init__(
        self,
        delays: List[float],
        decays: List[float],
        *,
        gain_in: float = 0.8,
        gain_out: float = 0.9
    ):
        if len(delays) != len(decays):
            raise ValueError("delays and decays must have same length")
        self.gain_in = gain_in
        self.gain_out = gain_out
        self.delays = delays
        self.decays = decays

    @property
    def name(self) -> str:
        return "echo"

    def to_args(self) -> List[str]:
        args = [str(self.gain_in), str(self.gain_out)]
        for delay, decay in zip(self.delays, self.decays):
            args.extend([str(delay), str(decay)])
        return args


class Chorus(Effect):
    """Add chorus effect.

    Args:
        gain_in: Input gain (0-1, default: 0.7).
        gain_out: Output gain (0-1, default: 0.9).
        delay: Base delay in milliseconds (default: 55).
        decay: Decay factor (default: 0.4).
        speed: Modulation speed in Hz (default: 0.25).
        depth: Modulation depth in milliseconds (default: 2).
        shape: Modulation shape 's' (sine) or 't' (triangle) (default: 's').

    Example:
        >>> fx.Chorus()  # Default chorus
        >>> fx.Chorus(depth=4, speed=0.5)  # Deeper, faster modulation
    """

    def __init__(
        self,
        *,
        gain_in: float = 0.7,
        gain_out: float = 0.9,
        delay: float = 55,
        decay: float = 0.4,
        speed: float = 0.25,
        depth: float = 2,
        shape: str = "s"
    ):
        if shape not in ("s", "t"):
            raise ValueError("shape must be 's' (sine) or 't' (triangle)")
        self.gain_in = gain_in
        self.gain_out = gain_out
        self.delay = delay
        self.decay = decay
        self.speed = speed
        self.depth = depth
        self.shape = shape

    @property
    def name(self) -> str:
        return "chorus"

    def to_args(self) -> List[str]:
        return [
            str(self.gain_in),
            str(self.gain_out),
            str(self.delay),
            str(self.decay),
            str(self.speed),
            str(self.depth),
            f"-{self.shape}",
        ]


class Flanger(Effect):
    """Add flanger effect.

    Args:
        delay: Base delay in milliseconds (default: 0).
        depth: Modulation depth in milliseconds (default: 2).
        regen: Regeneration/feedback percentage -95 to 95 (default: 0).
        width: Wet/dry mix percentage (default: 71).
        speed: Modulation speed in Hz (default: 0.5).
        shape: Modulation shape 'sine' or 'triangle' (default: 'sine').
        phase: Phase offset percentage for stereo (default: 25).
        interp: Interpolation 'linear' or 'quadratic' (default: 'linear').

    Example:
        >>> fx.Flanger()  # Default flanger
        >>> fx.Flanger(depth=5, speed=0.3, regen=50)  # Deeper effect
    """

    def __init__(
        self,
        *,
        delay: float = 0,
        depth: float = 2,
        regen: float = 0,
        width: float = 71,
        speed: float = 0.5,
        shape: str = "sine",
        phase: float = 25,
        interp: str = "linear"
    ):
        if shape not in ("sine", "triangle"):
            raise ValueError("shape must be 'sine' or 'triangle'")
        if interp not in ("linear", "quadratic"):
            raise ValueError("interp must be 'linear' or 'quadratic'")
        self.delay = delay
        self.depth = depth
        self.regen = regen
        self.width = width
        self.speed = speed
        self.shape = shape
        self.phase = phase
        self.interp = interp

    @property
    def name(self) -> str:
        return "flanger"

    def to_args(self) -> List[str]:
        return [
            str(self.delay),
            str(self.depth),
            str(self.regen),
            str(self.width),
            str(self.speed),
            self.shape,
            str(self.phase),
            self.interp,
        ]
