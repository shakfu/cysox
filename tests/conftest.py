"""Pytest configuration and fixtures for cysox tests."""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path

import pytest


# Directory paths
TESTS_DIR = Path(__file__).parent
PROJECT_ROOT = TESTS_DIR.parent
DATA_DIR = TESTS_DIR / "data"
BUILD_DIR = PROJECT_ROOT / "build"
TEST_OUTPUT_DIR = BUILD_DIR / "test_output"
BENCHMARK_DIR = TEST_OUTPUT_DIR / "benchmarks"


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


# =============================================================================
# Benchmark Configuration
# =============================================================================

def pytest_configure(config):
    """Configure pytest-benchmark to save results to build/test_output/benchmarks/."""
    BENCHMARK_DIR.mkdir(parents=True, exist_ok=True)

    # Set benchmark storage directory if pytest-benchmark is available
    if hasattr(config, '_inicache'):
        config._inicache['benchmark_storage'] = str(BENCHMARK_DIR)


def pytest_benchmark_update_json(config, benchmarks, output_json):
    """Hook called when benchmark JSON is being generated.

    Adds custom metadata to the benchmark output.
    """
    output_json['custom_info'] = {
        'project': 'cysox',
        'output_dir': str(BENCHMARK_DIR),
    }


def pytest_sessionfinish(session, exitstatus):
    """Save benchmark summary after test session completes."""
    # Check if benchmarks were run
    if not hasattr(session.config, '_benchmarksession'):
        return

    benchmarks = getattr(session.config, '_benchmarksession', None)
    if benchmarks is None:
        return

    # Get benchmark data
    benchmark_data = getattr(benchmarks, 'benchmarks', [])
    if not benchmark_data:
        return

    BENCHMARK_DIR.mkdir(parents=True, exist_ok=True)

    # Generate timestamp for this run
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create summary data
    summary = {
        'timestamp': datetime.now().isoformat(),
        'benchmarks': []
    }

    for bench in benchmark_data:
        stats = bench.stats
        summary['benchmarks'].append({
            'name': bench.name,
            'fullname': bench.fullname,
            'group': bench.group,
            'min': stats.min,
            'max': stats.max,
            'mean': stats.mean,
            'stddev': stats.stddev,
            'median': stats.median,
            'rounds': stats.rounds,
            'ops': stats.ops,
        })

    # Save JSON summary
    summary_file = BENCHMARK_DIR / f"benchmark_{timestamp}.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)

    # Also save a "latest" symlink/copy for easy access
    latest_file = BENCHMARK_DIR / "benchmark_latest.json"
    with open(latest_file, 'w') as f:
        json.dump(summary, f, indent=2)

    # Generate human-readable summary
    txt_file = BENCHMARK_DIR / f"benchmark_{timestamp}.txt"
    with open(txt_file, 'w') as f:
        f.write(f"Benchmark Results - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 70 + "\n\n")

        # Group benchmarks
        groups = {}
        for bench in summary['benchmarks']:
            group = bench.get('group', 'ungrouped')
            if group not in groups:
                groups[group] = []
            groups[group].append(bench)

        for group_name, group_benchmarks in sorted(groups.items()):
            f.write(f"\n{group_name.upper()}\n")
            f.write("-" * 40 + "\n")
            for bench in sorted(group_benchmarks, key=lambda x: x['mean']):
                f.write(f"  {bench['name']:<40} {bench['mean']*1000:>10.3f} ms  "
                       f"(+/- {bench['stddev']*1000:.3f} ms)\n")

    latest_txt = BENCHMARK_DIR / "benchmark_latest.txt"
    shutil.copy(txt_file, latest_txt)
