"""Base classes for typed audio effects."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List

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
            if not key.startswith('_'):
                args.append(f"{key}={value!r}")
        return ", ".join(args)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._repr_args()})"


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


class PythonEffect(Effect):
    """Base class for custom Python-based sample processing.

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
        self,
        samples: "np.ndarray",
        sample_rate: int,
        channels: int
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

    For advanced users who implement effects in C or Cython and need
    to register them with sox.

    Subclasses should:
    1. Set _handler_ptr to the pointer returned by their Cython module
    2. Call register() once at startup before using the effect
    """

    _handler_ptr: int = None

    @classmethod
    def register(cls) -> None:
        """Register this effect's handler with sox.

        Must be called once before using the effect.
        """
        if cls._handler_ptr is None:
            raise ValueError(f"{cls.__name__}._handler_ptr is not set")

        from cysox import sox
        if hasattr(sox, 'register_effect_handler'):
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
