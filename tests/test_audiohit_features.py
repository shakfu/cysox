"""Tests for AudioHit-ported features: auto_trim, split_by_silence, pitch_scale, batch."""

import shutil
from pathlib import Path

import pytest

import cysox
from cysox import fx


class TestSilenceEffect:
    """Tests for the Silence effect class."""

    def test_silence_default_args(self):
        """Silence effect produces correct default args."""
        s = fx.Silence()
        assert s.name == "silence"
        assert s.to_args() == ["1", "0.1", "-48d"]

    def test_silence_custom_threshold(self):
        """Silence effect respects custom threshold."""
        s = fx.Silence(threshold=-36)
        assert s.to_args() == ["1", "0.1", "-36d"]

    def test_silence_with_below_periods(self):
        """Silence effect includes trailing silence args."""
        s = fx.Silence(below_periods=1)
        args = s.to_args()
        assert len(args) == 6
        assert args[3] == "1"
        assert args[5] == "-48d"

    def test_silence_custom_below_params(self):
        """Silence effect allows independent trailing parameters."""
        s = fx.Silence(
            threshold=-48,
            below_periods=1,
            below_duration=0.2,
            below_threshold=-36,
        )
        args = s.to_args()
        assert args[4] == "0.2"
        assert args[5] == "-36d"

    def test_silence_negative_above_periods_raises(self):
        """Silence raises ValueError for negative above_periods."""
        with pytest.raises(ValueError):
            fx.Silence(above_periods=-1)

    def test_silence_negative_duration_raises(self):
        """Silence raises ValueError for negative duration."""
        with pytest.raises(ValueError):
            fx.Silence(duration=-0.1)

    def test_silence_repr(self):
        """Silence has useful repr."""
        s = fx.Silence(threshold=-36)
        assert "Silence" in repr(s)

    def test_silence_in_convert(self, test_wav_str, output_path):
        """Silence effect works in an effects chain."""
        cysox.convert(
            test_wav_str,
            output_path,
            effects=[fx.Silence(threshold=-60)],
        )
        assert output_path.exists()
        assert output_path.stat().st_size > 0


class TestAutoTrim:
    """Tests for cysox.auto_trim()."""

    def test_auto_trim_basic(self, test_wav_str, output_path):
        """auto_trim produces output file."""
        cysox.auto_trim(test_wav_str, output_path)
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_auto_trim_with_threshold(self, test_wav_str, output_path):
        """auto_trim respects threshold parameter."""
        cysox.auto_trim(test_wav_str, output_path, threshold_db=-36)
        assert output_path.exists()
        info = cysox.info(str(output_path))
        assert info.duration > 0

    def test_auto_trim_with_fades(self, test_wav_str, output_path):
        """auto_trim applies fade in/out."""
        cysox.auto_trim(
            test_wav_str, output_path, fade_in=10, fade_out=50
        )
        assert output_path.exists()
        assert output_path.stat().st_size > 0

    def test_auto_trim_with_speed(self, test_wav_str, output_path):
        """auto_trim applies speed factor."""
        original_info = cysox.info(test_wav_str)
        cysox.auto_trim(test_wav_str, output_path, speed_factor=2.0)
        assert output_path.exists()
        trimmed_info = cysox.info(str(output_path))
        # Speed 2x should roughly halve the duration
        assert trimmed_info.duration < original_info.duration

    def test_auto_trim_with_effects(self, test_wav_str, output_path):
        """auto_trim applies additional effects."""
        cysox.auto_trim(
            test_wav_str, output_path, effects=[fx.Normalize()]
        )
        assert output_path.exists()

    def test_auto_trim_preserves_format(self, test_wav_str, output_path):
        """auto_trim preserves sample rate and channels."""
        cysox.auto_trim(test_wav_str, output_path)
        original = cysox.info(test_wav_str)
        trimmed = cysox.info(str(output_path))
        assert trimmed.sample_rate == original.sample_rate
        assert trimmed.channels == original.channels

    def test_auto_trim_nonexistent_raises(self, output_path):
        """auto_trim raises exception for nonexistent input."""
        with pytest.raises(Exception):
            cysox.auto_trim("/nonexistent/file.wav", output_path)

    def test_auto_trim_path_objects(self, test_wav, output_path):
        """auto_trim accepts Path objects."""
        cysox.auto_trim(test_wav, output_path)
        assert output_path.exists()


