#!/usr/bin/env python3
"""Refuse to ship a wheel containing GPL-encumbered or unaudited native libraries.

cysox is MIT. The wheels bundle native libraries, and the licence of the
*distributed artifact* is decided by what ends up inside it -- not by what the
source says. `scripts/setup.sh` already hard-fails the macOS libsox build if
libmad (GPL-2.0-or-later) creeps in; this script extends the same refusal to
everything that is actually vendored into a wheel, on every platform.

Two modes:

    check_licenses.py libs [LIB ...]
        Pre-build check. Walks the DT_NEEDED / LC_LOAD_DYLIB graph of the
        libsox that is about to be linked and fails on a denylisted library.
        With no arguments it locates libsox itself.

    check_licenses.py wheel PATH [PATH ...]
        Post-repair check. PATH may be a wheel or a directory of wheels.
        Fails if a bundled native library is denylisted, or is not in the
        audited allowlist below.

The allowlist is the point: a library nobody has looked at is a licence
question nobody has answered, so an unrecognised `.so` fails the build and
forces a decision instead of silently shipping.
"""

import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path

# Native libraries that may not appear in a distributed wheel. Static-linking
# or bundling any of these makes the combined artifact GPL, which contradicts
# the MIT licence cysox is published under.
DENYLIST = {
    "libmad": "GPL-2.0-or-later -- mp3 decode; use libsndfile/libmpg123 or LAME instead",
    "libid3tag": "GPL-2.0-or-later -- ships alongside libmad in distro mp3 plugins",
    "libavcodec": "GPL-2.0-or-later when ffmpeg is built --enable-gpl; provenance unverifiable here",
    "libavformat": "GPL-2.0-or-later when ffmpeg is built --enable-gpl; provenance unverifiable here",
    "libavutil": "GPL-2.0-or-later when ffmpeg is built --enable-gpl; provenance unverifiable here",
    "libsamplerate": "GPL-2.0 before 0.1.9 (2016); audit the version before allowing",
}

# Native libraries that have been audited and are cleared to ship. Everything
# here is permissive or LGPL; the LGPL entries are why the wheel carries a
# third-party notice (see NOTICE-THIRD-PARTY.md).
ALLOWLIST = {
    # sox itself
    "libsox": "LGPL-2.1-or-later",
    "libsox_ng": "LGPL-2.1-or-later",
    # codecs / containers
    "libsndfile": "LGPL-2.1-or-later",
    "libFLAC": "BSD-3-Clause",
    "libmp3lame": "LGPL-2.0-or-later",
    "libmpg123": "LGPL-2.1-only",
    "libout123": "LGPL-2.1-only",
    "libsyn123": "LGPL-2.1-only",
    "libogg": "BSD-3-Clause",
    "libvorbis": "BSD-3-Clause",
    "libvorbisenc": "BSD-3-Clause",
    "libvorbisfile": "BSD-3-Clause",
    "libopus": "BSD-3-Clause",
    "libopusfile": "BSD-3-Clause",
    "libtwolame": "LGPL-2.1-or-later",
    # support libraries
    "libpng16": "PNG Reference Library License v2",
    "libpng": "PNG Reference Library License v2",
    "libz": "Zlib",
    "libmagic": "BSD-2-Clause",
    # Pulled in transitively by libmagic (compressed-file sniffing), so they
    # appear only after auditwheel repair -- not in libsox's direct link graph.
    "libbz2": "bzip2-1.0.6 (BSD-style)",
    "liblzma": "0BSD / public domain (XZ Utils)",
    "libltdl": "LGPL-2.1-or-later (GNU libtool)",
    "libgomp": "GPL-3.0-or-later WITH GCC-exception-3.1",
    "libsoxr": "LGPL-2.1-or-later",
    "libssp": "GPL-3.0-or-later WITH GCC-exception-3.1",
    # GSM 06.10 (Degener/Bormann, TU Berlin): permissive, retain-the-notice.
    # sox links it for the .gsm handler; Debian ships it as libgsm1.
    "libgsm": "Permissive (TU Berlin GSM 06.10 notice)",
}

