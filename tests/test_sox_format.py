import math

import pytest

from cysox import sox


@pytest.mark.skip(reason="format_init() can only be called once - conflicts with sox.init() in other tests")
def test_format_init_and_quit():
    """Test format_init and format_quit functions

    Note: This test is skipped because format_init() can only be called once
    per process. The function is already called internally by sox.init(), so
    calling it explicitly in tests causes conflicts with other tests that use
    the standard sox.init()/sox.quit() pattern.

    In practice, users should use sox.init() which handles format initialization
    automatically, rather than calling format_init() directly.
    """
    sox.format_init()
    sox.format_quit()


def test_sox_format():
    f = sox.Format("tests/data/s00.wav")
    assert f.signal.channels == 2
    assert f.signal.length == 502840
    assert f.signal.precision == 16
    assert f.signal.rate == 44100.0

    assert f.encoding.bits_per_sample == 16
    assert f.encoding.compression == math.inf
    assert f.encoding.encoding == 1
    assert sox.ENCODINGS[f.encoding.encoding] == (
        "SIGN2",
        "signed linear 2's comp: Mac",
    )
    assert f.encoding.opposite_endian == 0
    assert f.encoding.reverse_bits == 0
    assert f.encoding.reverse_bytes == 0
    assert f.encoding.reverse_nibbles == 0


def test_sox_format_mp3():
    f = sox.Format("tests/data/s00.mp3")
    assert f.signal.channels == 2
    assert f.signal.length == 506798
    assert f.signal.precision == 16
    assert f.signal.rate == 44100.0

    assert f.encoding.bits_per_sample == 0
    assert f.encoding.compression == math.inf
    assert f.encoding.encoding == 22
    assert sox.ENCODINGS[f.encoding.encoding] == ("MP3", "MP3 compression")
    assert f.encoding.opposite_endian == 0
    assert f.encoding.reverse_bits == 0
    assert f.encoding.reverse_bytes == 0
    assert f.encoding.reverse_nibbles == 0


# Test Format class
def test_format_creation():
    """Test Format creation"""
    f = sox.Format("tests/data/s00.wav")
    assert f is not None
    assert f.filename == "tests/data/s00.wav"


def test_format_properties():
    """Test Format properties"""
    f = sox.Format("tests/data/s00.wav")

    # Test signal properties
    assert isinstance(f.signal, sox.SignalInfo)
    assert f.signal.channels == 2
    assert f.signal.rate == 44100.0
    assert f.signal.precision == 16

    # Test encoding properties
    assert isinstance(f.encoding, sox.EncodingInfo)
    assert f.encoding.encoding == 1  # SIGN2
    assert f.encoding.bits_per_sample == 16

    # Test filetype
    assert isinstance(f.filetype, str)
    assert len(f.filetype) > 0


def test_format_with_signal_and_encoding():
    """Test Format creation with SignalInfo and EncodingInfo"""
    signal = sox.SignalInfo(rate=44100.0, channels=2, precision=16)
    encoding = sox.EncodingInfo(encoding=1, bits_per_sample=16)

    f = sox.Format("tests/data/s00.wav", signal=signal, encoding=encoding)
    assert f is not None


def test_format_nonexistent_file():
    """Test Format creation with non-existent file"""
    with pytest.raises(sox.SoxFormatError):
        sox.Format("nonexistent_file.wav")


# Test FormatHandler class
def test_format_handler_creation():
    """Test FormatHandler creation"""
    handler = sox.FormatHandler('tests/data/s00.wav')
    assert handler is not None


def test_format_handler_properties():
    """Test FormatHandler properties"""
    handler = sox.FormatHandler('tests/data/s00.wav')

    assert handler.sox_lib_version_code > 0
    assert isinstance(handler.description, str) or handler.description is None
    assert isinstance(handler.names, list)
    assert isinstance(handler.flags, int)
    assert handler.priv_size >= 0


def test_format_handler_nonexistent_file():
    """Test FormatHandler creation with non-existent file"""
    # FormatHandler finds handler by extension, doesn't check if file exists
    # So this should succeed
    handler = sox.FormatHandler('nonexistent_file.wav')
    assert handler is not None


# Test FormatTab class
def test_format_tab_creation():
    """Test FormatTab creation

    Note: name parameter is ignored for safety (read-only property).
    FormatTab is primarily for internal use by libsox.
    """
    tab = sox.FormatTab("wav")
    assert tab is not None
    # name is read-only and always None when created via __init__ (for safety)
    assert tab.name is None


def test_format_tab_default_values():
    """Test FormatTab with default values"""
    tab = sox.FormatTab()
    assert tab.name is None
    assert tab.fn is None


def test_format_tab_with_name():
    """Test FormatTab with name parameter (ignored for safety)

    Note: The name parameter is ignored in __init__ because the name
    pointer is managed by libsox and should not be set externally.
    """
    tab = sox.FormatTab("mp3")
    # name is read-only and always None when created via __init__
    assert tab.name is None


def test_find_format():
    """Test find_format function"""
    # Test finding a known format
    format_handler = sox.find_format("wav")
    assert format_handler is not None
    assert isinstance(format_handler, sox.FormatHandler)
    assert format_handler.description
    assert format_handler.names

    # Test finding a non-existent format
    format_info = sox.find_format("nonexistent_format")
    assert format_info is None


def test_format_supports_encoding():
    """Test format_supports_encoding function"""
    encoding = sox.EncodingInfo(encoding=1, bits_per_sample=16)  # SIGN2

    # Test with a format that supports the encoding
    supports = sox.format_supports_encoding('tests/data/s00.wav', encoding)
    assert isinstance(supports, bool)


# Test error handling
def test_format_invalid_file():
    """Test Format with invalid file"""
    with pytest.raises(sox.SoxFormatError):
        sox.Format("nonexistent_file.wav")


def test_format_handler_invalid_file():
    """Test FormatHandler with invalid file extension"""
    # FormatHandler finds handler by extension
    # An unknown extension should return None or raise error
    try:
        handler = sox.FormatHandler('file.unknownext12345')
        # If it doesn't raise, it might return a default handler
        assert handler is not None
    except sox.SoxFormatError:
        # This is also acceptable - means no handler found
        pass


# Test integration scenarios
def test_format_with_comments():
    """Test Format with metadata comments"""
    # This would require a file format that supports metadata
    # For now, we'll just test that we can create a Format object
    f = sox.Format("tests/data/s00.wav")
    assert f is not None
