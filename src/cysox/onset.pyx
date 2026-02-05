# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# cython: cdivision=True
"""Onset detection module for transient detection in audio.

This module provides C-optimized onset detection for finding transients,
drum hits, and other audio events. Useful for automatic slicing of loops.

Algorithms implemented:
- High-Frequency Content (HFC): Best for percussive transients
- Spectral Flux: Good for general onsets including tonal changes
- Energy-based: Simple and fast, good for drums
- Complex domain: Combines phase and magnitude changes

Example:
    >>> from cysox import onset
    >>> onsets = onset.detect('drums.wav', threshold=0.3, sensitivity=1.5)
    >>> print(f"Found {len(onsets)} onsets")
"""

from libc.stdlib cimport malloc, free, calloc
from libc.math cimport sqrt, fabs, log, exp, pow, sin, cos, atan2, M_PI
from libc.string cimport memset, memcpy

import cython


# Frame/hop sizes for analysis
DEF DEFAULT_FRAME_SIZE = 1024
DEF DEFAULT_HOP_SIZE = 256


cdef struct OnsetParams:
    double threshold       # Detection threshold (0.0-1.0)
    double sensitivity     # Peak picking sensitivity (1.0-3.0)
    double min_spacing     # Minimum time between onsets in seconds
    int frame_size         # FFT frame size
    int hop_size           # Hop size between frames
    int method             # Detection method


# Detection methods
DEF METHOD_HFC = 0        # High-Frequency Content
DEF METHOD_FLUX = 1       # Spectral Flux
DEF METHOD_ENERGY = 2     # Energy-based
DEF METHOD_COMPLEX = 3    # Complex domain


cdef inline double hann_window(int n, int N) noexcept nogil:
    """Hann window function."""
    return 0.5 * (1.0 - cos(2.0 * M_PI * n / (N - 1)))


cdef void apply_window(double* samples, double* windowed, int size) noexcept nogil:
    """Apply Hann window to samples."""
    cdef int i
    for i in range(size):
        windowed[i] = samples[i] * hann_window(i, size)


cdef void compute_magnitude_spectrum(double* windowed, double* magnitude,
                                     double* phase, int frame_size) noexcept nogil:
    """Compute magnitude and phase spectrum using DFT.

    Note: This is a simple O(n^2) DFT for correctness. For production use
    with very large frame sizes, consider using FFTW via cython bindings.
    For typical frame sizes (512-2048), this is efficient enough.
    """
    cdef int k, n
    cdef int half_size = frame_size // 2 + 1
    cdef double real_part, imag_part
    cdef double angle

    for k in range(half_size):
        real_part = 0.0
        imag_part = 0.0
        for n in range(frame_size):
            angle = -2.0 * M_PI * k * n / frame_size
            real_part += windowed[n] * cos(angle)
            imag_part += windowed[n] * sin(angle)

        magnitude[k] = sqrt(real_part * real_part + imag_part * imag_part)
        phase[k] = atan2(imag_part, real_part)


cdef double compute_hfc(double* magnitude, int half_size) noexcept nogil:
    """Compute High-Frequency Content detection function.

    HFC weights frequency bins by their index, emphasizing high frequencies
    which are prominent in percussive transients (drum attacks, etc).
    """
    cdef int k
    cdef double hfc = 0.0

    for k in range(half_size):
        # Weight by frequency bin index (higher frequencies weighted more)
        hfc += (<double>k * k) * magnitude[k] * magnitude[k]

    return sqrt(hfc) if hfc > 0 else 0.0


cdef double compute_spectral_flux(double* magnitude, double* prev_magnitude,
                                  int half_size) noexcept nogil:
    """Compute Spectral Flux detection function.

    Measures the increase in spectral energy between frames.
    Uses half-wave rectification (only counts increases, not decreases).
    """
    cdef int k
    cdef double flux = 0.0
    cdef double diff

    for k in range(half_size):
        diff = magnitude[k] - prev_magnitude[k]
        # Half-wave rectification: only positive differences (onsets, not offsets)
        if diff > 0:
            flux += diff * diff

    return sqrt(flux)


