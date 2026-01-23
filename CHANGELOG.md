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

- **Typed Effects Module** (`cysox.fx`): 28 effect classes with full parameter validation
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
