from cysox import sox


# Test OutOfBand class
# def test_out_of_band_creation():
#     """Test OutOfBand creation"""
#     oob = sox.OutOfBand()
#     assert oob is not None


# def test_out_of_band_comments():
#     """Test OutOfBand comment methods"""
#     oob = sox.OutOfBand()

#     # Test initial state
#     assert oob.num_comments() == 0
#     assert oob.comments == []

#     # Test appending comments
#     oob.append_comment("artist=Test Artist")
#     assert oob.num_comments() == 1
#     assert "artist=Test Artist" in oob.comments

#     oob.append_comment("title=Test Title")
#     assert oob.num_comments() == 2
#     assert "artist=Test Artist" in oob.comments
#     assert "title=Test Title" in oob.comments

#     # Test appending multiple comments
#     oob.append_comments("album=Test Album\nyear=2023")
#     assert oob.num_comments() == 4
#     assert "album=Test Album" in oob.comments
#     assert "year=2023" in oob.comments


# def test_out_of_band_find_comment():
#     """Test OutOfBand find_comment method"""
#     oob = sox.OutOfBand()
#     oob.append_comment("artist=Test Artist")
#     oob.append_comment("title=Test Title")

#     # Test finding existing comment
#     assert oob.find_comment("artist") == "Test Artist"
#     assert oob.find_comment("title") == "Test Title"

#     # Test finding non-existent comment
#     assert oob.find_comment("nonexistent") is None


# def test_out_of_band_instr():
#     """Test OutOfBand instr property"""
#     oob = sox.OutOfBand()
#     instr = oob.instr

#     assert isinstance(instr, sox.InstrInfo)
#     assert instr.note == 0
#     assert instr.low == 0
#     assert instr.high == 0
#     assert instr.loopmode == 0
#     assert instr.nloops == 0


# def test_out_of_band_memory_management():
#     """Test OutOfBand memory management"""
#     oob = sox.OutOfBand()
#     oob.append_comment("test=value")
#     assert oob.num_comments() == 1

#     # Test that the object can be properly cleaned up
#     del oob
