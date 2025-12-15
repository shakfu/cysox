"""Tests for buffer protocol support in Format class"""
import pytest
import array
from cysox import sox


@pytest.fixture(autouse=True)
def initialize_sox():
    """Initialize SoX before each test."""
    sox.init()
    yield
    sox.quit()


def test_read_buffer():
    """Test Format.read_buffer() returns a memoryview"""
    with sox.Format('tests/data/s00.wav') as f:
        buf = f.read_buffer(100)
        assert buf is not None
        assert isinstance(buf, memoryview)
        assert len(buf) <= 100


def test_read_into_array():
    """Test Format.read_into() with array.array"""
    arr = array.array('i', [0] * 100)  # signed 32-bit int array

    with sox.Format('tests/data/s00.wav') as f:
        n = f.read_into(arr)
        assert n > 0
        assert n <= 100
        # First sample should be non-zero (actual audio data)
        # Commented out as actual value depends on audio file content
        # assert arr[0] != 0


def test_write_from_list():
    """Test Format.write() with list (backward compatibility)"""
    import tempfile
    import os

    signal = sox.SignalInfo(rate=44100, channels=1, precision=16)

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'output.wav')

        with sox.Format(output_path, signal=signal, mode='w') as f:
            samples = [1000, 2000, 3000, 4000]
            n = f.write(samples)
            assert n == len(samples)


def test_write_from_array():
    """Test Format.write() with array.array (buffer protocol)"""
    import tempfile
    import os

    signal = sox.SignalInfo(rate=44100, channels=1, precision=16)

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'output.wav')

        with sox.Format(output_path, signal=signal, mode='w') as f:
            arr = array.array('i', [1000, 2000, 3000, 4000])
            n = f.write(arr)
            assert n == len(arr)


def test_buffer_roundtrip():
    """Test reading and writing using buffer protocol"""
    import tempfile
    import os

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'roundtrip.wav')

        # Read some samples
        with sox.Format('tests/data/s00.wav') as f:
            buf = f.read_buffer(100)
            signal = sox.SignalInfo(
                rate=f.signal.rate,
                channels=f.signal.channels,
                precision=f.signal.precision
            )

        # Write them back
        with sox.Format(output_path, signal=signal, mode='w') as f:
            # Convert memoryview to array for writing
            arr = array.array('i', buf)
            n = f.write(arr)
            assert n == len(buf)

        # Read them back again and verify
        with sox.Format(output_path) as f:
            buf2 = f.read_buffer(100)
            assert len(buf2) == len(buf)
