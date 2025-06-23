import math
import pytest
import tempfile
import os

import cysox as sox


def test_sox_format():
	f = sox.Format('tests/data/s00.wav')
	assert f.signal.channels == 2
	assert f.signal.length == 502840
	assert f.signal.precision == 16
	assert f.signal.rate == 44100.0	

	assert f.encoding.bits_per_sample == 16
	assert f.encoding.compression == math.inf
	assert f.encoding.encoding == 1
	assert sox.ENCODINGS[f.encoding.encoding] == ("SIGN2", "signed linear 2's comp: Mac")
	assert f.encoding.opposite_endian == 0
	assert f.encoding.reverse_bits == 0
	assert f.encoding.reverse_bytes == 0
	assert f.encoding.reverse_nibbles == 0

def test_sox_format_mp3():
	f = sox.Format('tests/data/s00.mp3')
	assert f.signal.channels == 2
	assert f.signal.length == 506798
	assert f.signal.precision == 16
	assert f.signal.rate == 44100.0	

	assert f.encoding.bits_per_sample == 0
	assert f.encoding.compression == math.inf
	assert f.encoding.encoding == 22
	assert sox.ENCODINGS[f.encoding.encoding] == ('MP3', 'MP3 compression')
	assert f.encoding.opposite_endian == 0
	assert f.encoding.reverse_bits == 0
	assert f.encoding.reverse_bytes == 0
	assert f.encoding.reverse_nibbles == 0


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


def test_encodings():
    """Test that ENCODINGS list is properly defined"""
    assert hasattr(sox, 'ENCODINGS')
    assert isinstance(sox.ENCODINGS, list)
    assert len(sox.ENCODINGS) > 0
    
    # Test some known encodings
    assert ("SIGN2", "signed linear 2's comp: Mac") in sox.ENCODINGS
    assert ("MP3", "MP3 compression") in sox.ENCODINGS
    assert ("FLOAT", "floating point (binary format)") in sox.ENCODINGS


# Test SignalInfo class
def test_signal_info_creation():
    """Test SignalInfo creation and properties"""
    signal = sox.SignalInfo(rate=44100.0, channels=2, precision=16, length=1000, mult=1.0)
    
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
        opposite_endian=False
    )
    
    assert encoding.encoding == 1
    assert encoding.bits_per_sample == 16
    assert encoding.compression == 1.0
    assert encoding.reverse_bytes == 0
    assert encoding.reverse_nibbles == 0
    assert encoding.reverse_bits == 0
    assert encoding.opposite_endian == False


def test_encoding_info_default_values():
    """Test EncodingInfo with default values"""
    encoding = sox.EncodingInfo()
    
    assert encoding.encoding == 0
    assert encoding.bits_per_sample == 0
    assert encoding.compression == 0.0
    assert encoding.reverse_bytes == 0
    assert encoding.reverse_nibbles == 0
    assert encoding.reverse_bits == 0
    assert encoding.opposite_endian == False


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
    assert encoding.opposite_endian == True


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


# Test Format class
def test_format_creation():
    """Test Format creation"""
    f = sox.Format('tests/data/s00.wav')
    assert f is not None
    assert f.filename == 'tests/data/s00.wav'


def test_format_properties():
    """Test Format properties"""
    f = sox.Format('tests/data/s00.wav')
    
    # Test signal properties
    assert isinstance(f.signal, sox.SignalInfo)
    assert f.signal.channels == 2
    assert f.signal.rate == 44100.0
    assert f.signal.precision == 16
    
    # Test encoding properties
    assert isinstance(f.encoding, sox.EncodingInfo)
    assert f.encoding.encoding == 1  # SIGN2
    assert f.encoding.bits_per_sample == 16
    
    # Test filetype
    assert isinstance(f.filetype, str)
    assert len(f.filetype) > 0


def test_format_with_signal_and_encoding():
    """Test Format creation with SignalInfo and EncodingInfo"""
    signal = sox.SignalInfo(rate=44100.0, channels=2, precision=16)
    encoding = sox.EncodingInfo(encoding=1, bits_per_sample=16)
    
    f = sox.Format('tests/data/s00.wav', signal=signal, encoding=encoding)
    assert f is not None


def test_format_nonexistent_file():
    """Test Format creation with non-existent file"""
    with pytest.raises(MemoryError):
        sox.Format('nonexistent_file.wav')


# # Test FormatHandler class
# def test_format_handler_creation():
#     """Test FormatHandler creation"""
#     handler = sox.FormatHandler('tests/data/s00.wav')
#     assert handler is not None


