# Type stubs for cysox.onset (Cython extension module)
# This file provides type hints for the onset detection API

from typing import List, Union
from pathlib import Path

def detect_onsets(
    samples: List[int],
    sample_rate: int,
    channels: int,
    threshold: float = 0.3,
    sensitivity: float = 1.5,
    min_spacing: float = 0.05,
    method: str = "hfc",
    frame_size: int = 1024,
    hop_size: int = 256,
    n_mels: int = 138,
    fmin: float = 27.5,
    fmax: float = 16000.0,
    max_size: int = 3,
    lag: int = 2,
) -> List[float]:
    """Detect onsets (transients) in audio samples.

    Args:
        samples: Audio samples as a list of int32 values (sox_sample_t format).
                 For stereo, samples are interleaved [L, R, L, R, ...].
        sample_rate: Sample rate in Hz.
        channels: Number of audio channels.
        threshold: Detection threshold 0.0-1.0 (lower = more sensitive).
                   Default 0.3 works well for most drum loops.
        sensitivity: Peak picking sensitivity 1.0-3.0 (higher = stricter).
                     Default 1.5 balances false positives and missed onsets.
        min_spacing: Minimum time between onsets in seconds.
                     Default 0.05 (50ms) prevents double triggers.
        method: Detection method - 'hfc' (default, best for drums),
                'flux' (spectral flux), 'energy', 'complex', or 'superflux'.
        frame_size: Analysis frame size (default 1024).
        hop_size: Hop size between frames (default 256).
        n_mels: Number of mel bands (superflux only, default 138).
        fmin: Min frequency in Hz (superflux only, default 27.5).
        fmax: Max frequency in Hz (superflux only, default 16000).
        max_size: Max-filter width (superflux only, default 3).
        lag: Frame lag for reference comparison (superflux only, default 2).

    Returns:
        List of onset times in seconds.
    """
    ...

def detect(
    path: Union[str, Path],
    threshold: float = 0.3,
    sensitivity: float = 1.5,
    min_spacing: float = 0.05,
    method: str = "hfc",
    frame_size: int = 1024,
    hop_size: int = 256,
    n_mels: int = 138,
    fmin: float = 27.5,
    fmax: float = 16000.0,
    max_size: int = 3,
    lag: int = 2,
) -> List[float]:
    """Detect onsets in an audio file.

    Convenience function that handles file reading.

    Args:
        path: Path to audio file.
        threshold: Detection threshold 0.0-1.0 (lower = more sensitive).
        sensitivity: Peak picking sensitivity 1.0-3.0.
        min_spacing: Minimum time between onsets in seconds.
        method: Detection method - 'hfc', 'flux', 'energy', 'complex',
                or 'superflux'.
        frame_size: Analysis frame size.
        hop_size: Hop size between frames.
        n_mels: Number of mel bands (superflux only, default 138).
        fmin: Min frequency in Hz (superflux only, default 27.5).
        fmax: Max frequency in Hz (superflux only, default 16000).
        max_size: Max-filter width (superflux only, default 3).
        lag: Frame lag for reference comparison (superflux only, default 2).

    Returns:
        List of onset times in seconds.
    """
    ...