cdef double compute_energy(double* samples, int frame_size) noexcept nogil:
    """Compute frame energy (RMS)."""
    cdef int i
    cdef double energy = 0.0

    for i in range(frame_size):
        energy += samples[i] * samples[i]

    return sqrt(energy / frame_size)


cdef double compute_complex_domain(double* magnitude, double* phase,
                                   double* prev_magnitude, double* prev_phase,
                                   double* prev_prev_phase,
                                   int half_size) noexcept nogil:
    """Compute Complex Domain detection function.

    Combines magnitude and phase information. Detects when there's a
    deviation from the expected phase (phase prediction error).
    """
    cdef int k
    cdef double cd = 0.0
    cdef double predicted_phase, phase_deviation
    cdef double target_real, target_imag
    cdef double actual_real, actual_imag
    cdef double diff_real, diff_imag

    for k in range(half_size):
        # Predict phase based on previous two frames (linear prediction)
        predicted_phase = 2.0 * prev_phase[k] - prev_prev_phase[k]

        # Target: what we expected
        target_real = prev_magnitude[k] * cos(predicted_phase)
        target_imag = prev_magnitude[k] * sin(predicted_phase)

        # Actual: what we got
        actual_real = magnitude[k] * cos(phase[k])
        actual_imag = magnitude[k] * sin(phase[k])

        # Complex distance
        diff_real = actual_real - target_real
        diff_imag = actual_imag - target_imag
        cd += sqrt(diff_real * diff_real + diff_imag * diff_imag)

    return cd


