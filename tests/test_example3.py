"""Tests for example3: Playback with trim and format conversion
Port of tests/examples/example3.c
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


def test_example3_trim_and_conversion():
    """Test trimming audio and handling rate/channel conversion.

    This is a port of example3.c which plays an audio file starting
    at 10 seconds with sample-rate and channel conversion if needed.
    For testing, we write to a file instead of playing to audio device.
    """
    input_file = 'tests/data/s00.wav'

    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = os.path.join(tmpdir, 'output.wav')

        # Open input file
        in_fmt = sox.Format(input_file)

        # For testing, we'll create output with different rate/channels
        # to exercise the conversion logic
        out_signal = sox.SignalInfo(
            rate=22050,  # Different from input (typically 44100)
            channels=1,  # Mono (input might be stereo)
            precision=in_fmt.signal.precision
        )
        out_fmt = sox.Format(output_file, signal=out_signal, mode='w')

        # Create effects chain
        chain = sox.EffectsChain(in_fmt.encoding, out_fmt.encoding)

        # Store intermediate signal
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

        # Add trim effect to start at a specific position
        # Using 0.1 seconds for testing (original uses 10 seconds)
        trim_handler = sox.find_effect("trim")
        trim_effect = sox.Effect(trim_handler)
        trim_effect.set_options(["0.1"])
        chain.add_effect(trim_effect, interm_signal, in_fmt.signal)

        # Add rate conversion if needed
        if in_fmt.signal.rate != out_fmt.signal.rate:
            rate_handler = sox.find_effect("rate")
            rate_effect = sox.Effect(rate_handler)
            rate_effect.set_options([])
            chain.add_effect(rate_effect, interm_signal, out_fmt.signal)

        # Add channel conversion if needed
        if in_fmt.signal.channels != out_fmt.signal.channels:
            channels_handler = sox.find_effect("channels")
            channels_effect = sox.Effect(channels_handler)
            channels_effect.set_options([])
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
        assert verify_fmt.signal.rate == 22050
        assert verify_fmt.signal.channels == 1
        verify_fmt.close()


def test_example3_no_conversion():
    """Test trim effect without rate/channel conversion."""
    input_file = 'tests/data/s00.wav'

    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = os.path.join(tmpdir, 'output.wav')

        in_fmt = sox.Format(input_file)

        # Output with same characteristics as input (no conversion needed)
        out_signal = sox.SignalInfo(
            rate=in_fmt.signal.rate,
            channels=in_fmt.signal.channels,
            precision=in_fmt.signal.precision
        )
        out_fmt = sox.Format(output_file, signal=out_signal, mode='w')

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

        # Trim effect
        trim_handler = sox.find_effect("trim")
        trim_effect = sox.Effect(trim_handler)
        trim_effect.set_options(["0.1"])
        chain.add_effect(trim_effect, interm_signal, in_fmt.signal)

        # Output effect (no rate/channel conversion needed)
        output_handler = sox.find_effect("output")
        output_effect = sox.Effect(output_handler)
        output_effect.set_options([out_fmt])
        chain.add_effect(output_effect, interm_signal, out_fmt.signal)

        result = chain.flow_effects()
        assert result == sox.SUCCESS

        in_fmt.close()
        out_fmt.close()

        # Verify output
        assert os.path.exists(output_file)
        assert os.path.getsize(output_file) > 0
