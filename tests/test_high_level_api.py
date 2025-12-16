"""Tests for the high-level cysox API."""

import pytest
import cysox
from cysox import fx


class TestInfo:
    """Tests for cysox.info()."""

    def test_info_returns_dict(self, test_wav_str):
        """info() returns a dictionary."""
        info = cysox.info(test_wav_str)
        assert isinstance(info, dict)

    def test_info_contains_required_keys(self, test_wav_str):
        """info() returns all required keys."""
        info = cysox.info(test_wav_str)
        required_keys = [
            "path",
            "format",
            "duration",
            "sample_rate",
            "channels",
            "bits_per_sample",
            "samples",
            "encoding",
        ]
        for key in required_keys:
            assert key in info, f"Missing key: {key}"

    def test_info_values(self, test_wav_str):
        """info() returns correct values for test file."""
        info = cysox.info(test_wav_str)
        assert info["path"] == test_wav_str
        assert info["format"] == "wav"
        assert info["sample_rate"] == 44100
        assert info["channels"] == 2
        assert info["bits_per_sample"] == 16
        assert info["samples"] > 0
        assert info["duration"] > 0
        assert info["encoding"] == "signed-integer"

    def test_info_nonexistent_file(self):
        """info() raises exception for nonexistent file."""
        with pytest.raises(Exception):
            cysox.info("/nonexistent/file.wav")


class TestConvert:
    """Tests for cysox.convert()."""

    def test_simple_conversion(self, test_wav_str, output_path):
        """Basic file conversion without effects."""
        cysox.convert(test_wav_str, output_path)
        assert output_path.exists()

        info = cysox.info(str(output_path))
        original = cysox.info(test_wav_str)
        assert info["sample_rate"] == original["sample_rate"]
        assert info["channels"] == original["channels"]

    def test_conversion_with_effects(self, test_wav_str, output_path):
        """Conversion with effects chain."""
        cysox.convert(
            test_wav_str,
            output_path,
            effects=[
                fx.Volume(db=3),
                fx.Bass(gain=2),
            ]
        )
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_conversion_with_sample_rate(self, test_wav_str, output_path):
        """Conversion with sample rate change."""
        cysox.convert(test_wav_str, output_path, sample_rate=22050)

        info = cysox.info(str(output_path))
        assert info["sample_rate"] == 22050

    def test_conversion_with_channels(self, test_wav_str, output_path):
        """Conversion with channel count change."""
        cysox.convert(test_wav_str, output_path, channels=1)

        info = cysox.info(str(output_path))
        assert info["channels"] == 1

    def test_conversion_with_all_options(self, test_wav_str, output_path):
        """Conversion with effects and format options."""
        cysox.convert(
            test_wav_str,
            output_path,
            effects=[fx.Normalize(), fx.Fade(fade_in=0.1)],
            sample_rate=22050,
            channels=1,
        )

        info = cysox.info(str(output_path))
        assert info["sample_rate"] == 22050
        assert info["channels"] == 1


class TestStream:
    """Tests for cysox.stream()."""

    def test_stream_yields_memoryview(self, test_wav_str):
        """stream() yields memoryview objects."""
        for chunk in cysox.stream(test_wav_str, chunk_size=1024):
            assert isinstance(chunk, memoryview)
            break  # Just test first chunk

    def test_stream_reads_all_samples(self, test_wav_str):
        """stream() reads all samples from file."""
        info = cysox.info(test_wav_str)
        expected_samples = info["samples"]

        total_samples = 0
        for chunk in cysox.stream(test_wav_str, chunk_size=8192):
            # memoryview len() returns number of int32 elements (samples)
            total_samples += len(chunk)

        assert total_samples == expected_samples

    def test_stream_chunk_size(self, test_wav_str):
        """stream() respects chunk_size parameter."""
        chunk_size = 1000
        for chunk in cysox.stream(test_wav_str, chunk_size=chunk_size):
            # Last chunk may be smaller
            assert len(chunk) // 4 <= chunk_size
            break

    def test_stream_empty_on_nonexistent_file(self):
        """stream() raises exception for nonexistent file."""
        with pytest.raises(Exception):
            list(cysox.stream("/nonexistent/file.wav"))


