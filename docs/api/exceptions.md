# Exceptions

cysox uses a custom exception hierarchy for error handling.

## Exception Hierarchy

```text
SoxError (base)
    SoxInitError
    SoxFormatError
    SoxEffectError
    SoxIOError
    SoxMemoryError
```

## Exception Classes

### `SoxError`

Base exception for all cysox errors. Catch this to handle all cysox-related errors:

```python
try:
    # cysox operations
except sox.SoxError as e:
    print(f"cysox error: {e}")
```

### `SoxInitError`

Raised when library initialization or cleanup fails.

Common causes:

- libsox not properly installed
- Calling `init()` when already initialized
- Resource exhaustion

```python
try:
    sox.init()
except sox.SoxInitError as e:
    print(f"Failed to initialize: {e}")
```

### `SoxFormatError`

Raised when format operations fail.

Common causes:

- File not found
- Unsupported format
- Corrupt audio file
- Permission denied

```python
try:
    f = sox.Format('nonexistent.wav')
except sox.SoxFormatError as e:
    print(f"Format error: {e}")
```

### `SoxEffectError`

Raised when effect operations fail.

Common causes:

- Invalid effect name
- Invalid effect options
- Effect chain misconfiguration

```python
try:
    chain.flow_effects()
except sox.SoxEffectError as e:
    print(f"Effect error: {e}")
```

### `SoxIOError`

Raised when I/O operations fail.

Common causes:

- Seek failure on non-seekable stream
- Write failure (disk full, permissions)
- Read failure (corrupt data)

```python
try:
    f.seek(1000000)
except sox.SoxIOError as e:
    print(f"I/O error: {e}")
```

### `SoxMemoryError`

Raised when memory allocation fails.

Common causes:

- Out of memory
- Allocation too large

```python
try:
    signal = sox.SignalInfo()
except sox.SoxMemoryError as e:
    print(f"Memory error: {e}")
```

## Best Practices

### Specific Exception Handling

Handle specific exceptions when you need different behavior:

```python
from cysox import sox

sox.init()

try:
    with sox.Format('input.wav') as f:
        samples = f.read(1024)
except sox.SoxFormatError:
    print("Could not open file")
except sox.SoxIOError:
    print("Could not read from file")
except sox.SoxError:
    print("Unknown cysox error")
finally:
    sox.quit()
```

### Callback Exception Handling

Exceptions in callbacks cannot propagate through C code. Use
`get_last_callback_exception()` to retrieve them:

```python
def my_callback(all_done, user_data):
    if some_condition:
        raise ValueError("Something went wrong")
    return True

chain.flow_effects(callback=my_callback)

exc_info = sox.get_last_callback_exception()
if exc_info:
    raise exc_info[1].with_traceback(exc_info[2])
```
