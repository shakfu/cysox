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
- **Linux Build Support**:
  - Automatic pkg-config detection
  - Fallback to common system paths
  - Support for x86_64 and aarch64 architectures
- **Windows Build Placeholder**: Environment variable configuration for Windows development

### Changed
- **Error Handling**: Replaced assertions with proper exceptions in init/quit functions
- **Memory Management**: Fixed memory leak in `SignalInfo.mult` setter
- **API Consistency**: All error messages now use custom exception classes with detailed context

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
- **Test Fixes**:
  - Uncommented and fixed 8 disabled tests in test_sox_format.py and test_sox_effects.py
  - Updated tests to use new custom exceptions

### Removed
- **Code Cleanup**: Removed 156 lines of commented-out code from `utils.py`
  - Sample conversion macros that were never implemented
  - Duplicate utility function stubs

### Security
- **Null Pointer Validation**: Added null pointer checks before dereferencing in all property accessors
- **Buffer Overflow Prevention**: Proper length validation in buffer protocol operations
- **Exception Safety**: Callback exceptions properly caught and logged without crashing C code

## [0.1.0] - Initial Release

- Project created
- Basic Cython wrapper for libsox
- Core classes: Format, Effect, EffectsChain, SignalInfo, EncodingInfo
- MacOS build support
