"""Demo of progress callbacks and cancellation."""

import sys
import cysox
from cysox import fx

src = "tests/data/s00.wav"


def progress(p):
    w = 40
    filled = int(w * p)
    sys.stdout.write(f"\r[{'#' * filled}{'-' * (w - filled)}] {p:6.1%}")
    sys.stdout.flush()
    return True


print("convert() with reverb + normalize:")
cysox.convert(src, "/tmp/demo.wav", effects=[fx.Reverb(), fx.Normalize()], on_progress=progress)
print()

print("\nconcat() 3 files:")
cysox.concat([src, src, src], "/tmp/demo_concat.wav", on_progress=progress)
print()

print("\nconvert() cancelled at ~30%:")
try:
    cysox.convert(src, "/tmp/demo_cancel.wav", on_progress=lambda p: p < 0.3)
except cysox.CancelledError as e:
    print(f"  {e}")
