# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# cython: cdivision=True
"""Onset detection module for transient detection in audio.

This module provides C-optimized onset detection for finding transients,
drum hits, and other audio events. Useful for automatic slicing of loops.

Uses KissFFT (BSD-3-Clause) for O(n log n) spectral analysis.

Algorithms implemented:
- High-Frequency Content (HFC): Best for percussive transients
- Spectral Flux: Good for general onsets including tonal changes
- Energy-based: Simple and fast, good for drums
- Complex domain: Combines phase and magnitude changes
- Superflux: Mel-scaled spectral flux with vibrato suppression and
  backtracking (Boeck & Widmer, DAFx 2013)

Example:
    >>> from cysox import onset
    >>> onsets = onset.detect('drums.wav', threshold=0.3, sensitivity=1.5)
    >>> print(f"Found {len(onsets)} onsets")
"""

from libc.stdlib cimport malloc, free, calloc
from libc.math cimport sqrt, fabs, log, log10, exp, pow, sin, cos, atan2, M_PI
from libc.string cimport memset, memcpy

from cysox.kissfft cimport (
    kiss_fft_scalar, kiss_fft_cpx, kiss_fft_free,
    kiss_fftr_cfg, kiss_fftr_alloc, kiss_fftr,
)

import cython


# Frame/hop sizes for analysis
DEF DEFAULT_FRAME_SIZE = 1024
DEF DEFAULT_HOP_SIZE = 256

# Superflux defaults (Boeck & Widmer 2013)
DEF DEFAULT_N_MELS = 138
DEF DEFAULT_FMIN = 27.5
DEF DEFAULT_FMAX = 16000.0
DEF DEFAULT_MAX_SIZE = 3
DEF DEFAULT_LAG = 2


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
DEF METHOD_SUPERFLUX = 4  # Superflux (mel-scaled flux + vibrato suppression)


cdef inline double hann_window(int n, int N) noexcept nogil:
    """Hann window function."""
    return 0.5 * (1.0 - cos(2.0 * M_PI * n / (N - 1)))


cdef void apply_window(double* samples, double* windowed, int size) noexcept nogil:
    """Apply Hann window to samples."""
    cdef int i
    for i in range(size):
        windowed[i] = samples[i] * hann_window(i, size)


cdef void compute_magnitude_spectrum(kiss_fftr_cfg fft_cfg,
                                     double* windowed, kiss_fft_cpx* fft_out,
                                     double* magnitude, double* phase,
                                     int frame_size) noexcept nogil:
    """Compute magnitude and phase spectrum using KissFFT (O(n log n))."""
    cdef int k
    cdef int half_size = frame_size // 2 + 1

    kiss_fftr(fft_cfg, windowed, fft_out)

    for k in range(half_size):
        magnitude[k] = sqrt(fft_out[k].r * fft_out[k].r + fft_out[k].i * fft_out[k].i)
        phase[k] = atan2(fft_out[k].i, fft_out[k].r)


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


# ---------------------------------------------------------------------------
# Mel filterbank for Superflux
# ---------------------------------------------------------------------------

cdef inline double hz_to_mel(double hz) noexcept nogil:
    """Convert frequency in Hz to mel scale."""
    return 2595.0 * log10(1.0 + hz / 700.0)


cdef inline double mel_to_hz(double mel) noexcept nogil:
    """Convert mel scale to frequency in Hz."""
    return 700.0 * (pow(10.0, mel / 2595.0) - 1.0)


cdef void build_mel_filterbank(double* filterbank, int n_mels, int n_fft_bins,
                                int sample_rate, double fmin, double fmax) noexcept nogil:
    """Build triangular mel filterbank matrix (n_mels x n_fft_bins).

    Each row is one triangular filter spanning two adjacent mel-spaced points.
    The filters are area-normalized so that narrow (high-frequency) filters
    have the same total weight as wide (low-frequency) ones.
    """
    cdef int i, k
    cdef double mel_min = hz_to_mel(fmin)
    cdef double mel_max = hz_to_mel(fmax)
    cdef double mel_step = (mel_max - mel_min) / (n_mels + 1)
    cdef double hz_per_bin = <double>sample_rate / (2 * (n_fft_bins - 1))
    cdef double center, lower, upper
    cdef double lower_slope, upper_slope, val

    for i in range(n_mels):
        lower = mel_to_hz(mel_min + mel_step * i)
        center = mel_to_hz(mel_min + mel_step * (i + 1))
        upper = mel_to_hz(mel_min + mel_step * (i + 2))

        for k in range(n_fft_bins):
            val = 0.0
            freq = k * hz_per_bin
            if lower < freq < center and center > lower:
                val = (freq - lower) / (center - lower)
            elif center <= freq < upper and upper > center:
                val = (upper - freq) / (upper - center)
            filterbank[i * n_fft_bins + k] = val


