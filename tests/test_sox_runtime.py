"""Tests for the SoxRuntime singleton."""

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import pytest

import cysox
from cysox import sox


class TestSoxRuntimeSingleton:
    """Tests for singleton identity and basic properties."""

    def test_singleton_identity(self):
        """SoxRuntime() always returns the same instance."""
        a = sox.SoxRuntime()
        b = sox.SoxRuntime()
        assert a is b

    def test_runtime_is_singleton(self):
        """sox._runtime is the singleton instance."""
        assert sox._runtime is sox.SoxRuntime()

    def test_initialized_property(self):
        """initialized property reflects init state."""
        # High-level API auto-inits, so it should be True by now
        _ = cysox.info("tests/data/s00.wav")
        assert sox._runtime.initialized is True

    def test_init_delegates_to_runtime(self):
        """sox.init() delegates to _runtime.ensure_init()."""
        # Should be a no-op since already initialized
        sox.init()
        assert sox._runtime.initialized is True

    def test_force_quit_and_reinit(self):
        """force_quit() sets initialized=False, ensure_init() re-inits."""
        sox._runtime.force_quit()
        assert sox._runtime.initialized is False

        sox._runtime.ensure_init()
        assert sox._runtime.initialized is True

        # Verify it actually works
        info = cysox.info("tests/data/s00.wav")
        assert info.sample_rate > 0

    def test_force_quit_idempotent(self):
        """Calling force_quit() when not initialized is a no-op."""
        sox._runtime.force_quit()
        sox._runtime.force_quit()  # Should not raise
        assert sox._runtime.initialized is False

        # Re-init for other tests
        sox._runtime.ensure_init()

    def test_ensure_init_idempotent(self):
        """Calling ensure_init() when already initialized is a no-op."""
        sox._runtime.ensure_init()
        sox._runtime.ensure_init()
        assert sox._runtime.initialized is True


class TestSoxRuntimeThreadSafety:
    """Tests for thread-safe initialization and callback management."""

    def test_concurrent_ensure_init(self):
        """Multiple threads calling ensure_init() simultaneously."""
        # Force quit first so we test the actual init path
        sox._runtime.force_quit()

        errors = []
        barrier = threading.Barrier(8)

        def init_thread():
            try:
                barrier.wait(timeout=5)
                sox._runtime.ensure_init()
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=init_thread) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        assert len(errors) == 0, f"Errors: {errors}"
        assert sox._runtime.initialized is True

        # Verify it works
        info = cysox.info("tests/data/s00.wav")
        assert info.sample_rate > 0

    def test_concurrent_callback_registration(self):
        """Concurrent register/unregister of callbacks."""
        errors = []

        def register_worker(thread_id):
            try:
                for i in range(100):
                    chain_id = thread_id * 1000 + i
                    cb = lambda done, data: True
                    sox._runtime.register_callback(chain_id, cb, None)
                    entry = sox._runtime.get_callback(chain_id)
                    assert entry is not None
                    sox._runtime.unregister_callback(chain_id)
                    entry = sox._runtime.get_callback(chain_id)
                    assert entry is None
            except Exception as e:
                errors.append((thread_id, e))

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(register_worker, i) for i in range(4)]
            for f in as_completed(futures):
                f.result()

        assert len(errors) == 0, f"Errors: {errors}"

    def test_callback_isolation(self):
        """Callbacks registered with different chain_ids are independent."""
        cb1 = lambda done, data: True
        cb2 = lambda done, data: False

        sox._runtime.register_callback(111, cb1, "data1")
        sox._runtime.register_callback(222, cb2, "data2")

        entry1 = sox._runtime.get_callback(111)
        entry2 = sox._runtime.get_callback(222)

        assert entry1 == (cb1, "data1")
        assert entry2 == (cb2, "data2")

        sox._runtime.unregister_callback(111)
        assert sox._runtime.get_callback(111) is None
        assert sox._runtime.get_callback(222) is not None

        sox._runtime.unregister_callback(222)

    def test_unregister_nonexistent_is_noop(self):
        """Unregistering a non-existent callback does not raise."""
        sox._runtime.unregister_callback(99999)  # Should not raise


class TestSoxRuntimeExceptionStorage:
    """Tests for callback exception storage."""

    def test_pop_clears_exception(self):
        """pop_last_exception returns and clears the stored exception."""
        try:
            raise ValueError("test")
        except ValueError:
            import sys
            sox._runtime.set_last_exception(sys.exc_info())

        exc = sox._runtime.pop_last_exception()
        assert exc is not None
        assert exc[0] is ValueError

        # Second call should return None
        assert sox._runtime.pop_last_exception() is None

    def test_no_exception_returns_none(self):
        """pop_last_exception returns None when no exception stored."""
        # Clear any leftover state
        sox._runtime.pop_last_exception()
        assert sox._runtime.pop_last_exception() is None

    def test_get_last_callback_exception_delegates(self):
        """Module-level get_last_callback_exception uses _runtime."""
        try:
            raise RuntimeError("test")
        except RuntimeError:
            import sys
            sox._runtime.set_last_exception(sys.exc_info())

        exc = sox.get_last_callback_exception()
        assert exc is not None
        assert exc[0] is RuntimeError
        assert sox.get_last_callback_exception() is None


class TestSoxRuntimeBackwardsCompat:
    """Tests that existing APIs still work through the runtime."""

    def test_sox_init_quit_cycle(self):
        """sox.init() and sox.quit() work as before."""
        sox.init()  # Should be no-op (already initialized)
        sox.quit()  # Should be no-op (never actually quits)
        assert sox._runtime.initialized is True

    def test_force_quit_via_module(self):
        """sox._force_quit() delegates to runtime."""
        sox._force_quit()
        assert sox._runtime.initialized is False
        sox.init()
        assert sox._runtime.initialized is True

    def test_high_level_api_auto_init(self):
        """High-level API triggers runtime.ensure_init()."""
        sox._runtime.force_quit()
        assert sox._runtime.initialized is False

        # High-level API should auto-init via _ensure_init -> _runtime.ensure_init
        info = cysox.info("tests/data/s00.wav")
        assert info.sample_rate > 0
        assert sox._runtime.initialized is True

    def test_progress_callback_works(self, test_wav_str, output_path):
        """Progress callbacks work through the runtime."""
        progress_values = []

        def on_progress(p):
            progress_values.append(p)
            return True

        cysox.convert(test_wav_str, output_path, on_progress=on_progress)
        assert output_path.exists()
        assert len(progress_values) > 0
        assert progress_values[-1] == 1.0

    def test_cancel_callback_works(self, test_wav_str, output_path):
        """Cancellation via progress callback works through the runtime."""
        with pytest.raises(cysox.CancelledError):
            cysox.convert(
                test_wav_str,
                output_path,
                on_progress=lambda p: False,
            )
