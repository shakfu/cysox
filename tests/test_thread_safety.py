"""Thread safety tests for cysox.

Tests concurrent access patterns to verify thread safety of the wrapper.
"""

import os
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import pytest
import cysox  # Import high-level API to trigger auto-init
from cysox import sox


TEST_WAV = "tests/data/s00.wav"


@pytest.fixture(scope="module")
def sox_initialized():
    """Ensure sox is initialized (handled automatically by high-level API).

    The high-level API (cysox) auto-initializes sox on first use and
    registers atexit cleanup. We don't call init/quit here because
    repeated init/quit cycles crash libsox.
    """
    # Trigger auto-init by calling a high-level function
    _ = cysox.info(TEST_WAV)
    yield


class TestConcurrentReads:
    """Test concurrent file reading operations."""

    def test_parallel_file_reads(self, sox_initialized):
        """Multiple threads reading the same file simultaneously."""
        results = []
        errors = []

        def read_file():
            try:
                with sox.Format(TEST_WAV) as f:
                    samples = f.read(1024)
                    return len(samples)
            except Exception as e:
                errors.append(e)
                return None

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(read_file) for _ in range(10)]
            for future in as_completed(futures):
                result = future.result()
                if result is not None:
                    results.append(result)

        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 10
        assert all(r == results[0] for r in results)  # All reads should return same length

    def test_parallel_different_files(self, sox_initialized):
        """Multiple threads reading different file instances."""
        results = []
        errors = []

        def read_and_get_info(thread_id):
            try:
                with sox.Format(TEST_WAV) as f:
                    rate = f.signal.rate
                    channels = f.signal.channels
                    length = f.signal.length
                    return (thread_id, rate, channels, length)
            except Exception as e:
                errors.append((thread_id, e))
                return None

        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(read_and_get_info, i) for i in range(20)]
            for future in as_completed(futures):
                result = future.result()
                if result is not None:
                    results.append(result)

        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 20
        # All threads should get the same file info
        rates = set(r[1] for r in results)
        channels = set(r[2] for r in results)
        lengths = set(r[3] for r in results)
        assert len(rates) == 1
        assert len(channels) == 1
        assert len(lengths) == 1


class TestConcurrentWrites:
    """Test concurrent file writing operations."""

    def test_parallel_writes_different_files(self, sox_initialized):
        """Multiple threads writing to different files."""
        errors = []

        def write_file(thread_id, output_dir):
            try:
                output_path = os.path.join(output_dir, f"output_{thread_id}.wav")
                with sox.Format(TEST_WAV) as input_fmt:
                    signal = input_fmt.signal
                    samples = input_fmt.read(4096)

                with sox.Format(output_path, signal=signal, mode='w') as output_fmt:
                    output_fmt.write(samples)

                return os.path.exists(output_path)
            except Exception as e:
                errors.append((thread_id, e))
                return False

        with tempfile.TemporaryDirectory() as tmpdir:
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = [executor.submit(write_file, i, tmpdir) for i in range(8)]
                results = [future.result() for future in as_completed(futures)]

        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert all(results)


class TestConcurrentEffectsChains:
    """Test concurrent effects chain processing."""

    def test_parallel_effects_chains(self, sox_initialized):
        """Multiple threads running effects chains simultaneously."""
        errors = []

        def run_effects_chain(thread_id, output_dir):
            try:
                output_path = os.path.join(output_dir, f"effects_{thread_id}.wav")
                input_fmt = sox.Format(TEST_WAV)
                output_fmt = sox.Format(output_path, signal=input_fmt.signal, mode='w')

                chain = sox.EffectsChain(input_fmt.encoding, output_fmt.encoding)

                # Input effect
                e = sox.Effect(sox.find_effect("input"))
                e.set_options([input_fmt])
                chain.add_effect(e, input_fmt.signal, input_fmt.signal)

                # Volume effect
                e = sox.Effect(sox.find_effect("vol"))
                e.set_options(["3dB"])
                chain.add_effect(e, input_fmt.signal, input_fmt.signal)

                # Output effect
                e = sox.Effect(sox.find_effect("output"))
                e.set_options([output_fmt])
                chain.add_effect(e, input_fmt.signal, input_fmt.signal)

                result = chain.flow_effects()

                input_fmt.close()
                output_fmt.close()

                return result == sox.SUCCESS
            except Exception as e:
                errors.append((thread_id, e))
                return False

        with tempfile.TemporaryDirectory() as tmpdir:
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = [executor.submit(run_effects_chain, i, tmpdir) for i in range(8)]
                results = [future.result() for future in as_completed(futures)]

        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert all(results)

    def test_parallel_different_effects(self, sox_initialized):
        """Multiple threads applying different effects."""
        errors = []
        effects_to_test = ["vol", "bass", "treble", "reverb"]

        def run_single_effect(thread_id, effect_name, output_dir):
            try:
                output_path = os.path.join(output_dir, f"{effect_name}_{thread_id}.wav")
                input_fmt = sox.Format(TEST_WAV)
                output_fmt = sox.Format(output_path, signal=input_fmt.signal, mode='w')

                chain = sox.EffectsChain(input_fmt.encoding, output_fmt.encoding)

                # Input
                e = sox.Effect(sox.find_effect("input"))
                e.set_options([input_fmt])
                chain.add_effect(e, input_fmt.signal, input_fmt.signal)

                # The specific effect
                e = sox.Effect(sox.find_effect(effect_name))
                if effect_name == "vol":
                    e.set_options(["3dB"])
                elif effect_name in ("bass", "treble"):
                    e.set_options(["3"])
                else:
                    e.set_options([])
                chain.add_effect(e, input_fmt.signal, input_fmt.signal)

                # Output
                e = sox.Effect(sox.find_effect("output"))
                e.set_options([output_fmt])
                chain.add_effect(e, input_fmt.signal, input_fmt.signal)

                result = chain.flow_effects()

                input_fmt.close()
                output_fmt.close()

                return result == sox.SUCCESS
            except Exception as e:
                errors.append((thread_id, effect_name, e))
                return False

        with tempfile.TemporaryDirectory() as tmpdir:
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = []
                for i, effect in enumerate(effects_to_test * 3):  # 12 total tasks
                    futures.append(executor.submit(run_single_effect, i, effect, tmpdir))
                results = [future.result() for future in as_completed(futures)]

        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert all(results)