# def test_format_handler_properties():
#     """Test FormatHandler properties"""
#     handler = sox.FormatHandler('tests/data/s00.wav')
    
#     assert handler.sox_lib_version_code > 0
#     assert isinstance(handler.description, str) or handler.description is None
#     assert isinstance(handler.names, list)
#     assert isinstance(handler.flags, int)
#     assert handler.priv_size >= 0


# def test_format_handler_nonexistent_file():
#     """Test FormatHandler creation with non-existent file"""
#     with pytest.raises(MemoryError):
#         sox.FormatHandler('nonexistent_file.wav')


# Test FormatTab class
def test_format_tab_creation():
    """Test FormatTab creation"""
    tab = sox.FormatTab("wav")
    assert tab is not None


def test_format_tab_default_values():
    """Test FormatTab with default values"""
    tab = sox.FormatTab()
    assert tab.name is None
    assert tab.fn is None


def test_format_tab_with_name():
    """Test FormatTab with name"""
    tab = sox.FormatTab("mp3")
    # Note: name setter is not fully implemented in the Cython code
    # so we can't test setting the name property


# Test EffectHandler class
def test_effect_handler_from_ptr():
    """Test EffectHandler creation from pointer"""
    # This would require a valid sox_effect_handler_t pointer
    # For now, we'll just test that the class exists
    assert hasattr(sox, 'EffectHandler')


# Test EffectsGlobals class
def test_effects_globals_creation():
    """Test EffectsGlobals creation"""
    g = sox.EffectsGlobals()
    assert g is not None


# def test_effects_globals_properties():
#     """Test EffectsGlobals properties"""
#     g = sox.EffectsGlobals()
    
#     assert isinstance(g.verbosity, int)
#     assert isinstance(g.repeatable, bool)
#     assert isinstance(g.bufsiz, int)
#     assert isinstance(g.input_bufsiz, int)
#     assert isinstance(g.ranqd1, int)
#     assert isinstance(g.use_magic, bool)
#     assert isinstance(g.use_threads, bool)
#     assert isinstance(g.log2_dft_min_size, int)


# def test_effects_globals_property_setters():
#     """Test EffectsGlobals property setters"""
#     g = sox.EffectsGlobals()
    
#     g.verbosity = 2
#     g.repeatable = True
#     g.bufsiz = 8192
#     g.input_bufsiz = 4096
#     g.ranqd1 = 12345
#     g.use_magic = False
#     g.use_threads = True
#     g.log2_dft_min_size = 8
    
#     assert g.verbosity == 2
#     assert g.repeatable == True
#     assert g.bufsiz == 8192
#     assert g.input_bufsiz == 4096
#     assert g.ranqd1 == 12345
#     assert g.use_magic == False
#     assert g.use_threads == True
#     assert g.log2_dft_min_size == 8


# # Test Effect class
# def test_effect_creation():
#     """Test Effect creation"""
#     effect = sox.Effect("trim", "0 10")
#     assert effect is not None


# def test_effect_properties():
#     """Test Effect properties"""
#     effect = sox.Effect("trim", "0 10")
    
#     assert effect.name == "trim"
#     assert effect.usage == "0 10"
#     assert isinstance(effect.flags, int)
#     assert effect.priv_size >= 0


# def test_effect_invalid_name():
#     """Test Effect creation with invalid name"""
#     with pytest.raises(MemoryError):
#         sox.Effect("invalid_effect", "params")


# Test EffectsChain class
def test_effects_chain_creation():
    """Test EffectsChain creation"""
    chain = sox.EffectsChain()
    assert chain is not None


# def test_effects_chain_properties():
#     """Test EffectsChain properties"""
#     chain = sox.EffectsChain()
    
#     assert isinstance(chain.effects, list)
#     assert chain.length == 0
#     assert isinstance(chain.global_info, sox.EffectsGlobals)
#     assert chain.in_enc is None
#     assert chain.out_enc is None
#     assert chain.table_size >= 0


# def test_effects_chain_add_effect():
#     """Test EffectsChain add_effect method"""
#     chain = sox.EffectsChain()
#     effect = sox.Effect("trim", "0 10")
    
#     chain.add_effect(effect)
#     assert chain.length == 1
#     assert len(chain.effects) == 1


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
    assert 'version' in info
    assert isinstance(info['version'], str) or info['version'] is None


def test_get_globals():
    """Test get_globals function"""
    globals = sox.get_globals()
    assert isinstance(globals, dict)
    assert 'verbosity' in globals
    assert 'repeatable' in globals
    assert 'bufsiz' in globals


