# TODO

**Legend:**

- `[ ]` Not started

- `[~]` In progress

- `[!]` Blocked

Completed work is recorded in [CHANGELOG.md](CHANGELOG.md), not here.

---

## P1 - High Priority

### Release Gates

*Both must clear before the next wheel publish. Neither is a code defect - they are claims the build makes that nothing has verified yet.*

- [ ] **PRE-PUBLISH GATE: audit sox_ng's in-tree codec sources**

  - `scripts/check_licenses.py` walks the link graph and classifies every *separate* library that lands in a wheel. It cannot see the codec trees sox_ng compiles into `libsox` itself: `lpc10`, `libdolbyb` and `libebur128`. Those are unclassified.

  - sox_ng's `COPYING` is muddier than upstream's: "SoX is distributed under GPLv2. Most individual source files are distributed under more permissive licenses compatible with the GPLv2." Spot-checking `src/formats.c` showed LGPL-2.1-or-later, same as upstream, but the claim `NOTICE-THIRD-PARTY.md` makes for libsox rests on every linked file, not a sample.

  - Owed for the macOS wheels already shipping.

- [ ] **PRE-PUBLISH GATE: run the sox_ng Linux build in a manylinux container**

  - `scripts/setup.sh`'s `SOX_NG=1` path (mpg123 -> LAME -> libsndfile -> sox_ng, all from source into `/usr/local`) has never executed inside the actual build container. The pinned dependency versions, the AlmaLinux/EPEL package names in `[tool.cibuildwheel.linux] before-all`, and the `--without-libltdl` flag name all need one real `cibuildwheel` run.

  - Two flag bugs were already caught by inspection alone, which is the kind of thing only a real run finds the rest of.

  - Budget for the aarch64 job: it runs under QEMU emulation and this adds four source builds to it. Native arm64 runners are worth considering if it becomes painful.

### Licensing

- [ ] **Satisfy the LGPL §6 relinking obligation for the macOS wheels**

  - The notices now ship: `pyproject.toml`'s `license-files` puts `NOTICE-THIRD-PARTY.md` in `dist-info/licenses/`, and README has a LICENSING section. What is left is the relinking allowance.

  - macOS wheels are a single statically linked `sox.cpython-*-darwin.so` (`CMakeLists.txt:24` defaults `STATIC` ON there), and libsox/libsndfile/libmpg123/LAME/libsoxr are LGPL-2.1. Static linking triggers §6, which dynamic linking satisfies outright - `Makefile:167` already runs `delocate-wheel`, so flipping `STATIC` off is the cheap cure. This is what `soundfile` and PyAV do.

  - The alternative is publishing the object files or an equivalent relinking mechanism per release, which is more standing work than the linking change.

  - Note libmpg123 is LGPL-2.1-**only**, so if cysox itself is ever relicensed it must be exactly LGPL-2.1, not LGPL-3.

  - Rejected options and their evidence are in [docs/dev/licensing-decisions.md](docs/dev/licensing-decisions.md).

### Correctness

