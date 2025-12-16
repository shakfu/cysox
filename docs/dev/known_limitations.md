# Known Limitations

This document describes known limitations and constraints of cysox, including issues inherited from the underlying libsox library.

---

## 1. Repeated init/quit Cycles Cause Crashes

### Summary

Calling `sox.init()` and `sox.quit()` multiple times within a single process lifetime can cause crashes (SIGABRT). The library should be initialized once at program start and quit once at program end.

### Symptoms

```text
Fatal Python error: Aborted

Current thread 0x00000001fd0a6140 (most recent call first):
  File "your_script.py", line XX in your_function
  ...
```

The crash typically occurs on the second or third init/quit cycle, manifesting as a `SIGABRT` signal.

### Root Cause

libsox uses global state that is not designed to be re-initialized after shutdown. The `sox_quit()` function frees internal data structures, but `sox_init()` does not fully reinitialize them on subsequent calls. This leads to:

1. **Dangling pointers**: Internal effect handler tables and format handler registries may contain stale references after quit.
2. **Double-free potential**: Some cleanup code may attempt to free already-freed memory on repeated cycles.
3. **Static initialization issues**: Certain global variables are initialized once via static initializers and are not reset by `sox_init()`.

### Affected Code

```c
// In libsox's sox.c (simplified)
static sox_globals_t sox_globals;
static int sox_is_initialized = 0;

int sox_init(void) {
    if (sox_is_initialized)
        return SOX_SUCCESS;  // No-op if already initialized
    // ... initialization code ...
    sox_is_initialized = 1;
    return SOX_SUCCESS;
}

int sox_quit(void) {
    if (!sox_is_initialized)
        return SOX_SUCCESS;
    // ... cleanup code that frees global structures ...
    sox_is_initialized = 0;  // Allows re-init, but state is corrupted
    return SOX_SUCCESS;
}
```

The issue is that while `sox_is_initialized` is reset, the internal state (effect tables, format handlers, etc.) is not properly restored to a clean pre-initialization state.

### Workaround

**Initialize once, quit once:**

```python
import cysox as sox
import atexit

# Initialize at module load
sox.init()

# Register cleanup for program exit
atexit.register(sox.quit)

# Now use sox throughout your program without calling init/quit again
def process_audio(input_path, output_path):
    with sox.Format(input_path) as f:
        # ... processing ...
        pass
```

**For applications requiring isolation:**

If you need truly isolated sox sessions (e.g., for testing), use separate processes:

```python
import multiprocessing

def isolated_sox_operation(input_path):
    """Run in a separate process for isolation."""
    import cysox as sox
    sox.init()
    try:
        with sox.Format(input_path) as f:
            return f.signal.rate
    finally:
        sox.quit()

if __name__ == '__main__':
    with multiprocessing.Pool(1) as pool:
        result = pool.apply(isolated_sox_operation, ('audio.wav',))
```

### Impact on Testing

The cysox test suite uses a module-scoped fixture to initialize sox once per test module:

```python
@pytest.fixture(scope="module")
def sox_initialized():
    sox.init()
    yield
    sox.quit()
```

Tests requiring repeated init/quit cycles are skipped:

```python
@pytest.mark.skip(reason="libsox does not support repeated init/quit cycles safely")
def test_operations_between_init_quit(self):
    ...
```

### Upstream Status

This is a known characteristic of libsox's architecture. The library was designed for command-line use (single init, process audio, quit) rather than long-running applications with multiple initialization cycles.

No upstream fix is expected, as changing this behavior would require significant architectural changes to libsox.

---

## 2. Memory I/O Functions Not Functional

### Summary

The memory-based I/O functions (`open_mem_read`, `open_mem_write`, `open_memstream_write`) have platform-specific issues and do not work reliably.

### Affected Functions

- `sox.open_mem_read()` - Read audio from memory buffer
- `sox.open_mem_write()` - Write audio to memory buffer
- `sox.open_memstream_write()` - Write audio to dynamically-sized memory stream

### Symptoms

- Functions may return `None` or raise exceptions
- Written data may be truncated or corrupted
- Platform-dependent behavior (works on some systems, fails on others)

### Root Cause

libsox's memory I/O implementation relies on platform-specific features (`fmemopen`, `open_memstream`) that have inconsistent behavior across operating systems:

- **macOS**: `fmemopen` available but has quirks with binary modes
- **Linux**: Generally works but has edge cases with buffer sizing
- **Windows**: Functions not available (would require custom implementation)

### Workaround

Use temporary files instead of memory buffers:

```python
import tempfile
import cysox as sox

def process_in_memory(input_bytes):
    """Process audio bytes using temporary files."""
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_in:
        tmp_in.write(input_bytes)
        tmp_in_path = tmp_in.name

    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_out:
        tmp_out_path = tmp_out.name

    try:
        # Process using file-based API
        with sox.Format(tmp_in_path) as input_fmt:
            with sox.Format(tmp_out_path, signal=input_fmt.signal, mode='w') as output_fmt:
                # ... effects chain ...
                pass

        with open(tmp_out_path, 'rb') as f:
            return f.read()
    finally:
        os.unlink(tmp_in_path)
        os.unlink(tmp_out_path)
```

### Tests

Memory I/O tests are skipped in the test suite:

```python
@pytest.mark.skip(reason="Memory I/O not functional - libsox upstream issue")
def test_memory_write():
    ...
```

---

## 3. Thread Safety Constraints

### Summary

While cysox supports concurrent operations on separate `Format` objects and effects chains, there are constraints on global operations.

### Safe Operations (Thread-Safe)

- Opening and reading from different `Format` objects concurrently
- Writing to different output files concurrently
- Running separate effects chains in parallel
- Creating `SignalInfo`, `EncodingInfo`, and other value objects
- Looking up effect handlers via `find_effect()`

### Unsafe Operations (Not Thread-Safe)

- Calling `init()` or `quit()` from multiple threads
- Sharing a single `Format` object across threads without synchronization
- Sharing a single `EffectsChain` across threads

### Recommendations

1. Call `init()` and `quit()` only from the main thread
2. Create separate `Format` and `EffectsChain` objects per thread
3. Use thread-local storage if needed for per-thread sox resources

---

## 4. Platform Support Limitations

### macOS

- **Fully supported**
- Static linking available for self-contained wheels
- Homebrew dependencies: `sox libsndfile mad libpng flac lame mpg123 libogg opus opusfile libvorbis`

### Linux

- **Fully supported**
- Dynamic linking to system libsox
- Package dependencies vary by distribution (see README.md)

### Windows

- **Placeholder support only**
- Requires manual installation of libsox
- Environment variables `SOX_INCLUDE_DIR` and `SOX_LIB_DIR` must be set
- No CI testing or pre-built wheels
- Contributions welcome

---

## References

- [libsox source code](https://sourceforge.net/p/sox/code/ci/master/tree/)
- [SoX documentation](http://sox.sourceforge.net/libsox.html)
- [cysox issue tracker](https://github.com/your-repo/cysox/issues)