def test_get_encodings_info():
    """Test get_encodings_info function"""
    encodings = sox.get_encodings_info()
    assert isinstance(encodings, list)
    assert len(encodings) > 0
    
    for encoding in encodings:
        assert isinstance(encoding, dict)
        assert 'flags' in encoding
        assert 'name' in encoding
        assert 'desc' in encoding


def test_get_encodings():
    """Test get_encodings function"""
    encodings = sox.get_encodings()
    assert isinstance(encodings, list)
    assert len(encodings) > 0
    
    for encoding in encodings:
        assert hasattr(encoding, 'flags')
        assert hasattr(encoding, 'name')
        assert hasattr(encoding, 'desc')
        assert hasattr(encoding, 'type')


def test_format_init_and_quit():
    """Test format_init and format_quit functions"""
    # These functions should not raise exceptions
    sox.format_init()
    sox.format_quit()


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
    assert not sox.is_playlist('tests/data/s00.wav')
    
    # Test with a playlist file (m3u format)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.m3u', delete=False) as f:
        f.write('#EXTM3U\n')
        f.write('tests/data/s00.wav\n')
        playlist_file = f.name
    
    try:
        assert sox.is_playlist(playlist_file)
    finally:
        os.unlink(playlist_file)


def test_basename():
    """Test basename function"""
    # Test with a simple filename
    assert sox.basename('tests/data/s00.wav') == 's00'
    
    # Test with a path
    assert sox.basename('/path/to/file.wav') == 'file'
    
    # Test with just a filename
    assert sox.basename('file.wav') == 'file'


def test_precision():
    """Test precision function"""
    # Test with SIGN2 encoding and 16 bits
    precision_val = sox.precision(1, 16)  # SIGN2 encoding
    assert isinstance(precision_val, int)
    assert precision_val >= 0


# def test_find_format():
#     """Test find_format function"""
#     # Test finding a known format
#     format_info = sox.find_format('wav')
#     assert format_info is not None
#     assert isinstance(format_info, dict)
#     assert 'description' in format_info
#     assert 'names' in format_info
    
#     # Test finding a non-existent format
#     format_info = sox.find_format('nonexistent_format')
#     assert format_info is None


def test_get_effects_globals():
    """Test get_effects_globals function"""
    globals = sox.get_effects_globals()
    assert isinstance(globals, dict)
    assert 'plot' in globals


def test_find_effect():
    """Test find_effect function"""
    # Test finding a known effect
    effect_info = sox.find_effect('trim')
    assert effect_info is not None
    assert isinstance(effect_info, dict)
    assert 'name' in effect_info
    assert 'usage' in effect_info
    assert 'flags' in effect_info
    assert 'priv_size' in effect_info
    
    # Test finding a non-existent effect
    effect_info = sox.find_effect('nonexistent_effect')
    assert effect_info is None


# def test_format_supports_encoding():
#     """Test format_supports_encoding function"""
#     encoding = sox.EncodingInfo(encoding=1, bits_per_sample=16)  # SIGN2
    
#     # Test with a format that supports the encoding
#     supports = sox.format_supports_encoding('tests/data/s00.wav', encoding)
#     assert isinstance(supports, bool)


# Test error handling
def test_format_invalid_file():
    """Test Format with invalid file"""
    with pytest.raises(MemoryError):
        sox.Format('nonexistent_file.wav')


# def test_format_handler_invalid_file():
#     """Test FormatHandler with invalid file"""
#     with pytest.raises(MemoryError):
#         sox.FormatHandler('nonexistent_file.wav')


# def test_effect_invalid_effect():
#     """Test Effect with invalid effect name"""
#     with pytest.raises(MemoryError):
#         sox.Effect('invalid_effect_name', 'params')


# Test memory management
def test_signal_info_memory_management():
    """Test SignalInfo memory management"""
    signal = sox.SignalInfo(rate=44100.0, channels=2, precision=16)
    assert signal.rate == 44100.0
    
    # Test that the object can be properly cleaned up
    del signal


def test_encoding_info_memory_management():
    """Test EncodingInfo memory management"""
    encoding = sox.EncodingInfo(encoding=1, bits_per_sample=16)
    assert encoding.encoding == 1
    
    # Test that the object can be properly cleaned up
    del encoding


def test_loop_info_memory_management():
    """Test LoopInfo memory management"""
    loop = sox.LoopInfo(start=100, length=500, count=3)
    assert loop.start == 100
    
    # Test that the object can be properly cleaned up
    del loop


def test_instr_info_memory_management():
    """Test InstrInfo memory management"""
    instr = sox.InstrInfo(note=60, low=0, high=127)
    assert instr.note == 60
    
    # Test that the object can be properly cleaned up
    del instr