cdef void median_filter(double* signal, double* filtered, int length,
                        int window_size) noexcept nogil:
    """Apply median filter to signal (for adaptive threshold)."""
    cdef int i, j, k
    cdef int half_window = window_size // 2
    cdef int start, end, count
    cdef double* window_vals = <double*>malloc(window_size * sizeof(double))
    cdef double temp

    if window_vals == NULL:
        return

    for i in range(length):
        # Gather window values
        start = i - half_window
        end = i + half_window + 1
        count = 0

        for j in range(start, end):
            if 0 <= j < length:
                window_vals[count] = signal[j]
                count += 1

        # Simple insertion sort for small window
        for j in range(1, count):
            temp = window_vals[j]
            k = j - 1
            while k >= 0 and window_vals[k] > temp:
                window_vals[k + 1] = window_vals[k]
                k -= 1
            window_vals[k + 1] = temp

        # Median is middle value
        filtered[i] = window_vals[count // 2]

    free(window_vals)


cdef int pick_peaks(double* odf, double* threshold_curve, int num_frames,
                    int min_spacing_frames, double sensitivity,
                    int* peaks, int max_peaks) noexcept nogil:
    """Pick peaks from onset detection function.

    Uses adaptive thresholding with the median filter output as baseline.
    """
    cdef int i, j
    cdef int num_peaks = 0
    cdef int last_peak = -min_spacing_frames - 1
    cdef double adaptive_threshold
    cdef bint is_peak

    for i in range(1, num_frames - 1):
        if num_peaks >= max_peaks:
            break

        # Adaptive threshold: median + sensitivity * median
        adaptive_threshold = threshold_curve[i] * sensitivity

        # Check if this is a local maximum and exceeds threshold
        is_peak = (odf[i] > odf[i - 1] and
                   odf[i] > odf[i + 1] and
                   odf[i] > adaptive_threshold)

        # Enforce minimum spacing
        if is_peak and (i - last_peak) >= min_spacing_frames:
            peaks[num_peaks] = i
            num_peaks += 1
            last_peak = i

    return num_peaks


def detect_onsets(samples, int sample_rate, int channels,
                  double threshold=0.3, double sensitivity=1.5,
                  double min_spacing=0.05, str method='hfc',
                  int frame_size=DEFAULT_FRAME_SIZE,
                  int hop_size=DEFAULT_HOP_SIZE):
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
                'flux' (spectral flux), 'energy', or 'complex'.
        frame_size: Analysis frame size (default 1024).
        hop_size: Hop size between frames (default 256).

    Returns:
        List of onset times in seconds.

    Example:
        >>> from cysox import sox, onset
        >>> sox.init()
        >>> with sox.Format('drums.wav') as f:
        ...     samples = f.read(f.signal.length)
        ...     onsets = onset.detect_onsets(
        ...         samples, int(f.signal.rate), f.signal.channels,
        ...         threshold=0.3, sensitivity=1.5)
        >>> print(f"Found {len(onsets)} transients")
    """
    cdef int method_id
    if method == 'hfc':
        method_id = METHOD_HFC
    elif method == 'flux':
        method_id = METHOD_FLUX
    elif method == 'energy':
        method_id = METHOD_ENERGY
    elif method == 'complex':
        method_id = METHOD_COMPLEX
    else:
        raise ValueError(f"Unknown method: {method}. Use 'hfc', 'flux', 'energy', or 'complex'.")

    cdef int num_samples = len(samples)
    cdef int mono_samples = num_samples // channels

    if mono_samples < frame_size:
        return []

    cdef int num_frames = (mono_samples - frame_size) // hop_size + 1
    if num_frames < 3:
        return []

    cdef int half_size = frame_size // 2 + 1

    # Allocate buffers
    cdef double* mono_buffer = <double*>calloc(mono_samples, sizeof(double))
    cdef double* frame_buffer = <double*>malloc(frame_size * sizeof(double))
    cdef double* windowed = <double*>malloc(frame_size * sizeof(double))
    cdef double* magnitude = <double*>calloc(half_size, sizeof(double))
    cdef double* phase = <double*>calloc(half_size, sizeof(double))
    cdef double* prev_magnitude = <double*>calloc(half_size, sizeof(double))
    cdef double* prev_phase = <double*>calloc(half_size, sizeof(double))
    cdef double* prev_prev_phase = <double*>calloc(half_size, sizeof(double))
    cdef double* odf = <double*>calloc(num_frames, sizeof(double))
    cdef double* threshold_curve = <double*>calloc(num_frames, sizeof(double))
    cdef int* peaks = <int*>malloc(num_frames * sizeof(int))

    if (mono_buffer == NULL or frame_buffer == NULL or windowed == NULL or
        magnitude == NULL or phase == NULL or prev_magnitude == NULL or
        prev_phase == NULL or prev_prev_phase == NULL or odf == NULL or
        threshold_curve == NULL or peaks == NULL):
        # Cleanup and raise
        free(mono_buffer)
        free(frame_buffer)
        free(windowed)
        free(magnitude)
        free(phase)
        free(prev_magnitude)
        free(prev_phase)
        free(prev_prev_phase)
        free(odf)
        free(threshold_curve)
        free(peaks)
        raise MemoryError("Failed to allocate onset detection buffers")

    cdef int i, j, frame_idx
    cdef double sample_val, max_odf, odf_val
    cdef int frame_start
    cdef int min_spacing_frames
    cdef int num_peaks
    cdef double* temp_ptr
    cdef int median_window

    try:
        # Convert to mono double (mix down channels, normalize from int32)
        for i in range(mono_samples):
            sample_val = 0.0
            for j in range(channels):
                sample_val += <double>samples[i * channels + j]
            mono_buffer[i] = sample_val / (channels * 2147483648.0)  # Normalize from int32

        # Compute onset detection function for each frame
        max_odf = 0.0
        for frame_idx in range(num_frames):
            frame_start = frame_idx * hop_size

            # Copy frame
            for i in range(frame_size):
                frame_buffer[i] = mono_buffer[frame_start + i]

            # Apply window
            apply_window(frame_buffer, windowed, frame_size)

            # Compute spectrum (needed for most methods)
            if method_id != METHOD_ENERGY:
                # Store previous phase for complex domain
                temp_ptr = prev_prev_phase
                prev_prev_phase = prev_phase
                prev_phase = phase
                phase = temp_ptr

                # Store previous magnitude
                memcpy(prev_magnitude, magnitude, half_size * sizeof(double))

                # Compute new spectrum
                compute_magnitude_spectrum(windowed, magnitude, phase, frame_size)

            # Compute detection function value
            if method_id == METHOD_HFC:
                odf_val = compute_hfc(magnitude, half_size)
            elif method_id == METHOD_FLUX:
                odf_val = compute_spectral_flux(magnitude, prev_magnitude, half_size)
            elif method_id == METHOD_ENERGY:
                odf_val = compute_energy(frame_buffer, frame_size)
            else:  # METHOD_COMPLEX
                odf_val = compute_complex_domain(magnitude, phase, prev_magnitude,
                                                 prev_phase, prev_prev_phase, half_size)

            odf[frame_idx] = odf_val
            if odf_val > max_odf:
                max_odf = odf_val

        # Normalize ODF
        if max_odf > 0:
            for frame_idx in range(num_frames):
                odf[frame_idx] /= max_odf

        # Compute adaptive threshold curve using median filter (on unthresholded ODF)
        # Window size: roughly 100ms worth of frames
        median_window = max(3, int(0.1 * sample_rate / hop_size))
        if median_window % 2 == 0:
            median_window += 1  # Ensure odd

        median_filter(odf, threshold_curve, num_frames, median_window)

        # Apply threshold as minimum floor for the adaptive threshold curve
        # This ensures peaks must exceed both the adaptive threshold AND the global threshold
        for frame_idx in range(num_frames):
            if threshold_curve[frame_idx] < threshold:
                threshold_curve[frame_idx] = threshold

        # Pick peaks
        min_spacing_frames = max(1, int(min_spacing * sample_rate / hop_size))
        num_peaks = pick_peaks(odf, threshold_curve, num_frames,
                               min_spacing_frames, sensitivity,
                               peaks, num_frames)

        # Convert frame indices to time
        result = []
        for i in range(num_peaks):
            frame_idx = peaks[i]
            time_sec = <double>(frame_idx * hop_size) / sample_rate
            result.append(time_sec)

        return result

    finally:
        free(mono_buffer)
        free(frame_buffer)
        free(windowed)
        free(magnitude)
        free(phase)
        free(prev_magnitude)
        free(prev_phase)
        free(prev_prev_phase)
        free(odf)
        free(threshold_curve)
        free(peaks)


def detect(path, double threshold=0.3, double sensitivity=1.5,
           double min_spacing=0.05, str method='hfc',
           int frame_size=DEFAULT_FRAME_SIZE, int hop_size=DEFAULT_HOP_SIZE):
    """Detect onsets in an audio file.

    Convenience function that handles file reading.

    Args:
        path: Path to audio file.
        threshold: Detection threshold 0.0-1.0 (lower = more sensitive).
        sensitivity: Peak picking sensitivity 1.0-3.0.
        min_spacing: Minimum time between onsets in seconds.
        method: Detection method - 'hfc', 'flux', 'energy', or 'complex'.
        frame_size: Analysis frame size.
        hop_size: Hop size between frames.

    Returns:
        List of onset times in seconds.

    Example:
        >>> from cysox import onset
        >>> onsets = onset.detect('drums.wav', threshold=0.3)
        >>> for t in onsets:
        ...     print(f"Onset at {t:.3f}s")
    """
    from . import sox
    from .audio import _ensure_init

    _ensure_init()

    path = str(path)
    with sox.Format(path) as f:
        samples = f.read(f.signal.length)
        sample_rate = int(f.signal.rate)
        channels = f.signal.channels

    return detect_onsets(samples, sample_rate, channels,
                         threshold=threshold, sensitivity=sensitivity,
                         min_spacing=min_spacing, method=method,
                         frame_size=frame_size, hop_size=hop_size)
