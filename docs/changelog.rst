Changelog
=========

For the full changelog, see `CHANGELOG.md <https://github.com/youruser/cysox/blob/main/CHANGELOG.md>`_ in the repository.

Recent Changes
--------------

Version 0.1.1
~~~~~~~~~~~~~

**Added:**

- Buffer Protocol Support for zero-copy operations
- Flow Effects Callbacks for progress monitoring
- Context Manager Support for Format class
- Custom Exception Hierarchy (SoxError, SoxInitError, etc.)
- Type Stub Files (.pyi) for IDE support
- Linux Build Support with pkg-config
- CI/CD Pipeline with GitHub Actions
- Comprehensive error handling tests

**Fixed:**

- Memory leak in SignalInfo.mult setter
- Use-after-free bug in OutOfBand.__dealloc__
- Missing null pointer checks in property accessors
- Double-close protection in Format.close()
- Buffer overflow vulnerability in basename()

**Security:**

- Null pointer validation in all property accessors
- Buffer bounds checking
- Memory allocation checks

Version 0.1.0
~~~~~~~~~~~~~

- Initial release
- Basic Cython wrapper for libsox
- Core classes: Format, Effect, EffectsChain, SignalInfo, EncodingInfo
- macOS build support
