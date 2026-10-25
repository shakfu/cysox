# TODO

**Legend:**

- `[ ]` Not started

- `[~]` In progress

- `[!]` Blocked

## Critical

## High

### Release Gates

- [ ] **PRE-PUBLISH GATE: find a licence for sox's in-tree lpc10**

  - `licenses/README.md` records no licence statement in lpc10's sources. It is statically linked into every wheel.

### Licensing

- [~] **Drop `libmad` (GPL-2.0+) from the macOS bundle - it conflicts with cysox's MIT license**

  - **Implemented 2026-10-24 by replacing libmad with libmpg123; verified on Linux, not yet on macOS.** This is option A in `docs/dev/licensing-decisions.md`, which that record calls impossible: sox 14.4.2 is patched to decode with libmpg123 (LGPL), so nothing GPL ships and mp3 reading needs no system library. Option C was built first and worked, but needed a system libmad and two loader patches. Two more corrections to that record: in 14.4.2 the flag is `--enable-dl-mad`, not `--with-mad=dyn`; and "sox has no mpg123 path, at any version" is false, since SoX_ng carried one from 2019 to 2024. See `docs/dev/mp3_decoding.md`.

  - **Open:** run the macOS wheel build.

- [ ] **Satisfy the LGPL §6 relinking obligation for the wheels**

  - The notices ship in `dist-info/licenses/` (`licenses/README.md`), which also points to the source and scripts needed to relink libsox. Decide whether that satisfies §6.

  - Every wheel statically links libsox (LGPL-2.1+) into `cysox/sox.*.so`: `CMakeLists.txt` sets `STATIC` whenever `lib/pkgconfig/sox.pc` exists, and `scripts/build-libsox.sh` builds only a static library. libmpg123 and LAME ship as shared libraries. Static linking triggers §6, which dynamic linking satisfies outright - `Makefile:175` already runs `delocate-wheel`, so building libsox shared is the cheap cure. This is what `soundfile` and PyAV do.

  - The alternative is publishing the object files or an equivalent relinking mechanism per release, which is more standing work than the linking change.

  - Note libmpg123 is LGPL-2.1-**only**, so if cysox itself is ever relicensed it must be exactly LGPL-2.1, not LGPL-3.

  - Rejected options and their evidence are in [docs/dev/licensing-decisions.md](docs/dev/licensing-decisions.md).

### Correctness

- [ ] **Audit every `from_ptr` call site for ownership**

  - `sox_create_effects_chain(in_enc, out_enc)` stores both pointers and dereferences them during `flow_effects()`. `EffectsChain.__init__` now keeps Python references so a temporary `EncodingInfo` cannot be collected out from under the chain - but that was one instance of a general problem.

  - `Effect.in_signal`/`out_signal` are still raw views into `effp->...`, and `add_effect()` passes `in_signal.ptr` straight through. Classify each `from_ptr` site as "borrowed, owner outlives it" or "needs a snapshot", and convert the second kind.

  - Two bugs of this shape have already shipped and been fixed (the `Format.signal` use-after-free and `convert()`'s aliased `signal_view`), so the class is demonstrated, not theoretical.

### Platform Support

- [~] **Bundle the common format handlers by default (mp3, flac, ogg/vorbis)**

  - **Implemented 2026-10-24 with the libmad item above; verified on Linux, not yet on macOS.** Codecs are compiled into libsox instead of loaded as plugins. A clean `python:3.12-slim` container reads wav/flac/ogg/opus/mp3 and writes wav/flac/ogg/mp3, with no system packages. sox 14.4.2 cannot write opus. cibuildwheel's `test-command` fails on a missing format and runs `tests/test_mp3_decode.py` against each wheel. Linux wheels ship no audio drivers, so `play()` works only on macOS.

  - **Motivation: this is the most likely first-run failure.** A user runs `pip install cysox`, points it at an mp3, and it fails - because format support is a property of whichever libsox the wheel linked, and the handlers ship as separate `libsox-fmt-*` packages on Debian. A wheel that silently depends on what the user happens to have already installed gives up most of the benefit of shipping a wheel at all. See the P2 ticket "Expose which formats this build actually supports" for the per-build variation that motivated both.

  - **Licensing is the constraint, and mp3 *decode* is the one genuinely hard case** - see the Licensing item above, whose original "just use mpg123" premise was investigated and disproved on 2026-08-01. Everything except mp3 decode is BSD or LGPL and bundles cleanly:

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

  - **Sequencing:** do the libmad removal first and independently. It is a small, self-contained correctness fix, whereas bundling is a packaging project - and shipping the bundle first would propagate the GPL problem into every wheel published from then on.

  - **Cost to weigh:** this compounds the open Windows build-automation item below (more vendored deps, more CI matrix, more platform-specific breakage). Scoping to macOS + Linux first is reasonable; Windows already needs its own solution. Also decide precedence when a system libsox is present - bundled or system - and make it explicit rather than incidental.

  - **What it does not retire:** the `supported_formats()` API ticket. Someone can still build against a system libsox, so runtime discovery stays necessary; bundling only makes the common case predictable, which is most but not all of the value.

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

## Medium

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

## Low

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

- [ ] **Fix memory I/O functions** (BLOCKED) #blocked

  - Functions: `open_mem_read()`, `open_mem_write()`, `open_memstream_write()`

  - Status: cysox wrapper bugs (see [docs/dev/known_limitations.md](docs/dev/known_limitations.md) §2)

  - Tracking: Documented in Known Limitations

### Backlog

- [ ] Async/await support for effects processing

- [ ] NumPy-native array returns (optional dependency)

- [ ] Audio visualization helpers (waveform, spectrogram)
