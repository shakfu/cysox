"""Tests for example1: Apply vol & flanger effects
Port of tests/examples/example1.c
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


def test_example1_vol_and_flanger():
    """Test applying vol and flanger effects to an audio file.

    This is a port of example1.c which reads an input file, applies
    vol (3dB) and flanger effects, and writes to an output file.
    """
    input_file = 'tests/data/s00.wav'

    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = os.path.join(tmpdir, 'output.wav')

        # Open input file
        in_fmt = sox.Format(input_file)

        # Open output file with same characteristics as input
        signal = sox.SignalInfo(
            rate=in_fmt.signal.rate,
            channels=in_fmt.signal.channels,
            precision=in_fmt.signal.precision
        )
        out_fmt = sox.Format(output_file, signal=signal, mode='w')

        # Create effects chain
        chain = sox.EffectsChain(in_fmt.encoding, out_fmt.encoding)

        # Add input effect
        input_handler = sox.find_effect("input")
        input_effect = sox.Effect(input_handler)
        input_effect.set_options([in_fmt])
        chain.add_effect(input_effect, in_fmt.signal, in_fmt.signal)

        # Add vol effect with 3dB gain
        vol_handler = sox.find_effect("vol")
        vol_effect = sox.Effect(vol_handler)
        vol_effect.set_options(["3dB"])
        chain.add_effect(vol_effect, in_fmt.signal, in_fmt.signal)

        # Add flanger effect with default parameters
        flanger_handler = sox.find_effect("flanger")
        flanger_effect = sox.Effect(flanger_handler)
        flanger_effect.set_options([])
        chain.add_effect(flanger_effect, in_fmt.signal, in_fmt.signal)

        # Add output effect
        output_handler = sox.find_effect("output")
        output_effect = sox.Effect(output_handler)
        output_effect.set_options([out_fmt])
        chain.add_effect(output_effect, in_fmt.signal, in_fmt.signal)

        # Flow samples through the effects chain
        result = chain.flow_effects()
        assert result == sox.SUCCESS

        # Cleanup
        in_fmt.close()
        out_fmt.close()

        # Verify output file was created and has content
        assert os.path.exists(output_file)
        assert os.path.getsize(output_file) > 0

        # Verify we can read the output file
        verify_fmt = sox.Format(output_file)
        assert verify_fmt.signal.rate == signal.rate
        assert verify_fmt.signal.channels == signal.channels
        verify_fmt.close()