- [ ] **Audit every `from_ptr` call site for ownership**

  - `sox_create_effects_chain(in_enc, out_enc)` stores both pointers and dereferences them during `flow_effects()`. `EffectsChain.__init__` now keeps Python references so a temporary `EncodingInfo` cannot be collected out from under the chain - but that was one instance of a general problem.

  - `Effect.in_signal`/`out_signal` are still raw views into `effp->...`, and `add_effect()` passes `in_signal.ptr` straight through. Classify each `from_ptr` site as "borrowed, owner outlives it" or "needs a snapshot", and convert the second kind.

  - Two bugs of this shape have already shipped and been fixed (the `Format.signal` use-after-free and `convert()`'s aliased `signal_view`), so the class is demonstrated, not theoretical.

### Platform Support

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

- [ ] **Deepen the remaining exists-only test assertions**

  - The two `fx` suites now assert behaviour (duration, level, spectral tilt) rather than `assert output_path.exists()`, which is what surfaced the `convert()` signal-negotiation bug. The same treatment has not been applied elsewhere.

  - Remaining, by count of `assert ... exists()`: `tests/test_slice_outputs.py` (15), `tests/test_audiohit_features.py` (14), `tests/test_cli.py` (7), `tests/test_high_level_api.py` (5).

  - The slice and audiohit suites are the most valuable: they cover `slice_loop`/`split_by_silence`, which do their own duration arithmetic and could hide the same class of bug. `tests/audio_metrics.py` provides the measurement helpers.

- [ ] **Integrate ASAN into CI** (requires custom Python build)

  - ASAN already available locally via `DEBUG=1 make build`

  - macOS `leaks` and Linux valgrind already in CI

### API / Usability

- [ ] **Expose which formats this build actually supports**

  - libsox format support is a **build-time** property. The wheels now bundle their own sox_ng with mp3/flac/ogg/opus compiled in, but a source build links whatever the system provides - and Debian ships mp3/flac/ogg as separate `libsox-fmt-*` packages, so `pip install cysox` against a stock `libsox-dev` yields a library that cannot open the formats most users have.

  - **Validated 2026-08-01.** Which formats are missing is per-build:

    | build | mp3 | flac | ogg | opus |
    |---|---|---|---|---|
    | machine the bug was reported from | absent | absent | - | - |
    | this repo's vendored libsox | present | present | present | **absent** |

    So the ticket should not be closed on the grounds that "mp3 works here" - on that build the hole was `opus`, and `find_format('opus')` is the only way to discover it.

  - Today the only ways to find out are to call the private-ish `cysox.sox.find_format(ext, False)` or to attempt the conversion and catch the failure. A downstream tool that wants to *prefer* cysox and fall back to ffmpeg has to reach into `cysox.sox` to do it. `cysox.__all__` exports nothing format-related.

  - Suggested: a public `cysox.supported_formats()` (or `cysox.supports('mp3')`), plus a line in the install docs stating that format support depends on the linked libsox build and naming the packages needed for mp3/flac/ogg.

- [ ] **Route libsox's own diagnostics through Python**

  - libsox writes warnings and errors straight to the process's stderr from C, so a caller sees unattributed text it cannot capture, suppress, or attach to the file that caused it. Two seen in normal use: `formats: no handler for detected file type 'flac'` (which is *also* raised as a Python exception, so it double-reports) and `wav: wave header missing extended part of fmt chunk` (benign, emitted for any 44-byte float WAV - which is what a lot of hardware writes).

  - **Validated 2026-08-01.** Confirmed uncapturable: under `contextlib.redirect_stderr(io.StringIO())` a `cysox.info()` on a 44-byte float WAV still prints to the terminal and the buffer captures `''` - it is written to fd 2 from C, below Python's `sys.stderr`.

  - `_build_output_encoding()` avoids emitting the encoding-fallback warnings by probing with `format_supports_encoding` first, but any legitimate libsox warning on a conversion still lands on the caller's stderr unattributed.

  - Suggested: install a `sox_get_globals()->output_message_handler` that forwards to the `logging` module, with a way to silence it. Would make cysox embeddable in tools with their own output.

### Build System

- [ ] **Add automatic version bumping**

  - Tool: bump2version or python-semantic-release

  - Sync: pyproject.toml, `__init__.py`, CHANGELOG.md

- [ ] **Tag-triggered wheel publishing with PyPI trusted publishing**

  - `.github/workflows/build-wheel.yml` is `workflow_dispatch`-only (the push/tag triggers are commented out) and there is no publish job, so releases go out via a manual `make publish`.

  - Wire it to tags and use PyPI trusted publishing before the release cadence picks up.

### Code Quality

- [ ] **Add pre-commit hooks**

  - ruff linting and formatting

  - isort import sorting

---

## P3 - Low Priority

### Performance

- [ ] **Release the GIL around blocking libsox calls**

  - There is no `with nogil` anywhere in `src/cysox/sox.pyx`: `sox_read`, `sox_write` and `sox_flow_effects` all run holding the GIL.

  - The docs advertise concurrent processing on separate `Format` objects (`docs/dev/known_limitations.md` §3, `docs/dev/architecture.md`), and `tests/test_thread_safety.py` exercises it, but threads cannot actually overlap file I/O or effect flow. The claim is only true in the sense that it does not crash.

  - `flow_effects` needs care: the progress callback re-acquires the GIL via `_flow_effects_callback_wrapper`, which is already correct, so the release has to wrap the call without breaking that path.

- [ ] **Move the `split_by_silence` peak scan into Cython**

  - The per-sample Python loop is gone (now `read_into` + `max`/`min`), but the reduction is still Python-level: measured 1.6x faster, x222 -> x356 realtime on the scan alone for a 57s file.

  - Remaining cost is the `max`/`min` pass, which is the floor without Cython or numpy. Block reads were tried and made no difference - `read_into` is not the bottleneck.

  - Worth doing only if profiling of a real workload says so; the pathological case is already fixed.

### API / Usability

- [ ] **Wrap the high-value effects that only `fx.Raw` reaches**

  - `fx.Raw(name, *args)` now makes all of them usable, so this is ergonomics rather than capability.

  - Best candidates, by how often they are structural: `compand` (the standard dynamics tool - the mastering presets currently approximate it with `gain`/`norm`), `vad` (voice activity detection, directly relevant to `auto_trim`), `noisered` (the cleanup preset category), `stats` (analysis), `synth` (test-tone generation).

  - 27 of 66 effects in a typical build have typed classes. Full list of the unwrapped ones is in `docs/api/effects.md` under "Raw - Untyped Effects".

- [ ] **Decide whether a trailing `Remix`/`Channels` should set the output channel count**

  - Today it does not: `convert()` opens the output file *before* negotiating the chain, so its channel count comes from the input or from `channels=`, and an in-chain effect that changes channel count is converted back to that target. `fx.Remix(mix=["1"])` therefore yields the left channel duplicated across a stereo file, not a mono file.

  - This is consistent with how an in-chain `fx.Rate` behaves, is lossless, and is documented in `convert()`'s docstring and in `tests/test_fx_outputs.py::TestConversionEffects::test_remix_left_only`. `channels=1` is the documented way to get mono.

  - Changing it means opening the output after the chain is negotiated, which is what sox's own driver does but needs restructuring: `sox.EffectsChain` requires the output encoding at construction.

- [ ] **Implement or remove `PythonEffect` and `CEffect`**

  - Both are exported from `cysox.fx` and appear in the architecture diagram, but `PythonEffect.process()` is never called by `convert()`/`play()` (raises `NotImplementedError`) and `CEffect.register()` raises because the low-level API has no `register_effect_handler`.

  - Declared-but-unimplemented classes in a public namespace read as features. Either wire them up or drop them to a design note.

### Code Structure

- [ ] **Extract the shared segment-write path in `audio.py`**

  - `slice_loop`, `stutter` and `split_by_silence` each do: open input -> compute sample ranges -> read segment -> optional temp-file effects hop -> write. That is roughly 100 lines of triplicated logic.

  - A shared `_write_segment(input_fmt, start, end, out_path, effects, encoding)` would give the encoding handling a single place to live - it currently has to be kept correct in three.

- [ ] **Split `audio.py` (1600+ lines) and `sox.pyx` (2500+ lines)**

  - `audio.py` holds twelve top-level functions of 60-210 lines each in one module.

  - `sox.pyx` would read better split along the struct boundaries `sox.pxd` already draws.

  - Cosmetic; do it when touching these files for another reason.

### Features

- [ ] **Implement playlist parsing**

  - File: `src/cysox/sox.pyx` lines 2472-2483 (commented out)

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

- [docs/dev/licensing-decisions.md](docs/dev/licensing-decisions.md) - Why the wheels bundle sox_ng built without libmad

- [docs/dev/high_level_api.md](docs/dev/high_level_api.md) - High-level API documentation and extension guide

- [libsox documentation](https://sourceforge.net/p/sox/code/ci/master/tree/src/sox.h)
