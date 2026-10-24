"""mp3 decoding: end of stream, truncation, seeking and length.

The first three classes hold for any decoder. TestMpg123Length covers the
libmpg123 reader in scripts/patches/, which replaced libmad in the wheels.
SoX_ng shipped an mpg123 reader that looped forever at the end of some files,
so stream termination runs in a subprocess with a timeout.
"""

import pathlib
import random
import subprocess
import sys

import pytest

from cysox import sox

DATA_DIR = pathlib.Path(__file__).parent / "data"
MP3_FILE = str(DATA_DIR / "s00.mp3")
# First 1.5 s of s00.wav, encoded by ffmpeg's libmp3lame: carries an Info
# frame with LAME encoder delay and padding, which cysox's writer does not.
TAGGED_FILE = str(DATA_DIR / "s00_lame_tag.mp3")
TAGGED_SOURCE_FRAMES = 66150

ALL_FILES = [MP3_FILE, TAGGED_FILE]


def _decode_all(path: str) -> list:
    sox.init()
    with sox.Format(path) as f:
        return f.read(1 << 22)


def _decode_in_subprocess(path: str) -> int:
    """Decode path to the end in a fresh interpreter; return the sample count."""
    script = (
        "import sys\nfrom cysox import sox\nsox.init()\n"
        "n = 0\n"
        "with sox.Format(sys.argv[1]) as f:\n"
        "    while True:\n"
        "        chunk = f.read(8192)\n"
        "        if not chunk:\n"
        "            break\n"
        "        n += len(chunk)\n"
        "print(n)\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script, path],
        cwd=str(pathlib.Path(__file__).parent.parent),
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr[-2000:]
    return int(result.stdout.strip())


class TestStreamEnd:
    @pytest.mark.parametrize("path", ALL_FILES)
    def test_decoding_terminates(self, path):
        assert _decode_in_subprocess(path) > 0

    def test_truncated_file_terminates(self, tmp_path):
        data = pathlib.Path(MP3_FILE).read_bytes()
        cut = tmp_path / "cut.mp3"
        # An odd byte count lands mid-frame.
        cut.write_bytes(data[: len(data) * 3 // 5 + 1])

        n = _decode_in_subprocess(str(cut))
        assert 0 < n < len(_decode_all(MP3_FILE))


class TestSeek:
    @pytest.mark.parametrize("path", ALL_FILES)
    def test_seek_matches_full_decode(self, path, mp3_decoder, request):
        if mp3_decoder == "mad":
            # Measured: sox 14.4.2's libmad seek lands one frame (1152 samples
            # per channel) late, and its first frame is decoded unprimed.
            request.applymarker(pytest.mark.xfail(strict=True, reason="libmad seek is a frame late"))
        full = _decode_all(path)
        channels = 2
        # Mid-file and not aligned to a 1152-sample frame.
        start = (len(full) // channels // 2 + 333) * channels

        with sox.Format(path) as f:
            assert f.signal.channels == channels
            f.seek(start)
            got = f.read(4096)

        assert got == full[start : start + 4096]


class TestHandles:
    def test_many_files_open_and_close_in_any_order(self):
        expected = _decode_all(MP3_FILE)[:4096]
        formats = [sox.Format(MP3_FILE) for _ in range(8)]
        for f in formats:
            assert f.read(4096) == expected

        random.Random(0).shuffle(formats)
        for f in formats:
            f.close()

        with sox.Format(MP3_FILE) as f:
            assert f.read(4096) == expected


class TestMpg123Length:
    @pytest.fixture(autouse=True)
    def _only_mpg123(self, mp3_decoder):
        if mp3_decoder != "mpg123":
            pytest.skip("libmad estimates length; exactness is an mpg123 property")

    @pytest.mark.parametrize("path", ALL_FILES)
    def test_length_equals_decoded_count(self, path):
        with sox.Format(path) as f:
            length = f.signal.length
        assert length == len(_decode_all(path))

    def test_gapless_trims_to_source_length(self):
        with sox.Format(TAGGED_FILE) as f:
            assert f.signal.length == TAGGED_SOURCE_FRAMES * f.signal.channels
