"""Performance benchmarks for cysox.

Benchmarks are disabled by default during normal test runs.
To run benchmarks:
  pytest tests/test_benchmarks.py --benchmark-enable  # Run with timing
  pytest tests/test_benchmarks.py --benchmark-only    # Run only benchmarks
  pytest tests/test_benchmarks.py --benchmark-compare # Compare with previous

Results are saved to: build/test_output/benchmarks/
  - benchmark_latest.json  (machine-readable)
  - benchmark_latest.txt   (human-readable summary)

These benchmarks measure:
1. File read throughput (list vs buffer protocol)
2. File write throughput (list vs buffer protocol)
3. Effects chain processing time
4. Memory usage patterns
"""

import array
import os
import tempfile
import pytest
import cysox  # For auto-init
from cysox import sox


# Use hardcoded path for benchmark inner functions (fixtures don't work in closures)
TEST_WAV = "tests/data/s00.wav"


@pytest.fixture
def temp_output_dir():
    """Create temporary directory for output files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


# =============================================================================
# Read Throughput Benchmarks
# =============================================================================

class TestReadThroughput:
    """Benchmark read operations with different methods."""

    @pytest.mark.benchmark(group="read")
    def test_read_list_small(self, benchmark):
        """Read small chunks using list-based read()."""
        def read_small():
            with sox.Format(TEST_WAV) as f:
                total = 0
                while True:
                    samples = f.read(1024)
                    if not samples:
                        break
                    total += len(samples)
                return total

        result = benchmark(read_small)
        assert result > 0

    @pytest.mark.benchmark(group="read")
    def test_read_list_large(self, benchmark):
        """Read large chunks using list-based read()."""
        def read_large():
            with sox.Format(TEST_WAV) as f:
                total = 0
                while True:
                    samples = f.read(65536)
                    if not samples:
                        break
                    total += len(samples)
                return total

        result = benchmark(read_large)
        assert result > 0

    @pytest.mark.benchmark(group="read")
    def test_read_buffer_small(self, benchmark):
        """Read small chunks using buffer protocol read_buffer()."""
        def read_buffer_small():
            with sox.Format(TEST_WAV) as f:
                total = 0
                remaining = f.signal.length
                chunk_size = 1024
                while remaining > 0:
                    to_read = min(chunk_size, remaining)
                    buf = f.read_buffer(to_read)
                    total += len(buf)
                    remaining -= len(buf)
                return total

        result = benchmark(read_buffer_small)
        assert result > 0

    @pytest.mark.benchmark(group="read")
    def test_read_buffer_large(self, benchmark):
        """Read large chunks using buffer protocol read_buffer()."""
        def read_buffer_large():
            with sox.Format(TEST_WAV) as f:
                total = 0
                remaining = f.signal.length
                chunk_size = 65536
                while remaining > 0:
                    to_read = min(chunk_size, remaining)
                    buf = f.read_buffer(to_read)
                    total += len(buf)
                    remaining -= len(buf)
                return total

        result = benchmark(read_buffer_large)
        assert result > 0

    @pytest.mark.benchmark(group="read")
    def test_read_into_preallocated(self, benchmark):
        """Read using pre-allocated buffer with read_into()."""
        def read_into():
            with sox.Format(TEST_WAV) as f:
                buffer = array.array('i', [0] * 65536)
                total = 0
                while True:
                    n = f.read_into(buffer)
                    if n == 0:
                        break
                    total += n
                return total

        result = benchmark(read_into)
        assert result > 0

    @pytest.mark.benchmark(group="read")
    def test_read_entire_file_list(self, benchmark):
        """Read entire file at once using list."""
        def read_entire():
            with sox.Format(TEST_WAV) as f:
                length = f.signal.length
                samples = f.read(length)
                return len(samples)

        result = benchmark(read_entire)
        assert result > 0

    @pytest.mark.benchmark(group="read")
    def test_read_entire_file_buffer(self, benchmark):
        """Read entire file at once using buffer protocol."""
        def read_entire_buffer():
            with sox.Format(TEST_WAV) as f:
                length = f.signal.length
                buf = f.read_buffer(length)
                return len(buf)

        result = benchmark(read_entire_buffer)
        assert result > 0


# =============================================================================
# Write Throughput Benchmarks
# =============================================================================

class TestWriteThroughput:
    """Benchmark write operations with different methods."""

    @pytest.fixture
    def sample_data_list(self):
        """Generate sample data as list."""
        with sox.Format(TEST_WAV) as f:
            return f.read(65536)

    @pytest.fixture
    def sample_data_array(self, sample_data_list):
        """Convert sample data to array.array."""
        return array.array('i', sample_data_list)

    @pytest.mark.benchmark(group="write")
    def test_write_list(self, benchmark, temp_output_dir, sample_data_list):
        """Write samples from Python list."""
        output_path = os.path.join(temp_output_dir, "output_list.wav")

        def write_list():
            signal = sox.SignalInfo(rate=44100, channels=2, precision=16)
            with sox.Format(output_path, signal=signal, mode='w') as f:
                for _ in range(10):  # Write multiple times
                    f.write(sample_data_list)

        benchmark(write_list)

    @pytest.mark.benchmark(group="write")
    def test_write_array(self, benchmark, temp_output_dir, sample_data_array):
        """Write samples from array.array (buffer protocol)."""
        output_path = os.path.join(temp_output_dir, "output_array.wav")

        def write_array():
            signal = sox.SignalInfo(rate=44100, channels=2, precision=16)
            with sox.Format(output_path, signal=signal, mode='w') as f:
                for _ in range(10):  # Write multiple times
                    f.write(sample_data_array)

        benchmark(write_array)

    @pytest.mark.benchmark(group="write")
    def test_write_memoryview(self, benchmark, temp_output_dir, sample_data_array):
        """Write samples from memoryview."""
        output_path = os.path.join(temp_output_dir, "output_mv.wav")
        mv = memoryview(sample_data_array)

        def write_memoryview():
            signal = sox.SignalInfo(rate=44100, channels=2, precision=16)
            with sox.Format(output_path, signal=signal, mode='w') as f:
                for _ in range(10):
                    f.write(mv)

        benchmark(write_memoryview)


# =============================================================================
# Effects Chain Benchmarks
# =============================================================================

class TestEffectsChain:
    """Benchmark effects chain processing."""

    @pytest.mark.benchmark(group="effects")
    def test_passthrough_chain(self, benchmark, temp_output_dir):
        """Minimal effects chain (input -> output only)."""
        output_path = os.path.join(temp_output_dir, "passthrough.wav")

        def passthrough():
            input_fmt = sox.Format(TEST_WAV)
            output_fmt = sox.Format(output_path, signal=input_fmt.signal, mode='w')

            chain = sox.EffectsChain(input_fmt.encoding, output_fmt.encoding)

            # Input
            e = sox.Effect(sox.find_effect("input"))
            e.set_options([input_fmt])
            chain.add_effect(e, input_fmt.signal, input_fmt.signal)

            # Output
            e = sox.Effect(sox.find_effect("output"))
            e.set_options([output_fmt])
            chain.add_effect(e, input_fmt.signal, input_fmt.signal)

            chain.flow_effects()

            input_fmt.close()
            output_fmt.close()

        benchmark(passthrough)

    @pytest.mark.benchmark(group="effects")
    def test_volume_effect(self, benchmark, temp_output_dir):
        """Effects chain with volume adjustment."""
        output_path = os.path.join(temp_output_dir, "volume.wav")

        def volume_chain():
            input_fmt = sox.Format(TEST_WAV)
            output_fmt = sox.Format(output_path, signal=input_fmt.signal, mode='w')

            chain = sox.EffectsChain(input_fmt.encoding, output_fmt.encoding)

            # Input
            e = sox.Effect(sox.find_effect("input"))
            e.set_options([input_fmt])
            chain.add_effect(e, input_fmt.signal, input_fmt.signal)

            # Volume
            e = sox.Effect(sox.find_effect("vol"))
            e.set_options(["3dB"])
            chain.add_effect(e, input_fmt.signal, input_fmt.signal)

            # Output
            e = sox.Effect(sox.find_effect("output"))
            e.set_options([output_fmt])
            chain.add_effect(e, input_fmt.signal, input_fmt.signal)

            chain.flow_effects()

            input_fmt.close()
            output_fmt.close()

        benchmark(volume_chain)

    @pytest.mark.benchmark(group="effects")
    def test_multiple_effects(self, benchmark, temp_output_dir):
        """Effects chain with multiple effects (vol + bass + treble)."""
        output_path = os.path.join(temp_output_dir, "multi_effect.wav")

        def multi_effect_chain():
            input_fmt = sox.Format(TEST_WAV)
            output_fmt = sox.Format(output_path, signal=input_fmt.signal, mode='w')

            chain = sox.EffectsChain(input_fmt.encoding, output_fmt.encoding)

            # Input
            e = sox.Effect(sox.find_effect("input"))
            e.set_options([input_fmt])
            chain.add_effect(e, input_fmt.signal, input_fmt.signal)

            # Volume
            e = sox.Effect(sox.find_effect("vol"))
            e.set_options(["3dB"])
            chain.add_effect(e, input_fmt.signal, input_fmt.signal)

            # Bass boost
            e = sox.Effect(sox.find_effect("bass"))
            e.set_options(["3"])
            chain.add_effect(e, input_fmt.signal, input_fmt.signal)

            # Treble cut
            e = sox.Effect(sox.find_effect("treble"))
            e.set_options(["-2"])
            chain.add_effect(e, input_fmt.signal, input_fmt.signal)

            # Output
            e = sox.Effect(sox.find_effect("output"))
            e.set_options([output_fmt])
            chain.add_effect(e, input_fmt.signal, input_fmt.signal)

            chain.flow_effects()

            input_fmt.close()
            output_fmt.close()

        benchmark(multi_effect_chain)

    @pytest.mark.benchmark(group="effects")
    def test_reverb_effect(self, benchmark, temp_output_dir):
        """Effects chain with computationally intensive reverb."""
        output_path = os.path.join(temp_output_dir, "reverb.wav")

        def reverb_chain():
            input_fmt = sox.Format(TEST_WAV)
            output_fmt = sox.Format(output_path, signal=input_fmt.signal, mode='w')

            chain = sox.EffectsChain(input_fmt.encoding, output_fmt.encoding)

            # Input
            e = sox.Effect(sox.find_effect("input"))
            e.set_options([input_fmt])
            chain.add_effect(e, input_fmt.signal, input_fmt.signal)

            # Reverb (CPU-intensive)
            e = sox.Effect(sox.find_effect("reverb"))
            e.set_options([])
            chain.add_effect(e, input_fmt.signal, input_fmt.signal)

            # Output
            e = sox.Effect(sox.find_effect("output"))
            e.set_options([output_fmt])
            chain.add_effect(e, input_fmt.signal, input_fmt.signal)

            chain.flow_effects()

            input_fmt.close()
            output_fmt.close()

        benchmark(reverb_chain)

    @pytest.mark.skip(reason="libsox rate effect has FFT assertion bug with test file")
    @pytest.mark.benchmark(group="effects")
    def test_rate_conversion(self, benchmark, temp_output_dir):
        """Effects chain with sample rate conversion."""
        output_path = os.path.join(temp_output_dir, "resample.wav")

        def resample_chain():
            input_fmt = sox.Format(TEST_WAV)

            # Create output signal with different rate (22050 for safe 2x downsample)
            out_signal = sox.SignalInfo(
                rate=22050,
                channels=input_fmt.signal.channels,
                precision=input_fmt.signal.precision
            )
            output_fmt = sox.Format(output_path, signal=out_signal, mode='w')

            chain = sox.EffectsChain(input_fmt.encoding, output_fmt.encoding)

            # Input
            e = sox.Effect(sox.find_effect("input"))
            e.set_options([input_fmt])
            chain.add_effect(e, input_fmt.signal, input_fmt.signal)

            # Rate conversion
            e = sox.Effect(sox.find_effect("rate"))
            e.set_options(["22050"])
            chain.add_effect(e, input_fmt.signal, out_signal)

            # Output
            e = sox.Effect(sox.find_effect("output"))
            e.set_options([output_fmt])
            chain.add_effect(e, out_signal, out_signal)

            chain.flow_effects()

            input_fmt.close()
            output_fmt.close()

        benchmark(resample_chain)


# =============================================================================
# Memory Usage Benchmarks
# =============================================================================

class TestMemoryUsage:
    """Benchmark memory usage patterns."""

    @pytest.mark.benchmark(group="memory")
    def test_repeated_open_close(self, benchmark):
        """Measure overhead of repeated file open/close cycles."""
        def open_close_cycle():
            for _ in range(100):
                f = sox.Format(TEST_WAV)
                _ = f.signal.rate
                f.close()

        benchmark(open_close_cycle)

    @pytest.mark.benchmark(group="memory")
    def test_context_manager_overhead(self, benchmark):
        """Measure context manager overhead."""
        def context_manager_cycle():
            for _ in range(100):
                with sox.Format(TEST_WAV) as f:
                    _ = f.signal.rate

        benchmark(context_manager_cycle)

    @pytest.mark.benchmark(group="memory")
    def test_signal_info_creation(self, benchmark):
        """Measure SignalInfo allocation overhead."""
        def create_signals():
            signals = []
            for i in range(1000):
                signals.append(sox.SignalInfo(
                    rate=44100 + i,
                    channels=2,
                    precision=16
                ))
            return len(signals)

        result = benchmark(create_signals)
        assert result == 1000

    @pytest.mark.benchmark(group="memory")
    def test_effect_creation(self, benchmark):
        """Measure Effect object creation overhead."""
        handler = sox.find_effect("vol")

        def create_effects():
            effects = []
            for _ in range(100):
                e = sox.Effect(handler)
                e.set_options(["3dB"])
                effects.append(e)
            return len(effects)

        result = benchmark(create_effects)
        assert result == 100

    @pytest.mark.benchmark(group="memory")
    def test_chain_creation_teardown(self, benchmark, temp_output_dir):
        """Measure effects chain creation and teardown."""
        output_path = os.path.join(temp_output_dir, "chain_test.wav")

        def create_teardown_chain():
            for _ in range(10):
                input_fmt = sox.Format(TEST_WAV)
                output_fmt = sox.Format(output_path, signal=input_fmt.signal, mode='w')

                chain = sox.EffectsChain(input_fmt.encoding, output_fmt.encoding)

                e = sox.Effect(sox.find_effect("input"))
                e.set_options([input_fmt])
                chain.add_effect(e, input_fmt.signal, input_fmt.signal)

                e = sox.Effect(sox.find_effect("output"))
                e.set_options([output_fmt])
                chain.add_effect(e, input_fmt.signal, input_fmt.signal)

                # Don't flow, just test creation/teardown
                input_fmt.close()
                output_fmt.close()

        benchmark(create_teardown_chain)


# =============================================================================
# Comparison Summary
# =============================================================================

class TestComparisonSummary:
    """High-level comparison benchmarks for documentation."""

    @pytest.mark.benchmark(group="comparison")
    def test_read_list_vs_buffer_ratio(self, benchmark):
        """Compare list read vs buffer read for same data size."""
        chunk_size = 32768

        def read_comparison():
            # Read with list
            with sox.Format(TEST_WAV) as f:
                list_samples = f.read(chunk_size)

            # Read with buffer
            with sox.Format(TEST_WAV) as f:
                buffer_samples = f.read_buffer(chunk_size)

            return len(list_samples), len(buffer_samples)

        result = benchmark(read_comparison)
        assert result[0] == result[1]
