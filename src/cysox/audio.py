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
    >>> print(f"Duration: {info['duration']:.2f}s")
    >>>
    >>> # Convert with effects
    >>> cysox.convert('input.wav', 'output.mp3', effects=[
    ...     fx.Normalize(),
    ...     fx.Fade(fade_in=0.5),
    ... ])
"""

import atexit
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Union

from . import sox
from .fx.base import Effect, CompositeEffect, PythonEffect

# Module state
_initialized = False


def _ensure_init() -> None:
    """Ensure sox is initialized (called automatically)."""
    global _initialized
    if not _initialized:
        sox.init()
        atexit.register(_cleanup)
        _initialized = True


def _cleanup() -> None:
    """Cleanup sox on exit (called automatically via atexit)."""
    global _initialized
    if _initialized:
        try:
            sox._force_quit()  # Use internal function for actual cleanup
        except Exception:
            pass  # Ignore errors during cleanup
        _initialized = False


def _expand_effects(effects: List[Effect]) -> List[Effect]:
    """Expand CompositeEffects into their constituent effects."""
    expanded = []
    for effect in effects:
        if isinstance(effect, CompositeEffect):
            expanded.extend(_expand_effects(effect.effects))
        else:
            expanded.append(effect)
    return expanded


def info(path: Union[str, Path]) -> Dict:
    """Get audio file metadata.

    Args:
        path: Path to audio file.

    Returns:
        Dictionary with file information:
        - path: Original path
        - format: File format (e.g., 'wav', 'mp3')
        - duration: Duration in seconds
        - sample_rate: Sample rate in Hz
        - channels: Number of channels
        - bits_per_sample: Bits per sample
        - samples: Total number of samples
        - encoding: Encoding type

    Example:
        >>> info = cysox.info('audio.wav')
        >>> print(f"Duration: {info['duration']:.2f}s")
        >>> print(f"Sample rate: {info['sample_rate']} Hz")
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

        return {
            "path": path,
            "format": f.filetype or "",
            "duration": duration,
            "sample_rate": int(signal.rate) if signal.rate else 0,
            "channels": signal.channels or 0,
            "bits_per_sample": encoding.bits_per_sample if encoding else 0,
            "samples": signal.length or 0,
            "encoding": _encoding_name(encoding.encoding) if encoding else "",
        }


def _encoding_name(encoding_type: int) -> str:
    """Convert encoding type constant to string."""
    encoding_names = {
        0: "unknown",
        1: "signed-integer",
        2: "unsigned-integer",
        3: "float",
        4: "float-text",
        5: "flac",
        6: "hcom",
        7: "wavpack",
        8: "wavpackf",
        9: "ulaw",
        10: "alaw",
        11: "g721",
        12: "g723",
        13: "cl-adpcm",
        14: "cl-adpcm16",
        15: "ms-adpcm",
        16: "ima-adpcm",
        17: "oki-adpcm",
        18: "dpcm",
        19: "dwvw",
        20: "dwvwn",
        21: "gsm",
        22: "mp3",
        23: "vorbis",
        24: "amr-wb",
        25: "amr-nb",
        26: "cvsd",
        27: "lpc10",
        28: "opus",
    }
    return encoding_names.get(encoding_type, "unknown")