cdef void apply_mel_filterbank(double* mel_out, double* magnitude,
                                double* filterbank, int n_mels,
                                int n_fft_bins) noexcept nogil:
    """Apply mel filterbank to magnitude spectrum, producing mel-band energies."""
    cdef int i, k
    cdef double energy

    for i in range(n_mels):
        energy = 0.0
        for k in range(n_fft_bins):
            energy += filterbank[i * n_fft_bins + k] * magnitude[k] * magnitude[k]
        mel_out[i] = energy


cdef void power_to_db(double* db_out, double* power, int n) noexcept nogil:
    """Convert power spectrum to dB (10 * log10), with floor at -80 dB."""
    cdef int i
    cdef double val
    for i in range(n):
        val = power[i]
        if val < 1e-10:
            val = 1e-10
        db_out[i] = 10.0 * log10(val)


cdef void max_filter_1d(double* output, double* input, int n,
                         int max_size) noexcept nogil:
    """Maximum filter along a 1-D array (frequency axis).

    For each position, takes the max over a centered window of *max_size*.
    This suppresses vibrato-induced false onsets by spreading each spectral
    peak across neighbouring bins in the reference frame.
    """
    cdef int i, j, start, end
    cdef int half = max_size // 2
    cdef double mx

    for i in range(n):
        start = i - half
        if start < 0:
            start = 0
        end = i + half + 1
        if end > n:
            end = n
        mx = input[start]
        for j in range(start + 1, end):
            if input[j] > mx:
                mx = input[j]
        output[i] = mx


cdef double compute_superflux_odf(double* current_db, double* ref_db_maxfilt,
                                   int n_mels) noexcept nogil:
    """Superflux onset detection function value for one frame.

    Computes half-wave rectified difference between the current frame's
    log-mel spectrum and the max-filtered reference (lagged) spectrum.
    """
    cdef int i
    cdef double flux = 0.0
    cdef double diff

    for i in range(n_mels):
        diff = current_db[i] - ref_db_maxfilt[i]
        if diff > 0:
            flux += diff

    return flux


cdef void backtrack_onsets(double* odf, int* peaks, int num_peaks) noexcept nogil:
    """Walk each detected peak backward to the nearest local minimum in the ODF.

    This places the onset marker at the actual start of the transient
    rather than at the peak of the detection function.
    """
    cdef int i, j
    for i in range(num_peaks):
        j = peaks[i]
        while j > 0 and odf[j - 1] <= odf[j]:
            j -= 1
        peaks[i] = j


# ---------------------------------------------------------------------------
# Adaptive thresholding & peak picking (shared by all methods)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Main detection function
# ---------------------------------------------------------------------------

