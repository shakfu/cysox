import tempfile
import os

import pytest
from cysox import sox


# Test utility functions
def test_version():
    """Test version function"""
    version_str = sox.version()
    assert isinstance(version_str, str)
    assert len(version_str) > 0


def test_version_info():
    """Test version_info function"""
    info = sox.version_info()
    assert isinstance(info, dict)
    assert "version" in info
    assert isinstance(info["version"], str) or info["version"] is None


# def test_format_init_and_quit():
#     """Test format_init and format_quit functions"""
#     # These functions should not raise exceptions
#     sox.format_init()
#     sox.format_quit()


@pytest.mark.skip(reason="Cannot test init/quit cycle: high-level API auto-initializes and libsox crashes on re-init. See KNOWN_LIMITATIONS.md")
def test_init_and_quit():
    """Test init and quit functions"""
    # These functions should not raise exceptions
    sox.init()
    sox.quit()


def test_strerror():
    """Test strerror function"""
    # Test with a known error code (SOX_SUCCESS = 0)
    error_str = sox.strerror(0)
    assert isinstance(error_str, str)
    assert len(error_str) > 0


def test_is_playlist():
    """Test is_playlist function"""
    # Test with a non-playlist file
    assert not sox.is_playlist("tests/data/s00.wav")

    # Test with a playlist file (m3u format)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".m3u", delete=False) as f:
        f.write("#EXTM3U\n")
        f.write("tests/data/s00.wav\n")
        playlist_file = f.name

    try:
        assert sox.is_playlist(playlist_file)
    finally:
        os.unlink(playlist_file)


def test_basename():
    """Test basename function"""
    # Test with a simple filename
    assert sox.basename("tests/data/s00.wav") == "s00"

    # Test with a path
    assert sox.basename("/path/to/file.wav") == "file"

    # Test with just a filename
    assert sox.basename("file.wav") == "file"


def test_precision():
    """Test precision function"""
    # Test with SIGN2 encoding and 16 bits
    precision_val = sox.precision(1, 16)  # SIGN2 encoding
    assert isinstance(precision_val, int)
    assert precision_val >= 0
