import cysox as sox


# Test constants
def test_constants():
    """Test that constants are properly defined"""
    assert hasattr(sox, 'constant')
    assert hasattr(sox.constant, 'INT8_MAX')
    assert hasattr(sox.constant, 'INT16_MAX')
    assert hasattr(sox.constant, 'INT24_MAX')
    assert hasattr(sox.constant, 'SAMPLE_PRECISION')
    assert hasattr(sox.constant, 'SAMPLE_MAX')
    assert hasattr(sox.constant, 'SAMPLE_MIN')
    assert hasattr(sox.constant, 'SIZE_MAX')
    assert hasattr(sox.constant, 'UNSPEC')
    assert hasattr(sox.constant, 'DEFAULT_RATE')
    assert hasattr(sox.constant, 'DEFAULT_PRECISION')
    assert hasattr(sox.constant, 'DEFAULT_ENCODING')
