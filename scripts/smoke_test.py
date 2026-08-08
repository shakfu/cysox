#!/usr/bin/env python3
"""Post-repair smoke test for a built wheel.

Run against the *installed* wheel, never the source tree -- cibuildwheel
invokes this from a temp directory so ``import cysox`` resolves to the wheel
under test.

The mp3 checks are the point. On Linux, a wheel built against a distro libsox
gets no mp3 handler at all: the distro delivers mp3 as a dlopen'd plugin, and
auditwheel only vendors what is in the link graph. That failure is silent --
the wheel imports, converts wav fine, and only falls over on an mp3 the user
brings. Asserting it here makes it a build failure instead.

Usage:  smoke_test.py <project-root>
"""

import sys
import tempfile
from pathlib import Path


def main():
    if len(sys.argv) < 2:
        print("usage: smoke_test.py <project-root>", file=sys.stderr)
        return 2
    data = Path(sys.argv[1]) / "tests" / "data"

    import cysox
    from cysox import sox

    sox.init()
    print(f"cysox {cysox.__version__}, libsox {sox.version()}")

    wav = data / "s00.wav"
    mp3 = data / "s00.mp3"
    if not wav.is_file():
        print(f"FAIL: test data missing at {wav}", file=sys.stderr)
        return 1

    # Baseline: the formats every build supports.
    info = cysox.info(str(wav))
    assert info.sample_rate > 0 and info.channels > 0, info
    print(f"wav read ok: {info.sample_rate} Hz, {info.channels} ch")

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "out.wav"
        cysox.convert(str(wav), str(out))
        assert out.is_file() and out.stat().st_size > 0, "wav convert produced nothing"
        print("wav convert ok")

        # mp3 decode -- fails on a wheel whose libsox has no mp3 handler.
        if mp3.is_file():
            minfo = cysox.info(str(mp3))
            assert minfo.sample_rate > 0, minfo
            print(f"mp3 read ok: {minfo.sample_rate} Hz, {minfo.channels} ch")
        else:
            print(f"FAIL: {mp3} missing, cannot verify mp3 decode", file=sys.stderr)
            return 1

        # mp3 encode -- exercises the LAME path and reads the result back.
        enc = Path(tmp) / "out.mp3"
        cysox.convert(str(wav), str(enc))
        assert enc.is_file() and enc.stat().st_size > 0, "mp3 encode produced nothing"
        einfo = cysox.info(str(enc))
        assert einfo.sample_rate > 0, einfo
        print(f"mp3 write ok: {enc.stat().st_size} bytes, reads back at {einfo.sample_rate} Hz")

    sox.quit()
    print("smoke test passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
