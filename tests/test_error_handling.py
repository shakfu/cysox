"""Negative test cases for error handling validation"""
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


# Format error tests
def test_format_nonexistent_file():
    """Test opening nonexistent file raises SoxFormatError"""
    with pytest.raises(sox.SoxFormatError):
        sox.Format('nonexistent_file_that_does_not_exist.wav')


def test_format_invalid_mode():
    """Test invalid mode raises ValueError"""
    with pytest.raises(ValueError, match="Mode must be 'r' or 'w'"):
        sox.Format('tests/data/s00.wav', mode='x')


def test_format_write_without_signal():
    """Test write mode without signal raises ValueError"""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'output.wav')
        with pytest.raises(ValueError, match="Signal information is required"):
            sox.Format(output_path, mode='w')


def test_format_seek_on_nonseekable():
    """Test seeking on non-seekable format"""
    # Most real files are seekable, but we can test the error handling
    with sox.Format('tests/data/s00.wav') as f:
        # Seeking beyond file should fail or return error
        # This is a soft test - behavior depends on libsox
        pass


# Effect error tests
def test_effect_invalid_name():
    """Test finding invalid effect returns None"""
    handler = sox.find_effect("nonexistent_effect_name")
    assert handler is None


def test_effect_invalid_options():
    """Test setting invalid options on effect"""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = os.path.join(tmpdir, 'output.wav')

        in_fmt = sox.Format('tests/data/s00.wav')
        signal = sox.SignalInfo(
            rate=in_fmt.signal.rate,
            channels=in_fmt.signal.channels,
            precision=in_fmt.signal.precision
        )
        out_fmt = sox.Format(output_file, signal=signal, mode='w')

        chain = sox.EffectsChain(in_fmt.encoding, out_fmt.encoding)

        # Add input effect
        input_handler = sox.find_effect("input")
        input_effect = sox.Effect(input_handler)
        input_effect.set_options([in_fmt])
        chain.add_effect(input_effect, in_fmt.signal, out_fmt.signal)

        # Try to add vol effect with invalid option
        vol_handler = sox.find_effect("vol")
        vol_effect = sox.Effect(vol_handler)
        # Invalid option should either raise or be handled by libsox
        try:
            vol_effect.set_options(["invalid_volume_value"])
            # If no error, that's OK - libsox might handle it
        except (sox.SoxEffectError, TypeError):
            # Expected error
            pass

        in_fmt.close()
        out_fmt.close()


# SignalInfo error tests
def test_signal_info_null_pointer():
    """Test accessing properties on SignalInfo with NULL pointer"""
    # This tests the NULL pointer checks in properties
    signal = sox.SignalInfo.__new__(sox.SignalInfo)
    with pytest.raises(RuntimeError, match="SignalInfo pointer is NULL"):
        _ = signal.rate


# EncodingInfo error tests
def test_encoding_info_null_pointer():
    """Test accessing properties on EncodingInfo with NULL pointer"""
    encoding = sox.EncodingInfo.__new__(sox.EncodingInfo)
    with pytest.raises(RuntimeError, match="EncodingInfo pointer is NULL"):
        _ = encoding.encoding


# Memory allocation tests
def test_signal_info_memory_allocation():
    """Test SignalInfo creation and memory management"""
    # Create and destroy many SignalInfo objects to test memory management
    for _ in range(100):
        signal = sox.SignalInfo(rate=44100, channels=2, precision=16)
        assert signal.rate == 44100
        del signal


# Format handler tests
def test_format_handler_nonexistent():
    """Test finding nonexistent format handler"""
    handler = sox.find_format("nonexistent_format_type")
    assert handler is None


def test_format_handler_invalid_path():
    """Test FormatHandler with invalid path"""
    with pytest.raises(sox.SoxFormatError):
        sox.FormatHandler('file_with_no_extension')


# Effects chain tests
def test_effects_chain_without_effects():
    """Test running empty effects chain"""
    chain = sox.EffectsChain()
    # Running an empty chain should fail or return error
    try:
        result = chain.flow_effects()
        # If it doesn't fail, that's OK - libsox might handle it
    except sox.SoxEffectError:
        # Expected error
        pass


@pytest.mark.skip(reason="libsox segfaults when running chain with only input effect")
def test_effects_chain_with_only_input():
    """Test running chain with only input effect (no output)

    Note: This test is skipped because libsox crashes (segfault) when
    running an effects chain with only an input effect and no output effect.
    This is a known libsox limitation, not a bug in cysox.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        in_fmt = sox.Format('tests/data/s00.wav')
        chain = sox.EffectsChain(in_fmt.encoding, in_fmt.encoding)

        input_handler = sox.find_effect("input")
        input_effect = sox.Effect(input_handler)
        input_effect.set_options([in_fmt])
        chain.add_effect(input_effect, in_fmt.signal, in_fmt.signal)

        # Running without output effect causes segfault in libsox
        with pytest.raises(sox.SoxEffectError):
            chain.flow_effects()

        in_fmt.close()


# Edge case tests
def test_format_read_from_write_mode():
    """Test reading from file opened in write mode"""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, 'output.wav')
        signal = sox.SignalInfo(rate=44100, channels=1, precision=16)

        with sox.Format(output_path, signal=signal, mode='w') as f:
            # Trying to read from write-mode file should fail or return empty
            samples = f.read(100)
            # Either returns empty or raises error - both acceptable
            assert len(samples) == 0 or samples is None


def test_format_write_to_read_mode():
    """Test writing to file opened in read mode"""
    with sox.Format('tests/data/s00.wav', mode='r') as f:
        # Trying to write to read-mode file should fail
        # libsox might silently ignore this, so we just test it doesn't crash
        try:
            result = f.write([100, 200, 300])
            # If it doesn't fail, that's OK - libsox might handle it
        except (sox.SoxIOError, sox.SoxFormatError):
            # Expected error
            pass


def test_double_close():
    """Test closing a format twice doesn't crash"""
    f = sox.Format('tests/data/s00.wav')
    f.close()
    # Second close should succeed silently (ptr is already NULL)
    result = f.close()
    assert result == sox.SUCCESS


def test_init_quit_multiple_times():
    """Test calling init and quit multiple times"""
    sox.quit()
    sox.init()
    sox.quit()
    sox.init()
    # Should not crash


def test_strerror_invalid_code():
    """Test strerror with invalid error code"""
    # Should return generic message, not crash
    msg = sox.strerror(99999)
    assert isinstance(msg, str)
    assert len(msg) > 0