class TestSplitBySilence:
    """Tests for cysox.split_by_silence()."""

    def test_split_produces_segments(self, test_wav_str, test_output_dir):
        """split_by_silence produces at least one segment."""
        out_dir = test_output_dir / "split_basic"
        if out_dir.exists():
            shutil.rmtree(out_dir)
        segments = cysox.split_by_silence(
            test_wav_str, out_dir, threshold_db=-20
        )
        assert len(segments) >= 1
        for seg in segments:
            assert Path(seg).exists()
            assert Path(seg).stat().st_size > 0

    def test_split_creates_output_dir(self, test_wav_str, test_output_dir):
        """split_by_silence creates output directory if missing."""
        out_dir = test_output_dir / "split_newdir"
        if out_dir.exists():
            shutil.rmtree(out_dir)
        cysox.split_by_silence(test_wav_str, out_dir)
        assert out_dir.is_dir()

    def test_split_segments_are_valid_audio(self, test_wav_str, test_output_dir):
        """Each segment is a valid audio file."""
        out_dir = test_output_dir / "split_valid"
        if out_dir.exists():
            shutil.rmtree(out_dir)
        segments = cysox.split_by_silence(
            test_wav_str, out_dir, threshold_db=-20
        )
        for seg in segments:
            info = cysox.info(seg)
            assert info.duration > 0
            assert info.sample_rate > 0

    def test_split_with_fades(self, test_wav_str, test_output_dir):
        """split_by_silence applies fades to segments."""
        out_dir = test_output_dir / "split_fades"
        if out_dir.exists():
            shutil.rmtree(out_dir)
        segments = cysox.split_by_silence(
            test_wav_str, out_dir, threshold_db=-20,
            fade_in=5, fade_out=10,
        )
        assert len(segments) >= 1

    def test_split_with_effects(self, test_wav_str, test_output_dir):
        """split_by_silence applies effects to segments."""
        out_dir = test_output_dir / "split_fx"
        if out_dir.exists():
            shutil.rmtree(out_dir)
        segments = cysox.split_by_silence(
            test_wav_str, out_dir, threshold_db=-20,
            effects=[fx.Normalize()],
        )
        assert len(segments) >= 1

    def test_split_min_segment_filters(self, test_wav_str, test_output_dir):
        """split_by_silence respects min_segment parameter."""
        out_dir = test_output_dir / "split_minseg"
        if out_dir.exists():
            shutil.rmtree(out_dir)
        segments = cysox.split_by_silence(
            test_wav_str, out_dir, threshold_db=-20,
            min_segment=5.0,  # Very long minimum
        )
        # With a very long min_segment, either no segments or only long ones
        for seg in segments:
            info = cysox.info(seg)
            assert info.duration >= 4.5  # Allow ~10% tolerance

    def test_split_naming_convention(self, test_wav_str, test_output_dir):
        """Segment filenames follow expected pattern."""
        out_dir = test_output_dir / "split_names"
        if out_dir.exists():
            shutil.rmtree(out_dir)
        segments = cysox.split_by_silence(
            test_wav_str, out_dir, threshold_db=-20
        )
        basename = Path(test_wav_str).stem
        for i, seg in enumerate(segments):
            assert f"{basename}_seg_{i:03d}.wav" in seg

    def test_split_nonexistent_raises(self, test_output_dir):
        """split_by_silence raises exception for nonexistent input."""
        with pytest.raises(Exception):
            cysox.split_by_silence(
                "/nonexistent/file.wav", test_output_dir / "nope"
            )


class TestPitchScale:
    """Tests for cysox.pitch_scale()."""

    def test_pitch_scale_default(self, test_wav_str, test_output_dir):
        """pitch_scale generates 12 files by default."""
        out_dir = test_output_dir / "scale_default"
        if out_dir.exists():
            shutil.rmtree(out_dir)
        files = cysox.pitch_scale(test_wav_str, out_dir)
        assert len(files) == 12
        for f in files:
            assert Path(f).exists()
            assert Path(f).stat().st_size > 0

    def test_pitch_scale_custom_range(self, test_wav_str, test_output_dir):
        """pitch_scale respects semitones parameter."""
        out_dir = test_output_dir / "scale_range"
        if out_dir.exists():
            shutil.rmtree(out_dir)
        files = cysox.pitch_scale(test_wav_str, out_dir, semitones=4)
        assert len(files) == 4

    def test_pitch_scale_with_offset(self, test_wav_str, test_output_dir):
        """pitch_scale respects offset parameter."""
        out_dir = test_output_dir / "scale_offset"
        if out_dir.exists():
            shutil.rmtree(out_dir)
        files = cysox.pitch_scale(
            test_wav_str, out_dir, semitones=3, offset=-1
        )
        assert len(files) == 3
        # Check naming includes offset
        assert "_pitch_-1." in files[0]
        assert "_pitch_+0." in files[1]
        assert "_pitch_+1." in files[2]

    def test_pitch_scale_files_are_valid(self, test_wav_str, test_output_dir):
        """Each pitch-shifted file is valid audio."""
        out_dir = test_output_dir / "scale_valid"
        if out_dir.exists():
            shutil.rmtree(out_dir)
        files = cysox.pitch_scale(test_wav_str, out_dir, semitones=3)
        original = cysox.info(test_wav_str)
        for f in files:
            info = cysox.info(f)
            assert info.sample_rate == original.sample_rate
            assert info.channels == original.channels
            assert info.duration > 0

    def test_pitch_scale_with_effects(self, test_wav_str, test_output_dir):
        """pitch_scale applies additional effects."""
        out_dir = test_output_dir / "scale_fx"
        if out_dir.exists():
            shutil.rmtree(out_dir)
        files = cysox.pitch_scale(
            test_wav_str, out_dir, semitones=2,
            effects=[fx.Normalize()],
        )
        assert len(files) == 2

    def test_pitch_scale_zero_semitones_raises(self, test_wav_str, test_output_dir):
        """pitch_scale raises ValueError for semitones < 1."""
        out_dir = test_output_dir / "scale_zero"
        with pytest.raises(ValueError):
            cysox.pitch_scale(test_wav_str, out_dir, semitones=0)

    def test_pitch_scale_creates_dir(self, test_wav_str, test_output_dir):
        """pitch_scale creates output directory if missing."""
        out_dir = test_output_dir / "scale_newdir"
        if out_dir.exists():
            shutil.rmtree(out_dir)
        cysox.pitch_scale(test_wav_str, out_dir, semitones=1)
        assert out_dir.is_dir()


