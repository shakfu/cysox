# Changelog

The full changelog is maintained in the repository at
[CHANGELOG.md](https://github.com/shakfu/cysox/blob/main/CHANGELOG.md).

## Recent Releases

### Unreleased

Behaviour changes that existing code may depend on:

- `Format.signal` returns an independent snapshot instead of a live view of the open format
- `EffectsChain.flow_effects()` returns its status instead of raising on `SOX_EOF`, which is normal early termination
- `Effect.set_options()` raises `SoxEffectError` when libsox rejects the arguments, rather than failing silently
- `convert()` and `play()` take the output rate and channel count from the effects chain, so `fx.Rate`, `fx.Channels` and `fx.Remix` are no longer undone
- `fx.Volume` and `fx.Dither` emit corrected sox arguments; three `fx.Dither` type names that sox never supported now raise `ValueError`
- `sox.ENCODINGS` and `info().encoding` follow the linked libsox's enum instead of hardcoded indices

Fixes:

- Use-after-close, double free on `Effect.delete()`, and borrowed wrappers outliving their owner no longer crash the interpreter
- Objects surviving a libsox shutdown are no longer closed through freed handler tables
- `fx.Trim` produces the requested duration; encodings past MP3 are no longer mislabelled
- Builds against SoX_ng 14.7, the version current Debian and Ubuntu ship

### v0.1.11

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