def detect_onsets(samples, int sample_rate, int channels,
                  double threshold=0.3, double sensitivity=1.5,
                  double min_spacing=0.05, str method='hfc',
                  int frame_size=DEFAULT_FRAME_SIZE,
                  int hop_size=DEFAULT_HOP_SIZE,
                  int n_mels=DEFAULT_N_MELS,
                  double fmin=DEFAULT_FMIN,
                  double fmax=DEFAULT_FMAX,
                  int max_size=DEFAULT_MAX_SIZE,
                  int lag=DEFAULT_LAG):
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
        n_mels: Number of mel bands for superflux (default 138).
        fmin: Lowest mel filter frequency in Hz for superflux (default 27.5).
        fmax: Highest mel filter frequency in Hz for superflux (default 16000).
        max_size: Maximum filter width for superflux vibrato suppression (default 3).
        lag: Number of frames to look back for superflux (default 2).

    Returns:
        List of onset times in seconds.

    Example:
        >>> from cysox import sox, onset
        >>> sox.init()
        >>> with sox.Format('drums.wav') as f:
        ...     samples = f.read(f.signal.length)
        ...     onsets = onset.detect_onsets(
        ...         samples, int(f.signal.rate), f.signal.channels,
        ...         threshold=0.3, method='superflux')
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
    elif method == 'superflux':
        method_id = METHOD_SUPERFLUX
    else:
        raise ValueError(f"Unknown method: {method}. "
                         "Use 'hfc', 'flux', 'energy', 'complex', or 'superflux'.")

    cdef int num_samples = len(samples)
    cdef int mono_samples = num_samples // channels

    if mono_samples < frame_size:
        return []

    cdef int num_frames = (mono_samples - frame_size) // hop_size + 1
    if num_frames < 3:
        return []

    cdef int half_size = frame_size // 2 + 1

    # --- Allocate common buffers ---
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

    # Allocate KissFFT config for real-valued FFT (frame_size must be even)
    cdef kiss_fftr_cfg fft_cfg = NULL
    cdef kiss_fft_cpx* fft_out = NULL
    if method_id != METHOD_ENERGY:
        fft_cfg = kiss_fftr_alloc(frame_size, 0, NULL, NULL)
        fft_out = <kiss_fft_cpx*>malloc(half_size * sizeof(kiss_fft_cpx))

    # --- Superflux-specific buffers ---
    cdef double* mel_filterbank = NULL
    cdef double* mel_spectrum = NULL
    cdef double* mel_db = NULL
    cdef double* mel_db_ring = NULL    # ring buffer: lag+1 frames of mel_db
    cdef double* ref_max_filtered = NULL
    cdef int ring_idx = 0
    cdef int ref_idx = 0
    cdef int mel_ring_size = 0

    if method_id == METHOD_SUPERFLUX:
        mel_ring_size = lag + 1
        mel_filterbank = <double*>calloc(n_mels * half_size, sizeof(double))
        mel_spectrum = <double*>calloc(n_mels, sizeof(double))
        mel_db = <double*>calloc(n_mels, sizeof(double))
        mel_db_ring = <double*>calloc(n_mels * mel_ring_size, sizeof(double))
        ref_max_filtered = <double*>calloc(n_mels, sizeof(double))

    # Check all allocations
    if (mono_buffer == NULL or frame_buffer == NULL or windowed == NULL or
        magnitude == NULL or phase == NULL or prev_magnitude == NULL or
        prev_phase == NULL or prev_prev_phase == NULL or odf == NULL or
        threshold_curve == NULL or peaks == NULL or
        (method_id != METHOD_ENERGY and (fft_cfg == NULL or fft_out == NULL))):
        _free_all(mono_buffer, frame_buffer, windowed, magnitude, phase,
                  prev_magnitude, prev_phase, prev_prev_phase, odf,
                  threshold_curve, peaks, fft_cfg, fft_out,
                  mel_filterbank, mel_spectrum, mel_db, mel_db_ring,
                  ref_max_filtered)
        raise MemoryError("Failed to allocate onset detection buffers")

    if (method_id == METHOD_SUPERFLUX and
        (mel_filterbank == NULL or mel_spectrum == NULL or mel_db == NULL or
         mel_db_ring == NULL or ref_max_filtered == NULL)):
        _free_all(mono_buffer, frame_buffer, windowed, magnitude, phase,
                  prev_magnitude, prev_phase, prev_prev_phase, odf,
                  threshold_curve, peaks, fft_cfg, fft_out,
                  mel_filterbank, mel_spectrum, mel_db, mel_db_ring,
                  ref_max_filtered)
        raise MemoryError("Failed to allocate superflux buffers")

    cdef int i, j, frame_idx
    cdef double sample_val, max_odf, odf_val
    cdef int frame_start
    cdef int min_spacing_frames
    cdef int num_peaks
    cdef double* temp_ptr
    cdef int median_window

    try:
        # Build mel filterbank if superflux
        if method_id == METHOD_SUPERFLUX:
            build_mel_filterbank(mel_filterbank, n_mels, half_size,
                                 sample_rate, fmin, fmax)

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

                # Compute new spectrum using KissFFT
                compute_magnitude_spectrum(fft_cfg, windowed, fft_out,
                                           magnitude, phase, frame_size)

            # Compute detection function value
            if method_id == METHOD_HFC:
                odf_val = compute_hfc(magnitude, half_size)
            elif method_id == METHOD_FLUX:
                odf_val = compute_spectral_flux(magnitude, prev_magnitude, half_size)
            elif method_id == METHOD_ENERGY:
                odf_val = compute_energy(frame_buffer, frame_size)
            elif method_id == METHOD_COMPLEX:
                odf_val = compute_complex_domain(magnitude, phase, prev_magnitude,
                                                 prev_phase, prev_prev_phase, half_size)
            elif method_id == METHOD_SUPERFLUX:
                # Mel filterbank -> log magnitude
                apply_mel_filterbank(mel_spectrum, magnitude, mel_filterbank,
                                     n_mels, half_size)
                power_to_db(mel_db, mel_spectrum, n_mels)

                # Store current frame's mel_db in ring buffer
                ring_idx = frame_idx % mel_ring_size
                memcpy(&mel_db_ring[ring_idx * n_mels], mel_db,
                       n_mels * sizeof(double))

                if frame_idx >= lag:
                    # Reference frame is `lag` frames back
                    ref_idx = (frame_idx - lag) % mel_ring_size
                    # Max-filter the reference along frequency axis
                    max_filter_1d(ref_max_filtered,
                                  &mel_db_ring[ref_idx * n_mels],
                                  n_mels, max_size)
                    odf_val = compute_superflux_odf(mel_db, ref_max_filtered,
                                                     n_mels)
                else:
                    odf_val = 0.0
            else:
                odf_val = 0.0

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

        # Superflux uses backtracking to find precise onset start
        if method_id == METHOD_SUPERFLUX and num_peaks > 0:
            backtrack_onsets(odf, peaks, num_peaks)

        # Convert frame indices to time
        result = []
        for i in range(num_peaks):
            frame_idx = peaks[i]
            time_sec = <double>(frame_idx * hop_size) / sample_rate
            result.append(time_sec)

        return result

    finally:
        _free_all(mono_buffer, frame_buffer, windowed, magnitude, phase,
                  prev_magnitude, prev_phase, prev_prev_phase, odf,
                  threshold_curve, peaks, fft_cfg, fft_out,
                  mel_filterbank, mel_spectrum, mel_db, mel_db_ring,
                  ref_max_filtered)


