# TODO - cysox

Prioritized task list derived from [PROJECT_REVIEW.md](PROJECT_REVIEW.md).

**Legend:**
- `[ ]` Not started
- `[~]` In progress
- `[x]` Completed
- `[!]` Blocked

---

## P0 - Critical (Do First)

Issues affecting correctness, security, or build reliability.

### Build

- [x] **Fix version mismatch in pyproject.toml** (Completed 2025-12-15)
  - Fixed: `version = "0.1.1"`
  - File: `pyproject.toml`

### Memory Safety

- [x] **Add missing null checks in EncodingInfo property accessors** (Completed 2025-12-15)
  - File: `src/cysox/sox.pyx`
  - Added null checks to: `compression`, `reverse_bytes`, `reverse_nibbles`, `reverse_bits`, `opposite_endian` (getters and setters)

- [x] **Add missing null checks in LoopInfo property accessors** (Completed 2025-12-15)
  - File: `src/cysox/sox.pyx`
  - Added null checks to: `start`, `length`, `count`, `type` (getters and setters)

### Security

- [x] **Fix potential buffer overflow in basename()** (Completed 2025-12-15)
  - File: `src/cysox/sox.pyx`
  - Solution: Dynamic allocation based on input filename length
  - Added proper memory management with try/finally

---

## P1 - High Priority

Improvements for maintainability, platform support, and developer experience.

### Platform Support

- [ ] **Implement Windows build automation**
  - Current: Placeholder requiring manual environment variables
  - Tasks:
    - [ ] Add vcpkg or conda integration for libsox
    - [ ] Update setup.py with Windows library paths
    - [ ] Add Windows to CI matrix
    - [ ] Document Windows build process

### Documentation

- [x] **Add generated API documentation** (Completed 2025-12-15)
  - Tool: Sphinx with Furo theme
  - Created:
    - [x] docs/ directory structure
    - [x] conf.py with autodoc, napoleon, myst-parser
    - [x] index.rst, installation.rst, quickstart.rst, examples.rst
    - [x] api/modules.rst, api/exceptions.rst
    - [x] changelog.rst, contributing.rst
  - Build: `make docs` (output in docs/_build/html)
  - Serve: `make docs-serve` (localhost:8000)

### Testing

- [x] **Add performance benchmarks** (Completed 2025-12-15)
  - Tool: pytest-benchmark
  - Benchmarks implemented:
    - [x] File read throughput (list vs buffer vs read_into)
    - [x] File write throughput (list vs array vs memoryview)
    - [x] Effects chain processing (passthrough, vol, multi-effect, reverb, rate)
    - [x] Memory usage (open/close cycles, object creation)
  - Run: `make benchmark`
  - Compare: `make benchmark-save` then `make benchmark-compare`
  - Docs: `docs/benchmarks.rst`

### Error Handling

- [x] **Improve callback exception handling** (Completed 2025-12-15)
  - File: `src/cysox/sox.pyx`
  - Added `_last_callback_exception` module-level storage
  - Added `get_last_callback_exception()` function to retrieve stored exceptions
  - Updated type stubs in `__init__.pyi`

---

## P2 - Medium Priority

Enhancements for robustness and completeness.

### Security Hardening

- [x] **Enable overflow checking in Cython** (Completed 2025-12-16)
  - File: `setup.py` line 168
  - Change: `'overflowcheck': DEBUG` - enabled in debug builds only
  - Rationale: Catches integer overflow bugs without production performance penalty

### Testing Improvements

- [x] **Add thread safety tests** (Completed 2025-12-16)
  - File: `tests/test_thread_safety.py`
  - Tests: 11 tests (10 passing, 1 skipped)
  - Coverage:
    - [x] Concurrent file reads (parallel, different files)
    - [x] Concurrent file writes
    - [x] Parallel effects chains (same effect, different effects)
    - [x] Concurrent object creation (SignalInfo, EncodingInfo, EffectHandler)
    - [x] Race conditions (rapid open/close, interleaved read/write)
  - Known limitation: libsox does not support repeated init/quit cycles (test skipped)

- [ ] **Add memory leak tests**
  - Integrate valgrind or ASAN into CI
  - Test allocation/deallocation cycles
  - Focus on Format, Effect, EffectsChain lifecycle
  - Note: ASAN already available via `DEBUG=1 make build`

- [x] **Add edge case tests** (Completed 2025-12-16)
  - File: `tests/test_edge_cases.py`
  - Tests: 46 tests
  - Coverage:
    - [x] Zero-length files and empty inputs
    - [x] Unusual sample rates (1 Hz to 384 kHz)
    - [x] Unusual channel counts (1-8 channels)
    - [x] Unusual bit depths (8, 16, 24, 32)
    - [x] Corrupt/truncated headers
    - [x] Large values and potential overflows
    - [x] Boundary conditions (EOF, single frame reads)
    - [x] Special characters in filenames

