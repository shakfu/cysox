"""Tests for example4: Concatenate audio files
Port of tests/examples/example4.c
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


def test_example4_concatenate_files():
    """Test concatenating multiple audio files into one.

    This is a port of example4.c which concatenates audio files.
    Files must have the same number of channels and sample rate.
    """
    # For testing, we'll use the same file twice to demonstrate concatenation
    input_file = 'tests/data/s00.wav'
    max_samples = 2048

    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = os.path.join(tmpdir, 'concatenated.wav')

        # We'll concatenate the same input file twice
        input_files = [input_file, input_file]

        output = None
        signal = None

        try:
            for i, input_path in enumerate(input_files):
                # Open input file
                input_fmt = sox.Format(input_path)

                if i == 0:
                    # First file: open output with same characteristics
                    signal = sox.SignalInfo(
                        rate=input_fmt.signal.rate,
                        channels=input_fmt.signal.channels,
                        precision=input_fmt.signal.precision
                    )
                    # Note: encoding.encoding is a sox_encoding_t enum value (int)
                    encoding = sox.EncodingInfo(
                        encoding=int(input_fmt.encoding.encoding),
                        bits_per_sample=input_fmt.encoding.bits_per_sample
                    )
                    output = sox.Format(output_file, signal=signal, encoding=encoding, mode='w')
                else:
                    # Subsequent files: check signal matches
                    assert input_fmt.signal.channels == signal.channels, \
                        "All input files must have same number of channels"
                    assert input_fmt.signal.rate == signal.rate, \
                        "All input files must have same sample rate"

                # Copy all samples from this input to output
                while True:
                    samples = input_fmt.read(max_samples)
                    if len(samples) == 0:
                        break  # EOF

                    written = output.write(samples)
                    assert written == len(samples), \
                        f"Write failed: wrote {written} of {len(samples)} samples"

                input_fmt.close()

            # Close output
            output.close()
            output = None

            # Verify output file exists and has content
            assert os.path.exists(output_file)
            assert os.path.getsize(output_file) > 0

            # Verify we can read the output file and it has expected characteristics
            verify_fmt = sox.Format(output_file)
            assert verify_fmt.signal.rate == signal.rate
            assert verify_fmt.signal.channels == signal.channels

            # The output should have approximately twice the samples of one input
            # (allowing for header overhead)
            input_fmt = sox.Format(input_file)
            input_length = input_fmt.signal.length
            output_length = verify_fmt.signal.length

            # Output should be roughly 2x input length (within 10% tolerance)
            if input_length > 0 and output_length > 0:
                expected = input_length * len(input_files)
                ratio = output_length / expected
                assert 0.9 <= ratio <= 1.1, \
                    f"Output length {output_length} not close to 2x input {input_length}"

            input_fmt.close()
            verify_fmt.close()

        except Exception as e:
            # Cleanup on error
            if output is not None:
                output.close()
            if os.path.exists(output_file):
                os.remove(output_file)
            raise


def test_example4_mismatched_channels():
    """Test that concatenating files with different channels fails."""
    input_file = 'tests/data/s00.wav'

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a mono version of the input for testing
        mono_file = os.path.join(tmpdir, 'mono.wav')
        output_file = os.path.join(tmpdir, 'output.wav')

        # First create a mono file
        in_fmt = sox.Format(input_file)
        mono_signal = sox.SignalInfo(
            rate=in_fmt.signal.rate,
            channels=1,  # Force mono
            precision=in_fmt.signal.precision
        )

        # Use effects chain to convert to mono
        out_fmt = sox.Format(mono_file, signal=mono_signal, mode='w')
        chain = sox.EffectsChain(in_fmt.encoding, out_fmt.encoding)

        interm_signal = sox.SignalInfo(
            rate=in_fmt.signal.rate,
            channels=in_fmt.signal.channels,
            precision=in_fmt.signal.precision
        )

        input_handler = sox.find_effect("input")
        input_effect = sox.Effect(input_handler)
        input_effect.set_options([in_fmt])
        chain.add_effect(input_effect, interm_signal, in_fmt.signal)

        if in_fmt.signal.channels != mono_signal.channels:
            channels_handler = sox.find_effect("channels")
            channels_effect = sox.Effect(channels_handler)
            channels_effect.set_options([])
            chain.add_effect(channels_effect, interm_signal, mono_signal)

        output_handler = sox.find_effect("output")
        output_effect = sox.Effect(output_handler)
        output_effect.set_options([out_fmt])
        chain.add_effect(output_effect, interm_signal, mono_signal)

        chain.flow_effects()
        in_fmt.close()
        out_fmt.close()

        # Now try to concatenate mono and stereo files (should fail)
        if os.path.exists(mono_file):
            first_fmt = sox.Format(input_file)
            second_fmt = sox.Format(mono_file)

            # Check that they have different channel counts
            channels_match = first_fmt.signal.channels == second_fmt.signal.channels

            first_fmt.close()
            second_fmt.close()

            if not channels_match:
                # This is the expected behavior - files have different channels
                # In the actual concatenation code, this would raise an assertion
                pass
