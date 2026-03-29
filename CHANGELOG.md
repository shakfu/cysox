# CHANGELOG

All notable project-wide changes will be documented in this file. Note that each subproject has its own CHANGELOG.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and [Commons Changelog](https://common-changelog.org). This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Types of Changes

- Added: for new features.
- Changed: for changes in existing functionality.
- Deprecated: for soon-to-be removed features.
- Removed: for now removed features.
- Fixed: for any bug fixes.
- Security: in case of vulnerabilities.

---

## [Unreleased]

## [0.1.11]

### Fixed

- **Documentation accuracy**: Corrected effect counts across all docs (README,
  index, effects reference, high-level API guide) to match actual source:
  27 base effects, 53 presets
- **README.md**: Fixed `fx.Remix(out_spec=[[1, 2]])` to correct parameter name
  `fx.Remix(mix=["1,2"])`
- **dev/high_level_api.md**: Fixed `info()` return type from `dict` to
  `AudioInfo` (supports both attribute and dict-style access)
- **cli.md**: Added missing `superflux` to `--method` options for slice command
- **installation.md**: Added missing `pkg-config` to Linux (Ubuntu and Fedora)
  install instructions

### Added

- **Sample Processing API reference** (`docs/api/samples.md`): Full documentation
  for `slice_loop()`, `stutter()`, `auto_trim()`, `split_by_silence()`,
  `pitch_scale()`, and `batch()` with parameter tables and practical examples
- **`Silence` effect** documented in effects reference (`docs/api/effects.md`)
  with all 6 parameters
- **Sample processing examples** in `docs/examples.md`: auto-trim, split by
  silence, pitch scale, and batch processing sections
- **Docs site link** in README.md: badge and nav links to
  https://shakfu.github.io/cysox/
- **docs/index.md**: Added Sample Processing and Drum Loop Tools to feature list

### Changed

- **dev/high_level_api.md**: Updated module structure to list all actual source
  files (`onset.pyx`, `utils.py`, `__main__.py`, individual `fx/` submodules)
- **docs/changelog.md**: Added recent release summaries instead of bare GitHub link
- **pyproject.toml**: Pinned `mkdocs>=1.6,<2` to avoid incompatibility with
  mkdocs-material (MkDocs 2.0 broke the Material theme)

## [0.1.10]

### Added

- **AudioHit Feature Port**: Batch sample processing features ported from
  [AudioHit](https://github.com/icaroferre/AudioHit) (Rust CLI tool for
  hardware/software sampler workflows)

- **`Silence` Effect** (`cysox.fx.Silence`): Wraps sox's `silence` effect for
  amplitude-based silence detection and removal
  - Configurable threshold in dB, minimum duration, and above/below period counts
  - Supports independent parameters for leading and trailing silence
  - Building block for `auto_trim()` and usable standalone in effects chains

- **`cysox.auto_trim()`**: Trim silence from beginning and end of audio files
  based on amplitude threshold (AudioHit's trim mode)
  - `threshold_db`: Amplitude threshold in dB (default: -48dB)
  - `fade_in`/`fade_out`: Fade durations in milliseconds
  - `speed_factor`: Playback speed change (AudioHit's `--speedup`/`--slowdown`)
  - Optional additional effects chain
  - Uses reverse trick for reliable fade-out behavior

- **`cysox.split_by_silence()`**: Split continuous recordings into separate
  one-shot samples at silence gaps (AudioHit's `--split true` mode)
  - Two-pass algorithm: scans peaks in ~10ms windows, then re-reads and writes segments
  - `threshold_db`, `min_silence`, `min_segment` for detection tuning
  - Per-segment fades (milliseconds), speed change, and effects
  - Returns list of created segment file paths

- **`cysox.pitch_scale()`**: Generate N pitch-shifted copies at semitone
  intervals (AudioHit's scale mode)
  - `semitones`: Number of copies (default: 12 for one octave)
  - `offset`: Starting semitone offset (default: 0)
  - Optional effects applied to each copy after pitch shifting
  - Output naming: `{basename}_pitch_{+N}.wav`

- **`cysox.batch()`**: Process all audio files in a directory tree
  (AudioHit's `--folder` mode)
  - Preserves relative directory structure in output
  - `recursive` flag (default: True)
  - `output_format` for bulk format conversion
  - `sample_rate`, `channels`, `bits` for bulk resampling
  - `on_file` callback for progress reporting
  - Recognizes common audio extensions: wav, mp3, flac, ogg, aiff, au, opus, wv, caf, amr

- **CLI Commands** for all new features:
  - `cysox auto-trim <input> <output>` with `--thresh`, `--fadein`, `--fadeout`,
    `--speedup`, `--slowdown`, `-p PRESET`
  - `cysox split <input> <output_dir>` with `--thresh`, `--min-silence`,
    `--min-segment`, `--fadein`, `--fadeout`, `-p PRESET`
  - `cysox pitch-scale <input> <output_dir>` with `--range`, `--offset`, `-p PRESET`
  - `cysox batch <input_dir> <output_dir>` with `--rate`, `--channels`, `--bits`,
    `--format`, `--no-recursive`, `-p PRESET`

- **Tests**: 40 new tests in `test_audiohit_features.py` covering all new
  functionality: Silence effect, auto_trim, split_by_silence, pitch_scale, and
  batch processing

- **`SoxRuntime` Singleton** (`sox.SoxRuntime`): Consolidates all global state
  (init tracking, callback storage, exception storage) into a single
  thread-safe singleton
  - Replaces three independent module-level globals (`_sox_initialized`,
    `_flow_callbacks`, `_last_callback_exception`) in `sox.pyx` and
    `_initialized` in `audio.py`
  - Double-checked locking pattern in `ensure_init()` prevents the race
    condition where two threads could both enter the `if not _initialized`
    branch under free-threaded Python (PEP 703)
  - Callback registration (`register_callback`, `unregister_callback`,
    `get_callback`) is lock-protected, replacing the previous reliance on
    the GIL for `_flow_callbacks` dict thread safety
  - Atexit handler registration moved into the singleton (registered exactly
    once on first init), eliminating the duplicate tracking between `sox.pyx`
    and `audio.py`
  - Accessible as `sox._runtime`; existing `sox.init()`, `sox.quit()`,
    `sox._force_quit()` delegate to the singleton for full backwards
    compatibility
  - No measurable performance impact: lock overhead is ~10 us per convert
    (128 callbacks x 78 ns per uncontended lock+lookup), well under 1% of
    typical processing time
  - 19 new tests in `test_sox_runtime.py`: singleton identity, thread-safe
    concurrent init, concurrent callback registration, exception storage,
    and backwards compatibility with existing APIs

### Changed

- **README.md**: Updated to reflect current state of the project
  - Added Sample Processing section documenting `auto_trim()`,
    `split_by_silence()`, `pitch_scale()`, and `batch()` with full parameter
    lists and examples
  - Added CLI examples for `auto-trim`, `split`, `pitch-scale`, `batch`
  - Updated `info()` return type from `dict` to `AudioInfo`
  - Updated base effect count to 27 (corrected from prior inaccurate counts)
  - Added `Silence` to Time-Based effects listing
  - Added `superflux` onset detection method to method lists and examples
  - Added Features bullet for sample processing capabilities

### Fixed

- **SIGSEGV in `OutOfBand.__dealloc__` on Linux** (valgrind CI crash):
  `OutOfBand.__init__` used `malloc` without zeroing, leaving the `comments`
  field (`char**`) as uninitialized garbage. `__dealloc__` checked
  `if self.ptr.comments:` -- the garbage evaluated as truthy, then
  `sox_delete_comments` dereferenced it, causing a segfault.
  - Root cause: `malloc(sizeof(sox_oob_t))` does not zero memory
  - Fix: replaced all 8 `malloc(sizeof(...))` calls across `SignalInfo`,
    `EncodingInfo`, `LoopInfo`, `InstrInfo`, `FileInfo`, `OutOfBand`, and
    `FormatTab` with `calloc(1, sizeof(...))` for zero-initialization
  - Defense in depth: even structs that manually initialize fields are now
    safe if an exception occurs between `calloc` and the field assignments

- **README.md**: Fixed unclosed code block before "## Low-Level API" section
  that caused downstream markdown rendering issues

## [0.1.9]

### Added

- **Memory Leak Detection in CI**: Automated leak checking on every push/PR
  - macOS: `leaks --atExit` via existing `check_leaks.py`, fails on any detected leak
  - Linux: valgrind with `--show-leak-kinds=definite` and `--error-exitcode=1`
  - New Makefile target: `make leaks-valgrind` for local Linux testing

- **Documentation Improvements**:
  - New [Effects Reference](docs/api/effects.md): Full parameter docs for all 27 effects and 53 presets
  - New [Onset Detection](docs/api/onset.md): API reference with detection method comparison and tuning guide
  - New [CLI Reference](docs/cli.md): All 7 commands documented with options and examples
  - Rewrote [Examples](docs/examples.md): High-level API examples now lead; covers convert, presets, streaming, progress callbacks, slicing, stutter, and onset detection
  - Updated [Home](docs/index.md): Feature list now links to relevant docs sections

- **Superflux Onset Detection** (`method='superflux'`): Implementation of the
  Boeck & Widmer (DAFx 2013) algorithm for onset detection with vibrato
  suppression and precise transient placement.
  - Mel-scaled spectral analysis via triangular filterbank (default 138 bands,
    27.5-16000 Hz), computed in C with `nogil`
  - Power-to-dB conversion with -80 dB floor
  - Maximum filter along frequency axis on the reference frame to suppress
    false onsets caused by vibrato and frequency modulation
  - Configurable frame lag for temporal comparison (default 2 frames)
  - Backtracking from detected peaks to nearest local ODF minimum for
    accurate transient start placement
  - Ring buffer for lagged mel-dB frames to avoid full spectrogram storage
  - New parameters for `detect()` and `detect_onsets()`:
    `n_mels`, `fmin`, `fmax`, `max_size`, `lag`
  - Updated type stubs (`onset.pyi`) with new parameters
  - 5 new tests: basic detection, sort order, backtracking behavior,
    custom parameters, minimum spacing enforcement
  - `slice_loop()` onset method list extended to include `'superflux'`

## [0.1.8]

### Added

- **Memory Leak Check** (`make leaks`): macOS `leaks --atExit` integration for C-heap leak detection
  - New `tests/check_leaks.py` exercises all major object lifecycles:
    SignalInfo, EncodingInfo, LoopInfo, InstrInfo, OutOfBand,
    EffectHandler, Format (read/write/buffer), EffectsChain
  - New Makefile target: `make leaks` (requires macOS)

- **CLI Preset Support for Convert**: `cysox convert` now accepts `-p`/`--preset` flag
  - Apply any preset during conversion: `cysox convert input.wav output.wav -p Telephone`
  - Consistent with `slice` and `stutter` commands

- **`AudioInfo` typed return from `info()`**: `cysox.info()` now returns an `AudioInfo` object
  - Attribute access: `info.sample_rate`, `info.duration`, etc.
  - Dict-style access preserved for backwards compatibility: `info['sample_rate']`
  - `AudioInfo` exported from `cysox` package

- **`CompositeEffect.__repr__`**: Shows constituent effects for debugging
  - e.g. `Telephone(sample_rate=8000) -> [HighPass(...), LowPass(...), ...]`

- **Onset module type stubs** (`onset.pyi`): IDE autocomplete and type checking for `onset.detect()` and `onset.detect_onsets()`

- **CLI tests** (`test_cli.py`): 30 tests covering every subcommand (info, convert, concat, play, preset list/info/apply, slice, stutter) with valid inputs, invalid inputs, and error paths

- **Format diversity tests** (`test_formats.py`): 19 tests exercising MP3, FLAC, mono 22kHz WAV, and amen break across info, convert, stream, concat, and onset detection

- **Progress callbacks and cancellation** for `convert()`, `play()`, and `concat()`
  - New `on_progress` keyword argument: receives progress `0.0`-`1.0`, return `False` to cancel
  - New `CancelledError` exception raised on cancellation
  - `convert()`/`play()` use libsox's `flow_effects` callback (no external dependencies)
  - `concat()` reports exact progress from sample counts
  - `ProgressCallback` type alias exported for type checking

### Fixed

- **Resource leak in `convert()`, `play()`, and `concat()`**: Wrapped Format objects in try/finally blocks to ensure cleanup on exceptions
- **CI triggers**: Enabled test workflow on push/PR to main/develop (was previously manual-only)
- **Test fixture scope in `test_error_handling.py`**: Changed from per-test to session scope to avoid repeated init/quit cycles
- **`read_buffer()` performance**: Replaced Python-level byte-by-byte copy with `memcpy`
- **`EncodingsInfo.type` crash**: Fixed `KeyError` on unexpected flag values (now returns `'unknown'`)
- **Trailing whitespace in ENCODINGS**: Stripped from `CL_ADPCM`, `MS_ADPCM`, `IMA_ADPCM`, `OKI_ADPCM`, `DWVW`
- **Commented-out dead code**: Removed stale code blocks in `sox.pyx`
- **`concat()` error messages**: Mismatch errors now suggest using `cysox.convert()` to normalize files first
- **`PythonEffect` and `CEffect` docs**: Marked as experimental with warnings that they are not yet functional
- **Opaque `SoxFormatError` messages**: Now reports specific cause (file not found, permission denied, unsupported format) instead of generic failure
- **`stream()` docstring**: Documents int32 sample range and how to convert to float [-1.0, 1.0]
- **`read_buffer()` crash at EOF**: `memcpy` on empty buffer caused `IndexError` when `sox_read` returned 0 samples
- **`stream()` failed on MP3 files**: Relied on `signal.length` which is inaccurate for MP3; simplified to read until EOF

### Changed

- **Onset detection uses KissFFT**: Replaced O(n^2) DFT with KissFFT (BSD-3-Clause) for ~100x speedup at typical frame sizes (1024)
  - Vendored KissFFT source (~750 lines of C) in `vendor/kissfft/`
  - Compiled as static library with double precision (`kiss_fft_scalar=double`)
  - New `kissfft.pxd` Cython declarations for real-valued FFT API
- **Documentation migrated from Sphinx to MkDocs**: Material theme with dark/light toggle, all `.rst` converted to Markdown, updated Makefile targets and `pyproject.toml` build dependencies
- **TODO.md Cleanup**: Removed all completed items, keeping only open/blocked tasks

## [0.1.7]

### Added

- **Composite Effect Presets Library** (`cysox.fx.presets`): 53 ready-to-use effect presets
  - Voice Effects: `Chipmunk`, `DeepVoice`, `Robot`, `HauntedVoice`, `VocalClarity`, `Whisper`
  - Lo-Fi Effects: `Telephone`, `AMRadio`, `Megaphone`, `Underwater`, `VinylWarmth`, `LoFiHipHop`, `Cassette`
  - Spatial Effects: `SmallRoom`, `LargeHall`, `Cathedral`, `Bathroom`, `Stadium`
  - Broadcast Effects: `Podcast`, `RadioDJ`, `Voiceover`, `Intercom`, `WalkieTalkie`
  - Musical Effects: `EightiesChorus`, `DreamyPad`, `SlowedReverb`, `SlapbackEcho`, `DubDelay`, `JetFlanger`, `ShoegazeWash`
  - Drum Loop Effects: `HalfTime`, `DoubleTime`, `DrumPunch`, `DrumCrisp`, `DrumFat`, `Breakbeat`, `VintageBreak`, `DrumRoom`, `GatedReverb`, `DrumSlice`, `ReverseCymbal`, `LoopReady`
  - Mastering Effects: `BroadcastLimiter`, `WarmMaster`, `BrightMaster`, `LoudnessMaster`
  - Cleanup Effects: `RemoveRumble`, `RemoveHiss`, `RemoveHum`, `CleanVoice`, `TapeRestoration`
  - Transition Effects: `FadeInOut`, `CrossfadeReady`

- **Drum Loop Slicing Utilities**: New functions for beat slicing and stutter effects
  - `cysox.slice_loop()`: Split audio into multiple segment files
    - Slice by count, BPM, or beat duration
    - Optional effects applied to each slice
    - Returns list of created file paths
  - `cysox.stutter()`: Create stutter/repeat effects
    - Extract segment from any position
    - Repeat with configurable count
    - Optional effects post-processing

- **Slice Output Tests**: 23 new tests in `test_slice_outputs.py`
  - Tests for `slice_loop()` with various configurations
  - Tests for `stutter()` with different segments and effects
  - Tests for drum presets on full loops
  - Output preserved in `build/test_output/slice_outputs/` for examination

- **CLI Preset Support**: New commands for working with presets from command line
  - `cysox preset list [category]`: List all presets or filter by category
  - `cysox preset info <name>`: Show detailed info and parameters for a preset
  - `cysox preset apply <name> <input> <output> [--param=value]`: Apply preset with optional parameters
  - `cysox slice <input> <output_dir> [-n slices] [--bpm] [-t threshold] [-s sensitivity] [-m method] [-p preset]`: Slice audio into segments
    - `-t, --threshold`: Enable onset detection (e.g., 0.3)
    - `-s, --sensitivity`: Peak picking strictness (default: 1.5)
    - `-m, --method`: Detection method: hfc, flux, energy, complex (default: hfc)
  - `cysox stutter <input> <output> [-s start] [-d duration] [-r repeats] [-p preset]`: Create stutter effects

- **Onset Detection Module** (`cysox.onset`): C-optimized transient detection for automatic slicing
  - Multiple detection algorithms implemented in Cython for high performance:
    - `hfc` (High-Frequency Content): Best for percussive transients like drums
    - `flux` (Spectral Flux): Good for general onsets including tonal changes
    - `energy`: Simple and fast energy-based detection
    - `complex`: Phase and magnitude analysis, most accurate but slower
  - Configurable parameters:
    - `threshold` (0.0-1.0): Detection sensitivity (lower = more sensitive)
    - `sensitivity` (1.0-3.0): Peak picking strictness
    - `min_spacing`: Minimum time between detected onsets
  - Functions:
    - `onset.detect(path, ...)`: Detect onsets in an audio file, returns list of times in seconds
    - `onset.detect_onsets(samples, ...)`: Low-level detection on raw sample data

- **Automatic Transient Slicing**: `slice_loop()` now supports onset-based slicing
  - New parameters: `threshold`, `sensitivity`, `onset_method`, `min_onset_spacing`
  - When `threshold` is set, automatically detects transients and slices at each onset
  - CLI support: `cysox slice <input> <output_dir> -t 0.3` for automatic slicing
  - Example: `cysox.slice_loop('drums.wav', 'slices/', threshold=0.3)`

## [0.1.6]

### Changed

- **Build System Migration**: Migrated from setuptools to scikit-build-core with CMake
  - New `CMakeLists.txt` handles Cython compilation and library linking
  - Platform-specific configuration (macOS static linking, Linux pkg-config, Windows env vars)
  - Uses CMake imported libraries to avoid target name conflicts with libsox
  - Removed `setuptools` dependency from cibuildwheel configuration
  - Added wheel/sdist include/exclude patterns in `pyproject.toml`
  - `setup.py` retained for reference but no longer used for builds

- **Makefile Overhaul**: Comprehensive rewrite with all targets restored
  - Build targets: `all`, `sync`, `build`, `rebuild`
  - Testing: `test`, `testpy`, `examples-p`, `examples-c`
  - Benchmarks: `benchmark`, `benchmark-save`, `benchmark-compare`
  - Code quality: `lint`, `typecheck`, `format`, `qa`
  - Distribution: `wheel`, `sdist`, `strip`, `delocate`, `check`, `publish`, `publish-test`
  - Documentation: `docs`, `docs-clean`, `docs-serve`
  - Cleanup: `clean`, `distclean`, `reset`
  - Debug mode support with `DEBUG=1`
  - Dependency on `$(LIBSOX)` ensures `scripts/setup.sh` runs first

- **GitHub Workflows Updated**: Modernized CI/CD for scikit-build-core
  - Switched from pip to uv for package management
  - Added `astral-sh/setup-uv@v4` action
  - Added cmake to Linux system dependencies
  - Changed linting from flake8 to ruff
  - Added mypy type checking to lint job
  - Updated cibuildwheel to version 3.3.1

### Added

- **Type Stubs for Cython Extension**: New `sox.pyi` stub file for mypy support
  - Complete type hints for all classes: `SignalInfo`, `EncodingInfo`, `Format`, `Effect`, `EffectsChain`, etc.
  - Function signatures for `init()`, `quit()`, `find_effect()`, `find_format()`, etc.
  - Accepts `Union[str, Path]` for file paths
  - Added `_force_quit()` internal function

- **Dev Dependencies**: Added `mypy` and `ruff` to `[dependency-groups] dev`

- **Mypy Configuration**: Added `[tool.mypy]` section to `pyproject.toml`

### Fixed

- **Missing `concat` in `__all__`**: Added `concat` to package exports in `__init__.py`

- **Type Annotations**: Fixed mypy errors in source code
  - `fx/base.py`: Changed `_handler_ptr: int = None` to `Optional[int]`
  - `audio.py`: Restructured `info()` to return outside `with` block for type narrowing
  - `audio.py`: Added assertions for `output_fmt` in `concat()` function

- **Updated `__init__.pyi`**: Added high-level API function signatures and module re-exports

- **CMake Target Name Conflict on Linux**: Fixed build failure when pkg-config finds libsox
  - Renamed internal CMake target from `sox` to `_sox` to avoid conflict with system `libsox`
  - CMake was interpreting `${SOX_LIBRARIES}` as our module target instead of the library
  - Output file remains `sox.cpython-*.so` via `OUTPUT_NAME` property

## [0.1.5]

### Fixed

- **Cross-Platform Build Script**: Rewrote `scripts/setup.sh` for proper Linux/macOS support
  - Added missing bash shebang that caused syntax errors on Linux
  - Linux now uses system libraries via pkg-config instead of Homebrew
  - macOS continues to use Homebrew with improved error handling
  - Clear status messages and dependency checking

- **Memory Corruption in SignalInfo**: Fixed uninitialized pointer bug in `SignalInfo.__init__`
  - After `malloc()`, `ptr.mult` contained garbage data
  - Setting `mult=0.0` (the default) caused `free()` on the garbage pointer
  - Now properly initializes `ptr.mult = NULL` before calling the setter

- **Crash in get_encodings()**: Fixed segfault when iterating encoding info array
  - System libsox doesn't reliably NULL-terminate the encodings array
  - Now uses `SOX_ENCODINGS` enum value as upper bound instead of checking for NULL
  - Prevents reading past the end of the array on Linux

## [0.1.4]

### Added

- **Command Line Interface**: New CLI exposing core functionality
  - `cysox --version`: Show cysox and libsox versions
  - `cysox info <file>`: Display audio file metadata
  - `cysox convert <input> <output>`: Convert audio files with optional `--rate`, `--channels`, `--bits`
  - `cysox play <file>`: Play audio to default device
  - `cysox concat <files...> -o <output>`: Concatenate multiple audio files

### Fixed

- **Broken CLI entry point**: Fixed `cysox:__main__` entry point in pyproject.toml that was declared but never implemented

## [0.1.3]

### Fixed

- **Fixed redundant dependencies**: `cython` was added as a dependency even though it is already required by the build-system. Also some sphinx-related dependences that weren't used have been removed.

## [0.1.2]

### Added

- **Test Output Fixtures**: Test outputs preserved in `build/test_output/` for manual inspection
  - Output files named after the tests that created them
  - Benchmark results saved to `build/test_output/benchmarks/` as JSON and text

- **FX Output Tests**: 54 new tests in `test_fx_outputs.py` with audible effect parameters
  - Tests for all effect types with recognizable audio transformations
  - Combined effect tests (telephone, underwater, radio, vinyl, etc.)

- **High-Level API**: New Pythonic interface that handles initialization automatically
  - `cysox.info(path)`: Get audio file metadata as dictionary
  - `cysox.convert(input, output, effects=[], ...)`: Convert with optional effects and format options
  - `cysox.stream(path, chunk_size)`: Iterator yielding memoryview chunks for streaming
  - `cysox.play(path, effects=[])`: Play audio to default device (macOS/Linux)
  - `cysox.concat(inputs, output)`: Concatenate multiple audio files
  - Auto-initialization via atexit - no manual `init()`/`quit()` needed
  - High-level API is now the default export from `import cysox`
  - Low-level API accessible via `from cysox import sox`

- **Typed Effects Module** (`cysox.fx`): 27 effect classes with full parameter validation
  - Base classes: `Effect`, `CompositeEffect`, `PythonEffect`, `CEffect`
  - Volume/Gain: `Volume`, `Gain`, `Normalize`
  - Equalization: `Bass`, `Treble`, `Equalizer`
  - Filters: `HighPass`, `LowPass`, `BandPass`, `BandReject`
  - Spatial/Reverb: `Reverb`, `Echo`, `Chorus`, `Flanger`
  - Time-based: `Trim`, `Pad`, `Speed`, `Tempo`, `Pitch`, `Reverse`, `Fade`, `Repeat`
  - Conversion: `Rate`, `Channels`, `Remix`, `Dither`
  - `CompositeEffect` for creating reusable effect combinations
  - All effects have `__repr__` for debugging

- **High-Level API Tests**: 30 new tests in `test_high_level_api.py`

### Changed

- **Package Exports**: `import cysox` now exports high-level API by default
  - Use `from cysox import sox` for low-level API access
  - Updated 25 test files to use new import pattern

- **Idempotent Initialization**: `sox.init()` is now safe to call multiple times
  - Subsequent calls after first initialization are no-ops
  - Prevents crashes from accidental double-initialization

- **Safe Quit Behavior**: `sox.quit()` is now a no-op during normal execution
  - Actual cleanup happens automatically at process exit via atexit
  - Prevents crashes from init/quit/init cycles (libsox limitation)
  - Internal `_force_quit()` used by atexit handler for real cleanup

- **Benchmark Output**: Disabled by default during normal test runs
  - Run explicitly with: `pytest --benchmark-enable`
  - Run only benchmarks with: `pytest --benchmark-only`

### Fixed

- **Rate-Changing Effects**: `Pitch`, `Speed`, and `Tempo` effects now correctly maintain output duration
  - Sox CLI auto-inserts `rate` effect after these effects; `convert()` now does the same
  - Fixed bug where `SignalInfo` mutation during `add_effect()` caused rate comparisons to fail
  - Uses `-q` (quick) rate conversion to avoid libsox FFT assertion bugs

- **Audio Playback**: `cysox.play()` now works correctly
  - Added `filetype` parameter to `sox.Format()` constructor
  - Enables audio device output via coreaudio (macOS), alsa/pulseaudio (Linux)

## [0.1.1]

### Added

- Missing `test_example0.py` corresponding to `example0.c`

- **Buffer Protocol Support**: Generic buffer protocol implementation for zero-copy operations
  - `Format.read_buffer(length)`: Returns memoryview compatible with NumPy, PyTorch, array.array
  - `Format.read_into(buffer)`: Zero-copy read into pre-allocated buffer
  - `Format.write(samples)`: Accepts any buffer protocol object or list
  - Works with stdlib `array.array` without requiring NumPy
- **Flow Effects Callbacks**: Full callback support for `EffectsChain.flow_effects()`
  - Real-time progress monitoring during effects processing
  - User-controlled abort capability
  - Thread-safe GIL-aware implementation
  - Custom user data support via `client_data` parameter
- **Context Manager Support**: `Format` class now implements `__enter__` and `__exit__`
  - Automatic resource cleanup with `with` statements
  - Proper exception handling during cleanup
  - Resource cleanup failures now logged with warnings during exception handling
- **Custom Exception Hierarchy**:
  - `SoxError` (base), `SoxInitError`, `SoxFormatError`, `SoxEffectError`, `SoxIOError`, `SoxMemoryError`
  - Better error messages with context throughout the codebase
- **Type Stub Files**: Complete `.pyi` type stubs for IDE support
  - Full autocomplete in VSCode, PyCharm, etc.
  - Type checking with mypy
  - `src/cysox/__init__.pyi` (200+ lines)
  - `src/cysox/utils.pyi`
- **Comprehensive Documentation**:
  - 500+ lines of docstrings added to major classes and methods
  - Examples for all major operations
  - Full parameter and return value documentation
  - Added missing docstrings to properties: `EncodingsInfo.type`, `Format.filename`, `Format.signal`, `Format.encoding`, `Format.filetype`
  - Note: Code review incorrectly flagged `EncodingsInfo.__repr__` as broken - it was always functional
- **Linux Build Support**:
  - Automatic pkg-config detection
  - Fallback to common system paths
  - Support for x86_64 and aarch64 architectures
- **Windows Build Placeholder**: Environment variable configuration for Windows development
- **CI/CD Pipeline** (2025-10-10):
  - GitHub Actions workflow for automated testing
  - macOS testing across Python 3.9-3.13
  - Linux (Ubuntu) testing across Python 3.9-3.13
  - Automated linting with flake8
  - Runs on push to main/develop and pull requests
- **Negative Test Cases** (2025-10-10):
  - Added comprehensive error handling test suite (`tests/test_error_handling.py`)
  - 18 tests covering invalid inputs, edge cases, and error paths
  - Tests for NULL pointer handling, memory allocation, double-close scenarios
  - Format, effect, and signal/encoding error validation

### Changed

- **Error Handling**: Replaced assertions with proper exceptions in init/quit functions
- **Memory Management**: Fixed memory leak in `SignalInfo.mult` setter
- **API Consistency**: All error messages now use custom exception classes with detailed context
- **API Guidance** (2025-10-10):
  - Added documentation notes to `EffectHandler.find()` and `FormatHandler.find()` static methods
  - Recommends using module-level `sox.find_effect()` and `sox.find_format()` for better consistency
- **Build System** (2025-10-10):
  - DEBUG macros now only defined when `DEBUG=1` environment variable is set
  - Previously always defined on macOS regardless of DEBUG setting
- **Documentation** (2025-10-10):
  - Updated README with accurate project status
  - Added "Known Issues" section documenting memory I/O limitations
  - Added "Platform Support" section with clear status indicators
  - Replaced outdated TODO list with completion status

### Fixed

- **Critical Memory Issues** (P0):
  - Memory leak in `SignalInfo.mult` setter when setting to 0.0
  - Use-after-free bug in `OutOfBand.__dealloc__`
  - Missing null pointer checks in `SignalInfo` and `EncodingInfo` properties
  - Missing allocation checks after malloc calls
- **Error Handling** (P0):
  - Replaced assertions with exceptions in `init()`, `quit()`, `format_init()`
  - Added descriptive error messages throughout
  - Fixed `FormatHandler` double-free bug (incorrect owner flag)
- **Type Conversions**:
  - Fixed `format_supports_encoding()` to return Python bool instead of sox_bool enum
- **String Encoding**:
  - Fixed filetype parameter encoding in `open_mem_read()`, `open_mem_write()`, and `open_memstream_write()`
  - Previously used incorrect cast `<bytes>filetype` which corrupted strings
  - Now properly encodes strings using `filetype.encode('utf-8')`
- **Memory I/O Investigation**:
  - Fixed string encoding bug, but memory I/O still non-functional
  - Attempted multiple approaches: bytearray, C-allocated memstream buffers
  - All approaches crash during write operations
  - Issue appears to be in libsox itself, not the Python bindings
  - Memory I/O tests remain skipped pending upstream investigation
- **Test Fixes**:
  - Uncommented and fixed 8 disabled tests in test_sox_format.py and test_sox_effects.py
  - Updated tests to use new custom exceptions
  - Added 11 new tests porting C examples 1-6 to Python (test_example1.py through test_example6.py)
  - 9 tests passing, 2 skipped (memory I/O has known buffer management issues)
- **Double-Close Protection** (2025-10-10):
  - Fixed segmentation fault when calling `Format.close()` twice
  - Method now checks if pointer is NULL before closing
  - Sets pointer to NULL after closing to prevent double-free
  - Second close returns success silently
- **Context Manager Cleanup** (2025-10-10):
  - Fixed silent exception swallowing during cleanup
  - Context manager now logs close failures with `warnings.warn()`
  - Uses `ResourceWarning` category for proper classification
  - Original exceptions still propagate correctly

### Removed

- **Code Cleanup**: Removed 156 lines of commented-out code from `utils.py`
  - Sample conversion macros that were never implemented
  - Duplicate utility function stubs
- **Unsafe Property Setters** (2025-10-10):
  - Removed `FileInfo.buf` setter to prevent dangling pointers
  - Removed `FormatTab.name` no-op setter that was misleading
  - Both properties now read-only with clear documentation
  - Constructors initialize struct members directly

### Security

- **Null Pointer Validation**: Added null pointer checks before dereferencing in all property accessors
- **Buffer Overflow Prevention**: Proper length validation in buffer protocol operations
- **Exception Safety**: Callback exceptions properly caught and logged without crashing C code
- **Memory Safety Improvements** (2025-10-10):
  - Eliminated dangling pointer vulnerability in `FileInfo.buf` property
  - Fixed double-free vulnerability in `Format.close()`
  - Added malloc() return value checks in `FileInfo` and `FormatTab` constructors
  - All C pointers now properly validated before use

## [0.1.0] - Initial Release

- Project created
- Basic Cython wrapper for libsox
- Core classes: Format, Effect, EffectsChain, SignalInfo, EncodingInfo
- MacOS build support