### Documentation

- [ ] **Create architecture documentation**
  - Document class hierarchy and relationships
  - Explain ownership model and memory management
  - Add sequence diagrams for common operations

- [ ] **Add performance guide**
  - When to use `read()` vs `read_buffer()` vs `read_into()`
  - Memory efficiency tips for large files
  - Effects chain optimization strategies

- [ ] **Add troubleshooting guide**
  - Common errors and solutions
  - Platform-specific issues
  - Debug mode usage

---

## P3 - Low Priority

Nice-to-have features and long-term improvements.

### Features

- [ ] **Implement playlist parsing**
  - File: `src/cysox/sox.pyx` lines 2136-2148 (commented out)
  - Requires: Callback mechanism for playlist entries

- [x] **Add streaming API** (Completed 2025-12-16)
  - Implemented: `cysox.stream(path, chunk_size)` returns `Iterator[memoryview]`
  - Works with numpy, array.array, and any buffer protocol consumer
  - File: `src/cysox/audio.py`

- [x] **Add high-level API** (Completed 2025-12-16)
  - Implemented in `src/cysox/audio.py`:
    - [x] `cysox.info(path)` - Get audio metadata as dict
    - [x] `cysox.convert(input, output, effects=[], ...)` - Convert with effects
    - [x] `cysox.stream(path, chunk_size)` - Stream samples as memoryview
    - [x] `cysox.play(path, effects=[])` - Play to audio device (macOS/Linux)
    - [x] `cysox.concat(inputs, output)` - Concatenate audio files
  - Auto-initialization via atexit (no manual init/quit needed)
  - Documentation: `docs/dev/high_level_api.md`

- [x] **Add typed effects module** (Completed 2025-12-16)
  - 28 effect classes in `src/cysox/fx/`
  - Categories: Volume, EQ, Filters, Reverb/Spatial, Time-based, Conversion
  - CompositeEffect for reusable effect combinations
  - Full IDE autocomplete and parameter validation

- [!] **Fix memory I/O functions** (BLOCKED)
  - Functions: `open_mem_read()`, `open_mem_write()`, `open_memstream_write()`
  - Status: Blocked by libsox upstream issue
  - Tracking: Document in Known Issues

### Build System

- [ ] **Add automatic version bumping**
  - Tool: bump2version or python-semantic-release
  - Sync: pyproject.toml, __init__.py, CHANGELOG.md

- [ ] **Add release automation**
  - GitHub Actions workflow for PyPI publishing
  - Automatic changelog generation
  - Git tag creation

### Code Quality

- [ ] **Add pre-commit hooks**
  - flake8 linting
  - isort import sorting
  - black formatting (for .py files)

---

## Backlog

Items to consider for future releases.

- [x] Custom effects support - Documented in `docs/dev/high_level_api.md` (CompositeEffect, PythonEffect, C/Cython approaches)
- [ ] Async/await support for effects processing
- [ ] NumPy-native array returns (optional dependency)
- [ ] Audio visualization helpers (waveform, spectrogram)
- [ ] CLI tool wrapping the Python API

---

## Completed

Items completed since this TODO was created.

### 2025-12-16

- **P3: Add high-level API** - `info()`, `convert()`, `stream()`, `play()`, `concat()`
- **P3: Add typed effects module** - 28 effect classes in `cysox.fx`
- **P3: Add streaming API** - `cysox.stream()` with memoryview output
- **Backlog: Custom effects support** - Documented 5 approaches in `docs/dev/high_level_api.md`
- **P2: Enable overflow checking in Cython** - Conditional on DEBUG mode
- **P2: Add thread safety tests** - 11 tests covering concurrent operations
- **P2: Add edge case tests** - 46 tests for boundary conditions and error handling

### 2025-12-15

- **P0: Fix version mismatch in pyproject.toml** - Updated to 0.1.1
- **P0: Add null checks to EncodingInfo properties** - Added to 5 properties (getters + setters)
- **P0: Add null checks to LoopInfo properties** - Added to 4 properties (getters + setters)
- **P0: Fix buffer overflow in basename()** - Dynamic allocation based on input length
- **P1: Improve callback exception handling** - Added `get_last_callback_exception()` function
- **P1: Add generated API documentation** - Sphinx docs with Furo theme, 9 pages
- **P1: Add performance benchmarks** - pytest-benchmark with 20 benchmark tests

---

## References

- [PROJECT_REVIEW.md](PROJECT_REVIEW.md) - Full code review
- [CHANGELOG.md](CHANGELOG.md) - Version history
- [docs/dev/high_level_api.md](docs/dev/high_level_api.md) - High-level API documentation and extension guide
- [libsox documentation](https://sourceforge.net/p/sox/code/ci/master/tree/src/sox.h)
