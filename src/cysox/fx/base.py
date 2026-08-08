"""Base classes for typed audio effects."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    import numpy as np


class Effect(ABC):
    """Base class for all typed effects.

    Subclasses must implement:
    - name: The sox effect name
    - to_args(): Convert parameters to sox argument list
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """The sox effect name."""
        pass

    @abstractmethod
    def to_args(self) -> List[str]:
        """Convert effect parameters to sox argument list."""
        pass

    def _repr_args(self) -> str:
        """Return string representation of arguments for __repr__."""
        args = []
        for key, value in self.__dict__.items():
            if not key.startswith("_"):
                args.append(f"{key}={value!r}")
        return ", ".join(args)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._repr_args()})"


class Raw(Effect):
    """Escape hatch for any sox effect that has no typed class yet.

    The typed classes cover 27 of the effects this libsox build provides.
    ``Raw`` reaches the rest -- ``compand``, ``vad``, ``noisered``, ``synth``,
    ``stats``, ``phaser``, ``overdrive`` and friends -- without waiting for a
    wrapper, at the cost of the validation and autocomplete a typed class
    gives you. Arguments are passed to sox verbatim; each is str()-ed.

    Prefer a typed class where one exists. If you find yourself using ``Raw``
    for the same effect repeatedly, that effect is a good candidate for a
    proper class.

    Args:
        name: The sox effect name, as `sox_find_effect` knows it.
        *args: Effect arguments, in the order sox expects them.

    Raises:
        ValueError: If `name` is empty.

    Example:
        >>> # Dynamic range compression, which has no typed class
        >>> fx.Raw('compand', '0.3,1', '6:-70,-60,-20', -5, -90, 0.2)
        >>> # Voice activity detection, trimming silence from the front
        >>> fx.Raw('vad')
        >>> # Mix with a synthesised tone
        >>> fx.Raw('synth', 3, 'sine', 440)

    Note:
        An unknown effect name is reported by :func:`cysox.convert` when the
        chain is built, not here -- the effect table belongs to libsox.
    """

    def __init__(self, name: str, *args: object):
        if not name:
            raise ValueError("Raw effect requires a sox effect name")
        self._name = name
        self._args = [str(a) for a in args]

    @property
    def name(self) -> str:
        return self._name

    def to_args(self) -> List[str]:
        return list(self._args)

    def __repr__(self) -> str:
        parts = [repr(self._name)] + [repr(a) for a in self._args]
        return f"Raw({', '.join(parts)})"


class CompositeEffect(Effect):
    """Base class for effects that combine multiple sox effects.

    Subclasses must implement the `effects` property returning a list
    of Effect instances to be applied in sequence.

    Example:
        class WarmReverb(CompositeEffect):
            def __init__(self, decay=60):
                self.decay = decay

            @property
            def effects(self):
                return [
                    HighPass(frequency=80),
                    Reverb(reverberance=self.decay),
                    Volume(db=-2),
                ]
    """

    @property
    @abstractmethod
    def effects(self) -> List[Effect]:
        """Return list of constituent effects."""
        pass

    @property
    def name(self) -> str:
        return self.__class__.__name__

    def to_args(self) -> List[str]:
        raise TypeError(
            f"CompositeEffect '{self.name}' must be expanded, not converted to args. "
            "Use expand_effects() to get the list of constituent effects."
        )

    def __repr__(self) -> str:
        args = self._repr_args()
        effects_repr = ", ".join(repr(e) for e in self.effects)
        if args:
            return f"{self.__class__.__name__}({args}) -> [{effects_repr}]"
        return f"{self.__class__.__name__}() -> [{effects_repr}]"


class PythonEffect(Effect):
    """Base class for custom Python-based sample processing.

    .. warning::
        Experimental. Not yet supported by ``convert()`` or ``play()``.
        Use ``stream()`` for custom Python sample processing.

    Subclasses must implement the `process()` method which receives
    samples as a numpy array and returns processed samples.

    Note: Python effects require numpy and run outside the sox pipeline,
    making them slower than native sox effects. Use for custom DSP that
    sox doesn't support.

    Example:
        class BitCrusher(PythonEffect):
            def __init__(self, bits=8):
                self.bits = bits

            def process(self, samples, sample_rate, channels):
                levels = 2 ** self.bits
                return np.round(samples * levels) / levels
    """

    @property
    def name(self) -> str:
        return self.__class__.__name__

    def to_args(self) -> List[str]:
        raise TypeError(
            f"PythonEffect '{self.name}' cannot be converted to sox args. "
            "It will be processed separately using the process() method."
        )

    @abstractmethod
    def process(
        self, samples: "np.ndarray", sample_rate: int, channels: int
    ) -> "np.ndarray":
        """Process audio samples.

        Args:
            samples: Input samples as numpy array of shape (n_samples,) for mono
                    or (n_samples, channels) for multi-channel.
            sample_rate: Sample rate in Hz.
            channels: Number of audio channels.

        Returns:
            Processed samples as numpy array with same shape as input.
        """
        pass


class CEffect(Effect):
    """Base class for custom C-level effects.

    .. warning::
        Experimental. Effect registration is not yet implemented in the
        low-level API. This class defines the intended interface for
        future C-level effect support.

    For advanced users who implement effects in C or Cython and need
    to register them with sox.

    Subclasses should:
    1. Set _handler_ptr to the pointer returned by their Cython module
    2. Call register() once at startup before using the effect
    """

    _handler_ptr: Optional[int] = None

    @classmethod
    def register(cls) -> None:
        """Register this effect's handler with sox.

        Must be called once before using the effect.
        """
        if cls._handler_ptr is None:
            raise ValueError(f"{cls.__name__}._handler_ptr is not set")

        from cysox import sox

        if hasattr(sox, "register_effect_handler"):
            sox.register_effect_handler(cls._handler_ptr)
        else:
            raise NotImplementedError(
                "Custom C effect registration not yet implemented in low-level API"
            )

    @property
    @abstractmethod
    def name(self) -> str:
        """The registered effect name."""
        pass

    @abstractmethod
    def to_args(self) -> List[str]:
        """Convert parameters to sox argument list."""
        pass
