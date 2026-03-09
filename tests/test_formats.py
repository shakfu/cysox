"""Tests for format diversity: MP3, FLAC, mono, different sample rates."""

from pathlib import Path

import pytest

import cysox
from cysox import fx


DATA_DIR = Path(__file__).parent / "data"

MP3_FILE = str(DATA_DIR / "s00.mp3")
FLAC_FILE = str(DATA_DIR / "s00.flac")
WAV_FILE = str(DATA_DIR / "s00.wav")
MONO_22K_FILE = str(DATA_DIR / "s00_mono_22k.wav")
AMEN_FILE = str(DATA_DIR / "amen.wav")


class TestInfoFormats:
    """info() works across formats."""

    def test_info_mp3(self):
        info = cysox.info(MP3_FILE)
        assert info["format"] == "mp3"
        assert info["sample_rate"] == 44100
        assert info["channels"] == 2
        assert info["duration"] > 5.0

    def test_info_flac(self):
        info = cysox.info(FLAC_FILE)
        assert info["format"] == "flac"
        assert info["sample_rate"] == 44100
        assert info["channels"] == 2
        assert info["bits_per_sample"] == 16

    def test_info_mono_22k(self):
        info = cysox.info(MONO_22K_FILE)
        assert info["format"] == "wav"
        assert info["sample_rate"] == 22050
        assert info["channels"] == 1

    def test_info_amen(self):
        info = cysox.info(AMEN_FILE)
        assert info["format"] == "wav"
        assert info["duration"] > 2.0


class TestConvertFormats:
    """convert() works across input/output formats."""

    def test_mp3_to_wav(self, output_path):
        cysox.convert(MP3_FILE, str(output_path))
        info = cysox.info(str(output_path))
        assert info["format"] == "wav"
        assert info["sample_rate"] == 44100

    def test_flac_to_wav(self, output_path):
        cysox.convert(FLAC_FILE, str(output_path))
        info = cysox.info(str(output_path))
        assert info["format"] == "wav"
        assert info["channels"] == 2

    def test_wav_to_flac(self, output_path_factory):
        out = str(output_path_factory("flac", ".flac"))
        cysox.convert(WAV_FILE, out)
        info = cysox.info(out)
        assert info["format"] == "flac"

    def test_mono_input(self, output_path):
        cysox.convert(MONO_22K_FILE, str(output_path))
        info = cysox.info(str(output_path))
        assert info["channels"] == 1
        assert info["sample_rate"] == 22050

    def test_mono_to_stereo(self, output_path):
        cysox.convert(MONO_22K_FILE, str(output_path), channels=2)
        info = cysox.info(str(output_path))
        assert info["channels"] == 2

    def test_resample_22k_to_44k(self, output_path):
        cysox.convert(MONO_22K_FILE, str(output_path), sample_rate=44100)
        info = cysox.info(str(output_path))
        assert info["sample_rate"] == 44100

    def test_mp3_with_effects(self, output_path):
        cysox.convert(MP3_FILE, str(output_path), effects=[fx.Volume(db=-3)])
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_flac_with_effects(self, output_path):
        cysox.convert(FLAC_FILE, str(output_path), effects=[fx.Normalize()])
        assert output_path.exists()
        assert output_path.stat().st_size > 0


class TestStreamFormats:
    """stream() works across formats."""

    def test_stream_mp3(self):
        chunks = list(cysox.stream(MP3_FILE, chunk_size=4096))
        assert len(chunks) > 0
        total = sum(len(c) for c in chunks)
        assert total > 0

    def test_stream_flac(self):
        chunks = list(cysox.stream(FLAC_FILE, chunk_size=4096))
        assert len(chunks) > 0

    def test_stream_mono(self):
        chunks = list(cysox.stream(MONO_22K_FILE, chunk_size=4096))
        assert len(chunks) > 0


class TestConcatFormats:
    """concat() works with different files."""

    def test_concat_amen_with_itself(self, output_path):
        cysox.concat([AMEN_FILE, AMEN_FILE], str(output_path))
        input_info = cysox.info(AMEN_FILE)
        output_info = cysox.info(str(output_path))
        expected = input_info["duration"] * 2
        assert 0.9 <= output_info["duration"] / expected <= 1.1


class TestOnsetFormats:
    """Onset detection works across formats and configurations."""

    def test_onset_amen(self):
        from cysox import onset
        onsets = onset.detect(AMEN_FILE, threshold=0.3)
        assert len(onsets) > 0
        for t in onsets:
            assert isinstance(t, float)
            assert t >= 0.0

    def test_onset_mono(self):
        from cysox import onset
        onsets = onset.detect(MONO_22K_FILE, threshold=0.3)
        # mono file should work without error
        assert isinstance(onsets, list)

    def test_onset_flac(self):
        from cysox import onset
        onsets = onset.detect(FLAC_FILE, threshold=0.3)
        assert isinstance(onsets, list)