class TestFxClasses:
    """Tests for fx effect classes."""

    def test_volume_effect(self):
        """Volume effect creates correct args."""
        v = fx.Volume(db=3)
        assert v.name == "vol"
        assert v.to_args() == ["3dB"]

        v = fx.Volume(db=-6, limiter=True)
        assert v.to_args() == ["-6dB", "limiter"]

    def test_bass_effect(self):
        """Bass effect creates correct args."""
        b = fx.Bass(gain=5)
        assert b.name == "bass"
        assert b.to_args() == ["5", "100", "0.5"]

    def test_treble_effect(self):
        """Treble effect creates correct args."""
        t = fx.Treble(gain=-2, frequency=4000)
        assert t.name == "treble"
        assert t.to_args() == ["-2", "4000", "0.5"]

    def test_reverb_effect(self):
        """Reverb effect creates correct args."""
        r = fx.Reverb(reverberance=80)
        assert r.name == "reverb"
        args = r.to_args()
        assert args[0] == "80"

    def test_trim_effect(self):
        """Trim effect creates correct args."""
        t = fx.Trim(start=1.5, end=10.0)
        assert t.name == "trim"
        assert t.to_args() == ["1.5", "=10.0"]

        t = fx.Trim(start=0, duration=5.0)
        assert t.to_args() == ["0", "5.0"]

    def test_trim_validation(self):
        """Trim effect validates parameters."""
        with pytest.raises(ValueError):
            fx.Trim(start=0, end=10, duration=5)

    def test_rate_effect(self):
        """Rate effect creates correct args."""
        r = fx.Rate(sample_rate=48000)
        assert r.name == "rate"
        assert "-h" in r.to_args()
        assert "48000" in r.to_args()

    def test_channels_effect(self):
        """Channels effect creates correct args."""
        c = fx.Channels(channels=1)
        assert c.name == "channels"
        assert c.to_args() == ["1"]

    def test_highpass_effect(self):
        """HighPass effect creates correct args."""
        h = fx.HighPass(frequency=80)
        assert h.name == "highpass"
        assert h.to_args() == ["-2", "80"]

    def test_highpass_validation(self):
        """HighPass effect validates parameters."""
        with pytest.raises(ValueError):
            fx.HighPass(frequency=100, poles=3)

    def test_fade_effect(self):
        """Fade effect creates correct args."""
        f = fx.Fade(fade_in=0.5, fade_out=1.0)
        assert f.name == "fade"
        args = f.to_args()
        assert "t" in args  # default type
        assert "0.5" in args

    def test_normalize_effect(self):
        """Normalize effect creates correct args."""
        n = fx.Normalize()
        assert n.name == "norm"
        assert n.to_args() == ["-1"]

        n = fx.Normalize(level=-3)
        assert n.to_args() == ["-3"]

    def test_effect_repr(self):
        """Effect classes have useful repr."""
        v = fx.Volume(db=3)
        assert "Volume" in repr(v)
        assert "db=3" in repr(v)


class TestCompositeEffect:
    """Tests for CompositeEffect."""

    def test_composite_effect_expand(self):
        """CompositeEffect can be defined and expanded."""
        class WarmReverb(fx.CompositeEffect):
            def __init__(self, decay=60):
                self.decay = decay

            @property
            def effects(self):
                return [
                    fx.HighPass(frequency=80),
                    fx.Reverb(reverberance=self.decay),
                    fx.Volume(db=-2),
                ]

        warm = WarmReverb(decay=70)
        assert len(warm.effects) == 3
        assert isinstance(warm.effects[0], fx.HighPass)
        assert isinstance(warm.effects[1], fx.Reverb)
        assert isinstance(warm.effects[2], fx.Volume)

    def test_composite_effect_to_args_raises(self):
        """CompositeEffect.to_args() raises TypeError."""
        class TestComposite(fx.CompositeEffect):
            @property
            def effects(self):
                return [fx.Volume(db=0)]

        c = TestComposite()
        with pytest.raises(TypeError):
            c.to_args()


class TestConcat:
    """Tests for cysox.concat()."""

    def test_concat_two_files(self, test_wav_str, output_path):
        """concat() joins two files."""
        cysox.concat([test_wav_str, test_wav_str], output_path)

        # Output should exist and have roughly 2x duration
        input_info = cysox.info(test_wav_str)
        output_info = cysox.info(str(output_path))

        assert output_info["sample_rate"] == input_info["sample_rate"]
        assert output_info["channels"] == input_info["channels"]
        # Allow 10% tolerance for duration
        expected_duration = input_info["duration"] * 2
        assert 0.9 <= output_info["duration"] / expected_duration <= 1.1

    def test_concat_three_files(self, test_wav_str, output_path):
        """concat() joins three files."""
        cysox.concat([test_wav_str, test_wav_str, test_wav_str], output_path)

        input_info = cysox.info(test_wav_str)
        output_info = cysox.info(str(output_path))

        expected_duration = input_info["duration"] * 3
        assert 0.9 <= output_info["duration"] / expected_duration <= 1.1

    def test_concat_single_file_raises(self, test_wav_str, output_path):
        """concat() raises ValueError for single file."""
        with pytest.raises(ValueError, match="at least 2"):
            cysox.concat([test_wav_str], output_path)

    def test_concat_empty_list_raises(self, output_path):
        """concat() raises ValueError for empty list."""
        with pytest.raises(ValueError, match="at least 2"):
            cysox.concat([], output_path)

    def test_concat_nonexistent_file_raises(self, test_wav_str, output_path):
        """concat() raises exception for nonexistent file."""
        with pytest.raises(Exception):
            cysox.concat([test_wav_str, "/nonexistent/file.wav"], output_path)


class TestPlay:
    """Tests for cysox.play()."""

    @pytest.mark.skip(reason="Requires audio hardware - run manually with: pytest -k test_play --run-audio")
    def test_play_basic(self, test_wav_str):
        """play() plays audio to default device."""
        cysox.play(test_wav_str, effects=[fx.Trim(start=0, duration=0.5)])

    @pytest.mark.skip(reason="Requires audio hardware - run manually with: pytest -k test_play --run-audio")
    def test_play_with_effects(self, test_wav_str):
        """play() applies effects during playback."""
        cysox.play(test_wav_str, effects=[
            fx.Trim(start=0, duration=0.5),
            fx.Volume(db=-6),
        ])

    def test_play_nonexistent_file(self):
        """play() raises exception for nonexistent file."""
        with pytest.raises(Exception):
            cysox.play("/nonexistent/file.wav")


class TestAutoInit:
    """Tests for auto-initialization behavior."""

    def test_no_manual_init_required(self, test_wav_str):
        """High-level API works without manual init()."""
        # This test verifies that we can use the API without calling sox.init()
        info = cysox.info(test_wav_str)
        assert info["sample_rate"] > 0

    def test_low_level_api_accessible(self):
        """Low-level API is accessible via cysox.sox."""
        from cysox import sox
        assert hasattr(sox, "Format")
        assert hasattr(sox, "init")
        assert hasattr(sox, "quit")