class TestConcurrentObjectCreation:
    """Test concurrent object creation and destruction."""

    def test_parallel_signal_info_creation(self, sox_initialized):
        """Multiple threads creating SignalInfo objects."""
        errors = []

        def create_signal_info(thread_id):
            try:
                signals = []
                for i in range(100):
                    s = sox.SignalInfo(
                        rate=44100 + thread_id * 100 + i,
                        channels=2,
                        precision=16
                    )
                    signals.append(s)
                # Verify last one
                return signals[-1].rate == 44100 + thread_id * 100 + 99
            except Exception as e:
                errors.append((thread_id, e))
                return False

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(create_signal_info, i) for i in range(8)]
            results = [future.result() for future in as_completed(futures)]

        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert all(results)

    def test_parallel_encoding_info_creation(self, sox_initialized):
        """Multiple threads creating EncodingInfo objects."""
        errors = []

        def create_encoding_info(thread_id):
            try:
                encodings = []
                for i in range(100):
                    e = sox.EncodingInfo(
                        encoding=1,
                        bits_per_sample=16 + (i % 2) * 8
                    )
                    encodings.append(e)
                return len(encodings) == 100
            except Exception as e:
                errors.append((thread_id, e))
                return False

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(create_encoding_info, i) for i in range(8)]
            results = [future.result() for future in as_completed(futures)]

        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert all(results)

    def test_parallel_effect_handler_lookup(self, sox_initialized):
        """Multiple threads looking up effect handlers."""
        errors = []
        effect_names = ["vol", "trim", "bass", "treble", "reverb", "rate", "channels"]

        def lookup_effects(thread_id):
            try:
                handlers = []
                for name in effect_names * 10:  # 70 lookups per thread
                    h = sox.find_effect(name)
                    if h is None:
                        return False
                    handlers.append(h)
                return len(handlers) == 70
            except Exception as e:
                errors.append((thread_id, e))
                return False

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(lookup_effects, i) for i in range(8)]
            results = [future.result() for future in as_completed(futures)]

        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert all(results)


class TestInitQuitThreading:
    """Test init/quit behavior with threading.

    Note: sox.init() and sox.quit() use global state and should only
    be called once per process lifetime. Repeated init/quit cycles
    can cause crashes due to libsox's global state management.
    """

    @pytest.mark.skip(reason="libsox does not support repeated init/quit cycles safely")
    def test_operations_between_init_quit(self):
        """Test that operations work correctly between init/quit cycles.

        KNOWN LIMITATION: libsox uses global state that does not support
        repeated initialization/shutdown cycles. This test documents this
        limitation rather than testing it.
        """
        for cycle in range(3):
            sox.init()

            # Run parallel operations
            errors = []

            def read_file(thread_id):
                try:
                    with sox.Format(TEST_WAV) as f:
                        return f.signal.rate
                except Exception as e:
                    errors.append((thread_id, e))
                    return None

            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = [executor.submit(read_file, i) for i in range(4)]
                results = [future.result() for future in as_completed(futures)]

            sox.quit()

            assert len(errors) == 0, f"Cycle {cycle} errors: {errors}"
            assert all(r is not None for r in results)


class TestRaceConditions:
    """Test potential race condition scenarios."""

    def test_rapid_open_close(self, sox_initialized):
        """Rapidly open and close files to stress test resource management."""
        errors = []

        def rapid_open_close(thread_id):
            try:
                for _ in range(50):
                    f = sox.Format(TEST_WAV)
                    _ = f.signal.rate
                    f.close()
                return True
            except Exception as e:
                errors.append((thread_id, e))
                return False

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(rapid_open_close, i) for i in range(4)]
            results = [future.result() for future in as_completed(futures)]

        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert all(results)

    def test_interleaved_read_write(self, sox_initialized):
        """Interleaved read and write operations."""
        errors = []

        def interleaved_ops(thread_id, output_dir):
            try:
                for i in range(5):
                    # Read
                    with sox.Format(TEST_WAV) as f:
                        samples = f.read(1024)
                        signal = f.signal

                    # Write
                    output_path = os.path.join(output_dir, f"interleaved_{thread_id}_{i}.wav")
                    with sox.Format(output_path, signal=signal, mode='w') as f:
                        f.write(samples)

                return True
            except Exception as e:
                errors.append((thread_id, e))
                return False

        with tempfile.TemporaryDirectory() as tmpdir:
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = [executor.submit(interleaved_ops, i, tmpdir) for i in range(4)]
                results = [future.result() for future in as_completed(futures)]

        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert all(results)
