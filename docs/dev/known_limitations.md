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

The test suite does not manage the lifecycle itself. It relies on the
high-level API auto-initializing on first use, and on the `atexit` handler
registered by `SoxRuntime` to shut down once at process exit. `tests/conftest.py`
has no init/quit fixture.

Tests that genuinely need a shutdown run it in a subprocess, so each cycle gets
a fresh interpreter. `tests/test_memory_safety.py::TestShutdownSafety` does
this. Doing it inline is not merely untidy: an earlier version of those tests
called `force_quit()` and `ensure_init()` in-process and crashed the whole
suite inside `sox_find_format()`, which is this limitation biting exactly as
described above.

Tests that would require repeated init/quit cycles in one process are skipped:

```python
@pytest.mark.skip(reason="libsox does not support repeated init/quit cycles safely")
def test_operations_between_init_quit(self):
    ...
```

One consequence reaches beyond tests. An object still open when `sox_quit()`
runs cannot be closed afterwards, because `sox_close()` dispatches through
handler tables that shutdown has freed, and re-initializing builds a fresh
table rather than restoring the old one. `Format` and `EffectsChain` record
the initialization generation they were created in and skip cleanup when it no
longer matches. See the Memory Ownership Model in the architecture document.

### Upstream Status

This is a known characteristic of libsox's architecture. The library was designed for command-line use (single init, process audio, quit) rather than long-running applications with multiple initialization cycles.

No upstream fix is expected, as changing this behavior would require significant architectural changes to libsox.

---

## 2. Memory I/O Functions Not Functional

### Summary

The memory-based I/O functions (`open_mem_read`, `open_mem_write`,
`open_memstream_write`) do not work.

### Root Cause

**This is a defect in cysox, not in libsox.** An earlier version of this
document attributed it to platform differences in `fmemopen` and
`open_memstream`; that was wrong, and the misattribution is why the functions
stayed broken -- the diagnosis stopped at the wrong layer and nobody looked at
the wrapper.

`sox.pyx` passes the buffer as `<void*>buffer`, where `buffer` is a Python
object. Casting a Python object to `void*` in Cython reinterprets the
**`PyObject*` itself**, not the payload. Compiling the construct in isolation
and reading the generated C shows it plainly:

```c
__pyx_t_1 = __Pyx_PyBytes_GET_SIZE(__pyx_v_buffer);
takes(((void *)__pyx_v_buffer), __pyx_t_1);
```

libsox is handed the address of the object header and told it is `len(buffer)`
bytes of audio.

`open_memstream_write` is separately broken: it returns its buffer pointer and
size by value at call time, but `sox_open_memstream_write()` only fills them in
when the format is closed. The pointer is still NULL at return, and Cython
converts a NULL `char*` to `None`.

### Fix

Use `PyBytes_AS_STRING` or `PyObject_GetBuffer` to obtain the data pointer. For
`open_memstream_write`, keep the `char**` and `size_t*` alive on the `Format`
wrapper and read the buffer back after `close()`.

### Workaround until then

Use temporary files:

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

The memory I/O tests in `tests/test_example5.py` are skipped. Their skip
reasons still blame libsox and should be corrected when the functions are
fixed.

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

- Sharing a single `Format` object across threads without synchronization

- Sharing a single `EffectsChain` across threads

Concurrent `init()` calls are safe. `SoxRuntime.ensure_init()` guards
initialization with double-checked locking, so racing callers get one
`sox_init()` between them. `quit()` is a documented no-op; the real shutdown
happens once, from the `atexit` handler. `_force_quit()` is not thread-safe and
is not intended for general use.

### Recommendations

1. Let the high-level API initialize on first use rather than calling
   `init()` yourself

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

- [cysox issue tracker](https://github.com/shakfu/cysox/issues)