# def test_file_info_memory_management():
#     """Test FileInfo memory management"""
#     file_info = sox.FileInfo(buf=b"test", size=4, count=1, pos=0)
#     assert file_info.size == 4
    
#     # Test that the object can be properly cleaned up
#     del file_info


# def test_out_of_band_memory_management():
#     """Test OutOfBand memory management"""
#     oob = sox.OutOfBand()
#     oob.append_comment("test=value")
#     assert oob.num_comments() == 1
    
#     # Test that the object can be properly cleaned up
#     del oob


# Test integration scenarios
def test_format_with_comments():
    """Test Format with metadata comments"""
    # This would require a file format that supports metadata
    # For now, we'll just test that we can create a Format object
    f = sox.Format('tests/data/s00.wav')
    assert f is not None


# def test_effects_chain_workflow():
#     """Test a complete effects chain workflow"""
#     chain = sox.EffectsChain()
    
#     # Add a trim effect
#     trim_effect = sox.Effect("trim", "0 10")
#     chain.add_effect(trim_effect)
    
#     assert chain.length == 1
#     assert len(chain.effects) == 1


# def test_multiple_effects():
#     """Test adding multiple effects to a chain"""
#     chain = sox.EffectsChain()
    
#     # Add multiple effects
#     trim_effect = sox.Effect("trim", "0 10")
#     vol_effect = sox.Effect("vol", "0.5")
    
#     chain.add_effect(trim_effect)
#     chain.add_effect(vol_effect)
    
#     assert chain.length == 2
#     assert len(chain.effects) == 2


# Test edge cases
def test_signal_info_edge_cases():
    """Test SignalInfo with edge case values"""
    # Test with maximum values
    signal = sox.SignalInfo(
        rate=192000.0,  # High sample rate
        channels=8,     # Many channels
        precision=32,   # High precision
        length=1000000, # Large length
        mult=10.0       # High multiplier
    )
    
    assert signal.rate == 192000.0
    assert signal.channels == 8
    assert signal.precision == 32
    assert signal.length == 1000000
    assert signal.mult == 10.0


def test_encoding_info_edge_cases():
    """Test EncodingInfo with edge case values"""
    encoding = sox.EncodingInfo(
        encoding=25,        # High encoding value
        bits_per_sample=32, # High bits per sample
        compression=100.0,  # High compression
        reverse_bytes=1,
        reverse_nibbles=1,
        reverse_bits=1,
        opposite_endian=True
    )
    
    assert encoding.encoding == 25
    assert encoding.bits_per_sample == 32
    assert encoding.compression == 100.0
    assert encoding.reverse_bytes == 1
    assert encoding.reverse_nibbles == 1
    assert encoding.reverse_bits == 1
    assert encoding.opposite_endian == True


def test_loop_info_edge_cases():
    """Test LoopInfo with edge case values"""
    loop = sox.LoopInfo(
        start=1000000,  # Large start value
        length=500000,  # Large length value
        count=100,      # High count
        type=2          # Different type
    )
    
    assert loop.start == 1000000
    assert loop.length == 500000
    assert loop.count == 100
    assert loop.type == 2


def test_instr_info_edge_cases():
    """Test InstrInfo with edge case values"""
    instr = sox.InstrInfo(
        note=127,  # Maximum MIDI note
        low=0,     # Minimum low
        high=127,  # Maximum high
        loopmode=2, # Different loop mode
        nloops=10   # Multiple loops
    )
    
    assert instr.note == 127
    assert instr.low == 0
    assert instr.high == 127
    assert instr.loopmode == 2
    assert instr.nloops == 10


# Test property access patterns
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


# # Test object lifecycle
# def test_object_lifecycle():
#     """Test object lifecycle and cleanup"""
#     # Create multiple objects
#     signal = sox.SignalInfo(rate=44100.0, channels=2, precision=16)
#     encoding = sox.EncodingInfo(encoding=1, bits_per_sample=16)
#     loop = sox.LoopInfo(start=100, length=500, count=3)
#     instr = sox.InstrInfo(note=60, low=0, high=127)
#     file_info = sox.FileInfo(buf=b"test", size=4, count=1, pos=0)
#     oob = sox.OutOfBand()
    
#     # Verify they were created successfully
#     assert signal.rate == 44100.0
#     assert encoding.encoding == 1
#     assert loop.start == 100
#     assert instr.note == 60
#     assert file_info.size == 4
#     assert oob.num_comments() == 0
    
#     # Clean up (should not raise exceptions)
#     del signal
#     del encoding
#     del loop
#     del instr
#     del file_info
#     del oob