cdef void _free_all(double* mono_buffer, double* frame_buffer, double* windowed,
                    double* magnitude, double* phase, double* prev_magnitude,
                    double* prev_phase, double* prev_prev_phase, double* odf,
                    double* threshold_curve, int* peaks,
                    kiss_fftr_cfg fft_cfg, kiss_fft_cpx* fft_out,
                    double* mel_filterbank, double* mel_spectrum,
                    double* mel_db, double* mel_db_ring,
                    double* ref_max_filtered) noexcept:
    """Free all allocated buffers."""
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
    if fft_cfg != NULL:
        kiss_fft_free(fft_cfg)
    free(fft_out)
    free(mel_filterbank)
    free(mel_spectrum)
    free(mel_db)
    free(mel_db_ring)
    free(ref_max_filtered)


def detect(path, double threshold=0.3, double sensitivity=1.5,
           double min_spacing=0.05, str method='hfc',
           int frame_size=DEFAULT_FRAME_SIZE, int hop_size=DEFAULT_HOP_SIZE,
           int n_mels=DEFAULT_N_MELS, double fmin=DEFAULT_FMIN,
           double fmax=DEFAULT_FMAX, int max_size=DEFAULT_MAX_SIZE,
           int lag=DEFAULT_LAG):
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

    Example:
        >>> from cysox import onset
        >>> onsets = onset.detect('drums.wav', threshold=0.3, method='superflux')
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
                         frame_size=frame_size, hop_size=hop_size,
                         n_mels=n_mels, fmin=fmin, fmax=fmax,
                         max_size=max_size, lag=lag)
