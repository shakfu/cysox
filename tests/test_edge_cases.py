"""Edge case tests for cysox.

Tests unusual inputs, boundary conditions, and error handling paths.
"""

import os
import struct
import tempfile

import pytest
import cysox  # For auto-init
from cysox import sox


class TestZeroLengthFiles:
    """Test handling of zero-length and minimal audio files."""

    def test_zero_length_signal_info(self):
        """Create SignalInfo with zero length."""
        signal = sox.SignalInfo(rate=44100, channels=2, precision=16, length=0)
        assert signal.length == 0
        assert signal.rate == 44100

    def test_write_empty_file(self, output_path):
        """Write a file with no samples."""
        signal = sox.SignalInfo(rate=44100, channels=2, precision=16)
        with sox.Format(str(output_path), signal=signal, mode='w') as f:
            # Write nothing, just close
            pass

        # File should exist but be minimal (just headers)
        assert output_path.exists()
        file_size = output_path.stat().st_size
        assert file_size > 0  # At least headers
        assert file_size < 100  # But not much more

    def test_read_zero_samples(self, test_wav_str):
        """Request zero samples from a file."""
        with sox.Format(test_wav_str) as f:
            samples = f.read(0)
            assert len(samples) == 0


class TestUnusualSampleRates:
    """Test handling of unusual sample rates."""

    @pytest.mark.parametrize("rate", [
        1,           # Minimum
        8000,        # Telephony
        11025,       # Low quality
        22050,       # Medium quality
        44100,       # CD quality
        48000,       # Professional
        96000,       # High-res
        192000,      # Ultra high-res
        384000,      # Maximum common
    ])
    def test_various_sample_rates(self, rate):
        """Test SignalInfo with various sample rates."""
        signal = sox.SignalInfo(rate=rate, channels=2, precision=16)
        assert signal.rate == rate

    def test_fractional_sample_rate(self):
        """Test SignalInfo with fractional sample rate."""
        signal = sox.SignalInfo(rate=44100.5, channels=2, precision=16)
        assert abs(signal.rate - 44100.5) < 0.01

    def test_rate_conversion_extreme(self, test_wav_str, output_path):
        """Test rate conversion between extreme rates."""
        input_fmt = sox.Format(test_wav_str)
        out_signal = sox.SignalInfo(
            rate=8000,  # Downsample significantly
            channels=input_fmt.signal.channels,
            precision=input_fmt.signal.precision
        )
        output_fmt = sox.Format(str(output_path), signal=out_signal, mode='w')

        chain = sox.EffectsChain(input_fmt.encoding, output_fmt.encoding)

        # Input
        e = sox.Effect(sox.find_effect("input"))
        e.set_options([input_fmt])
        chain.add_effect(e, input_fmt.signal, input_fmt.signal)

        # Rate conversion
        e = sox.Effect(sox.find_effect("rate"))
        e.set_options(["8000"])
        chain.add_effect(e, input_fmt.signal, out_signal)

        # Output
        e = sox.Effect(sox.find_effect("output"))
        e.set_options([output_fmt])
        chain.add_effect(e, out_signal, out_signal)

        result = chain.flow_effects()
        assert result == sox.SUCCESS

        input_fmt.close()
        output_fmt.close()

        # Verify output was created
        assert output_path.exists()
        assert output_path.stat().st_size > 0


