"""Memory-safety regression tests for the low-level wrappers.

Each test here corresponds to a way Python code could previously corrupt or
free memory it did not own. Before the guards existed these did not raise -
they returned garbage, aborted in glibc, or segfaulted the interpreter, so a
plain `pytest.raises` here is the whole point.
"""

import gc
import pathlib
import subprocess
import sys

import pytest

from cysox import sox


@pytest.fixture(scope="module", autouse=True)
def initialized():
    sox.init()
    yield


TEST_WAV = "tests/data/s00.wav"


class TestFormatUseAfterClose:
    """Accessors on a closed Format must raise, not dereference NULL.

    ``close()`` sets the pointer to NULL. Every accessor below used to
    dereference it unchecked; ``f.close(); f.filename`` exited with SIGSEGV.
    """

    ACCESSORS = [
        "filename",
        "signal",
        "encoding",
        "filetype",
        "seekable",
        "mode",
        "olength",
        "clips",
        "sox_errno",
        "sox_errstr",
        "io_type",
        "tell_off",
        "data_start",
    ]

    @pytest.mark.parametrize("attribute", ACCESSORS)
    def test_property_raises_after_close(self, attribute):
        fmt = sox.Format(TEST_WAV)
        fmt.close()
        with pytest.raises(sox.SoxIOError, match="closed Format"):
            getattr(fmt, attribute)

    def test_read_raises_after_close(self):
        fmt = sox.Format(TEST_WAV)
        fmt.close()
        with pytest.raises(sox.SoxIOError, match="closed Format"):
            fmt.read(16)

    def test_read_buffer_raises_after_close(self):
        fmt = sox.Format(TEST_WAV)
        fmt.close()
        with pytest.raises(sox.SoxIOError, match="closed Format"):
            fmt.read_buffer(16)

    def test_read_into_raises_after_close(self):
        fmt = sox.Format(TEST_WAV)
        fmt.close()
        with pytest.raises(sox.SoxIOError, match="closed Format"):
            fmt.read_into(bytearray(64))

    def test_seek_raises_after_close(self):
        fmt = sox.Format(TEST_WAV)
        fmt.close()
        with pytest.raises(sox.SoxIOError, match="closed Format"):
            fmt.seek(0)

    def test_close_is_idempotent(self):
        fmt = sox.Format(TEST_WAV)
        assert fmt.close() == sox.SUCCESS
        assert fmt.close() == sox.SUCCESS

    def test_context_manager_exit_then_access(self):
        with sox.Format(TEST_WAV) as fmt:
            assert fmt.signal.rate > 0
        with pytest.raises(sox.SoxIOError, match="closed Format"):
            fmt.signal


class TestEffectUseAfterDelete:
    """delete() must leave the Effect inert, not holding a freed pointer.

    ``sox_delete_effect()`` frees the struct. The pointer used to be left set
    with ownership intact, so ``__dealloc__`` freed it again and glibc aborted
    with "free(): double free detected in tcache 2".
    """

    def test_delete_then_dealloc_does_not_double_free(self):
        effect = sox.Effect(sox.find_effect("vol"))
        effect.delete()
        del effect
        gc.collect()

    def test_delete_is_idempotent(self):
        effect = sox.Effect(sox.find_effect("vol"))
        effect.delete()
        effect.delete()

    @pytest.mark.parametrize(
        "attribute", ["in_signal", "out_signal", "handler", "clips", "flows", "flow"]
    )
    def test_property_raises_after_delete(self, attribute):
        effect = sox.Effect(sox.find_effect("vol"))
        effect.delete()
        with pytest.raises(sox.SoxEffectError, match="deleted Effect"):
            getattr(effect, attribute)

    def test_set_options_raises_after_delete(self):
        effect = sox.Effect(sox.find_effect("vol"))
        effect.delete()
        with pytest.raises(sox.SoxEffectError, match="deleted Effect"):
            effect.set_options(["-6", "dB"])


class TestBorrowedWrapperKeepalive:
    """Non-owning wrappers must keep their owner alive.

    ``Format.signal`` points into the Format's own ``sox_format_t``. Without a
    strong reference back to the Format, this one-liner read freed memory and
    reported a sample rate of about -1.3e-147.
    """

    def test_signal_outlives_temporary_format(self):
        signal = sox.Format(TEST_WAV).signal
        gc.collect()
        assert signal.rate == 44100.0
        assert signal.channels == 2

    def test_encoding_outlives_temporary_format(self):
        encoding = sox.Format(TEST_WAV).encoding
        gc.collect()
        assert encoding.bits_per_sample > 0

    def test_effect_signals_outlive_temporary_effect(self):
        in_signal = sox.Effect(sox.find_effect("vol")).in_signal
        gc.collect()
        assert in_signal.channels >= 0

    def test_effect_handler_outlives_temporary_effect(self):
        handler = sox.Effect(sox.find_effect("vol")).handler
        gc.collect()
        assert handler.name == "vol"

    def test_chain_effects_outlive_temporary_chain(self):
        chain = sox.EffectsChain()
        effect = sox.Effect(sox.find_effect("vol"))
        effect.set_options(["-6", "dB"])
        signal = sox.SignalInfo(rate=44100, channels=2, precision=16)
        chain.add_effect(effect, signal, signal)
        borrowed = chain.effects
        del chain
        gc.collect()
        assert borrowed[0].handler.name == "vol"

    def test_signal_survives_explicit_close(self):
        """Format.signal is a snapshot, so closing the file cannot stale it.

        This previously read freed memory and returned nan. It was resolved by
        making the property copy rather than alias - which also fixed the trim
        corruption, since libsox writes back through the struct it is handed.
        """
        fmt = sox.Format(TEST_WAV)
        signal = fmt.signal
        fmt.close()
        assert signal.rate == 44100.0
        assert signal.channels == 2

    def test_chain_retains_its_encodings(self):
        """EffectsChain must keep the EncodingInfo objects it was built from.

        sox_create_effects_chain() stores the pointers, so temporaries used to
        be collected out from under it and read back as 0.
        """
        chain = sox.EffectsChain(
            sox.EncodingInfo(encoding=1, bits_per_sample=16),
            sox.EncodingInfo(encoding=1, bits_per_sample=16),
        )
        gc.collect()
        assert chain.in_enc.bits_per_sample == 16
        assert chain.out_enc.bits_per_sample == 16

    @pytest.mark.xfail(
        strict=True,
        reason="Format.encoding is still a live view into the open format, so "
        "reading it after close() reads freed memory - it happens to return "
        "the right value rather than raising. Snapshotting it the way signal "
        "was is now safe (EffectsChain retains its encodings), but it is a "
        "separate public-API change and has not been made.",
    )
    def test_encoding_is_safe_after_close(self):
        fmt = sox.Format(TEST_WAV)
        encoding = fmt.encoding
        fmt.close()
        with pytest.raises((sox.SoxIOError, RuntimeError)):
            encoding.bits_per_sample