class TestBatch:
    """Tests for cysox.batch()."""

    @pytest.fixture
    def batch_input_dir(self, test_wav, test_output_dir):
        """Create a temporary directory with test audio files."""
        in_dir = test_output_dir / "batch_input"
        in_dir.mkdir(exist_ok=True)
        # Copy test wav into the input dir
        shutil.copy(test_wav, in_dir / "a.wav")
        shutil.copy(test_wav, in_dir / "b.wav")
        # Create a subdirectory
        sub = in_dir / "sub"
        sub.mkdir(exist_ok=True)
        shutil.copy(test_wav, sub / "c.wav")
        return in_dir

    def test_batch_processes_all_files(self, batch_input_dir, test_output_dir):
        """batch processes all audio files."""
        out_dir = test_output_dir / "batch_output"
        if out_dir.exists():
            shutil.rmtree(out_dir)
        processed = cysox.batch(batch_input_dir, out_dir)
        assert len(processed) == 3
        for f in processed:
            assert Path(f).exists()

    def test_batch_preserves_structure(self, batch_input_dir, test_output_dir):
        """batch preserves relative directory structure."""
        out_dir = test_output_dir / "batch_struct"
        if out_dir.exists():
            shutil.rmtree(out_dir)
        processed = cysox.batch(batch_input_dir, out_dir)
        assert (out_dir / "a.wav").exists()
        assert (out_dir / "b.wav").exists()
        assert (out_dir / "sub" / "c.wav").exists()

    def test_batch_non_recursive(self, batch_input_dir, test_output_dir):
        """batch with recursive=False skips subdirectories."""
        out_dir = test_output_dir / "batch_norec"
        if out_dir.exists():
            shutil.rmtree(out_dir)
        processed = cysox.batch(
            batch_input_dir, out_dir, recursive=False
        )
        assert len(processed) == 2  # Only a.wav and b.wav

    def test_batch_with_effects(self, batch_input_dir, test_output_dir):
        """batch applies effects to all files."""
        out_dir = test_output_dir / "batch_fx"
        if out_dir.exists():
            shutil.rmtree(out_dir)
        processed = cysox.batch(
            batch_input_dir, out_dir,
            effects=[fx.Normalize()],
        )
        assert len(processed) == 3

    def test_batch_with_format_change(self, batch_input_dir, test_output_dir):
        """batch changes output format."""
        out_dir = test_output_dir / "batch_format"
        if out_dir.exists():
            shutil.rmtree(out_dir)
        processed = cysox.batch(
            batch_input_dir, out_dir, output_format="flac"
        )
        for f in processed:
            assert f.endswith(".flac")
            assert Path(f).exists()

    def test_batch_with_sample_rate(self, batch_input_dir, test_output_dir):
        """batch changes sample rate."""
        out_dir = test_output_dir / "batch_rate"
        if out_dir.exists():
            shutil.rmtree(out_dir)
        processed = cysox.batch(
            batch_input_dir, out_dir, sample_rate=22050
        )
        for f in processed:
            info = cysox.info(f)
            assert info.sample_rate == 22050

    def test_batch_on_file_callback(self, batch_input_dir, test_output_dir):
        """batch calls on_file callback for each processed file."""
        out_dir = test_output_dir / "batch_cb"
        if out_dir.exists():
            shutil.rmtree(out_dir)
        callbacks = []
        cysox.batch(
            batch_input_dir, out_dir,
            on_file=lambda i, o: callbacks.append((i, o)),
        )
        assert len(callbacks) == 3

    def test_batch_empty_dir(self, test_output_dir):
        """batch returns empty list for empty directory."""
        empty_dir = test_output_dir / "batch_empty_in"
        empty_dir.mkdir(exist_ok=True)
        out_dir = test_output_dir / "batch_empty_out"
        processed = cysox.batch(empty_dir, out_dir)
        assert processed == []

    def test_batch_nonexistent_dir_raises(self, test_output_dir):
        """batch raises ValueError for nonexistent input directory."""
        with pytest.raises(ValueError, match="does not exist"):
            cysox.batch(
                "/nonexistent/dir", test_output_dir / "nope"
            )