class TestUnusualChannelCounts:
    """Test handling of unusual channel configurations."""

    @pytest.mark.parametrize("channels", [1, 2, 4, 6, 8])
    def test_various_channel_counts(self, channels):
        """Test SignalInfo with various channel counts."""
        signal = sox.SignalInfo(rate=44100, channels=channels, precision=16)
        assert signal.channels == channels

    def test_mono_to_stereo_conversion(self, test_wav_str, output_path):
        """Test converting mono to stereo."""
        input_fmt = sox.Format(test_wav_str)
        out_signal = sox.SignalInfo(
            rate=input_fmt.signal.rate,
            channels=2,
            precision=input_fmt.signal.precision
        )
        output_fmt = sox.Format(str(output_path), signal=out_signal, mode='w')

        chain = sox.EffectsChain(input_fmt.encoding, output_fmt.encoding)

        # Input
        e = sox.Effect(sox.find_effect("input"))
        e.set_options([input_fmt])
        chain.add_effect(e, input_fmt.signal, input_fmt.signal)

        # Channel conversion
        e = sox.Effect(sox.find_effect("channels"))
        e.set_options(["2"])
        chain.add_effect(e, input_fmt.signal, out_signal)

        # Output
        e = sox.Effect(sox.find_effect("output"))
        e.set_options([output_fmt])
        chain.add_effect(e, out_signal, out_signal)

        result = chain.flow_effects()
        assert result == sox.SUCCESS

        input_fmt.close()
        output_fmt.close()

        # Verify output
        with sox.Format(str(output_path)) as f:
            assert f.signal.channels == 2


class TestUnusualBitDepths:
    """Test handling of unusual bit depths."""

    @pytest.mark.parametrize("bits", [8, 16, 24, 32])
    def test_various_bit_depths(self, bits):
        """Test SignalInfo with various precisions."""
        signal = sox.SignalInfo(rate=44100, channels=2, precision=bits)
        assert signal.precision == bits

    @pytest.mark.parametrize("bits", [8, 16, 24])
    def test_encoding_info_bits(self, bits):
        """Test EncodingInfo with various bits_per_sample."""
        encoding = sox.EncodingInfo(encoding=1, bits_per_sample=bits)
        assert encoding.bits_per_sample == bits


