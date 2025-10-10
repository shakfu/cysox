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

### Added
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
