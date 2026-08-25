"""High-level audio processing API for cysox.

This module provides a simplified, Pythonic interface for audio processing.
It handles initialization automatically and provides convenient functions
for common operations.

Example:
    >>> import cysox
    >>> from cysox import fx
    >>>
    >>> # Get file info
    >>> info = cysox.info('audio.wav')
    >>> print(f"Duration: {info.duration:.2f}s")
    >>>
    >>> # Convert with effects
    >>> cysox.convert('input.wav', 'output.mp3', effects=[
    ...     fx.Normalize(),
    ...     fx.Fade(fade_in=0.5),
    ... ])
"""

import os
import tempfile
from pathlib import Path
from types import TracebackType
from typing import Callable, Dict, Iterator, List, Optional, Union

from . import sox
from .fx.base import Effect, CompositeEffect, PythonEffect

# Type alias for progress callbacks.
# Receives progress (0.0 to 1.0), returns True to continue or False to cancel.
ProgressCallback = Callable[[float], bool]


class CancelledError(Exception):
    """Raised when an operation is cancelled via a progress callback."""

    pass


class AudioInfo:
    """Audio file metadata returned by :func:`info`.

    Supports both attribute access (``info.sample_rate``) and dict-style
    access (``info['sample_rate']``) for backwards compatibility.
    """

    __slots__ = (
        "path",
        "format",
        "duration",
        "sample_rate",
        "channels",
        "bits_per_sample",
        "samples",
        "encoding",
    )

    def __init__(
        self,
        path: str,
        format: str,
        duration: float,
        sample_rate: int,
        channels: int,
        bits_per_sample: int,
        samples: int,
        encoding: str,
    ):
        self.path = path
        self.format = format
        self.duration = duration
        self.sample_rate = sample_rate
        self.channels = channels
        self.bits_per_sample = bits_per_sample
        self.samples = samples
        self.encoding = encoding

    def __getitem__(self, key: str):
        """Dict-style access for backwards compatibility."""
        try:
            return getattr(self, key)
        except AttributeError:
            raise KeyError(key)

    def __contains__(self, key: str) -> bool:
        return key in self.__slots__

    def __repr__(self) -> str:
        return (
            f"AudioInfo(path={self.path!r}, format={self.format!r}, "
            f"duration={self.duration:.2f}, sample_rate={self.sample_rate}, "
            f"channels={self.channels}, bits_per_sample={self.bits_per_sample}, "
            f"samples={self.samples}, encoding={self.encoding!r})"
        )

    def __eq__(self, other: object) -> bool:
        if isinstance(other, AudioInfo):
            return all(getattr(self, k) == getattr(other, k) for k in self.__slots__)
        return NotImplemented

    def keys(self):
        """Dict-like keys for compatibility."""
        return self.__slots__

    def values(self):
        """Dict-like values for compatibility."""
        return tuple(getattr(self, k) for k in self.__slots__)

    def items(self):
        """Dict-like items for compatibility."""
        return tuple((k, getattr(self, k)) for k in self.__slots__)


def _ensure_init() -> None:
    """Ensure sox is initialized (called automatically).

    Delegates to :meth:`SoxRuntime.ensure_init` which handles
    initialization, idempotency, locking, and atexit registration
    in one place.
    """
    sox._runtime.ensure_init()


def _expand_effects(effects: List[Effect]) -> List[Effect]:
    """Expand CompositeEffects into their constituent effects."""
    expanded = []
    for effect in effects:
        if isinstance(effect, CompositeEffect):
            expanded.extend(_expand_effects(effect.effects))
        else:
            expanded.append(effect)
    return expanded


_SOX_BUFFER_SIZE = 8192  # libsox's default internal buffer size


