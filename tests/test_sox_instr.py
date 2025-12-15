from cysox import sox


# Test InstrInfo class
def test_instr_info_creation():
    """Test InstrInfo creation and properties"""
    instr = sox.InstrInfo(note=60, low=0, high=127, loopmode=1, nloops=2)

    assert instr.note == 60
    assert instr.low == 0
    assert instr.high == 127
    assert instr.loopmode == 1
    assert instr.nloops == 2


def test_instr_info_default_values():
    """Test InstrInfo with default values"""
    instr = sox.InstrInfo()

    assert instr.note == 0
    assert instr.low == 0
    assert instr.high == 0
    assert instr.loopmode == 0
    assert instr.nloops == 0


def test_instr_info_property_setters():
    """Test InstrInfo property setters"""
    instr = sox.InstrInfo()

    instr.note = 72
    instr.low = 10
    instr.high = 100
    instr.loopmode = 2
    instr.nloops = 3

    assert instr.note == 72
    assert instr.low == 10
    assert instr.high == 100
    assert instr.loopmode == 2
    assert instr.nloops == 3


def test_instr_info_edge_cases():
    """Test InstrInfo with edge case values"""
    instr = sox.InstrInfo(
        note=127,  # Maximum MIDI note
        low=0,  # Minimum low
        high=127,  # Maximum high
        loopmode=2,  # Different loop mode
        nloops=10,  # Multiple loops
    )

    assert instr.note == 127
    assert instr.low == 0
    assert instr.high == 127
    assert instr.loopmode == 2
    assert instr.nloops == 10


def test_instr_info_memory_management():
    """Test InstrInfo memory management"""
    instr = sox.InstrInfo(note=60, low=0, high=127)
    assert instr.note == 60

    # Test that the object can be properly cleaned up
    del instr
