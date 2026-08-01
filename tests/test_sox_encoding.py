import math
import struct

import pytest

import cysox
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


# --- convert() output encoding -------------------------------------------
#
# Regression tests for convert() dropping the input's sample encoding: a float
# WAV came back as 32-bit *integer* PCM because the output Format was opened
# with no encoding=, leaving libsox to pick the handler default for the given
# precision. Valid file, plausible samples, wrong format.


def _write_wav(path, fmt_tag, bits, n=2048, rate=44100):
    """Write a minimal 44-byte-header WAV. fmt_tag: 1=PCM, 3=IEEE float."""
    frame_bytes = bits // 8
    frames = []
    for i in range(n):
        v = 0.5 * math.sin(2 * math.pi * 440 * i / rate)
        if fmt_tag == 3:
            frames.append(struct.pack("<f", v))
        elif bits == 16:
            frames.append(struct.pack("<h", int(v * 32767)))
        elif bits == 24:
            frames.append(struct.pack("<i", int(v * (2**23 - 1)))[:3])
        else:
            raise ValueError(f"unsupported: tag={fmt_tag} bits={bits}")
    data = b"".join(frames)
    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        36 + len(data),
        b"WAVE",
        b"fmt ",
        16,
        fmt_tag,
        1,
        rate,
        rate * frame_bytes,
        frame_bytes,
        bits,
        b"data",
        len(data),
    )
    path.write_bytes(header + data)
    return path


@pytest.mark.parametrize(
    "fmt_tag,bits,expected",
    [
        (3, 32, "float"),
        (1, 16, "signed-integer"),
        (1, 24, "signed-integer"),
    ],
    ids=["float32", "int16", "int24"],
)
def test_convert_preserves_input_encoding(tmp_path, fmt_tag, bits, expected):
    """convert() must not silently change the sample encoding."""
    src = _write_wav(tmp_path / "in.wav", fmt_tag, bits)
    dst = tmp_path / "out.wav"

    cysox.convert(str(src), str(dst), sample_rate=48000, channels=1)

    assert cysox.info(str(src)).encoding == expected
    assert cysox.info(str(dst)).encoding == expected
    assert cysox.info(str(dst)).bits_per_sample == bits


def test_convert_falls_back_when_format_cannot_encode(tmp_path):
    """float32 -> mp3 has no float encoding available; it must still succeed."""
    if not sox.find_format("mp3", False):
        pytest.skip("libsox build has no mp3 handler")
    src = _write_wav(tmp_path / "in.wav", 3, 32)
    dst = tmp_path / "out.mp3"

    cysox.convert(str(src), str(dst))

    assert dst.exists() and dst.stat().st_size > 0
    assert cysox.info(str(dst)).encoding == "mp3"


def test_convert_explicit_encoding_overrides_input(tmp_path):
    """An explicit encoding= wins over the inherited one."""
    src = _write_wav(tmp_path / "in.wav", 3, 32)
    dst = tmp_path / "out.wav"

    cysox.convert(str(src), str(dst), encoding="signed-integer", bits=16)

    out = cysox.info(str(dst))
    assert out.encoding == "signed-integer"
    assert out.bits_per_sample == 16


def test_convert_explicit_bits_not_silently_ignored(tmp_path):
    """bits= must hold even when the inherited encoding cannot honour it.

    WAV cannot write float at 16 bits. Pairing the input's float encoding with
    bits=16 makes libsox discard the width and emit float/32 - so the inherited
    encoding has to yield to the explicit bits.
    """
    src = _write_wav(tmp_path / "in.wav", 3, 32)
    dst = tmp_path / "out.wav"

    cysox.convert(str(src), str(dst), bits=16)

    assert cysox.info(str(dst)).bits_per_sample == 16


def test_convert_rejects_impossible_explicit_encoding(tmp_path):
    """An explicit request the format cannot satisfy is an error, not a shrug."""
    src = _write_wav(tmp_path / "in.wav", 3, 32)

    with pytest.raises(ValueError, match="cannot encode"):
        cysox.convert(str(src), str(tmp_path / "out.wav"), encoding="float", bits=16)


