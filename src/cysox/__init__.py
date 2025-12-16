"""cysox - A Cython wrapper for libsox.

High-level API (recommended):
    >>> import cysox
    >>> from cysox import fx
    >>>
    >>> # Get file info
    >>> info = cysox.info('audio.wav')
    >>>
    >>> # Convert with effects
    >>> cysox.convert('input.wav', 'output.mp3', effects=[
    ...     fx.Volume(db=3),
    ...     fx.Reverb(),
    ... ])
    >>>
    >>> # Stream samples
    >>> for chunk in cysox.stream('audio.wav'):
    ...     process(chunk)
    >>>
    >>> # Play audio
    >>> cysox.play('audio.wav')

Low-level API (power users):
    >>> from cysox import sox
    >>> sox.init()
    >>> f = sox.Format('audio.wav')
    >>> # ... low-level operations ...
    >>> sox.quit()
"""

# High-level API (auto-initializing)
from .audio import (
    info,
    convert,
    stream,
    play,
    concat,
)

# Effects module
from . import fx

# Low-level API (explicit init/quit required)
from . import sox

# get libsox version via cysox.sox.version()
__version__ = "0.1.3"


__all__ = [
    # High-level functions
    "info",
    "convert",
    "stream",
    "play",
    # Modules
    "fx",
    "sox",
    # Version
    "__version__",
]
