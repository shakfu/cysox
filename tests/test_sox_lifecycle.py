from cysox import sox

# Test object lifecycle


def test_object_lifecycle():
    """Test object lifecycle and cleanup"""
    # Create multiple objects
    signal = sox.SignalInfo(rate=44100.0, channels=2, precision=16)
    encoding = sox.EncodingInfo(encoding=1, bits_per_sample=16)
    loop = sox.LoopInfo(start=100, length=500, count=3)
    instr = sox.InstrInfo(note=60, low=0, high=127)
    file_info = sox.FileInfo(buf=b"test", size=4, count=1, pos=0)
    # oob = sox.OutOfBand()

    # Verify they were created successfully
    assert signal.rate == 44100.0
    assert encoding.encoding == 1
    assert loop.start == 100
    assert instr.note == 60
    assert file_info.size == 4
    # assert oob.num_comments() == 0

    # Clean up (should not raise exceptions)
    del signal
    del encoding
    del loop
    del instr
    del file_info
    # del oob
