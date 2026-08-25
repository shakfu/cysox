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


def test_version_info_time_is_none():
    """The build-time field is deliberately not read.

    SoX_ng 14.7 removed ``sox_version_info_t.time`` for reproducible builds.
    Declaring it in sox.pxd made cysox fail to compile against the libsox that
    Debian/Ubuntu now ship, so the field is no longer declared or read. Do not
    "fix" this by restoring it: the key is reported as None on every version.
    """
    assert sox.version_info()["time"] is None


def test_version_info_other_fields_survive():
    """Dropping `time` must not disturb the neighbouring fields."""
    info = sox.version_info()
    for key in ("size", "flags", "version_code", "version", "arch"):
        assert key in info
    assert info["version_code"] > 0


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
