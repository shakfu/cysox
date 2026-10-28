# TODO

## High

### Licensing

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

- [ ] **Implement Windows build automation**

  - Current: placeholder requiring manual environment variables. Linux and macOS wheels build libsox from source (`scripts/build-libsox.sh`); Windows needs the same.

  - Tasks:

    - [ ] Add vcpkg or conda integration for libsox

    - [ ] Add Windows library paths to `CMakeLists.txt`

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

  - Remaining, by count of `assert ... exists()`: `tests/test_slice_outputs.py` (15), `tests/test_audiohit_features.py` (34), `tests/test_cli.py` (7), `tests/test_high_level_api.py` (5).

  - The slice and audiohit suites are the most valuable: they cover `slice_loop`/`split_by_silence`, which do their own duration arithmetic and could hide the same class of bug. `tests/audio_metrics.py` provides the measurement helpers.

- [ ] **Integrate ASAN into CI** (requires custom Python build)

  - ASAN already available locally via `DEBUG=1 make build`

  - macOS `leaks` and Linux valgrind already in CI

### API / Usability

- [ ] **Expose which formats this build actually supports**

  - libsox format support is a **build-time** property. The wheels build libsox 14.4.2 with mp3/flac/ogg/opus compiled in, but a source build links whatever the system provides - and Debian ships mp3/flac/ogg as separate `libsox-fmt-*` packages, so `pip install cysox` against a stock `libsox-dev` yields a library that cannot open the formats most users have.

  - **Validated 2026-08-01.** Missing formats vary per build: one system libsox lacked mp3 and flac; the then-vendored build lacked opus.

  - Today the only ways to find out are to call the private-ish `cysox.sox.find_format(ext, False)` or to attempt the conversion and catch the failure. A downstream tool that wants to *prefer* cysox and fall back to ffmpeg has to reach into `cysox.sox` to do it. `cysox.__all__` exports nothing format-related.

  - Suggested: a public `cysox.supported_formats()` (or `cysox.supports('mp3')`), plus a line in the install docs stating that format support depends on the linked libsox build and naming the packages needed for mp3/flac/ogg.

  - Also decide whether a source build prefers a system libsox or the vendored one, and document it.

- [ ] **Route libsox's own diagnostics through Python**

  - libsox writes warnings and errors straight to the process's stderr from C, so a caller sees unattributed text it cannot capture, suppress, or attach to the file that caused it. Two seen in normal use: `formats: no handler for detected file type 'flac'` (which is *also* raised as a Python exception, so it double-reports) and `wav: wave header missing extended part of fmt chunk` (benign, emitted for any 44-byte float WAV - which is what a lot of hardware writes).

  - **Validated 2026-08-01.** Confirmed uncapturable: under `contextlib.redirect_stderr(io.StringIO())` a `cysox.info()` on a 44-byte float WAV still prints to the terminal and the buffer captures `''` - it is written to fd 2 from C, below Python's `sys.stderr`.

  - `_build_output_encoding()` avoids emitting the encoding-fallback warnings by probing with `format_supports_encoding` first, but any legitimate libsox warning on a conversion still lands on the caller's stderr unattributed.

  - Suggested: install a `sox_get_globals()->output_message_handler` that forwards to the `logging` module, with a way to silence it. Would make cysox embeddable in tools with their own output.

### Build System

- [ ] **Add automatic version bumping**

  - Tool: bump2version or python-semantic-release

  - Sync: pyproject.toml, `__init__.py`, CHANGELOG.md

- [ ] **Publish wheels to PyPI from CI with trusted publishing**

  - `.github/workflows/build-wheel.yml` builds on `v*` tags but has no publish job, so releases go out via a manual `make publish`.

### Code Quality

- [ ] **Add pre-commit hooks**

  - ruff linting and formatting

  - isort import sorting

## Low

### Performance

- [ ] **Run effect flows in parallel across threads**

  - `flow_effects()` releases the GIL, but `_flow_lock` in `sox.pyx` serializes flows: libsox built `--disable-openmp` leaves its shared FFT cache (`effects_i_dsp.c`) unlocked.

  - Options: build libsox with OpenMP (adds a libgomp/libomp runtime to the wheels), or patch a mutex around the cache in `scripts/patches/`. Either way, a source build against a system libsox still needs the lock.

  - `sox_version_info()` reports `sox_version_have_threads` for an OpenMP build, so the lock could be skipped at runtime when it is set.

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

- [ ] **Split `audio.py` (1700+ lines) and `sox.pyx` (2800+ lines)**

  - `audio.py` holds twelve top-level functions of 60-210 lines each in one module.

  - `sox.pyx` would read better split along the struct boundaries `sox.pxd` already draws.

  - Cosmetic; do it when touching these files for another reason.

### Features

- [ ] **Implement playlist parsing**

  - File: `src/cysox/sox.pyx`, commented-out `parse_playlist`

  - Requires: Callback mechanism for playlist entries

- [ ] **Fix memory I/O functions**

  - Functions: `open_mem_read()`, `open_mem_write()`, `open_memstream_write()`

  - Status: cysox wrapper bugs (see [docs/dev/known_limitations.md](docs/dev/known_limitations.md) §2)


### Backlog

- [ ] Async/await support for effects processing

- [ ] NumPy-native array returns (optional dependency)

- [ ] Audio visualization helpers (waveform, spectrogram)
