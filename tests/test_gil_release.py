"""Tests for running libsox I/O and effect flows without the GIL."""

import threading
import time

import pytest

import cysox
from cysox import sox

TEST_WAV = "tests/data/s00.wav"


@pytest.fixture(scope="module", autouse=True)
def sox_initialized():
    cysox.info(TEST_WAV)


def build_chain(output_path, n_reverbs=1):
    """input -> reverb x n -> output. Returns (chain, input_fmt, output_fmt)."""
    input_fmt = sox.Format(TEST_WAV)
    output_fmt = sox.Format(str(output_path), signal=input_fmt.signal, mode="w")
    chain = sox.EffectsChain(input_fmt.encoding, output_fmt.encoding)
    stages = [("input", [input_fmt])]
    stages += [("reverb", ["100"])] * n_reverbs
    stages += [("output", [output_fmt])]
    for name, opts in stages:
        e = sox.Effect(sox.find_effect(name))
        e.set_options(opts)
        chain.add_effect(e, input_fmt.signal, input_fmt.signal)
    return chain, input_fmt, output_fmt


def outcome(fn):
    """Run fn and return the exception it raised, or None.

    Flow callbacks record outcomes rather than assert: the callback wrapper
    swallows BaseException subclasses such as pytest's Failed.
    """
    try:
        fn()
    except Exception as e:
        return e
    return None


def test_flow_effects_releases_gil(output_path):
    """Another Python thread runs for most of a flow's duration."""
    chain, input_fmt, output_fmt = build_chain(output_path, n_reverbs=8)
    in_flow = threading.Event()
    done = threading.Event()
    timing = {}

    def worker():
        in_flow.set()
        t0 = time.perf_counter()
        chain.flow_effects()
        timing["flow"] = time.perf_counter() - t0
        done.set()

    t = threading.Thread(target=worker)
    t.start()
    in_flow.wait()
    t0 = time.perf_counter()
    while not done.is_set():
        pass
    observed = time.perf_counter() - t0
    t.join()
    input_fmt.close()
    output_fmt.close()

    # Holding the GIL, the worker blocks this loop for the whole flow, so it
    # observes at most one switch interval of it.
    assert timing["flow"] > 0.02
    assert observed > 0.5 * timing["flow"]


def test_callback_cannot_read_or_close_format_in_flow(output_path):
    chain, input_fmt, output_fmt = build_chain(output_path)
    seen = {}

    def callback(all_done, _):
        if not seen:
            seen["rate"] = input_fmt.signal.rate  # accessors stay usable
            seen["read"] = outcome(lambda: input_fmt.read(16))
            seen["seek"] = outcome(lambda: input_fmt.seek(0))
            seen["close"] = outcome(input_fmt.close)
        return True

    chain.flow_effects(callback=callback)
    assert seen["rate"] == 44100
    for op in ("read", "seek", "close"):
        assert isinstance(seen[op], sox.SoxIOError), op
        assert "in use" in str(seen[op])

    # Busy state is cleared once the flow returns.
    input_fmt.read(16)
    input_fmt.seek(0)
    input_fmt.close()
    output_fmt.close()


def test_flow_with_closed_format_raises(output_path):
    chain, input_fmt, output_fmt = build_chain(output_path)
    input_fmt.close()
    with pytest.raises(sox.SoxIOError, match="closed"):
        chain.flow_effects()
    # The output format was released when the input check failed.
    output_fmt.close()


def test_nested_flow_in_callback(output_path_factory):
    """A flow started from a flow callback on the same thread does not deadlock."""
    outer, outer_in, outer_out = build_chain(output_path_factory("outer"))
    inner, inner_in, inner_out = build_chain(output_path_factory("inner"))
    results = []

    def callback(all_done, _):
        if not results:
            results.append(inner.flow_effects())
        return True

    outer.flow_effects(callback=callback)
    assert results == [sox.SUCCESS]
    for f in (outer_in, outer_out, inner_in, inner_out):
        f.close()


def test_quit_refused_during_flow(output_path):
    chain, input_fmt, output_fmt = build_chain(output_path)
    errors = []

    def callback(all_done, _):
        if not errors:
            errors.append(outcome(sox._do_sox_quit))
        return True

    chain.flow_effects(callback=callback)
    assert isinstance(errors[0], sox.SoxInitError)
    assert "in progress" in str(errors[0])
    assert sox._libsox_is_up()
    input_fmt.close()
    output_fmt.close()