def _make_flow_callback(total_samples, user_callback):
    """Create a flow_effects callback that estimates progress.

    Args:
        total_samples: Total number of samples to process (for estimation).
        user_callback: User's progress callback (progress: float) -> bool.

    Returns:
        Tuple of (callback, state_dict) for use with chain.flow_effects().
    """
    estimated_buffers = max(1, total_samples // _SOX_BUFFER_SIZE)
    state = {"count": 0, "cancelled": False}

    def callback(all_done, _user_data):
        state["count"] += 1
        if all_done:
            progress = 1.0
        else:
            progress = min(state["count"] / estimated_buffers, 0.99)

        result = user_callback(progress)
        if result is False:
            state["cancelled"] = True
            return False
        return True

    return callback, state


def _predict_chain_output(effects: List[Effect], in_signal) -> tuple:
    """Rate and channel count the effects chain will hand to the output file.

    Only effects that redefine the stream's output format are counted. ``speed``,
    ``pitch`` and ``tempo`` also move the rate mid-chain, but they do so as an
    implementation detail - sox expects the original rate to be restored
    afterwards - so counting them would change the output file's rate and alter
    the pitch of the result. They are deliberately excluded.

    Returns:
        ``(rate, channels)`` as floats/ints.
    """
    rate = in_signal.rate
    channels = in_signal.channels
    for effect in effects:
        name = effect.name
        if name == "rate":
            # Rate.to_args() is [quality_flag, rate]; the rate is always last.
            rate = float(effect.to_args()[-1])
        elif name == "channels":
            channels = int(effect.to_args()[0])
        elif name == "remix":
            # One argument per output channel.
            channels = len(effect.to_args())
    return rate, channels


def _check_flow_outcome(flow_state, label: str) -> None:
    """Re-raise whatever a flow callback reported out of band.

    libsox collapses "the callback cancelled", "the callback raised" and "a
    length-limiting effect ended the chain" into a single SOX_EOF return, so
    the callback's own recorded state is the only way to tell them apart.
    Called on both the success and the failure path for that reason.
    """
    if flow_state["cancelled"]:
        raise CancelledError(f"{label} cancelled by progress callback")
    exc_info = sox.get_last_callback_exception()
    if exc_info is not None:
        tb = exc_info[2] if isinstance(exc_info[2], TracebackType) else None
        raise exc_info[1].with_traceback(tb)


def info(path: Union[str, Path]) -> AudioInfo:
    """Get audio file metadata.

    Args:
        path: Path to audio file.

    Returns:
        AudioInfo named tuple with fields:
        - path: Original path
        - format: File format (e.g., 'wav', 'mp3')
        - duration: Duration in seconds
        - sample_rate: Sample rate in Hz
        - channels: Number of channels
        - bits_per_sample: Bits per sample
        - samples: Total number of samples
        - encoding: Encoding type

        Supports both attribute access (``info.sample_rate``) and
        dict-style access (``info['sample_rate']``).

    Example:
        >>> info = cysox.info('audio.wav')
        >>> print(f"Duration: {info.duration:.2f}s")
        >>> print(f"Sample rate: {info.sample_rate} Hz")
    """
    _ensure_init()

    path = str(path)
    with sox.Format(path) as f:
        signal = f.signal
        encoding = f.encoding

        # Calculate duration
        if signal.length and signal.rate and signal.channels:
            duration = signal.length / (signal.rate * signal.channels)
        else:
            duration = 0.0

        return AudioInfo(
            path=path,
            format=f.filetype or "",
            duration=duration,
            sample_rate=int(signal.rate) if signal.rate else 0,
            channels=signal.channels or 0,
            bits_per_sample=encoding.bits_per_sample if encoding else 0,
            samples=signal.length or 0,
            encoding=_encoding_name(encoding.encoding) if encoding else "",
        )
    raise AssertionError("unreachable")


# Friendly names keyed by the *symbolic* libsox enum member, never by its
# integer value. sox_encoding_t's values are assigned by whichever libsox is
# linked, and they are not stable: SoX_ng inserted MP1 and MP2, moving MP3 from
# 22 to 24 and shifting everything after it. A hardcoded index table silently
# mislabels every encoding past the insertion point - info() reported an MP3
# file as 'amr-wb'.
_ENCODING_NAMES_BY_SYMBOL: Dict[str, str] = {
    "SOX_ENCODING_UNKNOWN": "unknown",
    "SOX_ENCODING_SIGN2": "signed-integer",
    "SOX_ENCODING_UNSIGNED": "unsigned-integer",
    "SOX_ENCODING_FLOAT": "float",
    "SOX_ENCODING_FLOAT_TEXT": "float-text",
    "SOX_ENCODING_FLAC": "flac",
    "SOX_ENCODING_HCOM": "hcom",
    "SOX_ENCODING_WAVPACK": "wavpack",
    "SOX_ENCODING_WAVPACKF": "wavpackf",
    "SOX_ENCODING_ULAW": "ulaw",
    "SOX_ENCODING_ALAW": "alaw",
    "SOX_ENCODING_G721": "g721",
    "SOX_ENCODING_G723": "g723",
    "SOX_ENCODING_CL_ADPCM": "cl-adpcm",
    "SOX_ENCODING_CL_ADPCM16": "cl-adpcm16",
    "SOX_ENCODING_MS_ADPCM": "ms-adpcm",
    "SOX_ENCODING_IMA_ADPCM": "ima-adpcm",
    "SOX_ENCODING_OKI_ADPCM": "oki-adpcm",
    "SOX_ENCODING_DPCM": "dpcm",
    "SOX_ENCODING_DWVW": "dwvw",
    "SOX_ENCODING_DWVWN": "dwvwn",
    "SOX_ENCODING_GSM": "gsm",
    "SOX_ENCODING_MP3": "mp3",
    "SOX_ENCODING_VORBIS": "vorbis",
    "SOX_ENCODING_AMR_WB": "amr-wb",
    "SOX_ENCODING_AMR_NB": "amr-nb",
    "SOX_ENCODING_CVSD": "cvsd",
    "SOX_ENCODING_LPC10": "lpc10",
    "SOX_ENCODING_OPUS": "opus",
}


def _build_encoding_names() -> Dict[int, str]:
    """Map each libsox encoding value to its cysox name.

    The values come from ``sox.sox_encoding_t``, which Cython compiles from
    the linked ``sox.h`` - so they are whatever this build of libsox actually
    uses. ``SOX_ENCODINGS`` is an end-of-list marker, not an encoding, and is
    skipped.
    """
    names: Dict[int, str] = {}
    for member in sox.sox_encoding_t:
        if member.name == "SOX_ENCODINGS":
            continue
        friendly = _ENCODING_NAMES_BY_SYMBOL.get(member.name)
        if friendly is not None:
            names[int(member.value)] = friendly
    return names


_ENCODING_NAMES: Dict[int, str] = _build_encoding_names()

# Reverse map for the ``encoding=`` argument of convert(). "unknown" is
# excluded deliberately - it is a read-side result, not something to request.
_ENCODING_TYPES: Dict[str, int] = {
    name: value for value, name in _ENCODING_NAMES.items() if name != "unknown"
}


def _encoding_name(encoding_type: int) -> str:
    """Convert encoding type constant to string.

    Maps libsox encoding enum values (indices into sox.ENCODINGS) to
    human-readable names.
    """
    return _ENCODING_NAMES.get(encoding_type, "unknown")


def _supports(path: str, enc_type: int, bits: int) -> bool:
    """Whether the handler for ``path`` can write this encoding/bits pair.

    Both halves matter: a format may accept the encoding type at one width
    and reject it at another (WAV takes float at 32 bits but not at 16).
    """
    try:
        probe = sox.EncodingInfo(encoding=enc_type, bits_per_sample=bits)
        return sox.format_supports_encoding(path, probe)
    except Exception:
        # Unknown extension or unloadable handler - let libsox decide.
        return False


def _build_output_encoding(
    output_path: str,
    input_fmt: "sox.Format",
    encoding: Optional[str],
    bits: Optional[int],
) -> Optional["sox.EncodingInfo"]:
    """Choose the encoding to open the output file with.

    Returns None to mean "let the format handler pick its default", which is
    what libsox does when no encoding is supplied.

    An explicitly requested ``encoding`` that the target format cannot write
    is an error; an encoding merely *inherited* from the input is a preference
    and falls back to the handler default. Passing an unsupported pair through
    to libsox is never useful: it silently substitutes something else and
    writes a warning to stderr that Python cannot capture.
    """
    in_encoding = input_fmt.encoding

    if encoding is not None:
        try:
            enc_type = _ENCODING_TYPES[encoding]
        except KeyError:
            valid = ", ".join(sorted(_ENCODING_TYPES))
            raise ValueError(
                f"Unknown encoding: {encoding!r}. Expected one of: {valid}"
            )
        # An explicit bits= wins; otherwise keep the input's width.
        enc_bits = bits or (in_encoding.bits_per_sample if in_encoding else 0)
        if not _supports(output_path, enc_type, enc_bits):
            raise ValueError(
                f"Output format of {output_path!r} cannot encode "
                f"{encoding!r} at {enc_bits} bits"
            )
        return sox.EncodingInfo(encoding=enc_type, bits_per_sample=enc_bits)

    # No explicit request: preserve the input's encoding where the target
    # format can represent it, so a float WAV does not come back as int PCM.
    if in_encoding is None:
        return None

    enc_type = in_encoding.encoding
    enc_bits = bits or in_encoding.bits_per_sample
    if _supports(output_path, enc_type, enc_bits):
        return sox.EncodingInfo(encoding=enc_type, bits_per_sample=enc_bits)

    # Cannot preserve it (float -> mp3, or float paired with an explicit
    # bits= the format rejects). Defer to the handler default at the
    # requested precision rather than forcing a mismatch.
    return None


def convert(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
    effects: Optional[List[Effect]] = None,
    *,
    sample_rate: Optional[int] = None,
    channels: Optional[int] = None,
    bits: Optional[int] = None,
    encoding: Optional[str] = None,
    on_progress: Optional[ProgressCallback] = None,
) -> None:
    """Convert audio file with optional effects.

    Args:
        input_path: Path to input audio file.
        output_path: Path for output audio file. Format determined by extension.
        effects: List of effect objects to apply (from cysox.fx).
        sample_rate: Target sample rate in Hz (optional).
        channels: Target number of channels (optional).
        bits: Target bits per sample (optional).
        encoding: Target sample encoding, using the same names :func:`info`
            reports (``'float'``, ``'signed-integer'``, ...). Defaults to the
            input's encoding where the output format supports it, falling back
            to that format's default otherwise.
        on_progress: Optional callback receiving progress (0.0 to 1.0).
            Return True to continue, False to cancel. Called periodically
            during processing (approximately once per internal buffer).

    Raises:
        CancelledError: If the progress callback returns False.
        ValueError: If ``encoding`` is not a known name, or the output format
            cannot write the requested encoding at the requested width.

    Example:
        >>> # Simple conversion
        >>> cysox.convert('input.wav', 'output.mp3')
        >>>
        >>> # With effects
        >>> cysox.convert('input.wav', 'output.wav', effects=[
        ...     fx.Volume(db=3),
        ...     fx.Reverb(),
        ... ])
        >>>
        >>> # With format options
        >>> cysox.convert('input.wav', 'output.wav',
        ...     sample_rate=48000,
        ...     channels=1,
        ... )
        >>>
        >>> # Stating the output encoding explicitly
        >>> cysox.convert('input.wav', 'output.wav',
        ...     encoding='float',
        ...     bits=32,
        ... )
        >>>
        >>> # With progress reporting
        >>> cysox.convert('input.wav', 'output.wav',
        ...     on_progress=lambda p: print(f"{p:.0%}") or True,
        ... )
    """
    _ensure_init()

    input_path = str(input_path)
    output_path = str(output_path)

    # Open input
    input_fmt = sox.Format(input_path)
    output_fmt = None

    try:
        in_signal = input_fmt.signal

        expanded = _expand_effects(effects) if effects else []
        for effect in expanded:
            if isinstance(effect, PythonEffect):
                raise NotImplementedError(
                    "PythonEffect not yet supported in convert(). "
                    "Use stream() for custom Python processing."
                )

        # Work out what the chain will actually produce *before* opening the
        # output, so the file is created with the rate and channel count the
        # effects deliver. Building out_signal from the keyword arguments alone
        # meant a user's fx.Rate()/fx.Channels() was silently undone by the
        # gap-filling conversions added further down.
        chain_rate, chain_channels = _predict_chain_output(expanded, in_signal)

        # An explicit keyword argument always wins over what the effects imply.
        target_rate = float(sample_rate) if sample_rate is not None else chain_rate
        target_channels = channels if channels is not None else chain_channels

        out_signal = sox.SignalInfo(
            rate=target_rate,
            channels=target_channels,
            precision=bits or in_signal.precision,
        )

        # Open output. Without an explicit encoding libsox picks the handler
        # default for the precision, which drops the input's encoding type.
        out_encoding = _build_output_encoding(output_path, input_fmt, encoding, bits)
        output_fmt = sox.Format(
            output_path, signal=out_signal, encoding=out_encoding, mode="w"
        )

        # Create effects chain
        chain = sox.EffectsChain(input_fmt.encoding, output_fmt.encoding)

        # Save original input properties (before any mutation)
        original_rate = in_signal.rate

        # Track the signal as it flows through the chain.
        current_signal = in_signal

        # Add input effect
        e = sox.Effect(sox.find_effect("input"))
        e.set_options([input_fmt])
        chain.add_effect(e, current_signal, current_signal)

        # Process effects
        if expanded:
            for effect in expanded:
                handler = sox.find_effect(effect.name)
                if handler is None:
                    raise ValueError(f"Unknown effect: {effect.name}")

                e = sox.Effect(handler)
                e.set_options(effect.to_args())

                # Handle effects that explicitly change signal properties
                if effect.name == "rate":
                    new_signal = sox.SignalInfo(
                        rate=float(effect.to_args()[-1]),
                        channels=current_signal.channels,
                        precision=current_signal.precision,
                    )
                    chain.add_effect(e, current_signal, new_signal)
                    current_signal = new_signal
                elif effect.name == "channels":
                    new_signal = sox.SignalInfo(
                        rate=current_signal.rate,
                        channels=int(effect.to_args()[0]),
                        precision=current_signal.precision,
                    )
                    chain.add_effect(e, current_signal, new_signal)
                    current_signal = new_signal
                else:
                    # For other effects, pass same signal (allows libsox in-place updates)
                    chain.add_effect(e, current_signal, current_signal)

                    # After add_effect, current_signal may have been mutated
                    # Check if rate changed (pitch, speed, tempo, etc.)
                    # Always create fresh signal for next effect to avoid stale state
                    if e.out_signal.rate > 0 and e.out_signal.rate != original_rate:
                        current_signal = sox.SignalInfo(
                            rate=e.out_signal.rate,
                            channels=e.out_signal.channels,
                            precision=e.out_signal.precision,
                        )

        # Add rate conversion if the chain has not already reached the target.
        # This is what restores the rate after speed/pitch/tempo, which move it
        # mid-chain; it must not fire for an explicit fx.Rate(), and does not,
        # because target_rate already accounts for one.
        if current_signal.rate != target_rate:
            new_signal = sox.SignalInfo(
                rate=target_rate,
                channels=current_signal.channels,
                precision=current_signal.precision,
            )
            e = sox.Effect(sox.find_effect("rate"))
            e.set_options(
                ["-q", str(int(target_rate))]
            )  # -q for quick to avoid FFT issues
            chain.add_effect(e, current_signal, new_signal)
            current_signal = new_signal

        # Add channel conversion if the chain has not already reached the target
        if current_signal.channels != target_channels:
            new_signal = sox.SignalInfo(
                rate=current_signal.rate,
                channels=target_channels,
                precision=current_signal.precision,
            )
            e = sox.Effect(sox.find_effect("channels"))
            e.set_options([str(target_channels)])
            chain.add_effect(e, current_signal, new_signal)
            current_signal = new_signal

        # Add output effect
        e = sox.Effect(sox.find_effect("output"))
        e.set_options([output_fmt])
        chain.add_effect(e, current_signal, out_signal)

        # Process
        if on_progress is not None:
            flow_cb, flow_state = _make_flow_callback(
                input_fmt.signal.length, on_progress
            )
            try:
                chain.flow_effects(callback=flow_cb)
            except Exception:
                _check_flow_outcome(flow_state, "convert()")
                raise
            _check_flow_outcome(flow_state, "convert()")
        else:
            chain.flow_effects()

    finally:
        input_fmt.close()
        if output_fmt is not None:
            output_fmt.close()


def stream(
    path: Union[str, Path],
    chunk_size: int = 8192,
) -> Iterator[memoryview]:
    """Stream audio samples from a file.

    Yields chunks of samples as memoryview objects that can be used
    with numpy, array.array, or any buffer protocol consumer.

    Args:
        path: Path to audio file.
        chunk_size: Number of samples per chunk (default: 8192).

    Yields:
        memoryview of samples as signed 32-bit integers (int32).
        Sample values are in the range [-2147483648, 2147483647].
        To convert to float [-1.0, 1.0], divide by 2147483648.0.

    Example:
        >>> import numpy as np
        >>> for chunk in cysox.stream('audio.wav'):
        ...     arr = np.frombuffer(chunk, dtype=np.int32)
        ...     # Convert to float [-1.0, 1.0]:
        ...     floats = arr.astype(np.float64) / 2147483648.0
    """
    _ensure_init()

    path = str(path)
    with sox.Format(path) as f:
        while True:
            buf = f.read_buffer(chunk_size)
            if len(buf) == 0:
                break
            yield memoryview(buf)


def play(
    path: Union[str, Path],
    effects: Optional[List[Effect]] = None,
    *,
    on_progress: Optional[ProgressCallback] = None,
) -> None:
    """Play audio to the default audio device.

    Uses libsox's audio output handlers (coreaudio on macOS,
    alsa/pulseaudio on Linux). Blocks until playback is complete
    or cancelled via the progress callback.

    Args:
        path: Path to audio file.
        effects: Optional list of effects to apply during playback.
        on_progress: Optional callback receiving progress (0.0 to 1.0).
            Return True to continue, False to cancel playback.

    Raises:
        CancelledError: If the progress callback returns False.

    Example:
        >>> cysox.play('audio.wav')
        >>> cysox.play('audio.wav', effects=[fx.Volume(db=-6)])
        >>> cysox.play('audio.wav', on_progress=lambda p: p < 0.5)  # stop at 50%
    """
    _ensure_init()

    import platform

    path = str(path)

    # Determine audio output type based on platform
    system = platform.system()
    if system == "Darwin":
        output_type = "coreaudio"
    elif system == "Linux":
        # Try pulseaudio first, fall back to alsa
        output_type = "pulseaudio"
    else:
        raise NotImplementedError(f"Playback not supported on {system}")

    # Open input
    input_fmt = sox.Format(path)
    output_fmt = None

    try:
        in_signal = input_fmt.signal

        expanded = _expand_effects(effects) if effects else []
        for effect in expanded:
            if isinstance(effect, PythonEffect):
                raise NotImplementedError("PythonEffect not supported in play()")

        # Open the device at the rate and channel count the effects will
        # deliver, not the input's. Opening at the input's meant fx.Rate() or
        # fx.Channels() resampled the data while the device kept the old
        # format, so playback ran at the wrong speed.
        device_rate, device_channels = _predict_chain_output(expanded, in_signal)
        device_signal = sox.SignalInfo(
            rate=device_rate,
            channels=device_channels,
            precision=in_signal.precision,
        )

        # Open audio output
        try:
            output_fmt = sox.Format(
                "default", signal=device_signal, filetype=output_type, mode="w"
            )
        except Exception:
            # Try alsa as fallback on Linux
            if system == "Linux":
                output_type = "alsa"
                output_fmt = sox.Format(
                    "default", signal=device_signal, filetype=output_type, mode="w"
                )
            else:
                raise

        # Create effects chain
        chain = sox.EffectsChain(input_fmt.encoding, output_fmt.encoding)
        current_signal = in_signal
        original_rate = in_signal.rate

        # Add input effect
        e = sox.Effect(sox.find_effect("input"))
        e.set_options([input_fmt])
        chain.add_effect(e, current_signal, current_signal)

        # Add user effects
        for effect in expanded:
            handler = sox.find_effect(effect.name)
            if handler is None:
                raise ValueError(f"Unknown effect: {effect.name}")

            e = sox.Effect(handler)
            e.set_options(effect.to_args())

            if effect.name in ("rate", "channels", "remix"):
                new_signal = sox.SignalInfo(
                    rate=float(effect.to_args()[-1])
                    if effect.name == "rate"
                    else current_signal.rate,
                    channels=current_signal.channels
                    if effect.name == "rate"
                    else (
                        int(effect.to_args()[0])
                        if effect.name == "channels"
                        else len(effect.to_args())
                    ),
                    precision=current_signal.precision,
                )
                chain.add_effect(e, current_signal, new_signal)
                current_signal = new_signal
            else:
                chain.add_effect(e, current_signal, current_signal)
                # speed/pitch/tempo move the rate mid-chain; track it so the
                # restoring conversion below knows what it is starting from.
                if e.out_signal.rate > 0 and e.out_signal.rate != original_rate:
                    current_signal = sox.SignalInfo(
                        rate=e.out_signal.rate,
                        channels=e.out_signal.channels,
                        precision=e.out_signal.precision,
                    )

        # Restore the device rate after speed/pitch/tempo.
        if current_signal.rate != device_rate:
            new_signal = sox.SignalInfo(
                rate=device_rate,
                channels=current_signal.channels,
                precision=current_signal.precision,
            )
            e = sox.Effect(sox.find_effect("rate"))
            e.set_options(["-q", str(int(device_rate))])
            chain.add_effect(e, current_signal, new_signal)
            current_signal = new_signal

        # Add output effect
        e = sox.Effect(sox.find_effect("output"))
        e.set_options([output_fmt])
        chain.add_effect(e, current_signal, device_signal)

        # Play (blocks until complete or cancelled)
        if on_progress is not None:
            flow_cb, flow_state = _make_flow_callback(
                input_fmt.signal.length, on_progress
            )
            try:
                chain.flow_effects(callback=flow_cb)
            except Exception:
                _check_flow_outcome(flow_state, "play()")
                raise
            _check_flow_outcome(flow_state, "play()")
        else:
            chain.flow_effects()

    finally:
        input_fmt.close()
        if output_fmt is not None:
            output_fmt.close()


def concat(
    inputs: List[Union[str, Path]],
    output_path: Union[str, Path],
    *,
    chunk_size: int = 8192,
    encoding: Optional[str] = None,
    on_progress: Optional[ProgressCallback] = None,
) -> None:
    """Concatenate multiple audio files into one.

    All input files must have the same sample rate and number of channels.
    The output format is determined by the output file extension.

    Args:
        inputs: List of paths to input audio files (minimum 2).
        output_path: Path for the concatenated output file.
        chunk_size: Number of samples to read/write at a time (default: 8192).
        encoding: Sample encoding for the output, using the names :func:`info`
            reports. Defaults to the first input's encoding where the output
            format supports it, falling back to that format's default.
        on_progress: Optional callback receiving progress (0.0 to 1.0).
            Return True to continue, False to cancel.

    Raises:
        ValueError: If fewer than 2 input files provided.
        ValueError: If input files have mismatched sample rates or channels.
        ValueError: If the output format cannot write the requested encoding.
        CancelledError: If the progress callback returns False.

    Example:
        >>> cysox.concat(['intro.wav', 'main.wav', 'outro.wav'], 'full.wav')
    """
    _ensure_init()

    if len(inputs) < 2:
        raise ValueError("concat() requires at least 2 input files")

    inputs = [str(p) for p in inputs]
    output_path = str(output_path)

    # Pre-compute total samples for progress reporting
    total_samples = 0
    if on_progress is not None:
        for p in inputs:
            file_info = info(p)
            total_samples += file_info.samples

    output_fmt = None
    input_fmt = None
    reference_rate = None
    reference_channels = None
    samples_written = 0

    try:
        for i, input_path in enumerate(inputs):
            input_fmt = sox.Format(input_path)

            if i == 0:
                # First file: capture reference signal and open output
                reference_rate = input_fmt.signal.rate
                reference_channels = input_fmt.signal.channels

                out_signal = sox.SignalInfo(
                    rate=reference_rate,
                    channels=reference_channels,
                    precision=input_fmt.signal.precision,
                )
                out_encoding = _build_output_encoding(
                    output_path, input_fmt, encoding, None
                )
                output_fmt = sox.Format(
                    output_path, signal=out_signal, encoding=out_encoding, mode="w"
                )
            else:
                # Subsequent files: verify compatibility
                if input_fmt.signal.rate != reference_rate:
                    raise ValueError(
                        f"Sample rate mismatch: {input_path} has {input_fmt.signal.rate}Hz, "
                        f"expected {reference_rate}Hz. "
                        f"Use cysox.convert() to resample files before concatenating."
                    )
                if input_fmt.signal.channels != reference_channels:
                    raise ValueError(
                        f"Channel count mismatch: {input_path} has {input_fmt.signal.channels} channels, "
                        f"expected {reference_channels}. "
                        f"Use cysox.convert() to match channel counts before concatenating."
                    )

            # Copy all samples from this input to output
            assert output_fmt is not None  # Set on first iteration
            while True:
                samples = input_fmt.read(chunk_size)
                if len(samples) == 0:
                    break
                output_fmt.write(samples)

                if on_progress is not None:
                    samples_written += len(samples)
                    progress = (
                        min(samples_written / total_samples, 0.99)
                        if total_samples > 0
                        else 0.0
                    )
                    if on_progress(progress) is False:
                        raise CancelledError("concat() cancelled by progress callback")

            input_fmt.close()
            input_fmt = None

        assert output_fmt is not None  # Loop always runs (len >= 2)

        if on_progress is not None:
            on_progress(1.0)

    finally:
        if input_fmt is not None:
            input_fmt.close()
        if output_fmt is not None:
            output_fmt.close()


def slice_loop(
    path: Union[str, Path],
    output_dir: Union[str, Path],
    *,
    slices: int = 4,
    beat_duration: Optional[float] = None,
    bpm: Optional[float] = None,
    beats_per_slice: int = 1,
    threshold: Optional[float] = None,
    sensitivity: float = 1.5,
    onset_method: str = "hfc",
    min_onset_spacing: float = 0.05,
    output_format: str = "wav",
    effects: Optional[List[Effect]] = None,
    encoding: Optional[str] = None,
) -> List[str]:
    """Slice a drum loop or audio file into multiple segments.

    Splits an audio file into segments, useful for chopping drum loops,
    creating sample packs, or beat slicing. Can slice by count, BPM,
    or automatically at transients.

    Args:
        path: Path to input audio file.
        output_dir: Directory to save slices (created if doesn't exist).
        slices: Number of slices to create (default: 4). Ignored if bpm
                or threshold is set.
        beat_duration: Duration of each slice in seconds. If not set, the file
                      is divided into equal `slices` parts.
        bpm: If set, calculate slice duration based on BPM and beats_per_slice.
             Takes precedence over `slices`.
        beats_per_slice: Number of beats per slice when using bpm (default: 1).
        threshold: Onset detection threshold 0.0-1.0 (lower = more sensitive).
                   If set, enables automatic transient detection for slicing.
                   Typical values: 0.2-0.4 for drums, 0.3-0.5 for mixed audio.
                   Takes precedence over bpm and slices.
        sensitivity: Peak picking sensitivity for onset detection (default: 1.5).
                     Higher values (2.0-3.0) are stricter, fewer false positives.
                     Lower values (1.0-1.3) catch more subtle transients.
        onset_method: Onset detection method (default: "hfc"):
                      - "hfc": High-Frequency Content, best for drums
                      - "flux": Spectral flux, good for general onsets
                      - "energy": Simple energy-based, fast
                      - "complex": Phase+magnitude, most accurate but slower
        min_onset_spacing: Minimum time between detected onsets in seconds
                           (default: 0.05). Prevents double triggers.
        output_format: Output file format/extension (default: "wav").
        effects: Optional list of effects to apply to each slice.
        encoding: Sample encoding for the slices, using the names :func:`info`
            reports. Defaults to the input's encoding where the output format
            supports it, falling back to that format's default.

    Returns:
        List of paths to the created slice files.

    Example:
        >>> # Slice into 8 equal parts
        >>> slices = cysox.slice_loop('drums.wav', 'slices/', slices=8)
        >>>
        >>> # Slice by BPM (one beat per slice at 120 BPM)
        >>> slices = cysox.slice_loop('drums.wav', 'slices/', bpm=120)
        >>>
        >>> # Slice at transients (automatic beat detection)
        >>> slices = cysox.slice_loop('drums.wav', 'slices/', threshold=0.3)
        >>>
        >>> # Slice with high sensitivity for subtle transients
        >>> slices = cysox.slice_loop('drums.wav', 'slices/',
        ...     threshold=0.2, sensitivity=1.2)
        >>>
        >>> # Slice with effects applied to each slice
        >>> from cysox import fx
        >>> slices = cysox.slice_loop('drums.wav', 'slices/',
        ...     slices=4, effects=[fx.DrumPunch()])

    Note:
        For stutter effects, use the returned slice paths with
        convert() and fx.Repeat() in a second pass.
    """
    import tempfile
    import os

    _ensure_init()

    path = str(path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Get audio info
    file_info = info(path)
    duration = file_info["duration"]
    rate = file_info["sample_rate"]
    channels = file_info["channels"]

    # Determine slice points
    slice_times: List[float] = []

    if threshold is not None:
        # Use onset detection to find slice points
        from . import onset

        onsets = onset.detect(
            path,
            threshold=threshold,
            sensitivity=sensitivity,
            min_spacing=min_onset_spacing,
            method=onset_method,
        )

        # Slice times are the onset times
        slice_times = onsets if onsets else [0.0]

    elif bpm is not None:
        # Calculate based on BPM
        beat_duration_secs = 60.0 / bpm
        slice_duration = beat_duration_secs * beats_per_slice
        num_slices = int(duration / slice_duration)
        slice_times = [i * slice_duration for i in range(num_slices)]

    elif beat_duration is not None:
        num_slices = int(duration / beat_duration)
        slice_times = [i * beat_duration for i in range(num_slices)]

    else:
        slice_duration = duration / slices
        slice_times = [i * slice_duration for i in range(slices)]

    if not slice_times:
        return []

    # Add end time for calculating durations
    slice_times_with_end = slice_times + [duration]

    # Generate slice files using direct read/write (trim effect has issues)
    output_paths = []
    basename = Path(path).stem

    # Open input file
    input_fmt = sox.Format(path)
    precision = input_fmt.signal.precision

    # Track current position in samples
    current_sample = 0

    for i in range(len(slice_times)):
        slice_name = f"{basename}_slice_{i:03d}.{output_format}"
        slice_path = output_dir / slice_name

        # Calculate sample range for this slice
        start_time = slice_times_with_end[i]
        end_time = slice_times_with_end[i + 1]
        start_sample = int(start_time * rate * channels)
        end_sample = int(end_time * rate * channels)
        samples_to_read = end_sample - start_sample

        if samples_to_read <= 0:
            continue

        # Skip to start position if needed
        samples_to_skip = start_sample - current_sample
        if samples_to_skip > 0:
            _ = input_fmt.read(samples_to_skip)
            current_sample += samples_to_skip

        # Read slice samples
        segment = input_fmt.read(samples_to_read)
        current_sample += len(segment)

        if len(segment) == 0:
            break

        # Write slice to temporary file first if we need to apply effects
        if effects:
            with tempfile.TemporaryDirectory() as tmpdir:
                temp_path = os.path.join(tmpdir, "temp.wav")

                # Write raw segment. The temp file keeps the input's encoding
                # rather than the caller's - degrading here would throw away
                # resolution before the effects run. convert() applies the
                # requested encoding on the way out.
                out_signal = sox.SignalInfo(
                    rate=rate, channels=channels, precision=precision
                )
                temp_fmt = sox.Format(
                    temp_path,
                    signal=out_signal,
                    encoding=_build_output_encoding(temp_path, input_fmt, None, None),
                    mode="w",
                )
                temp_fmt.write(segment)
                temp_fmt.close()

                # Apply effects
                convert(temp_path, str(slice_path), effects=effects, encoding=encoding)
        else:
            # Write directly without effects
            out_signal = sox.SignalInfo(
                rate=rate, channels=channels, precision=precision
            )
            output_fmt = sox.Format(
                str(slice_path),
                signal=out_signal,
                encoding=_build_output_encoding(
                    str(slice_path), input_fmt, encoding, None
                ),
                mode="w",
            )
            output_fmt.write(segment)
            output_fmt.close()

        output_paths.append(str(slice_path))

    input_fmt.close()
    return output_paths


def stutter(
    path: Union[str, Path],
    output_path: Union[str, Path],
    *,
    segment_start: float = 0,
    segment_duration: float = 0.125,
    repeats: int = 8,
    effects: Optional[List[Effect]] = None,
    encoding: Optional[str] = None,
) -> None:
    """Create a stutter effect by extracting and repeating a segment.

    This is a two-step operation (trim then repeat) that cannot be done
    in a single effects chain due to sox limitations.

    Args:
        path: Path to input audio file.
        output_path: Path for output file.
        segment_start: Start position of segment in seconds (default: 0).
        segment_duration: Length of segment in seconds (default: 0.125,
                         which is 1/8 note at 120 BPM).
        repeats: Total number of times the segment plays (default: 8).
        effects: Optional effects to apply after stuttering.
        encoding: Sample encoding for the output, using the names :func:`info`
            reports. Defaults to the input's encoding where the output format
            supports it, falling back to that format's default.

    Example:
        >>> # Create 8x stutter from first 1/8 note
        >>> cysox.stutter('drums.wav', 'stutter.wav',
        ...     segment_duration=0.125, repeats=8)
        >>>
        >>> # Stutter with effects
        >>> cysox.stutter('drums.wav', 'stutter.wav',
        ...     segment_start=0.5, segment_duration=0.25, repeats=4,
        ...     effects=[fx.DrumPunch()])
    """
    import tempfile
    import os

    _ensure_init()

    from .fx.time import Repeat

    path = str(path)
    output_path = str(output_path)

    # Get audio info
    input_fmt = sox.Format(path)
    rate = input_fmt.signal.rate
    channels = input_fmt.signal.channels
    precision = input_fmt.signal.precision

    # Calculate sample positions
    start_samples = int(segment_start * rate * channels)
    read_samples = int(segment_duration * rate * channels)

    # Skip to start position
    if start_samples > 0:
        _ = input_fmt.read(start_samples)

    # Read segment
    segment = input_fmt.read(read_samples)
    # Resolve the temp file's encoding while the input is still open. Only the
    # extension is consulted, and the temp file below is always a WAV. The temp
    # keeps the input's encoding rather than the caller's; convert() applies
    # the requested one at the end so nothing is degraded before the effects.
    temp_encoding = _build_output_encoding("segment.wav", input_fmt, None, None)
    input_fmt.close()

    with tempfile.TemporaryDirectory() as tmpdir:
        # Write segment to temp file
        temp_path = os.path.join(tmpdir, "segment.wav")
        out_signal = sox.SignalInfo(rate=rate, channels=channels, precision=precision)
        temp_fmt = sox.Format(
            temp_path, signal=out_signal, encoding=temp_encoding, mode="w"
        )
        temp_fmt.write(segment)
        temp_fmt.close()

        # Apply repeat and any additional effects
        repeat_effects: List[Effect] = []
        if repeats > 1:
            repeat_effects.append(Repeat(count=repeats - 1))
        if effects:
            repeat_effects.extend(_expand_effects(effects))

        if repeat_effects:
            convert(temp_path, output_path, effects=repeat_effects, encoding=encoding)
        else:
            # Just copy if no repeat or effects
            convert(temp_path, output_path, encoding=encoding)


# Supported audio file extensions for batch processing
_AUDIO_EXTENSIONS = {
    ".wav",
    ".mp3",
    ".flac",
    ".ogg",
    ".aiff",
    ".aif",
    ".au",
    ".opus",
    ".wv",
    ".caf",
    ".raw",
    ".amr",
}


def auto_trim(
    path: Union[str, Path],
    output_path: Union[str, Path],
    *,
    threshold_db: float = -48,
    min_silence: float = 0.1,
    fade_in: float = 0,
    fade_out: float = 0,
    speed_factor: Optional[float] = None,
    effects: Optional[List[Effect]] = None,
) -> None:
    """Trim silence from the beginning and end of an audio file.

    Detects the start and end points of the main audio content based on
    amplitude and removes the surrounding silence. Optionally applies
    fade in/out and speed change.

    Ported from AudioHit's trim mode.

    Args:
        path: Path to input audio file.
        output_path: Path for output audio file.
        threshold_db: Amplitude threshold in decibels (default: -48dB).
            Audio below this level is considered silence.
        min_silence: Minimum duration in seconds that non-silent audio must
            persist before it is considered the start of content (default: 0.1).
        fade_in: Fade-in duration in milliseconds (default: 0, no fade).
        fade_out: Fade-out duration in milliseconds (default: 0, no fade).
        speed_factor: If set, change playback speed by this factor.
            Values > 1.0 speed up, < 1.0 slow down. Affects pitch.
        effects: Optional additional effects to apply after trimming.

    Example:
        >>> cysox.auto_trim('raw.wav', 'trimmed.wav')
        >>> cysox.auto_trim('raw.wav', 'trimmed.wav', threshold_db=-36,
        ...     fade_in=10, fade_out=50)
    """
    from .fx.time import Silence, Fade, Reverse, Speed

    _ensure_init()

    fx_chain: List[Effect] = []

    # Remove leading silence
    fx_chain.append(
        Silence(above_periods=1, duration=min_silence, threshold=threshold_db)
    )

    # Remove trailing silence: reverse -> strip leading -> reverse back
    fx_chain.append(Reverse())
    fx_chain.append(
        Silence(above_periods=1, duration=min_silence, threshold=threshold_db)
    )
    fx_chain.append(Reverse())

    # Apply speed change
    if speed_factor is not None and speed_factor != 1.0:
        fx_chain.append(Speed(factor=speed_factor))

    # Apply fades
    fade_in_secs = fade_in / 1000.0 if fade_in > 0 else 0
    fade_out_secs = fade_out / 1000.0 if fade_out > 0 else 0

    if fade_in_secs > 0 or fade_out_secs > 0:
        if fade_out_secs > 0:
            # Use reverse trick for reliable fade-out
            fx_chain.append(Fade(fade_in=fade_in_secs))
            fx_chain.append(Reverse())
            fx_chain.append(Fade(fade_in=fade_out_secs))
            fx_chain.append(Reverse())
        else:
            fx_chain.append(Fade(fade_in=fade_in_secs))

    # Apply any additional user effects
    if effects:
        fx_chain.extend(_expand_effects(effects))

    convert(str(path), str(output_path), effects=fx_chain)


def split_by_silence(
    path: Union[str, Path],
    output_dir: Union[str, Path],
    *,
    threshold_db: float = -48,
    min_silence: float = 0.25,
    min_segment: float = 0.25,
    fade_in: float = 0,
    fade_out: float = 0,
    speed_factor: Optional[float] = None,
    output_format: str = "wav",
    effects: Optional[List[Effect]] = None,
    encoding: Optional[str] = None,
) -> List[str]:
    """Split a continuous audio recording into segments at silence gaps.

    Scans the audio for regions below the amplitude threshold and splits
    the file at those silence boundaries. Each segment is written as a
    separate file with automatic fading.

    Ported from AudioHit's trim --split mode.

    Args:
        path: Path to input audio file.
        output_dir: Directory to save segments (created if doesn't exist).
        threshold_db: Amplitude threshold in dB (default: -48dB).
            Audio below this level is considered silence.
        min_silence: Minimum silence duration in seconds required to
            trigger a split (default: 0.25).
        min_segment: Minimum segment duration in seconds. Segments
            shorter than this are discarded (default: 0.25).
        fade_in: Fade-in duration in milliseconds for each segment
            (default: 0, no fade).
        fade_out: Fade-out duration in milliseconds for each segment
            (default: 0, no fade).
        speed_factor: If set, change playback speed of each segment.
        output_format: Output file format/extension (default: "wav").
        effects: Optional effects to apply to each segment.
        encoding: Sample encoding for the segments, using the names :func:`info`
            reports. Defaults to the input's encoding where the output format
            supports it, falling back to that format's default.

    Returns:
        List of paths to the created segment files.

    Example:
        >>> segments = cysox.split_by_silence('recording.wav', 'one_shots/')
        >>> segments = cysox.split_by_silence('recording.wav', 'one_shots/',
        ...     threshold_db=-36, min_silence=0.5, fade_in=5, fade_out=20)
    """
    from .fx.time import Fade, Speed

    _ensure_init()

    path = str(path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    file_info = info(path)
    rate = file_info.sample_rate
    channels = file_info.channels

    # Convert threshold from dB to linear amplitude (int32 scale)
    threshold_linear = int(2147483647 * (10 ** (threshold_db / 20.0)))

    # Analysis window size in samples (~10ms)
    window_samples = max(1, int(rate * channels * 0.01))
    min_silence_windows = max(1, int(min_silence * rate * channels / window_samples))
    min_segment_windows = max(1, int(min_segment * rate * channels / window_samples))

    # Pass 1: scan audio to build silence map
    input_fmt = sox.Format(path)
    precision = input_fmt.signal.precision

    peaks: List[int] = []
    while True:
        chunk = input_fmt.read(window_samples)
        if len(chunk) == 0:
            break
        peak = 0
        for s in chunk:
            a = s if s >= 0 else -s
            if a > peak:
                peak = a
        peaks.append(peak)
    input_fmt.close()

    if not peaks:
        return []

    # Find segment boundaries from peak data
    segments: List[tuple] = []  # (start_window, end_window)
    seg_start: Optional[int] = None
    silence_run = 0

    for i, peak in enumerate(peaks):
        if peak > threshold_linear:
            if seg_start is None:
                seg_start = i
            silence_run = 0
        else:
            silence_run += 1
            if seg_start is not None and silence_run >= min_silence_windows:
                seg_end = i - silence_run + 1
                if seg_end - seg_start >= min_segment_windows:
                    segments.append((seg_start, seg_end))
                seg_start = None
                silence_run = 0

    # Handle last segment
    if seg_start is not None:
        seg_end = len(peaks)
        if seg_end - seg_start >= min_segment_windows:
            segments.append((seg_start, seg_end))

    if not segments:
        return []

    # Build per-segment effects
    from .fx.time import Reverse

    seg_effects: List[Effect] = []
    if speed_factor is not None and speed_factor != 1.0:
        seg_effects.append(Speed(factor=speed_factor))

    fade_in_secs = fade_in / 1000.0 if fade_in > 0 else 0
    fade_out_secs = fade_out / 1000.0 if fade_out > 0 else 0
    if fade_in_secs > 0:
        seg_effects.append(Fade(fade_in=fade_in_secs))
    if fade_out_secs > 0:
        # Use reverse trick for reliable fade-out (sox fade_out is unreliable)
        seg_effects.append(Reverse())
        seg_effects.append(Fade(fade_in=fade_out_secs))
        seg_effects.append(Reverse())

    if effects:
        seg_effects.extend(_expand_effects(effects))

    # Pass 2: re-read and write segments
    input_fmt = sox.Format(path)
    current_sample = 0
    output_paths: List[str] = []
    basename = Path(path).stem

    for i, (start_w, end_w) in enumerate(segments):
        start_sample = start_w * window_samples
        end_sample = min(end_w * window_samples, file_info.samples)
        samples_to_read = end_sample - start_sample

        if samples_to_read <= 0:
            continue

        # Skip to start position
        skip = start_sample - current_sample
        if skip > 0:
            _ = input_fmt.read(skip)
            current_sample += skip

        # Read segment
        segment = input_fmt.read(samples_to_read)
        current_sample += len(segment)

        if len(segment) == 0:
            break

        seg_name = f"{basename}_seg_{i:03d}.{output_format}"
        seg_path = output_dir / seg_name

        if seg_effects:
            with tempfile.TemporaryDirectory() as tmpdir:
                temp_path = os.path.join(tmpdir, "temp.wav")
                out_signal = sox.SignalInfo(
                    rate=rate, channels=channels, precision=precision
                )
                # Temp keeps the input's encoding; convert() applies the
                # requested one so nothing degrades before the effects run.
                temp_fmt = sox.Format(
                    temp_path,
                    signal=out_signal,
                    encoding=_build_output_encoding(temp_path, input_fmt, None, None),
                    mode="w",
                )
                temp_fmt.write(segment)
                temp_fmt.close()
                convert(
                    temp_path, str(seg_path), effects=seg_effects, encoding=encoding
                )
        else:
            out_signal = sox.SignalInfo(
                rate=rate, channels=channels, precision=precision
            )
            output_fmt = sox.Format(
                str(seg_path),
                signal=out_signal,
                encoding=_build_output_encoding(
                    str(seg_path), input_fmt, encoding, None
                ),
                mode="w",
            )
            output_fmt.write(segment)
            output_fmt.close()

        output_paths.append(str(seg_path))

    input_fmt.close()
    return output_paths


def pitch_scale(
    path: Union[str, Path],
    output_dir: Union[str, Path],
    *,
    semitones: int = 12,
    offset: int = 0,
    output_format: str = "wav",
    effects: Optional[List[Effect]] = None,
) -> List[str]:
    """Generate pitch-shifted copies of an audio file.

    Creates multiple copies of the input file, each transposed by one
    semitone. Useful for creating playable melodic sample libraries from
    a single sample.

    Ported from AudioHit's scale mode.

    Args:
        path: Path to input audio file.
        output_dir: Directory to save pitch-shifted files (created if
            doesn't exist).
        semitones: Number of pitch-shifted copies to generate (default: 12,
            one full octave). Each copy is transposed up by one additional
            semitone from the previous.
        offset: Starting semitone offset from the original pitch
            (default: 0). For example, offset=-6 starts a tritone below.
        output_format: Output file format/extension (default: "wav").
        effects: Optional effects to apply to each copy after pitch shifting.

    Returns:
        List of paths to the created pitch-shifted files.

    Example:
        >>> # Generate one octave of chromatic variations
        >>> files = cysox.pitch_scale('c3_piano.wav', 'scale/')
        >>>
        >>> # Generate 24 semitones starting from -12
        >>> files = cysox.pitch_scale('sample.wav', 'scale/',
        ...     semitones=24, offset=-12)
    """
    from .fx.time import Pitch

    _ensure_init()

    if semitones < 1:
        raise ValueError("semitones must be at least 1")

    path = str(path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    basename = Path(path).stem
    output_paths: List[str] = []

    for i in range(semitones):
        shift = i + offset
        cents = shift * 100

        out_name = f"{basename}_pitch_{shift:+d}.{output_format}"
        out_path = output_dir / out_name

        pitch_effects: List[Effect] = []
        if cents != 0:
            pitch_effects.append(Pitch(cents=cents))

        if effects:
            pitch_effects.extend(_expand_effects(effects))

        if pitch_effects:
            convert(path, str(out_path), effects=pitch_effects)
        else:
            # No shift needed (offset=0, first iteration) - just copy
            convert(path, str(out_path))

        output_paths.append(str(out_path))

    return output_paths


def batch(
    input_dir: Union[str, Path],
    output_dir: Union[str, Path],
    *,
    effects: Optional[List[Effect]] = None,
    sample_rate: Optional[int] = None,
    channels: Optional[int] = None,
    bits: Optional[int] = None,
    recursive: bool = True,
    output_format: Optional[str] = None,
    on_file: Optional[Callable[[str, str], None]] = None,
) -> List[str]:
    """Process all audio files in a directory.

    Walks the input directory, applies effects and format conversions to
    each audio file, and writes results to the output directory. The
    relative directory structure is preserved.

    Args:
        input_dir: Directory containing audio files to process.
        output_dir: Directory for processed output files (created if
            doesn't exist).
        effects: Optional effects to apply to each file.
        sample_rate: Target sample rate in Hz (optional).
        channels: Target number of channels (optional).
        bits: Target bits per sample (optional).
        recursive: If True, process subdirectories recursively
            (default: True).
        output_format: Output file format/extension. If None, keeps the
            original format (default: None).
        on_file: Optional callback called after each file is processed,
            receiving (input_path, output_path).

    Returns:
        List of paths to the processed output files.

    Example:
        >>> # Convert a folder to mono 22050Hz
        >>> processed = cysox.batch('samples/', 'processed/',
        ...     sample_rate=22050, channels=1)
        >>>
        >>> # Apply effects to all files
        >>> from cysox import fx
        >>> processed = cysox.batch('raw/', 'ready/',
        ...     effects=[fx.Normalize(), fx.Fade(fade_in=0.01)])
    """
    _ensure_init()

    input_dir = Path(input_dir)
    output_dir = Path(output_dir)

    if not input_dir.is_dir():
        raise ValueError(f"Input directory does not exist: {input_dir}")

    if recursive:
        files = sorted(
            f
            for f in input_dir.rglob("*")
            if f.is_file() and f.suffix.lower() in _AUDIO_EXTENSIONS
        )
    else:
        files = sorted(
            f
            for f in input_dir.glob("*")
            if f.is_file() and f.suffix.lower() in _AUDIO_EXTENSIONS
        )

    if not files:
        return []

    processed: List[str] = []

    for input_path in files:
        rel = input_path.relative_to(input_dir)

        if output_format:
            out_path = output_dir / rel.with_suffix(f".{output_format}")
        else:
            out_path = output_dir / rel

        out_path.parent.mkdir(parents=True, exist_ok=True)

        convert(
            str(input_path),
            str(out_path),
            effects=effects,
            sample_rate=sample_rate,
            channels=channels,
            bits=bits,
        )

        if on_file is not None:
            on_file(str(input_path), str(out_path))

        processed.append(str(out_path))

    return processed