# Platform libraries. auditwheel and delocate never vendor these -- they are
# assumed present on the target -- so their licences do not attach to the
# wheel. Listed so they do not trip the unknown-library failure.
SYSTEM_LIBS = {
    "libc",
    "libm",
    "libdl",
    "libpthread",
    "librt",
    "libutil",
    "libgcc_s",
    "libstdc++",
    "ld-linux",
    "ld-linux-x86-64",
    "ld-linux-aarch64",
    "libSystem",
}

# Extension modules built from this project, not third-party payload.
OWN_MODULES = ("sox.", "onset.", "_sox.")

LIB_SUFFIXES = (".so", ".dylib")


def _stem(filename):
    """Reduce a vendored library filename to its bare library name.

    auditwheel and delocate rewrite names to carry a content hash, e.g.
    ``libsox-8f4a2c1d.so.3.0.0`` or ``libFLAC-3ea1c1b2.12.dylib``. Strip the
    hash and every version suffix so the result matches the tables above.
    """
    name = os.path.basename(filename)
    name = re.sub(r"\.(so|dylib)(\.\d+)*$", "", name)  # trailing .so.3.0.0
    name = re.sub(r"(\.\d+)+$", "", name)  # trailing .12 (delocate style)
    name = re.sub(r"-[0-9a-f]{6,}$", "", name)  # auditwheel/delocate hash
    return name


def _is_library(filename):
    base = os.path.basename(filename)
    if base.startswith(OWN_MODULES):
        return False
    return any(s in base for s in LIB_SUFFIXES)


def _classify(stem):
    """Return (verdict, detail) for a library name.

    Verdict is one of deny / allow / system / unknown.
    """
    if stem in DENYLIST:
        return "deny", DENYLIST[stem]
    if stem in ALLOWLIST:
        return "allow", ALLOWLIST[stem]
    if stem in SYSTEM_LIBS:
        return "system", "platform library, not vendored into the wheel"
    return "unknown", "not in the audited allowlist"


# --------------------------------------------------------------------------
# mode: libs -- inspect the libsox that is about to be linked
# --------------------------------------------------------------------------