# Shutdown behaviour is exercised in subprocesses. Each case has to call
# force_quit(), and libsox does not survive repeated init/quit cycles in one
# process - doing it inline crashed the suite in sox_find_format(), which is
# the limitation docs/dev/known_limitations.md documents. Isolating per
# process is what that document recommends, and it keeps these tests from
# destabilising every test that runs after them.


def _run_isolated(body: str):
    """Run a snippet in a fresh interpreter; return the CompletedProcess."""
    script = "import gc, sys\nfrom cysox import sox\nsox.init()\n" + body
    return subprocess.run(
        [sys.executable, "-c", script],
        cwd=str(pathlib.Path(__file__).parent.parent),
        capture_output=True,
        text=True,
        timeout=120,
    )


def _assert_clean(body: str):
    """The snippet must exit 0 - not by a signal, and not with a traceback."""
    result = _run_isolated(body)
    assert result.returncode == 0, (
        f"exited {result.returncode} "
        f"({'signal ' + str(-result.returncode) if result.returncode < 0 else 'error'})\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr[-2000:]}"
    )
    assert "OK" in result.stdout, f"body did not complete: {result.stdout!r}"


class TestShutdownSafety:
    """Objects that outlive libsox must not be closed through dead handlers.

    A sox_format_t carries a by-value copy of its format handler. sox_quit()
    frees the tables those function pointers refer to, so closing such a
    format afterwards jumps through a dangling pointer. This crashed the whole
    test suite: a failing test left an open Format alive in its traceback, a
    later test called force_quit(), and the eventual gc pass that cleared the
    traceback segfaulted the interpreter - taking pytest's summary and exit
    code with it, so `make test` reported 139 no matter what the results were.

    Re-initialising is not enough to make the old format safe again: sox_init()
    builds a *fresh* handler table, so the stale format's pointers still refer
    to freed memory. That is why the guard compares init generations rather
    than checking a boolean.
    """

    def test_open_format_collected_after_quit(self):
        _assert_clean(
            "f = sox.Format('tests/data/s00.wav')\n"
            "sox._runtime.force_quit()\n"
            "del f\n"
            "gc.collect()\n"
            "print('OK')\n"
        )

    def test_mp3_format_collected_after_quit(self):
        """mp3 dispatches through a handler that sox_quit() tears down."""
        _assert_clean(
            "f = sox.Format('tests/data/s00.mp3')\n"
            "sox._runtime.force_quit()\n"
            "del f\n"
            "gc.collect()\n"
            "print('OK')\n"
        )

    def test_open_format_collected_after_quit_and_reinit(self):
        """The generation check, not just an up/down flag, is what saves this."""
        _assert_clean(
            "f = sox.Format('tests/data/s00.wav')\n"
            "sox._runtime.force_quit()\n"
            "sox._runtime.ensure_init()\n"
            "del f\n"
            "gc.collect()\n"
            "print('OK')\n"
        )

    def test_format_held_in_traceback_across_quit(self):
        """The exact shape that crashed the suite."""
        _assert_clean(
            "saved = []\n"
            "def failing():\n"
            "    f = sox.Format('tests/data/s00.mp3')\n"
            "    raise AssertionError('holds f alive in the traceback')\n"
            "try:\n"
            "    failing()\n"
            "except AssertionError:\n"
            "    saved.append(sys.exc_info())\n"
            "sox._runtime.force_quit()\n"
            "del saved[:]\n"
            "gc.collect()\n"
            "print('OK')\n"
        )

    def test_explicit_close_after_quit_is_safe(self):
        _assert_clean(
            "f = sox.Format('tests/data/s00.wav')\n"
            "sox._runtime.force_quit()\n"
            "assert f.close() == sox.SUCCESS\n"
            "print('OK')\n"
        )

    def test_chain_collected_after_quit(self):
        _assert_clean(
            "f = sox.Format('tests/data/s00.wav')\n"
            "chain = sox.EffectsChain(f.encoding, f.encoding)\n"
            "sox._runtime.force_quit()\n"
            "del f, chain\n"
            "gc.collect()\n"
            "print('OK')\n"
        )

    def test_generation_advances_on_reinit(self):
        _assert_clean(
            "before = sox._libsox_generation_id()\n"
            "sox._runtime.force_quit()\n"
            "sox._runtime.ensure_init()\n"
            "assert sox._libsox_generation_id() > before\n"
            "assert sox._libsox_is_up()\n"
            "print('OK')\n"
        )
