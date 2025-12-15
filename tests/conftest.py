"""Pytest configuration and fixtures for cysox tests."""

import os
import shutil
from pathlib import Path

import pytest


# Directory paths
TESTS_DIR = Path(__file__).parent
PROJECT_ROOT = TESTS_DIR.parent
DATA_DIR = TESTS_DIR / "data"
BUILD_DIR = PROJECT_ROOT / "build"
TEST_OUTPUT_DIR = BUILD_DIR / "test_output"


@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    """Path to the tests/data directory containing test audio files."""
    assert DATA_DIR.exists(), f"Test data directory not found: {DATA_DIR}"
    return DATA_DIR


@pytest.fixture(scope="session")
def test_output_dir() -> Path:
    """Path to build/test_output directory for test artifacts.

    Files written here are preserved after tests complete, allowing
    manual inspection of processed audio files.
    """
    TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return TEST_OUTPUT_DIR


@pytest.fixture(scope="session")
def test_wav(test_data_dir) -> Path:
    """Path to the primary test WAV file (s00.wav)."""
    wav_path = test_data_dir / "s00.wav"
    assert wav_path.exists(), f"Test WAV file not found: {wav_path}"
    return wav_path


@pytest.fixture(scope="session")
def test_wav_str(test_wav) -> str:
    """String path to the primary test WAV file."""
    return str(test_wav)


@pytest.fixture
def output_path(test_output_dir, request) -> Path:
    """Generate a unique output path for the current test.

    Creates a file path like: build/test_output/<test_module>/<test_name>.wav
    The parent directory is created automatically.

    Usage:
        def test_my_effect(output_path):
            cysox.convert(input_path, output_path)
            # File is preserved at build/test_output/test_module/test_my_effect.wav
    """
    # Get test module and function names
    module_name = request.module.__name__.replace("tests.", "").replace("test_", "")
    test_name = request.node.name

    # Create subdirectory for this test module
    module_dir = test_output_dir / module_name
    module_dir.mkdir(exist_ok=True)

    # Return path with .wav extension
    return module_dir / f"{test_name}.wav"


@pytest.fixture
def output_path_factory(test_output_dir, request):
    """Factory fixture to generate multiple output paths for a single test.

    Usage:
        def test_multiple_effects(output_path_factory):
            path1 = output_path_factory("reverb")
            path2 = output_path_factory("chorus")
            cysox.convert(input_path, path1, effects=[fx.Reverb()])
            cysox.convert(input_path, path2, effects=[fx.Chorus()])
    """
    module_name = request.module.__name__.replace("tests.", "").replace("test_", "")
    test_name = request.node.name

    module_dir = test_output_dir / module_name
    module_dir.mkdir(exist_ok=True)

    def _make_path(suffix: str, extension: str = ".wav") -> Path:
        return module_dir / f"{test_name}_{suffix}{extension}"

    return _make_path


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Session-scoped setup that runs once before all tests."""
    # Ensure output directory exists
    TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Could add cleanup of old test outputs here if desired:
    # shutil.rmtree(TEST_OUTPUT_DIR, ignore_errors=True)
    # TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    yield

    # Post-test session cleanup (if needed)
    # Currently we preserve all outputs for inspection


@pytest.fixture(scope="session")
def all_test_wavs(test_data_dir) -> list:
    """List of all WAV files in the test data directory."""
    return list(test_data_dir.glob("*.wav"))
