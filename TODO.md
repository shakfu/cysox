# TODO

**Legend:**

- `[ ]` Not started
- `[~]` In progress
- `[!]` Blocked

---

## P1 - High Priority

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

- [ ] **Integrate ASAN into CI** (requires custom Python build)
  - ASAN already available locally via `DEBUG=1 make build`
  - macOS `leaks` and Linux valgrind already in CI

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
