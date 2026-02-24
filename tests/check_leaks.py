"""Script to exercise cysox object lifecycles for macOS leaks tool.

Run with: leaks --atExit -- python tests/check_leaks.py
"""

import gc
import os
import tempfile

from cysox import sox

WAV = os.path.join(os.path.dirname(__file__), "data", "s00.wav")

def exercise_signal_info(n=500):
    """Create/destroy SignalInfo objects, including mult allocation."""
    for _ in range(n):
        s = sox.SignalInfo(rate=44100.0, channels=2, precision=16, length=0, mult=1.5)
        del s
    # Also test with mult=0 (no inner alloc)
    for _ in range(n):
        s = sox.SignalInfo(rate=48000.0, channels=1, precision=24, length=0, mult=0.0)
        del s

def exercise_encoding_info(n=500):
    for _ in range(n):
        e = sox.EncodingInfo(encoding=1, bits_per_sample=16)
        del e

def exercise_loop_info(n=500):
    for _ in range(n):
        l = sox.LoopInfo(start=100, length=500, count=3, type=0)
        del l

def exercise_instr_info(n=500):
    for _ in range(n):
        i = sox.InstrInfo(note=60, low=0, high=127)
        del i

def exercise_format_read(n=100):
    """Open, read, close a wav file repeatedly."""
    for _ in range(n):
        with sox.Format(WAV) as f:
            _ = f.read(1024)

def exercise_format_read_buffer(n=100):
    """Open, read_buffer, close a wav file repeatedly."""
    for _ in range(n):
        with sox.Format(WAV) as f:
            _ = f.read_buffer(1024)

def exercise_format_write(n=50):
    """Open for write, write samples, close repeatedly."""
    sig = sox.SignalInfo(rate=44100.0, channels=1, precision=16, length=0)
    samples = [0] * 1024

    with tempfile.TemporaryDirectory() as tmpdir:
        for i in range(n):
            path = os.path.join(tmpdir, f"out_{i}.wav")
            with sox.Format(path, signal=sig, mode='w') as f:
                f.write(samples)

def exercise_effects_chain(n=50):
    """Build and run effects chains repeatedly."""
    for _ in range(n):
        with sox.Format(WAV) as inp:
            in_sig = inp.signal
            in_enc = inp.encoding

            out_sig = sox.SignalInfo(
                rate=in_sig.rate, channels=in_sig.channels,
                precision=in_sig.precision, length=0
            )
            out_enc = sox.EncodingInfo(
                encoding=in_enc.encoding,
                bits_per_sample=in_enc.bits_per_sample,
            )

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as tmp:
                out = sox.Format(
                    tmp.name, signal=out_sig, encoding=out_enc, mode='w'
                )

                chain = sox.EffectsChain(in_enc, out_enc)

                # input effect
                e_in = sox.Effect(sox.find_effect("input"))
                e_in.set_options([inp])
                chain.add_effect(e_in, in_sig, in_sig)

                # vol effect
                e_vol = sox.Effect(sox.find_effect("vol"))
                e_vol.set_options(["3dB"])
                chain.add_effect(e_vol, in_sig, in_sig)

                # output effect
                e_out = sox.Effect(sox.find_effect("output"))
                e_out.set_options([out])
                chain.add_effect(e_out, in_sig, in_sig)

                chain.flow_effects()

                del chain
                out.close()
                del out

def exercise_effect_handler_lookup(n=500):
    """Find effect handlers repeatedly (static pointers, should not leak)."""
    names = ["vol", "rate", "channels", "gain", "reverb", "echo"]
    for _ in range(n):
        for name in names:
            try:
                h = sox.find_effect(name)
                del h
            except Exception:
                pass

def exercise_out_of_band(n=500):
    """Create/destroy OutOfBand objects."""
    for _ in range(n):
        oob = sox.OutOfBand()
        del oob

def main():
    print("Initializing libsox...")
    sox.init()

    print("Exercise: SignalInfo")
    exercise_signal_info()
    gc.collect()

    print("Exercise: EncodingInfo")
    exercise_encoding_info()
    gc.collect()

    print("Exercise: LoopInfo")
    exercise_loop_info()
    gc.collect()

    print("Exercise: InstrInfo")
    exercise_instr_info()
    gc.collect()

    print("Exercise: OutOfBand")
    exercise_out_of_band()
    gc.collect()

    print("Exercise: EffectHandler lookup")
    exercise_effect_handler_lookup()
    gc.collect()

    print("Exercise: Format read")
    exercise_format_read()
    gc.collect()

    print("Exercise: Format read_buffer")
    exercise_format_read_buffer()
    gc.collect()

    print("Exercise: Format write")
    exercise_format_write()
    gc.collect()

    print("Exercise: EffectsChain")
    exercise_effects_chain()
    gc.collect()

    print("Final GC...")
    gc.collect()
    gc.collect()

    print("Done. leaks tool will now inspect the process.")

if __name__ == "__main__":
    main()
