"""Cheap, dependency-free signal measurements for effect tests.

The fx suites used to assert only that an output file exists, which cannot
tell a working effect from one that emitted silence, dropped a channel, or
changed behaviour across a libsox version. These helpers give the tests
something to actually check, without pulling numpy into a zero-dependency
project.

Everything here is built from `cysox.stream()` and `cysox.info()`, and is
written to stay at C speed: the per-sample work is done by `max`, `min`,
`sum(map(abs, ...))`, `bytes.translate`, and a big-integer XOR popcount for
zero crossings, so a full pass over the test file costs single-digit
milliseconds.
"""

from array import array

import cysox

# sox_sample_t is int32; full scale is 2**31.
FULL_SCALE = 2147483648.0

# Cap on the samples used for zero-crossing rate. The measurement is a coarse
# spectral-centroid proxy, so a couple of seconds is plenty and keeps the
# suite fast.
ZCR_SAMPLE_CAP = 200_000

# Maps a signed int32's most-significant byte to a 0/1 sign flag.
_SIGN_TABLE = bytes(1 if b >= 128 else 0 for b in range(256))


def read_samples(path):
    """Read a whole file as an `array('i')` of interleaved int32 samples."""
    samples = array("i")
    for chunk in cysox.stream(str(path)):
        samples.frombytes(bytes(chunk))
    return samples


def zero_crossing_rate(channel):
    """Sign changes per sample in a single channel.

    A rough spectral-centroid proxy: low-passed audio crosses zero less often,
    high-passed audio more often. Computed by reducing each sample to its sign
    bit, then XOR-ing the signal against itself shifted by one sample and
    counting set bits -- all of which happens in C.
    """
    if len(channel) < 2:
        return 0.0
    signs = channel.tobytes()[3::4].translate(_SIGN_TABLE)
    if len(signs) < 2:
        return 0.0
    a = int.from_bytes(signs[:-1], "big")
    b = int.from_bytes(signs[1:], "big")
    return bin(a ^ b).count("1") / (len(signs) - 1)


class Metrics:
    """Measured properties of an audio file."""

    __slots__ = (
        "path",
        "rate",
        "channels",
        "encoding",
        "bits",
        "duration",
        "peak",
        "mean_abs",
        "n_samples",
        "_first_channel",
        "_zcr",
    )

    def __init__(self, path):
        info = cysox.info(str(path))
        self.path = str(path)
        self.rate = info.sample_rate
        self.channels = info.channels
        self.encoding = info.encoding
        self.bits = info.bits_per_sample
        self.duration = info.duration

        samples = read_samples(path)
        self.n_samples = len(samples)
        self._zcr = None

        if not samples:
            self.peak = 0.0
            self.mean_abs = 0.0
            self._first_channel = samples
            return

        self.peak = max(max(samples), -min(samples)) / FULL_SCALE
        self.mean_abs = sum(map(abs, samples)) / len(samples) / FULL_SCALE

        # Zero crossings are computed on demand -- only the filter and pitch
        # tests need them, and they are the priciest measurement. Keep the
        # first channel only; interleaving would manufacture crossings that
        # are not in the signal.
        first = samples[:: self.channels] if self.channels > 1 else samples
        self._first_channel = first[:ZCR_SAMPLE_CAP]

    @property
    def zcr(self):
        """Zero-crossing rate of the first channel (computed on first access)."""
        if self._zcr is None:
            self._zcr = zero_crossing_rate(self._first_channel)
        return self._zcr

    def __repr__(self):
        return (
            f"Metrics({self.path!r}, {self.rate} Hz, {self.channels} ch, "
            f"{self.encoding!r}/{self.bits}, {self.duration:.3f}s, "
            f"peak={self.peak:.4f}, mean_abs={self.mean_abs:.5f}, zcr={self.zcr:.4f})"
        )


def measure(path):
    """Measure an audio file. See :class:`Metrics`."""
    return Metrics(path)


def assert_audio(
    path,
    *,
    rate=None,
    channels=None,
    encoding=None,
    bits=None,
    duration=None,
    duration_tol=0.05,
    min_peak=1e-4,
    max_peak=1.0,
):
    """Assert an output file is real audio with the expected shape.

    `min_peak` defaults above zero, so silence -- the most common way for an
    effect to fail while still producing a valid file -- is caught by default.

    Returns the :class:`Metrics` so callers can make further assertions.
    """
    m = measure(path)

    assert m.n_samples > 0, f"{path}: no samples"
    if rate is not None:
        assert m.rate == rate, f"{path}: rate {m.rate} != {rate}"
    if channels is not None:
        assert m.channels == channels, f"{path}: channels {m.channels} != {channels}"
    if encoding is not None:
        assert m.encoding == encoding, f"{path}: encoding {m.encoding!r} != {encoding!r}"
    if bits is not None:
        assert m.bits == bits, f"{path}: bits {m.bits} != {bits}"
    if duration is not None:
        assert abs(m.duration - duration) <= duration_tol * max(duration, 1e-9), (
            f"{path}: duration {m.duration:.3f}s != {duration:.3f}s "
            f"(tolerance {duration_tol:.0%})"
        )
    assert m.peak >= min_peak, f"{path}: peak {m.peak:.6f} below {min_peak} (silent?)"
    assert m.peak <= max_peak, f"{path}: peak {m.peak:.6f} above {max_peak}"
    return m


def assert_ratio(actual, expected, tol, what):
    """Assert `actual` is within `tol` (fractional) of `expected`."""
    assert expected > 0, f"{what}: expected must be positive, got {expected}"
    ratio = actual / expected
    assert abs(ratio - 1.0) <= tol, (
        f"{what}: {actual:.6g} vs expected {expected:.6g} "
        f"(ratio {ratio:.3f}, tolerance {tol:.0%})"
    )
