import math

from cysox import sox


def test_get_encodings():
    """Test get_encodings function"""
    encodings = sox.get_encodings()
    assert isinstance(encodings, list)
    assert len(encodings) > 0

    for encoding in encodings:
        assert hasattr(encoding, "flags")
        assert hasattr(encoding, "name")
        assert hasattr(encoding, "desc")
        assert hasattr(encoding, "type")


def test_encodings():
    """Test that ENCODINGS list is properly defined"""
    assert hasattr(sox, "ENCODINGS")
    assert isinstance(sox.ENCODINGS, list)
    assert len(sox.ENCODINGS) > 0

    # Test some known encodings
    assert ("SIGN2", "signed linear 2's comp: Mac") in sox.ENCODINGS
    assert ("MP3", "MP3 compression") in sox.ENCODINGS
    assert ("FLOAT", "floating point (binary format)") in sox.ENCODINGS


# Test EncodingInfo class
def test_encoding_info_creation():
    """Test EncodingInfo creation and properties"""
    encoding = sox.EncodingInfo(
        encoding=1,  # SIGN2
        bits_per_sample=16,
        compression=1.0,
        reverse_bytes=0,
        reverse_nibbles=0,
        reverse_bits=0,
        opposite_endian=False,
    )

    assert encoding.encoding == 1
    assert encoding.bits_per_sample == 16
    assert encoding.compression == 1.0
    assert encoding.reverse_bytes == 0
    assert encoding.reverse_nibbles == 0
    assert encoding.reverse_bits == 0
    assert not encoding.opposite_endian


def test_encoding_info_default_values():
    """Test EncodingInfo with default values"""
    encoding = sox.EncodingInfo()

    assert encoding.encoding == 0
    assert encoding.bits_per_sample == 0
    assert encoding.compression == 0.0
    assert encoding.reverse_bytes == 0
    assert encoding.reverse_nibbles == 0
    assert encoding.reverse_bits == 0
    assert not encoding.opposite_endian


def test_encoding_info_property_setters():
    """Test EncodingInfo property setters"""
    encoding = sox.EncodingInfo()

    encoding.encoding = 22  # MP3
    encoding.bits_per_sample = 0
    encoding.compression = math.inf
    encoding.reverse_bytes = 1
    encoding.reverse_nibbles = 1
    encoding.reverse_bits = 1
    encoding.opposite_endian = True

    assert encoding.encoding == 22
    assert encoding.bits_per_sample == 0
    assert encoding.compression == math.inf
    assert encoding.reverse_bytes == 1
    assert encoding.reverse_nibbles == 1
    assert encoding.reverse_bits == 1
    assert encoding.opposite_endian


def test_encoding_info_property_access():
    """Test EncodingInfo property access patterns"""
    encoding = sox.EncodingInfo(encoding=1, bits_per_sample=16)

    # Test getting properties multiple times
    assert encoding.encoding == 1
    assert encoding.encoding == 1  # Should be consistent

    assert encoding.bits_per_sample == 16
    assert encoding.bits_per_sample == 16  # Should be consistent

    # Test setting and getting
    encoding.encoding = 22  # MP3
    assert encoding.encoding == 22

    encoding.bits_per_sample = 0
    assert encoding.bits_per_sample == 0


def test_encoding_info_edge_cases():
    """Test EncodingInfo with edge case values"""
    encoding = sox.EncodingInfo(
        encoding=25,  # High encoding value
        bits_per_sample=32,  # High bits per sample
        compression=100.0,  # High compression
        reverse_bytes=1,
        reverse_nibbles=1,
        reverse_bits=1,
        opposite_endian=True,
    )

    assert encoding.encoding == 25
    assert encoding.bits_per_sample == 32
    assert encoding.compression == 100.0
    assert encoding.reverse_bytes == 1
    assert encoding.reverse_nibbles == 1
    assert encoding.reverse_bits == 1
    assert encoding.opposite_endian


def test_encoding_info_memory_management():
    """Test EncodingInfo memory management"""
    encoding = sox.EncodingInfo(encoding=1, bits_per_sample=16)
    assert encoding.encoding == 1

    # Test that the object can be properly cleaned up
    del encoding
