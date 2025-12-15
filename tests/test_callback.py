"""Tests for flow_effects callback support"""
import pytest
import tempfile
import os
from cysox import sox


@pytest.fixture(autouse=True)
def initialize_sox():
    """Initialize SoX before each test."""
    sox.init()
    yield
    sox.quit()


def test_flow_effects_no_callback():
    """Test flow_effects without callback (backward compatibility)"""
    input_file = 'tests/data/s00.wav'

    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = os.path.join(tmpdir, 'output.wav')

        # Open input and output files
        in_fmt = sox.Format(input_file)
        signal = sox.SignalInfo(
            rate=in_fmt.signal.rate,
            channels=in_fmt.signal.channels,
            precision=in_fmt.signal.precision
        )
        out_fmt = sox.Format(output_file, signal=signal, mode='w')

        # Create effects chain
        chain = sox.EffectsChain(in_fmt.encoding, out_fmt.encoding)

        # Add input effect
        input_handler = sox.find_effect("input")
        input_effect = sox.Effect(input_handler)
        input_effect.set_options([in_fmt])
        chain.add_effect(input_effect, in_fmt.signal, out_fmt.signal)

        # Add output effect
        output_handler = sox.find_effect("output")
        output_effect = sox.Effect(output_handler)
        output_effect.set_options([out_fmt])
        chain.add_effect(output_effect, in_fmt.signal, out_fmt.signal)

        # Flow without callback (should work as before)
        result = chain.flow_effects()
        assert result == sox.SUCCESS

        in_fmt.close()
        out_fmt.close()


def test_flow_effects_with_callback():
    """Test flow_effects with a simple callback"""
    input_file = 'tests/data/s00.wav'

    callback_calls = []

    def progress_callback(all_done, user_data):
        """Track callback invocations"""
        callback_calls.append({'all_done': all_done, 'user_data': user_data})
        return True  # Continue processing

    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = os.path.join(tmpdir, 'output.wav')

        in_fmt = sox.Format(input_file)
        signal = sox.SignalInfo(
            rate=in_fmt.signal.rate,
            channels=in_fmt.signal.channels,
            precision=in_fmt.signal.precision
        )
        out_fmt = sox.Format(output_file, signal=signal, mode='w')

        chain = sox.EffectsChain(in_fmt.encoding, out_fmt.encoding)

        # Add input effect
        input_handler = sox.find_effect("input")
        input_effect = sox.Effect(input_handler)
        input_effect.set_options([in_fmt])
        chain.add_effect(input_effect, in_fmt.signal, out_fmt.signal)

        # Add output effect
        output_handler = sox.find_effect("output")
        output_effect = sox.Effect(output_handler)
        output_effect.set_options([out_fmt])
        chain.add_effect(output_effect, in_fmt.signal, out_fmt.signal)

        # Flow with callback
        user_data = {'test': 'data'}
        result = chain.flow_effects(callback=progress_callback, client_data=user_data)
        assert result == sox.SUCCESS

        # Verify callback was called
        assert len(callback_calls) > 0, "Callback should have been called at least once"

        # Check that we got an all_done=True call at the end
        assert callback_calls[-1]['all_done'] is True, "Last callback should have all_done=True"
        assert callback_calls[-1]['user_data'] == user_data

        in_fmt.close()
        out_fmt.close()


def test_callback_abort():
    """Test that returning False from callback aborts processing"""
    input_file = 'tests/data/s00.wav'

    def abort_callback(all_done, user_data):
        """Abort after first call"""
        if not all_done:
            return False  # Abort
        return True

    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = os.path.join(tmpdir, 'output.wav')

        in_fmt = sox.Format(input_file)
        signal = sox.SignalInfo(
            rate=in_fmt.signal.rate,
            channels=in_fmt.signal.channels,
            precision=in_fmt.signal.precision
        )
        out_fmt = sox.Format(output_file, signal=signal, mode='w')

        chain = sox.EffectsChain(in_fmt.encoding, out_fmt.encoding)

        input_handler = sox.find_effect("input")
        input_effect = sox.Effect(input_handler)
        input_effect.set_options([in_fmt])
        chain.add_effect(input_effect, in_fmt.signal, out_fmt.signal)

        output_handler = sox.find_effect("output")
        output_effect = sox.Effect(output_handler)
        output_effect.set_options([out_fmt])
        chain.add_effect(output_effect, in_fmt.signal, out_fmt.signal)

        # Flow with abort callback - should raise SoxEffectError
        with pytest.raises(sox.SoxEffectError):
            chain.flow_effects(callback=abort_callback)

        in_fmt.close()
        out_fmt.close()


def test_callback_with_counter():
    """Test callback can track progress with user data"""
    input_file = 'tests/data/s00.wav'

    class ProgressTracker:
        def __init__(self):
            self.buffer_count = 0
            self.done = False

        def callback(self, all_done, user_data):
            if all_done:
                self.done = True
            else:
                self.buffer_count += 1
            return True

    tracker = ProgressTracker()

    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = os.path.join(tmpdir, 'output.wav')

        in_fmt = sox.Format(input_file)
        signal = sox.SignalInfo(
            rate=in_fmt.signal.rate,
            channels=in_fmt.signal.channels,
            precision=in_fmt.signal.precision
        )
        out_fmt = sox.Format(output_file, signal=signal, mode='w')

        chain = sox.EffectsChain(in_fmt.encoding, out_fmt.encoding)

        input_handler = sox.find_effect("input")
        input_effect = sox.Effect(input_handler)
        input_effect.set_options([in_fmt])
        chain.add_effect(input_effect, in_fmt.signal, out_fmt.signal)

        output_handler = sox.find_effect("output")
        output_effect = sox.Effect(output_handler)
        output_effect.set_options([out_fmt])
        chain.add_effect(output_effect, in_fmt.signal, out_fmt.signal)

        result = chain.flow_effects(callback=tracker.callback, client_data=None)
        assert result == sox.SUCCESS

        # Verify we got some callbacks
        assert tracker.buffer_count > 0, "Should have processed at least one buffer"
        assert tracker.done is True, "Should have received done callback"

        in_fmt.close()
        out_fmt.close()


def test_callback_none_return():
    """Test that returning None continues processing"""
    input_file = 'tests/data/s00.wav'

    def none_callback(all_done, user_data):
        """Return None (should continue)"""
        return None

    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = os.path.join(tmpdir, 'output.wav')

        in_fmt = sox.Format(input_file)
        signal = sox.SignalInfo(
            rate=in_fmt.signal.rate,
            channels=in_fmt.signal.channels,
            precision=in_fmt.signal.precision
        )
        out_fmt = sox.Format(output_file, signal=signal, mode='w')

        chain = sox.EffectsChain(in_fmt.encoding, out_fmt.encoding)

        input_handler = sox.find_effect("input")
        input_effect = sox.Effect(input_handler)
        input_effect.set_options([in_fmt])
        chain.add_effect(input_effect, in_fmt.signal, out_fmt.signal)

        output_handler = sox.find_effect("output")
        output_effect = sox.Effect(output_handler)
        output_effect.set_options([out_fmt])
        chain.add_effect(output_effect, in_fmt.signal, out_fmt.signal)

        # Should complete successfully
        result = chain.flow_effects(callback=none_callback)
        assert result == sox.SUCCESS

        in_fmt.close()
        out_fmt.close()