def _needed(path):
    """Direct dynamic dependencies of a shared library, by filename."""
    if sys.platform == "darwin":
        out = subprocess.run(
            ["otool", "-L", str(path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            universal_newlines=True,
        ).stdout
        return [line.split()[0] for line in out.splitlines()[1:] if line.strip()]
    out = subprocess.run(
        ["readelf", "-d", str(path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        universal_newlines=True,
    ).stdout
    return re.findall(r"\(NEEDED\).*\[(.+?)\]", out)


def _find_libsox():
    candidates = []
    local = Path("lib/libsox.a")
    if local.is_file() and local.stat().st_size > 1024:  # not setup.sh's placeholder
        candidates.append(local)
    out = subprocess.run(
        ["pkg-config", "--variable=libdir", "sox"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        universal_newlines=True,
    ).stdout.strip()
    libdirs = [out] if out else []
    libdirs += ["/usr/lib", "/usr/local/lib", "/usr/lib64", "/lib"]
    for d in libdirs:
        p = Path(d)
        if not p.is_dir():
            continue
        candidates += sorted(p.glob("libsox.so*")) + sorted(p.glob("libsox.dylib"))
        for arch in p.glob("*-linux-gnu"):
            candidates += sorted(arch.glob("libsox.so*"))
    seen, unique = set(), []
    for c in candidates:
        r = c.resolve()
        if r not in seen:
            seen.add(r)
            unique.append(r)
    return unique


def check_libs(argv):
    targets = [Path(a) for a in argv] if argv else _find_libsox()
    if not targets:
        print("check_licenses: no libsox found to inspect", file=sys.stderr)
        return 1

    failures = []
    for target in targets:
        if target.suffix == ".a":
            # A static archive carries its dependencies' symbols, not a link
            # graph. setup.sh's HAVE_MAD grep is the check that applies there;
            # look for mad_ symbols as a backstop.
            out = subprocess.run(
                ["nm", "-g", str(target)],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                universal_newlines=True,
            ).stdout
            if re.search(r"\bT _?mad_\w+", out):
                failures.append(
                    f"{target}: contains libmad symbols ({DENYLIST['libmad']})"
                )
            else:
                print(f"ok    {target}: no libmad symbols")
            continue

        deps = _needed(target)
        print(f"      {target}")
        for dep in deps:
            stem = _stem(dep)
            verdict, detail = _classify(stem)
            if verdict == "deny":
                failures.append(f"{target} links {dep}: {detail}")
                print(f"  DENY  {dep} -- {detail}")
            else:
                print(
                    f"  {'ok  ' if verdict == 'allow' else 'note'}  {dep} -- {detail}"
                )

    # sox loads its format handlers as dlopen'd plugins that are invisible to
    # the link graph above, and therefore invisible to auditwheel/delocate too.
    # Not a licence failure -- a packaging caveat worth stating out loud.
    for d in ("/usr/lib/x86_64-linux-gnu/sox", "/usr/lib64/sox", "/usr/local/lib/sox"):
        if Path(d).is_dir():
            print(
                f"note  {d} holds dlopen'd sox format plugins (mp3 lives here on "
                "Debian/Ubuntu). These are NOT vendored into the wheel, so wheel "
                "mp3 support depends on the target system having them."
            )
            break

    if failures:
        print("\nFAILED -- refusing to build a GPL-encumbered wheel:", file=sys.stderr)
        for f in failures:
            print(f"  {f}", file=sys.stderr)
        return 1
    print("\nlibsox link graph is clean")
    return 0


# --------------------------------------------------------------------------
# mode: wheel -- inspect what was actually bundled
# --------------------------------------------------------------------------


def _wheels(paths):
    found = []
    for raw in paths:
        p = Path(raw)
        if p.is_dir():
            found += sorted(p.glob("*.whl"))
        elif p.suffix == ".whl":
            found.append(p)
    return found


def check_wheel(argv):
    wheels = _wheels(argv)
    if not wheels:
        print(f"check_licenses: no wheels found in {argv}", file=sys.stderr)
        return 1

    failures = []
    for wheel in wheels:
        print(f"\n{wheel.name}")
        with zipfile.ZipFile(wheel) as zf:
            names = zf.namelist()
            libs = sorted({n for n in names if _is_library(n)})
            has_notice = any(
                "NOTICE-THIRD-PARTY" in n
                or n.endswith("licenses/NOTICE-THIRD-PARTY.md")
                for n in names
            )

        if not libs:
            print("  (no bundled native libraries)")
        for lib in libs:
            stem = _stem(lib)
            verdict, detail = _classify(stem)
            if verdict in ("allow", "system"):
                print(f"  ok    {os.path.basename(lib)} -- {detail}")
            elif verdict == "deny":
                print(f"  DENY  {os.path.basename(lib)} -- {detail}")
                failures.append(
                    f"{wheel.name} bundles {os.path.basename(lib)}: {detail}"
                )
            else:
                print(f"  ???   {os.path.basename(lib)} -- {detail}")
                failures.append(
                    f"{wheel.name} bundles {os.path.basename(lib)}, which is {detail}. "
                    "Audit its licence, then add it to ALLOWLIST or DENYLIST in "
                    "scripts/check_licenses.py."
                )

        if libs and not has_notice:
            failures.append(
                f"{wheel.name} bundles native libraries but ships no "
                "NOTICE-THIRD-PARTY.md. LGPL components require the notice."
            )

    if failures:
        print("\nFAILED -- refusing to ship this wheel:", file=sys.stderr)
        for f in failures:
            print(f"  {f}", file=sys.stderr)
        return 1
    print("\nall wheels clean")
    return 0


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("libs", "wheel"):
        print(__doc__, file=sys.stderr)
        return 2
    mode, rest = sys.argv[1], sys.argv[2:]
    return check_libs(rest) if mode == "libs" else check_wheel(rest)


if __name__ == "__main__":
    sys.exit(main())
