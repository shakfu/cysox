"""Tests for example6: Explicit format conversion
Port of tests/examples/example6.c
"""
import pytest
import tempfile
import os
from cysox import sox


@pytest.fixture(autouse=True)
def initialize_sox():
    """Initialize SoX before each test."""
    sox.init()
    yield
    sox.quit()


def test_example6_explicit_conversion():
    """Test explicit format conversion to mono mu-law at 8kHz.

    This is a port of example6.c which demonstrates explicitly specifying
    output file signal and encoding attributes to convert any input file
    to mono mu-law at 8kHz sampling rate.
    """
    input_file = 'tests/data/s00.wav'

    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = os.path.join(tmpdir, 'output.wav')

        # Open input file
        in_fmt = sox.Format(input_file)

        # Specify output encoding: mu-law, 8-bit
        # SOX_ENCODING_ULAW = 9 (from sox.pxd enum sox_encoding_t)
        out_encoding = sox.EncodingInfo(
            encoding=9,  # ULAW encoding
            bits_per_sample=8
        )

        # Specify output signal: 8kHz, mono
        out_signal = sox.SignalInfo(
            rate=8000,
            channels=1
        )

        # Open output file with explicit signal and encoding
        out_fmt = sox.Format(output_file, signal=out_signal,
                            encoding=out_encoding, mode='w')

        # Create effects chain
        chain = sox.EffectsChain(in_fmt.encoding, out_fmt.encoding)

        # Intermediate signal (starts as input characteristics)
        interm_signal = sox.SignalInfo(
            rate=in_fmt.signal.rate,
            channels=in_fmt.signal.channels,
            precision=in_fmt.signal.precision
        )

        # Add input effect
        input_handler = sox.find_effect("input")
        input_effect = sox.Effect(input_handler)
        input_effect.set_options([in_fmt])
        chain.add_effect(input_effect, interm_signal, in_fmt.signal)

        # Add rate conversion if needed
        if in_fmt.signal.rate != out_fmt.signal.rate:
            rate_handler = sox.find_effect("rate")
            rate_effect = sox.Effect(rate_handler)
            rate_effect.set_options([])  # Use default parameters
            chain.add_effect(rate_effect, interm_signal, out_fmt.signal)

        # Add channel conversion if needed
        if in_fmt.signal.channels != out_fmt.signal.channels:
            channels_handler = sox.find_effect("channels")
            channels_effect = sox.Effect(channels_handler)
            channels_effect.set_options([])  # Use default parameters
            chain.add_effect(channels_effect, interm_signal, out_fmt.signal)

        # Add output effect
        output_handler = sox.find_effect("output")
        output_effect = sox.Effect(output_handler)
        output_effect.set_options([out_fmt])
        chain.add_effect(output_effect, interm_signal, out_fmt.signal)

        # Flow samples through the chain
        result = chain.flow_effects()
        assert result == sox.SUCCESS

        # Cleanup
        in_fmt.close()
        out_fmt.close()

        # Verify output file was created
        assert os.path.exists(output_file)
        assert os.path.getsize(output_file) > 0

        # Verify output characteristics
        verify_fmt = sox.Format(output_file)
        assert verify_fmt.signal.rate == 8000, \
            f"Expected rate 8000, got {verify_fmt.signal.rate}"
        assert verify_fmt.signal.channels == 1, \
            f"Expected 1 channel, got {verify_fmt.signal.channels}"
        assert verify_fmt.encoding.encoding == 9, \
            f"Expected ULAW encoding (9), got {verify_fmt.encoding.encoding}"
        assert verify_fmt.encoding.bits_per_sample == 8, \
            f"Expected 8 bits per sample, got {verify_fmt.encoding.bits_per_sample}"
        verify_fmt.close()


def test_example6_different_output_format():
    """Test conversion to different output format specifications."""
    input_file = 'tests/data/s00.wav'

    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = os.path.join(tmpdir, 'output.wav')

        in_fmt = sox.Format(input_file)

        # Test with different output specs: 16kHz, stereo, signed PCM
        # SOX_ENCODING_SIGN2 = 1 (from sox.pxd enum sox_encoding_t)
        out_encoding = sox.EncodingInfo(
            encoding=1,  # SIGN2 encoding
            bits_per_sample=16
        )

        out_signal = sox.SignalInfo(
            rate=16000,
            channels=2
        )

        out_fmt = sox.Format(output_file, signal=out_signal,
                            encoding=out_encoding, mode='w')

        chain = sox.EffectsChain(in_fmt.encoding, out_fmt.encoding)

        interm_signal = sox.SignalInfo(
            rate=in_fmt.signal.rate,
            channels=in_fmt.signal.channels,
            precision=in_fmt.signal.precision
        )

        # Input effect
        input_handler = sox.find_effect("input")
        input_effect = sox.Effect(input_handler)
        input_effect.set_options([in_fmt])
        chain.add_effect(input_effect, interm_signal, in_fmt.signal)

        # Rate conversion
        if in_fmt.signal.rate != out_fmt.signal.rate:
            rate_handler = sox.find_effect("rate")
            rate_effect = sox.Effect(rate_handler)
            rate_effect.set_options([])
            chain.add_effect(rate_effect, interm_signal, out_fmt.signal)

        # Channel conversion
        if in_fmt.signal.channels != out_fmt.signal.channels:
            channels_handler = sox.find_effect("channels")
            channels_effect = sox.Effect(channels_handler)
            channels_effect.set_options([])
            chain.add_effect(channels_effect, interm_signal, out_fmt.signal)

        # Output effect
        output_handler = sox.find_effect("output")
        output_effect = sox.Effect(output_handler)
        output_effect.set_options([out_fmt])
        chain.add_effect(output_effect, interm_signal, out_fmt.signal)

        result = chain.flow_effects()
        assert result == sox.SUCCESS

        in_fmt.close()
        out_fmt.close()

        # Verify output characteristics
        verify_fmt = sox.Format(output_file)
        assert verify_fmt.signal.rate == 16000
        assert verify_fmt.signal.channels == 2
        assert verify_fmt.encoding.bits_per_sample == 16
        verify_fmt.close()
