# Changelog

The full changelog is maintained in the repository at
[CHANGELOG.md](https://github.com/shakfu/cysox/blob/main/CHANGELOG.md).

## Recent Releases

### Unreleased

- Fixed documentation accuracy: corrected effect counts (27 base, 53 presets), parameter names, return types
- Added Sample Processing API reference page (`docs/api/samples.md`)
- Added `Silence` effect to effects reference
- Added sample processing examples (auto-trim, split, pitch scale, batch)
- Added docs site link and badge to README
- Pinned `mkdocs>=1.6,<2` to avoid MkDocs 2.0 incompatibility with Material theme

### v0.1.10

- Memory leak fix (calloc replacing malloc for zero-initialization)
- AudioHit feature port: `auto_trim()`, `split_by_silence()`, `pitch_scale()`, `batch()`
- `Silence` effect wrapping sox's silence detection
- `SoxRuntime` singleton for thread-safe global state
- CLI commands for all new sample processing features

### v0.1.9

- Superflux onset detection (Boeck & Widmer, DAFx 2013)
- Memory leak detection in CI (macOS leaks, Linux valgrind)
- Documentation rewrite: effects reference, onset detection, CLI reference, examples
- KissFFT integration for onset detection (~100x speedup)
- Migration from Sphinx to MkDocs

### v0.1.8

- CLI preset support for convert (`-p` flag)
- `AudioInfo` typed return from `info()`
- Onset module type stubs
- Progress callbacks and cancellation for `convert()`, `play()`, `concat()`

See [CHANGELOG.md](https://github.com/shakfu/cysox/blob/main/CHANGELOG.md) for earlier releases.
