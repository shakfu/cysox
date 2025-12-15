from cysox import sox


# Test SignalInfo class
def test_signal_info_creation():
    """Test SignalInfo creation and properties"""
    signal = sox.SignalInfo(
        rate=44100.0, channels=2, precision=16, length=1000, mult=1.0
    )

    assert signal.rate == 44100.0
    assert signal.channels == 2
    assert signal.precision == 16
    assert signal.length == 1000
    assert signal.mult == 1.0


def test_signal_info_default_values():
    """Test SignalInfo with default values"""
    signal = sox.SignalInfo()

    assert signal.rate == 0.0
    assert signal.channels == 0
    assert signal.precision == 0
    assert signal.length == 0
    assert signal.mult == 0.0


def test_signal_info_property_setters():
    """Test SignalInfo property setters"""
    signal = sox.SignalInfo()

    signal.rate = 48000.0
    signal.channels = 1
    signal.precision = 24
    signal.length = 2000
    signal.mult = 2.0

    assert signal.rate == 48000.0
    assert signal.channels == 1
    assert signal.precision == 24
    assert signal.length == 2000
    assert signal.mult == 2.0


def test_signal_info_mult_zero():
    """Test SignalInfo mult property when set to 0.0"""
    signal = sox.SignalInfo(mult=1.0)
    assert signal.mult == 1.0

    signal.mult = 0.0
    assert signal.mult == 0.0


def test_signal_info_property_access():
    """Test SignalInfo property access patterns"""
    signal = sox.SignalInfo(rate=44100.0, channels=2, precision=16)

    # Test getting properties multiple times
    assert signal.rate == 44100.0
    assert signal.rate == 44100.0  # Should be consistent

    assert signal.channels == 2
    assert signal.channels == 2  # Should be consistent

    # Test setting and getting
    signal.rate = 48000.0
    assert signal.rate == 48000.0

    signal.channels = 1
    assert signal.channels == 1


def test_signal_info_memory_management():
    """Test SignalInfo memory management"""
    signal = sox.SignalInfo(rate=44100.0, channels=2, precision=16)
    assert signal.rate == 44100.0

    # Test that the object can be properly cleaned up
    del signal


def test_signal_info_edge_cases():
    """Test SignalInfo with edge case values"""
    # Test with maximum values
    signal = sox.SignalInfo(
        rate=192000.0,  # High sample rate
        channels=8,  # Many channels
        precision=32,  # High precision
        length=1000000,  # Large length
        mult=10.0,  # High multiplier
    )

    assert signal.rate == 192000.0
    assert signal.channels == 8
    assert signal.precision == 32
    assert signal.length == 1000000
    assert signal.mult == 10.0
