# TODO

**Legend:**

- `[ ]` Not started
- `[~]` In progress
- `[!]` Blocked

---

## P1 - High Priority

### Correctness

- [x] **`convert()` silently changes the sample encoding: float in -> integer out**
  - **Fixed 2026-08-01** in `src/cysox/audio.py` (`_build_output_encoding`), tests in
    `tests/test_sox_encoding.py`. Reproduced first: float32 in -> `signed-integer`/32 out, while int16
    and int24 round-tripped correctly. Two corrections to the analysis below, found while fixing:
    1. Step 2's stated rationale is wrong. Passing an unsupported encoding to libsox does **not** make
       float -> mp3 "start failing" - libsox silently substitutes the handler default and writes an
       uncapturable stderr warning. The guard is still needed, but to suppress that warning and to
       handle (2), not to prevent a failure.
    2. **The guard is load-bearing for `bits=`, which the analysis missed.** Pairing the inherited
       encoding with an explicit `bits=` can produce a pair the format rejects - WAV cannot write
       float at 16 bits - and libsox then discards the *width* and writes float/32, silently ignoring
       `bits=16`. That is the same class of bug the fix exists to remove. So the probe must test the
       `(encoding, bits)` pair jointly, and an explicit `bits=` outranks an inherited encoding.
    Resolution: inherited encoding is a preference and falls back to the handler default; an explicit
    `encoding=` that the format cannot write raises `ValueError` rather than silently substituting.
    Non-PCM source encodings (flac -> wav) fall back through the same path.
  - **The same bug was live in four sibling functions - also fixed 2026-08-01.** `convert()` was not
    the only writer that opened its output with no `encoding=`. Confirmed by repro before fixing:
    float32 in -> `signed-integer`/32 out from `slice_loop()` and `stutter()`, and the same in
    `split_by_silence()`. `concat()` was the odd one out - it already propagated the encoding, but
    by hand and *without* the supports-check, so float32 -> mp3 forced an unsupported pair on libsox
    and took the silent-substitution path. All five now route through `_build_output_encoding()`.
    - The temp-file hop matters: `slice_loop`/`stutter`/`split_by_silence` write an intermediate WAV
      and re-read it, so encoding has to survive *both* hops or preservation is undone mid-pipeline.
      The temp deliberately keeps the *input's* encoding rather than the caller's, so an explicit
      `encoding=` never degrades resolution before the effects chain runs; `convert()` applies it on
      the final hop.
    - All five gained an `encoding=` parameter for symmetry with `convert()`.
    - Checked while here: `precision` and `encoding.bits_per_sample` are genuinely different
      quantities - a float32 WAV reports `precision=25` (mantissa bits) and `bits_per_sample=32`.
      Pairing them as-is is correct, so the loose end flagged during the `convert()` fix is benign.
  - **Severity: data corruption, silent.** A float WAV converted to a WAV comes back as 32-bit
    *integer* PCM. Nothing errors, the file is valid, the samples are numerically reasonable - but any
    consumer that reads it as declared-in / expects float gets a different format than it put in. This
    was found downstream in [sk-engines](https://github.com/shakfu/sk-engines), where 32-bit int and
    32-bit float WAV are the single most damaging confusion on the target device: the firmware reads
    file bytes straight into float audio frames with no format check on that path, so an int32 file
    plays as full-scale noise. The workaround there is to route around `convert()` for WAV output
    entirely - decode to headerless `.f32` and re-encode with a hand-written WAV writer.

  - **Reproduce** (cysox 0.1.11, Linux, libsox 14.4.2):

    ```python
    import cysox
    # in.wav = 32-bit IEEE float, mono, 44100
    cysox.convert('in.wav', 'out.wav', sample_rate=48000, channels=1)
    print(cysox.info('out.wav').encoding)   # -> 'signed-integer'   (expected: 'float')
    ```

    Converting to `out.f32` instead gives correct raw floats, which is why the bug is specifically in
    how the *output format* is opened, not in the effects chain or the sample pipeline.

  - **Root cause.** `convert()` (`src/cysox/audio.py:261`) builds an output `SignalInfo` carrying
    `rate`/`channels`/`precision` and then opens the output with

    ```python
    output_fmt = sox.Format(output_path, signal=out_signal, mode="w")   # audio.py:326
    ```

    with **no `encoding=`**. `sox.Format.__init__` accepts an `EncodingInfo` and passes it to
    `sox_open_write` (`src/cysox/sox.pyx:1164`), but when it is NULL libsox picks the format handler's
    default for the given precision - for WAV at 32-bit that is `SIGN2`, not `FLOAT`. So the input's
    encoding *type* is dropped on the floor while its precision is preserved, which is exactly the
    combination that produces a plausible-looking wrong file. Note `info()` already reads and reports
    `encoding` (`audio.py:215`), so the information is available; `convert()` just never propagates it.

  - **Suggested fix** (two parts, the first is the actual bug):
    1. **Default to preserving the input encoding.** Build an `EncodingInfo` from
       `input_fmt.encoding` (type + bits) and pass it to the output `Format`.
    2. **Guard it against formats that cannot represent it**, so converting float WAV -> mp3 does not
       start failing. `sox.format_supports_encoding` already exists and answers exactly this - verified:

       ```python
       e = sox.EncodingInfo(encoding=3, bits_per_sample=32)      # FLOAT / 32
       sox.format_supports_encoding('x.wav', e)   # True
       sox.format_supports_encoding('x.mp3', e)   # False  -> fall back to the handler default
       ```

  - **Also worth adding while in here:** an explicit `encoding=` parameter on `convert()` (accepting
    the same names `info()` returns - `'float'`, `'signed-integer'`, ...), so callers can *state* the
    output encoding rather than relying on either the input or a handler default. `bits=` without a
    matching `encoding=` is currently under-specified for any format supporting more than one encoding
    at a given width.

  - **Tests to add:** round-trip each of float32 / int16 / int24 WAV through `convert()` and assert
    `info(out).encoding == info(in).encoding`; assert float -> mp3 still succeeds via the fallback;
    assert an explicit `encoding=` overrides the input. `tests/test_sox_encoding.py` is the natural
    home.

### Licensing

- [ ] **Drop `libmad` (GPL-2.0+) from the macOS bundle - it conflicts with cysox's MIT license**
  - **This is live today, not hypothetical.** `scripts/setup.sh:53` lists `mad` in `DEPS`, and
    `:62-80` goes further: when Homebrew has no static lib it **downloads and builds `libmad.a` from
    source** and copies it into `lib/`. libmad is **GPL-2.0-or-later**. cysox is MIT
    (`LICENSE`, `pyproject.toml:6`). Statically linking a GPL library into a distributed MIT wheel
    makes the combined work GPL - so a published macOS wheel built this way cannot be offered under
    the license the project claims.
  - **Scope: macOS only.** The Linux branch (`setup.sh:11-28`) links system libsox via pkg-config and
    bundles nothing, so it inherits whatever the distro built and is not affected by this.

  - **CORRECTION 2026-08-01: the fix is not "remove `mad` from `DEPS`", and that was already tried.**
    This ticket originally claimed libmad was redundant because `DEPS` also carries `mpg123`, and that
    removing `mad` would leave mp3 working through mpg123. That premise is false, and acting on it
    breaks the build. Evidence:
    - **sox has no mpg123 path, at any version.** `configure.ac` declares
      `SOX_FMT_REQ([mp3], [MAD LAME TWOLAME])` - decode is libmad, encode is LAME/TwoLAME. The word
      "mpg123" appears nowhere in sox's ChangeLog for any release. Debian's `libsox_fmt_mp3.so` links
      `libmad.so.0`, `libmp3lame.so.0`, `libtwolame.so.0` and no mpg123. libsox binds its mp3 decoder
      at **compile** time, so a prebuilt libsox compiled against libmad cannot be redirected to mpg123
      by changing what we copy alongside it.
    - **The two libraries are there for two different consumers.** `DEPS` is the union of the
      dependency closures of the two bundle roots: Homebrew `sox` depends on `mad` (and *not* on
      mpg123); Homebrew `libsndfile` depends on `mpg123`, lame, flac, libogg, libvorbis, opus. libmad
      is sox's mp3 decoder; mpg123 is libsndfile's. They are not two copies of one decision.
    - **This was already attempted and reverted.** `3ffc8ac` "make libmad optional" (2026-03-10 00:46)
      made the CMake link conditional and left the comment
      `# libmad is optional (mpg123 provides the same MP3 decoding)`. `c66195a` "fix libmod"
      (01:00, fourteen minutes later) reverted it exactly *and* added the from-source libmad build to
      `setup.sh` - i.e. replaced "link it if present" with machinery guaranteeing it is always present.
      The duplicated comment block still at `setup.sh:58-61` is the fingerprint of that hurried edit.
      (That `3ffc8ac` failed specifically on undefined `mad_*` symbols is inference from the revert's
      shape and timing; the commit message does not say. Confirming needs a macOS box.)

  - **Framing correction: this is a mislabeling, not a forbidden combination.** MIT is
    GPL-compatible, so *combining* cysox with libmad is permitted. What is not permitted is conveying
    the result as MIT. The wheel is currently GPL-encumbered in substance while its metadata
    (`pyproject.toml:6`) advertises MIT. That means "stop shipping libmad" and "relabel the wheel" are
    both valid cures - see option E.

  - **Solution space, investigated 2026-08-01.** Three live options (C, D, E); two dead ends (A, B):

    | # | approach | keeps mp3 read? | verdict |
    |---|---|---|---|
    | A | route mp3 decode through mpg123 | - | **impossible** - no such path exists in sox |
    | B | let libsndfile's handler cover mp3 (it has mpg123) | - | **does not work** - tested |
    | C | build libsox from source with `--with-mad=dyn` | yes | **viable** - preferred |
    | D | drop mp3 decode from the bundle | no (write still works) | viable, cheapest |
    | E | keep libmad, convey the *wheel* under GPL | yes | viable, no build work, high downstream cost |

    - **B, tested directly:** `sox.Format('x.mp3', filetype='sndfile')` fails on two different mp3
      files while the default handler opens both. sox 14.4.2's sndfile handler advertises only `aiff`
      and `flac`; it does not claim mp3 regardless of what the linked libsndfile can do.
    - **C is the standard answer to exactly this problem.** sox's `SOX_DL_LIB` macro (`m4/sox.m4`)
      defines a `dyn` mode: `--with-mad=dyn` sets `AC_DEFINE([DL_MAD], 1, [Define to dlopen() ...])`,
      so sox **dlopen()s libmad at runtime** instead of linking it. Nothing GPL is then distributed in
      the wheel - the user supplies libmad or does without. This is essentially the Debian model,
      where mp3 lives in a separately-packaged plugin that libsox dlopens (which is why
      `libsox.so.3` itself has no libmad dependency).
      **Cost:** the macOS branch currently copies Homebrew's *prebuilt* `libsox.a`, so C means
      building libsox from source in `setup.sh` - a real change in the packaging story, not a
      one-line edit. It also makes mp3 decode conditional at runtime, which is another argument for
      the `supported_formats()` ticket in P2.
    - **D is the cheap fallback.** Note that decode and encode are separable: **LAME is LGPL-2.1**, so
      mp3 *writing* is unaffected by any of this. Only *reading* depends on GPL libmad. Whether sox
      will build an encode-only mp3 handler with `mad` absent is unverified - `SOX_FMT_REQ` may
      require the decoder - so this needs checking before committing to it.
    - **E costs no build work but taxes every downstream user.** Keep libmad as-is; convey the binary
      wheel under GPL-2.0+ instead of MIT. The *source* can stay MIT - it is only the distributed
      artifact that must carry GPL terms, along with the source-offer obligation for the GPL
      components. Legally coherent and it preserves mp3 read for free, but it makes everyone who
      `pip install`s cysox subject to GPL, which for a library binding is usually the outcome you
      least want. Listed for completeness, not recommended.

  - **Bundling libmad as a `.dylib` instead of a `.a` does NOT help - considered and rejected.**
    Worth recording because the mechanical change is small enough to look attractive:
    - *Technically it is nearly free.* Homebrew's `mad` ships **only** a dylib - which is exactly why
      `setup.sh:58-80` builds the static lib from source. `copy_lib` (`setup.sh:50`) already copies
      `*.dylib`, so `libmad.dylib` is most likely already landing in `lib/`. `Makefile:167` already
      runs `delocate-wheel`, which bundles dylibs into the wheel. And the dynamic branch of
      `CMakeLists.txt` (the `else()` at :143) already links without `-lmad` entirely.
    - *Legally it changes nothing.* Static-vs-dynamic is the distinction **LGPL** draws (its §6
      relinking allowance); GPL-2.0 has no equivalent. GPL obligations attach to **distribution** of
      the GPL work and works based on it. Putting `libmad.dylib` inside the wheel *is* distributing
      libmad - arguably more plainly than static linking does. The variable that matters is whether
      libmad ships in the wheel at all, not how it is linked. That is precisely why C works: with
      `--with-mad=dyn` the wheel contains no libmad at all.
  - **Note on libsox itself:** libsox is LGPL-2.1+ (only the `sox`/`play`/`rec`/`soxi` frontends are
    GPL-2.0+), so MIT bindings over it are fine, but static linking carries LGPL relinking
    obligations. Dynamic linking is the simpler story for wheels. Worth a short LICENSING section in
    the README stating what is linked and under what terms.
  - MP3 patents expired in 2017, so licensing is the only remaining constraint here.
  - **Recommended sequencing:** decide C vs D vs E first, because it determines whether the bundling
    ticket below is "copy Homebrew's prebuilt libs" or "build libsox from source" - a materially
    different project. Do not start by deleting `mad` from `DEPS`; that is the path already reverted
    once.
  - **Caveat on all of the above:** this is the standard reading of the GPL, not legal advice. Option
    E in particular - publishing wheels under GPL while the source stays MIT - is worth confirming
    with someone qualified before acting on it.

### Platform Support

- [ ] **Bundle the common format handlers by default (mp3, flac, ogg/vorbis)**
  - **Motivation: this is the most likely first-run failure.** A user runs `pip install cysox`, points
    it at an mp3, and it fails - because format support is a property of whichever libsox the wheel
    linked, and the handlers ship as separate `libsox-fmt-*` packages on Debian. A wheel that silently
    depends on what the user happens to have already installed gives up most of the benefit of
    shipping a wheel at all. See the P2 ticket "Expose which formats this build actually supports" for
    the per-build variation that motivated both.
  - **Licensing is the constraint, and mp3 *decode* is the one genuinely hard case** - see the
    Licensing item above, whose original "just use mpg123" premise was investigated and disproved on
    2026-08-01. Everything except mp3 decode is BSD or LGPL and bundles cleanly:

    | format | library | license | bundles cleanly? |
    |---|---|---|---|
    | mp3 encode | LAME | LGPL-2.1 | yes |
    | flac | libFLAC | BSD-3-Clause | yes |
    | ogg / vorbis | libogg, libvorbis | BSD-3-Clause | yes |
    | opus | opus, opusfile | BSD-3-Clause | yes |
    | **mp3 decode** | **libmad** | **GPL-2.0+** | **no - sox has no alternative decoder** |

    mpg123 is *not* a substitute here: it is libsndfile's mp3 decoder, and sox cannot use it. Bundling
    mp3 *reading* therefore means either `--with-mad=dyn` (dlopen, nothing GPL in the wheel) or
    shipping without mp3 read.

  - **Sequencing:** do the libmad removal first and independently. It is a small, self-contained
    correctness fix, whereas bundling is a packaging project - and shipping the bundle first would
    propagate the GPL problem into every wheel published from then on.
  - **Cost to weigh:** this compounds the open Windows build-automation item below (more vendored
    deps, more CI matrix, more platform-specific breakage). Scoping to macOS + Linux first is
    reasonable; Windows already needs its own solution. Also decide precedence when a system libsox is
    present - bundled or system - and make it explicit rather than incidental.
  - **What it does not retire:** the `supported_formats()` API ticket. Someone can still build against
    a system libsox, so runtime discovery stays necessary; bundling only makes the common case
    predictable, which is most but not all of the value.

- [ ] **Implement Windows build automation**
  - Current: Placeholder requiring manual environment variables
  - Tasks:
    - [ ] Add vcpkg or conda integration for libsox
    - [ ] Update setup.py with Windows library paths
    - [ ] Add Windows to CI matrix
    - [ ] Document Windows build process

### Documentation

- [ ] **Add troubleshooting guide**
  - Common errors and solutions
  - Platform-specific issues
  - Debug mode usage

---

## P2 - Medium Priority

### Testing

- [ ] **Integrate ASAN into CI** (requires custom Python build)
  - ASAN already available locally via `DEBUG=1 make build`
  - macOS `leaks` and Linux valgrind already in CI

### API / Usability

*Both found alongside the `convert()` encoding bug above, while writing a tool that uses cysox as its
preferred backend and needs to decide at runtime whether it can handle a given file.*

- [ ] **Expose which formats this build actually supports**
  - libsox format support is a **build-time** property, and the common ones are frequently absent:
    Debian ships mp3/flac/ogg as separate `libsox-fmt-*` packages, so `pip install cysox` on a machine
    with a stock `libsox-dev` yields a library that cannot open the formats most users have.
  - **Validated 2026-08-01** against the vendored libsox in this repo. The API gap is real, but the
    original example does not generalise - which formats are missing is per-build:

    | build | mp3 | flac | ogg | opus |
    |---|---|---|---|---|
    | machine the bug was reported from | absent | absent | - | - |
    | this repo's vendored libsox | present | present | present | **absent** |

    So the ticket should not be closed on the grounds that "mp3 works here" - on this build the hole is
    `opus`, and `find_format('opus')` is the only way to discover it.
  - Today the only ways to find out are to call the private-ish `cysox.sox.find_format(ext, False)` or
    to attempt the conversion and catch the failure. A downstream tool that wants to *prefer* cysox and
    fall back to ffmpeg has to reach into `cysox.sox` to do it. Confirmed: `cysox.__all__` exports
    nothing format-related, and neither `supported_formats` nor `supports` exists on the public API.
  - Suggested: a public `cysox.supported_formats()` (or `cysox.supports('mp3')`) on the high-level API,
    plus a line in the README/install docs stating that format support depends on the linked libsox
    build and naming the packages needed for mp3/flac/ogg. This is the single most likely reason a new
    user's first `cysox.convert()` fails.

- [ ] **Route libsox's own diagnostics through Python**
  - libsox writes warnings and errors straight to the process's stderr from C, so a caller sees
    unattributed text it cannot capture, suppress, or attach to the file that caused it. Two seen in
    normal use: `formats: no handler for detected file type 'flac'` (which is *also* raised as a Python
    exception, so it double-reports) and `wav: wave header missing extended part of fmt chunk` (benign,
    emitted for any 44-byte float WAV - which is what a lot of hardware writes).
  - **Validated 2026-08-01.** Confirmed uncapturable: under
    `contextlib.redirect_stderr(io.StringIO())` a `cysox.info()` on a 44-byte float WAV still prints
    `wav: wave header missing extended part of fmt chunk` to the terminal and the buffer captures `''`
    - it is written to fd 2 from C, below Python's `sys.stderr`. (The flac double-report could not be
    checked here; this build has a working flac handler.)
  - **Raised in priority by the `convert()` encoding fix.** That fix has to choose between preserving
    the input encoding and falling back to the format default, and every fallback libsox performs
    itself emits one of these uncapturable lines (`formats: mp3 can't encode Floating Point PCM`,
    `formats: wav can't encode Floating Point PCM to 16-bit`). The fix avoids emitting them by probing
    with `format_supports_encoding` first - verified silent - but any *legitimate* libsox warning on a
    conversion still lands on the caller's stderr unattributed.
  - Suggested: install a `sox_get_globals()->output_message_handler` that forwards to the `logging`
    module, with a way to silence it. Would make cysox embeddable in tools with their own output.

