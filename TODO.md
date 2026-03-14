# TODO

**Legend:**

- `[ ]` Not started
- `[~]` In progress
- `[!]` Blocked

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

---

## P2 - Medium Priority

Enhancements for robustness and completeness.

### Testing Improvements

- [~] **Add memory leak tests**
  - [x] CI job: macOS `leaks` tool (via existing `check_leaks.py`)
  - [x] CI job: Linux valgrind (`--show-leak-kinds=definite`)
  - [x] `make leaks-valgrind` target for local Linux testing
  - [ ] Integrate ASAN into CI (requires custom Python build)
  - Note: ASAN already available locally via `DEBUG=1 make build`

### Documentation

- [x] **Effects reference** (`docs/api/effects.md`)
  - All 28 effects with parameter tables, types, defaults, examples
  - All 40+ presets organized by category
  - Custom preset creation guide

- [x] **Onset detection docs** (`docs/api/onset.md`)
  - API reference for `detect()` and `detect_onsets()`
  - Detection method comparison table
  - Parameter tuning guide

- [x] **CLI reference** (`docs/cli.md`)
  - All 7 commands with option tables and examples

- [x] **Examples rewrite** (`docs/examples.md`)
  - High-level API examples now lead (was 100% low-level)
  - Covers convert, presets, streaming, progress, slicing, stutter, onset

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

- [!] **Fix memory I/O functions** (BLOCKED)
  - Functions: `open_mem_read()`, `open_mem_write()`, `open_memstream_write()`
  - Status: Blocked by libsox upstream issue
  - Tracking: Document in Known Issues

### Build System

- [ ] **Add automatic version bumping**
  - Tool: bump2version or python-semantic-release
  - Sync: pyproject.toml, **init**.py, CHANGELOG.md

- [ ] **Add release automation**
  - GitHub Actions workflow for PyPI publishing
  - Automatic changelog generation
  - Git tag creation

### Architecture

- [ ] **Consolidate init state into a SoxRuntime singleton**
  - Currently `audio.py` (`_initialized`) and `sox.pyx` (`_sox_initialized`) independently track init state
  - Both paths converge correctly today (`sox.init()` is idempotent), but the dual tracking is unnecessary indirection
  - A `SoxRuntime` singleton would:
    - Own initialization/cleanup lifecycle in one place
    - Provide a natural place for a lock (needed for free-threaded Python / PEP 703)
    - Hold runtime configuration (verbosity, buffer sizes, etc.)
  - Also address: `_ensure_init()` race under free-threading (two threads can both enter the `if not _initialized` branch)
  - Also address: `_flow_callbacks` global dict relies on GIL for thread safety
  - Scope: consider for 1.0 release, not urgent given current correctness

### Code Quality

- [ ] **Add pre-commit hooks**
  - flake8 linting
  - isort import sorting
  - black formatting (for .py files)

---

## Backlog

Items to consider for future releases.

- [ ] Async/await support for effects processing
- [ ] NumPy-native array returns (optional dependency)
- [ ] Audio visualization helpers (waveform, spectrogram)
- [x] CLI tool wrapping the Python API

---

## References

- [CHANGELOG.md](CHANGELOG.md) - Version history
- [docs/dev/high_level_api.md](docs/dev/high_level_api.md) - High-level API documentation and extension guide
- [libsox documentation](https://sourceforge.net/p/sox/code/ci/master/tree/src/sox.h)