def convert(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
    effects: Optional[List[Effect]] = None,
    *,
    sample_rate: Optional[int] = None,
    channels: Optional[int] = None,
    bits: Optional[int] = None,
) -> None:
    """Convert audio file with optional effects.

    Args:
        input_path: Path to input audio file.
        output_path: Path for output audio file. Format determined by extension.
        effects: List of effect objects to apply (from cysox.fx).
        sample_rate: Target sample rate in Hz (optional).
        channels: Target number of channels (optional).
        bits: Target bits per sample (optional).

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
    """
    _ensure_init()

    input_path = str(input_path)
    output_path = str(output_path)

    # Open input
    input_fmt = sox.Format(input_path)

    # Build output signal info
    out_signal = sox.SignalInfo(
        rate=sample_rate or input_fmt.signal.rate,
        channels=channels or input_fmt.signal.channels,
        precision=bits or input_fmt.signal.precision,
    )

    # Open output
    output_fmt = sox.Format(output_path, signal=out_signal, mode='w')

    # Create effects chain
    chain = sox.EffectsChain(input_fmt.encoding, output_fmt.encoding)

    # Save original input properties (before any mutation)
    original_rate = input_fmt.signal.rate

    # Track current signal - use same object pattern to allow libsox in-place updates
    current_signal = input_fmt.signal

    # Target output rate
    target_rate = sample_rate or original_rate

    # Add input effect
    e = sox.Effect(sox.find_effect("input"))
    e.set_options([input_fmt])
    chain.add_effect(e, current_signal, current_signal)

    # Process effects
    if effects:
        expanded = _expand_effects(effects)

        for effect in expanded:
            if isinstance(effect, PythonEffect):
                raise NotImplementedError(
                    "PythonEffect not yet supported in convert(). "
                    "Use stream() for custom Python processing."
                )

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

    # Add rate conversion if current rate differs from target
    if current_signal.rate != target_rate:
        new_signal = sox.SignalInfo(
            rate=target_rate,
            channels=current_signal.channels,
            precision=current_signal.precision,
        )
        e = sox.Effect(sox.find_effect("rate"))
        e.set_options(["-q", str(int(target_rate))])  # -q for quick to avoid FFT issues
        chain.add_effect(e, current_signal, new_signal)
        current_signal = new_signal

    # Add channel conversion if needed
    target_channels = channels or input_fmt.signal.channels
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
    result = chain.flow_effects()

    # Cleanup
    input_fmt.close()
    output_fmt.close()

    if result != sox.SUCCESS:
        raise RuntimeError(f"Effects processing failed with code {result}")


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
        memoryview of samples (int32 format).

    Example:
        >>> import numpy as np
        >>> for chunk in cysox.stream('audio.wav'):
        ...     arr = np.frombuffer(chunk, dtype=np.int32)
        ...     process(arr)
    """
    _ensure_init()

    path = str(path)
    with sox.Format(path) as f:
        remaining = f.signal.length
        while remaining > 0:
            to_read = min(chunk_size, remaining)
            buf = f.read_buffer(to_read)
            if len(buf) == 0:
                break
            remaining -= len(buf)
            yield memoryview(buf)


def play(
    path: Union[str, Path],
    effects: Optional[List[Effect]] = None,
) -> None:
    """Play audio to the default audio device.

    Uses libsox's audio output handlers (coreaudio on macOS,
    alsa/pulseaudio on Linux).

    Args:
        path: Path to audio file.
        effects: Optional list of effects to apply during playback.

    Example:
        >>> cysox.play('audio.wav')
        >>> cysox.play('audio.wav', effects=[fx.Volume(db=-6)])

    Note:
        This function blocks until playback is complete.
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

    # Open audio output
    try:
        output_fmt = sox.Format(
            "default",
            signal=input_fmt.signal,
            filetype=output_type,
            mode='w'
        )
    except Exception:
        # Try alsa as fallback on Linux
        if system == "Linux":
            output_type = "alsa"
            output_fmt = sox.Format(
                "default",
                signal=input_fmt.signal,
                filetype=output_type,
                mode='w'
            )
        else:
            raise

    # Create effects chain
    chain = sox.EffectsChain(input_fmt.encoding, output_fmt.encoding)
    current_signal = input_fmt.signal

    # Add input effect
    e = sox.Effect(sox.find_effect("input"))
    e.set_options([input_fmt])
    chain.add_effect(e, current_signal, current_signal)

    # Add user effects
    if effects:
        expanded = _expand_effects(effects)
        for effect in expanded:
            if isinstance(effect, PythonEffect):
                raise NotImplementedError(
                    "PythonEffect not supported in play()"
                )

            handler = sox.find_effect(effect.name)
            if handler is None:
                raise ValueError(f"Unknown effect: {effect.name}")

            e = sox.Effect(handler)
            e.set_options(effect.to_args())
            chain.add_effect(e, current_signal, current_signal)

    # Add output effect
    e = sox.Effect(sox.find_effect("output"))
    e.set_options([output_fmt])
    chain.add_effect(e, current_signal, current_signal)

    # Play (blocks until complete)
    result = chain.flow_effects()

    # Cleanup
    input_fmt.close()
    output_fmt.close()

    if result != sox.SUCCESS:
        raise RuntimeError(f"Playback failed with code {result}")


def concat(
    inputs: List[Union[str, Path]],
    output_path: Union[str, Path],
    *,
    chunk_size: int = 8192,
) -> None:
    """Concatenate multiple audio files into one.

    All input files must have the same sample rate and number of channels.
    The output format is determined by the output file extension.

    Args:
        inputs: List of paths to input audio files (minimum 2).
        output_path: Path for the concatenated output file.
        chunk_size: Number of samples to read/write at a time (default: 8192).

    Raises:
        ValueError: If fewer than 2 input files provided.
        ValueError: If input files have mismatched sample rates or channels.

    Example:
        >>> cysox.concat(['intro.wav', 'main.wav', 'outro.wav'], 'full.wav')
    """
    _ensure_init()

    if len(inputs) < 2:
        raise ValueError("concat() requires at least 2 input files")

    inputs = [str(p) for p in inputs]
    output_path = str(output_path)

    output_fmt = None
    reference_rate = None
    reference_channels = None

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
                out_encoding = sox.EncodingInfo(
                    encoding=int(input_fmt.encoding.encoding),
                    bits_per_sample=input_fmt.encoding.bits_per_sample,
                )
                output_fmt = sox.Format(
                    output_path, signal=out_signal, encoding=out_encoding, mode='w'
                )
            else:
                # Subsequent files: verify compatibility
                if input_fmt.signal.rate != reference_rate:
                    raise ValueError(
                        f"Sample rate mismatch: {input_path} has {input_fmt.signal.rate}Hz, "
                        f"expected {reference_rate}Hz"
                    )
                if input_fmt.signal.channels != reference_channels:
                    raise ValueError(
                        f"Channel count mismatch: {input_path} has {input_fmt.signal.channels} channels, "
                        f"expected {reference_channels}"
                    )

            # Copy all samples from this input to output
            while True:
                samples = input_fmt.read(chunk_size)
                if len(samples) == 0:
                    break
                output_fmt.write(samples)

            input_fmt.close()

        output_fmt.close()

    except Exception:
        if output_fmt is not None:
            output_fmt.close()
        raise
