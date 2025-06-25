import cysox as sox


# Test FileInfo class
def test_file_info_creation():
    """Test FileInfo creation and properties"""
    test_data = b"test data"
    file_info = sox.FileInfo(buf=test_data, size=len(test_data), count=5, pos=2)

    assert file_info.buf == test_data
    assert file_info.size == len(test_data)
    assert file_info.count == 5
    assert file_info.pos == 2


def test_file_info_default_values():
    """Test FileInfo with default values"""
    file_info = sox.FileInfo()

    assert file_info.buf is None
    assert file_info.size == 0
    assert file_info.count == 0
    assert file_info.pos == 0


def test_file_info_property_setters():
    """Test FileInfo property setters"""
    file_info = sox.FileInfo()

    test_data = b"new test data"
    file_info.buf = test_data
    file_info.size = len(test_data)
    file_info.count = 10
    file_info.pos = 5

    assert file_info.buf == test_data
    assert file_info.size == len(test_data)
    assert file_info.count == 10
    assert file_info.pos == 5


# def test_file_info_buf_none():
#     """Test FileInfo buf property when set to None"""
#     test_data = b"test data"
#     file_info = sox.FileInfo(buf=test_data)
#     assert file_info.buf == test_data

#     file_info.buf = None
#     assert file_info.buf is None


# def test_file_info_memory_management():
#     """Test FileInfo memory management"""
#     file_info = sox.FileInfo(buf=b"test", size=4, count=1, pos=0)
#     assert file_info.size == 4

#     # Test that the object can be properly cleaned up
#     del file_info
