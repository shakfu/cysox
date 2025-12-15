from cysox import sox


# Test constants
def test_constants():
    """Test that constants are properly defined"""
    assert hasattr(sox, "constant")
    c = sox.constant
    assert c.DEFAULT_ENCODING == 1
    assert c.DEFAULT_PRECISION == 16
    assert c.DEFAULT_RATE == 48000
    assert c.EFF_ALPHA == 512
    assert c.EFF_CHAN == 1
    assert c.EFF_DEPRECATED == 64
    assert c.EFF_GAIN == 128
    assert c.EFF_INTERNAL == 1024
    assert c.EFF_LENGTH == 8
    assert c.EFF_MCHAN == 16
    assert c.EFF_MODIFY == 256
    assert c.EFF_NULL == 32
    assert c.EFF_PREC == 4
    assert c.EFF_RATE == 2
    assert c.FILE_BIG_END == 192
    assert c.FILE_BIT_REV == 16
    assert c.FILE_CHANS == 1792
    assert c.FILE_DEVICE == 2
    assert c.FILE_ENDBIG == 128
    assert c.FILE_ENDIAN == 64
    assert c.FILE_LIT_END == 64
    assert c.FILE_MONO == 256
    assert c.FILE_NIB_REV == 32
    assert c.FILE_NOSTDIO == 1
    assert c.FILE_PHONY == 4
    assert c.FILE_QUAD == 1024
    assert c.FILE_REWIND == 8
    assert c.FILE_STEREO == 512
    assert c.IGNORE_LENGTH == 18446744073709551614
    assert c.INT16_MAX == 32767
    assert c.INT24_MAX == 8388607
    assert c.INT8_MAX == 127
    assert c.LOOP_8 == 32
    assert c.LOOP_NONE == 0
    assert c.LOOP_SUSTAIN_DECAY == 64
    assert c.MAX_NLOOPS == 8
    assert c.SAMPLE_MAX == 2147483647
    assert c.SAMPLE_MIN == -2147483648
    assert c.SAMPLE_NEG == -2147483648
    assert c.SAMPLE_PRECISION == 32
    assert c.SEEK_SET == 0
    assert c.SIZE_MAX == 18446744073709551615
    assert c.UNKNOWN_LEN == 18446744073709551615
    assert c.UNSPEC == 0