### Build System

- [ ] **Add automatic version bumping**
  - Tool: bump2version or python-semantic-release
  - Sync: pyproject.toml, `__init__.py`, CHANGELOG.md

- [ ] **Add release automation**
  - GitHub Actions workflow for PyPI publishing
  - Automatic changelog generation
  - Git tag creation

### Code Quality

- [ ] **Add pre-commit hooks**
  - ruff linting and formatting
  - isort import sorting

---

## P3 - Low Priority

### Features

- [ ] **Implement playlist parsing**
  - File: `src/cysox/sox.pyx` lines 2136-2148 (commented out)
  - Requires: Callback mechanism for playlist entries

- [!] **Fix memory I/O functions** (BLOCKED)
  - Functions: `open_mem_read()`, `open_mem_write()`, `open_memstream_write()`
  - Status: Blocked by libsox upstream issue
  - Tracking: Documented in Known Limitations

---

## Backlog

- [ ] Async/await support for effects processing
- [ ] NumPy-native array returns (optional dependency)
- [ ] Audio visualization helpers (waveform, spectrogram)

---

## References

- [CHANGELOG.md](CHANGELOG.md) - Version history
- [docs/dev/high_level_api.md](docs/dev/high_level_api.md) - High-level API documentation and extension guide
- [libsox documentation](https://sourceforge.net/p/sox/code/ci/master/tree/src/sox.h)