def test_convert_rejects_unknown_encoding_name(tmp_path):
    src = _write_wav(tmp_path / "in.wav", 1, 16)

    with pytest.raises(ValueError, match="Unknown encoding"):
        cysox.convert(str(src), str(tmp_path / "out.wav"), encoding="flooat")


# --- encoding preservation in convert()'s siblings -------------------------
#
# Same defect as above, same cause: slice_loop/stutter/split_by_silence opened
# their output (and intermediate temp) Formats with no encoding=. concat() did
# propagate the encoding but without the supports-check, so it forced an
# unsupported pair on libsox instead of falling back.


def test_slice_loop_preserves_input_encoding(tmp_path):
    src = _write_wav(tmp_path / "in.wav", 3, 32, n=8192)
    out_dir = tmp_path / "slices"

    paths = cysox.slice_loop(str(src), str(out_dir), slices=2)

    assert paths
    for p in paths:
        assert cysox.info(p).encoding == "float"


def test_slice_loop_preserves_encoding_through_effects(tmp_path):
    """The effects path routes through a temp file - encoding must survive both hops."""
    from cysox import fx

    src = _write_wav(tmp_path / "in.wav", 3, 32, n=8192)
    out_dir = tmp_path / "slices"

    paths = cysox.slice_loop(
        str(src), str(out_dir), slices=2, effects=[fx.Volume(db=1)]
    )

    assert paths
    for p in paths:
        assert cysox.info(p).encoding == "float"


def test_stutter_preserves_input_encoding(tmp_path):
    src = _write_wav(tmp_path / "in.wav", 3, 32, n=8192)
    dst = tmp_path / "out.wav"

    cysox.stutter(str(src), str(dst), segment_duration=0.01, repeats=2)

    assert cysox.info(str(dst)).encoding == "float"


def test_split_by_silence_preserves_input_encoding(tmp_path):
    """Segments of a float master must stay float."""
    src = _write_wav(tmp_path / "in.wav", 3, 32, n=16384)
    out_dir = tmp_path / "segs"

    paths = cysox.split_by_silence(str(src), str(out_dir), min_segment=0.01)

    for p in paths:
        assert cysox.info(p).encoding == "float"


def test_concat_preserves_input_encoding(tmp_path):
    src = _write_wav(tmp_path / "in.wav", 3, 32)
    dst = tmp_path / "out.wav"

    cysox.concat([str(src), str(src)], str(dst))

    assert cysox.info(str(dst)).encoding == "float"


def test_concat_falls_back_when_format_cannot_encode(tmp_path):
    """concat() propagated encoding unguarded; float32 -> mp3 must fall back."""
    if not sox.find_format("mp3", False):
        pytest.skip("libsox build has no mp3 handler")
    src = _write_wav(tmp_path / "in.wav", 3, 32)
    dst = tmp_path / "out.mp3"

    cysox.concat([str(src), str(src)], str(dst))

    assert dst.exists() and dst.stat().st_size > 0
    assert cysox.info(str(dst)).encoding == "mp3"


@pytest.mark.parametrize(
    "call",
    [
        lambda src, out: cysox.stutter(
            str(src),
            str(out / "s.wav"),
            segment_duration=0.01,
            repeats=2,
            encoding="signed-integer",
        ),
        lambda src, out: cysox.concat(
            [str(src), str(src)], str(out / "s.wav"), encoding="signed-integer"
        ),
    ],
    ids=["stutter", "concat"],
)
def test_explicit_encoding_overrides_input(tmp_path, call):
    src = _write_wav(tmp_path / "in.wav", 3, 32, n=8192)
    out = tmp_path / "out"
    out.mkdir()

    call(src, out)

    assert cysox.info(str(out / "s.wav")).encoding == "signed-integer"


def test_slice_loop_explicit_encoding_overrides_input(tmp_path):
    src = _write_wav(tmp_path / "in.wav", 3, 32, n=8192)

    paths = cysox.slice_loop(
        str(src), str(tmp_path / "slices"), slices=2, encoding="signed-integer"
    )

    assert paths
    for p in paths:
        assert cysox.info(p).encoding == "signed-integer"
