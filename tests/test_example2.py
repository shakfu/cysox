"""Tests for example2: Display waveform visualization
Port of tests/examples/example2.c
"""
import pytest
from cysox import sox


@pytest.fixture(autouse=True)
def initialize_sox():
    """Initialize SoX before each test."""
    sox.init()
    yield
    sox.quit()


def test_example2_waveform_display():
    """Test reading and analyzing waveform blocks from an audio file.

    This is a port of example2.c which reads blocks of audio samples,
    calculates peak volumes for each channel, and displays a waveform.
    For testing, we verify the calculations work correctly.
    """
    input_file = 'tests/data/s00.wav'

    # Parameters matching example2.c
    block_period = 0.025  # seconds per block
    start_secs = 0.0
    period = 0.1  # Read 0.1 seconds for testing (faster than 2 seconds)

    # Open input file
    with sox.Format(input_file) as in_fmt:
        # Get signal info
        rate = in_fmt.signal.rate
        channels = in_fmt.signal.channels

        # Skip test if not stereo (example requires stereo)
        if channels != 2:
            pytest.skip("Example 2 requires stereo audio")

        # Calculate seek position
        seek = int(start_secs * rate * channels + 0.5)
        # Align to wide sample boundary
        seek -= seek % channels

        # Seek to starting position
        if seek > 0:
            in_fmt.seek(seek, sox.constant.SEEK_SET)

        # Calculate block size in samples
        block_size = int(block_period * rate * channels + 0.5)
        # Align to wide sample boundary
        block_size -= block_size % channels

        # Read and process blocks
        blocks_processed = 0
        max_blocks = int(period / block_period)

        while blocks_processed < max_blocks:
            samples = in_fmt.read(block_size)

            if len(samples) == 0:
                break  # EOF reached

            if len(samples) < block_size:
                # Partial block at end
                break

            # Calculate peak volumes for left and right channels
            left_peak = 0.0
            right_peak = 0.0

            for i in range(len(samples)):
                # Convert sox_sample_t (32-bit signed int) to float in range [-1.0, 1.0]
                # SOX_SAMPLE_MAX is typically 2147483647 (2^31 - 1)
                sample_float = samples[i] / 2147483647.0

                # Samples are interleaved: even indices are left, odd are right
                if i % 2 == 0:
                    left_peak = max(left_peak, abs(sample_float))
                else:
                    right_peak = max(right_peak, abs(sample_float))

            # Verify peaks are in valid range [0.0, 1.0]
            assert 0.0 <= left_peak <= 1.0, f"Left peak {left_peak} out of range"
            assert 0.0 <= right_peak <= 1.0, f"Right peak {right_peak} out of range"

            blocks_processed += 1

        # Verify we processed some blocks
        assert blocks_processed > 0, "Should have processed at least one block"


def test_example2_with_seek():
    """Test waveform reading starting from a non-zero position."""
    input_file = 'tests/data/s00.wav'

    with sox.Format(input_file) as in_fmt:
        if in_fmt.signal.channels != 2:
            pytest.skip("Example 2 requires stereo audio")

        # Seek to 0.5 seconds in
        start_secs = 0.5
        rate = in_fmt.signal.rate
        channels = in_fmt.signal.channels

        seek = int(start_secs * rate * channels + 0.5)
        seek -= seek % channels

        result = in_fmt.seek(seek, sox.constant.SEEK_SET)
        assert result == sox.SUCCESS

        # Read a block and verify we got data
        block_size = 1024
        samples = in_fmt.read(block_size)
        assert len(samples) > 0, "Should be able to read after seeking"
