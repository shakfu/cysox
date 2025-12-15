from cysox import sox


# Test LoopInfo class
def test_loop_info_creation():
    """Test LoopInfo creation and properties"""
    loop = sox.LoopInfo(start=100, length=500, count=3, type=1)

    assert loop.start == 100
    assert loop.length == 500
    assert loop.count == 3
    assert loop.type == 1


def test_loop_info_default_values():
    """Test LoopInfo with default values"""
    loop = sox.LoopInfo()

    assert loop.start == 0
    assert loop.length == 0
    assert loop.count == 0
    assert loop.type == 0


def test_loop_info_property_setters():
    """Test LoopInfo property setters"""
    loop = sox.LoopInfo()

    loop.start = 200
    loop.length = 1000
    loop.count = 5
    loop.type = 2

    assert loop.start == 200
    assert loop.length == 1000
    assert loop.count == 5
    assert loop.type == 2


def test_loop_info_edge_cases():
    """Test LoopInfo with edge case values"""
    loop = sox.LoopInfo(
        start=1000000,  # Large start value
        length=500000,  # Large length value
        count=100,  # High count
        type=2,  # Different type
    )

    assert loop.start == 1000000
    assert loop.length == 500000
    assert loop.count == 100
    assert loop.type == 2


def test_loop_info_memory_management():
    """Test LoopInfo memory management"""
    loop = sox.LoopInfo(start=100, length=500, count=3)
    assert loop.start == 100

    # Test that the object can be properly cleaned up
    del loop
