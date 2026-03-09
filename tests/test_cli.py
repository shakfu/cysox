"""Tests for the cysox CLI (__main__.py)."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from cysox.__main__ import main


def run_cli(*args):
    """Run main() with the given argv and return exit code."""
    with patch.object(sys, "argv", ["cysox", *args]):
        return main()


class TestVersion:
    """Tests for --version flag."""

    def test_version_flag(self, capsys):
        code = run_cli("--version")
        assert code == 0
        out = capsys.readouterr().out
        assert "cysox" in out
        assert "libsox" in out

    def test_version_short_flag(self, capsys):
        code = run_cli("-V")
        assert code == 0
        out = capsys.readouterr().out
        assert "cysox" in out


class TestNoCommand:
    """Tests for invocation without a command."""

    def test_no_args_prints_help(self, capsys):
        code = run_cli()
        assert code == 0
        out = capsys.readouterr().out
        assert "cysox" in out.lower() or "usage" in out.lower()


class TestInfoCommand:
    """Tests for the 'info' subcommand."""

    def test_info_basic(self, test_wav_str, capsys):
        code = run_cli("info", test_wav_str)
        assert code == 0
        out = capsys.readouterr().out
        assert "44100" in out
        assert "wav" in out.lower()
        assert "2" in out  # channels

    def test_info_nonexistent_file(self):
        with pytest.raises(Exception):
            run_cli("info", "/nonexistent/file.wav")


class TestConvertCommand:
    """Tests for the 'convert' subcommand."""

    def test_convert_basic(self, test_wav_str, output_path, capsys):
        code = run_cli("convert", test_wav_str, str(output_path))
        assert code == 0
        assert output_path.exists()
        assert "Converted" in capsys.readouterr().out

    def test_convert_with_rate(self, test_wav_str, output_path):
        import cysox

        code = run_cli("convert", test_wav_str, str(output_path), "--rate", "22050")
        assert code == 0
        info = cysox.info(str(output_path))
        assert info["sample_rate"] == 22050

    def test_convert_with_channels(self, test_wav_str, output_path):
        import cysox

        code = run_cli("convert", test_wav_str, str(output_path), "--channels", "1")
        assert code == 0
        info = cysox.info(str(output_path))
        assert info["channels"] == 1

    def test_convert_with_preset(self, test_wav_str, output_path, capsys):
        code = run_cli("convert", test_wav_str, str(output_path), "--preset", "Telephone")
        assert code == 0
        assert output_path.exists()

    def test_convert_with_unknown_preset(self, test_wav_str, output_path, capsys):
        code = run_cli("convert", test_wav_str, str(output_path), "--preset", "NonExistent")
        assert code == 1
        assert "Unknown preset" in capsys.readouterr().err

    def test_convert_nonexistent_input(self, output_path):
        with pytest.raises(Exception):
            run_cli("convert", "/nonexistent/input.wav", str(output_path))


class TestConcatCommand:
    """Tests for the 'concat' subcommand."""

    def test_concat_basic(self, test_wav_str, output_path, capsys):
        code = run_cli("concat", test_wav_str, test_wav_str, "-o", str(output_path))
        assert code == 0
        assert output_path.exists()
        assert "Concatenated" in capsys.readouterr().out

    def test_concat_single_file(self, test_wav_str, output_path, capsys):
        code = run_cli("concat", test_wav_str, "-o", str(output_path))
        assert code == 1
        assert "at least 2" in capsys.readouterr().err


class TestPresetCommand:
    """Tests for the 'preset' subcommand."""

    def test_preset_list(self, capsys):
        code = run_cli("preset", "list")
        assert code == 0
        out = capsys.readouterr().out
        assert "VOICE" in out
        assert "Chipmunk" in out

    def test_preset_list_category(self, capsys):
        code = run_cli("preset", "list", "drums")
        assert code == 0
        out = capsys.readouterr().out
        assert "DRUMS" in out
        assert "HalfTime" in out

    def test_preset_list_invalid_category(self, capsys):
        code = run_cli("preset", "list", "nonexistent")
        assert code == 1
        assert "Unknown category" in capsys.readouterr().err

    def test_preset_info(self, capsys):
        code = run_cli("preset", "info", "Telephone")
        assert code == 0
        out = capsys.readouterr().out
        assert "Telephone" in out

    def test_preset_info_unknown(self, capsys):
        code = run_cli("preset", "info", "NonExistent")
        assert code == 1
        assert "Unknown preset" in capsys.readouterr().err

    def test_preset_apply(self, test_wav_str, output_path, capsys):
        code = run_cli("preset", "apply", "Telephone", test_wav_str, str(output_path))
        assert code == 0
        assert output_path.exists()
        assert "Applied" in capsys.readouterr().out

    def test_preset_apply_unknown(self, test_wav_str, output_path, capsys):
        code = run_cli("preset", "apply", "NonExistent", test_wav_str, str(output_path))
        assert code == 1
        assert "Unknown preset" in capsys.readouterr().err

    def test_preset_apply_with_params(self, test_wav_str, output_path, capsys):
        code = run_cli(
            "preset", "apply", "Chipmunk", test_wav_str, str(output_path),
            "--intensity=2.0",
        )
        assert code == 0
        assert output_path.exists()

    def test_preset_apply_ignores_unknown_params(self, test_wav_str, output_path, capsys):
        code = run_cli(
            "preset", "apply", "Telephone", test_wav_str, str(output_path),
            "--bogus=42",
        )
        assert code == 0
        err = capsys.readouterr().err
        assert "ignoring unknown parameter" in err.lower()

    def test_preset_no_subcommand(self, capsys):
        code = run_cli("preset")
        assert code == 0


class TestSliceCommand:
    """Tests for the 'slice' subcommand."""

    def test_slice_basic(self, test_wav_str, test_output_dir, capsys):
        out_dir = str(test_output_dir / "cli" / "slices")
        code = run_cli("slice", test_wav_str, out_dir, "--slices", "2")
        assert code == 0
        out = capsys.readouterr().out
        assert "slices" in out.lower()
        assert Path(out_dir).exists()

    def test_slice_with_threshold(self, test_wav_str, test_output_dir, capsys):
        out_dir = str(test_output_dir / "cli" / "slices_onset")
        code = run_cli("slice", test_wav_str, out_dir, "--threshold", "0.3")
        assert code == 0

    def test_slice_with_preset(self, test_wav_str, test_output_dir, capsys):
        out_dir = str(test_output_dir / "cli" / "slices_preset")
        code = run_cli("slice", test_wav_str, out_dir, "--slices", "2", "--preset", "Telephone")
        assert code == 0

    def test_slice_unknown_preset(self, test_wav_str, test_output_dir, capsys):
        out_dir = str(test_output_dir / "cli" / "slices_bad")
        code = run_cli("slice", test_wav_str, out_dir, "--preset", "NonExistent")
        assert code == 1
        assert "Unknown preset" in capsys.readouterr().err


class TestStutterCommand:
    """Tests for the 'stutter' subcommand."""

    def test_stutter_basic(self, test_wav_str, output_path, capsys):
        code = run_cli(
            "stutter", test_wav_str, str(output_path),
            "--start", "0", "--duration", "0.1", "--repeats", "4",
        )
        assert code == 0
        assert output_path.exists()
        assert "stutter" in capsys.readouterr().out.lower()

    def test_stutter_with_preset(self, test_wav_str, output_path, capsys):
        code = run_cli(
            "stutter", test_wav_str, str(output_path),
            "--start", "0", "--duration", "0.1", "--repeats", "2",
            "--preset", "Telephone",
        )
        assert code == 0

    def test_stutter_unknown_preset(self, test_wav_str, output_path, capsys):
        code = run_cli(
            "stutter", test_wav_str, str(output_path),
            "--preset", "NonExistent",
        )
        assert code == 1
        assert "Unknown preset" in capsys.readouterr().err