class TestCorruptHeaders:
    """Test handling of corrupt or malformed files."""

    def test_nonexistent_file(self):
        """Opening a nonexistent file should raise an error."""
        with pytest.raises(Exception):
            sox.Format("/nonexistent/path/to/file.wav")

    def test_empty_file(self):
        """Opening an empty file should raise an error."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            empty_path = f.name

        try:
            with pytest.raises(Exception):
                sox.Format(empty_path)
        finally:
            os.unlink(empty_path)

    def test_truncated_wav_header(self):
        """Opening a file with truncated WAV header should raise an error."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            # Write partial WAV header (only RIFF chunk, incomplete)
            f.write(b'RIFF')
            f.write(struct.pack('<I', 36))  # File size (incorrect)
            f.write(b'WAVE')
            # Missing fmt and data chunks
            truncated_path = f.name

        try:
            with pytest.raises(Exception):
                sox.Format(truncated_path)
        finally:
            os.unlink(truncated_path)

    def test_invalid_wav_header(self):
        """Opening a file with invalid WAV header should raise an error."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            # Write invalid header
            f.write(b'INVALID_HEADER_DATA_NOT_WAVE')
            invalid_path = f.name

        try:
            with pytest.raises(Exception):
                sox.Format(invalid_path)
        finally:
            os.unlink(invalid_path)

    def test_wrong_extension(self, test_wav_str):
        """Test opening a file with wrong extension."""
        # Create a valid WAV file with wrong extension
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            wrong_ext_path = f.name

        try:
            # Copy actual WAV content
            with open(test_wav_str, 'rb') as src:
                with open(wrong_ext_path, 'wb') as dst:
                    dst.write(src.read())

            # sox should still be able to detect the format
            with sox.Format(wrong_ext_path) as f:
                assert f.signal.rate > 0
        finally:
            os.unlink(wrong_ext_path)


class TestLargeValues:
    """Test handling of large values and potential overflows."""

    def test_large_length(self):
        """Test SignalInfo with very large length."""
        # 4GB worth of samples at 16-bit stereo
        large_length = (4 * 1024 * 1024 * 1024) // 4
        signal = sox.SignalInfo(rate=44100, channels=2, precision=16, length=large_length)
        assert signal.length == large_length

    def test_large_read_request(self, test_wav_str):
        """Request more samples than file contains."""
        with sox.Format(test_wav_str) as f:
            file_length = f.signal.length
            # Request 10x more than available
            samples = f.read(file_length * 10)
            # Should return only what's available
            assert len(samples) <= file_length

    def test_large_buffer_allocation(self, test_wav_str):
        """Test read_buffer with large size."""
        with sox.Format(test_wav_str) as f:
            file_length = f.signal.length
            # Request exact file length
            buf = f.read_buffer(file_length)
            assert len(buf) == file_length


class TestBoundaryConditions:
    """Test boundary conditions and edge values."""

    def test_read_exactly_file_length(self, test_wav_str):
        """Read exactly the file length."""
        with sox.Format(test_wav_str) as f:
            length = f.signal.length
            samples = f.read(length)
            assert len(samples) == length

    def test_read_minimal_samples(self, test_wav_str):
        """Read minimal number of samples (one frame = channels samples)."""
        with sox.Format(test_wav_str) as f:
            channels = f.signal.channels
            # Read one frame worth of samples
            samples = f.read(channels)
            assert len(samples) == channels

    def test_read_after_eof(self, test_wav_str):
        """Read after reaching end of file."""
        with sox.Format(test_wav_str) as f:
            # Read entire file
            length = f.signal.length
            _ = f.read(length)
            # Try to read more
            samples = f.read(1000)
            assert len(samples) == 0

    def test_write_single_sample(self, output_path):
        """Write a single sample."""
        signal = sox.SignalInfo(rate=44100, channels=1, precision=16)
        with sox.Format(str(output_path), signal=signal, mode='w') as f:
            f.write([0])  # Single sample

        assert output_path.exists()

    def test_loop_info_boundaries(self):
        """Test LoopInfo with boundary values."""
        # Zero values
        loop = sox.LoopInfo(start=0, length=0, count=0, type=0)
        assert loop.start == 0
        assert loop.length == 0
        assert loop.count == 0

        # Large values
        loop = sox.LoopInfo(start=2**31 - 1, length=2**31 - 1, count=255, type=7)
        assert loop.start == 2**31 - 1
        assert loop.length == 2**31 - 1


class TestNullAndEmptyInputs:
    """Test handling of null and empty inputs."""

    def test_empty_filename(self):
        """Opening with empty filename should raise an error."""
        with pytest.raises(Exception):
            sox.Format("")

    def test_write_empty_list(self, output_path):
        """Writing an empty list of samples."""
        signal = sox.SignalInfo(rate=44100, channels=2, precision=16)
        with sox.Format(str(output_path), signal=signal, mode='w') as f:
            result = f.write([])
            assert result == 0  # Zero samples written

    def test_effect_empty_options(self):
        """Test effect with empty options list."""
        handler = sox.find_effect("reverb")
        effect = sox.Effect(handler)
        # Should not raise - reverb has defaults
        effect.set_options([])

    def test_basename_edge_cases(self):
        """Test basename with edge case inputs."""
        # Just extension
        assert sox.basename(".wav") == ""
        # No extension
        assert sox.basename("filename") == "filename"
        # Multiple dots
        assert sox.basename("file.name.wav") == "file.name"
        # Path with dots
        assert sox.basename("/path.to/file.wav") == "file"


class TestSpecialCharacters:
    """Test handling of special characters in filenames."""

    def test_filename_with_spaces(self, test_wav_str):
        """Test file with spaces in name."""
        with tempfile.NamedTemporaryFile(suffix=".wav", prefix="test file ", delete=False) as f:
            space_path = f.name

        try:
            # Copy test file
            with open(test_wav_str, 'rb') as src:
                with open(space_path, 'wb') as dst:
                    dst.write(src.read())

            with sox.Format(space_path) as f:
                assert f.signal.rate > 0
        finally:
            os.unlink(space_path)

    def test_filename_with_unicode(self, test_wav_str):
        """Test file with unicode characters in name."""
        with tempfile.NamedTemporaryFile(suffix=".wav", prefix="test_audio_", delete=False) as f:
            unicode_path = f.name

        try:
            # Copy test file
            with open(test_wav_str, 'rb') as src:
                with open(unicode_path, 'wb') as dst:
                    dst.write(src.read())

            with sox.Format(unicode_path) as f:
                assert f.signal.rate > 0
        finally:
            os.unlink(unicode_path)
