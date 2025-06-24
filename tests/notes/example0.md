# Example0 Integration Test

This directory contains integration tests and examples based on `tests/examples/example0.c` using the Python bindings from `src/cysox/sox.pyx`.

## Files

- `test_example0.py` - Unit test suite replicating example0.c functionality
- `example0.py` - Standalone script equivalent to example0.c
- `README.example0.md` - This documentation file

## Overview

The original C example (`tests/examples/example0.c`) demonstrates:

1. Reading an input audio file
2. Applying volume and flanger effects
3. Writing the processed audio to an output file

The Python equivalents replicate this functionality using the cysox Python bindings.

## Running the Integration Test

```bash
# Run the unit test
python3 -m pytest tests/test_example0.py -v

# Or run with unittest
python3 -m unittest tests.test_example0 -v
```

## Running the Example Script

```bash
# Process an audio file with volume and flanger effects
python3 tests/examples/example0.py input.wav output.wav
```

## Test Coverage

The integration test covers:

1. **Complete Effects Chain** (`test_example0_effects_chain`)
   - File I/O operations
   - Effects chain creation and management
   - Effect addition and configuration
   - Audio processing flow
   - Output verification

2. **Signal Properties** (`test_example0_signal_properties`)
   - Signal information access
   - Encoding information access
   - Property validation

3. **Effect Creation** (`test_example0_effect_creation`)
   - Effect handler discovery
   - Effect instantiation
   - Option configuration

4. **Error Handling** (`test_example0_error_handling`)
   - Invalid file operations
   - Non-existent effects

## Key Differences from C Example

### Python Bindings Usage

The Python version uses object-oriented wrappers around the C API:

```python
# C: sox_format_t *in = sox_open_read(filename, NULL, NULL, NULL);
# Python:
input_format = sox.Format(filename, mode='r')

# C: sox_effects_chain_t *chain = sox_create_effects_chain(&in->encoding, &out->encoding);
# Python:
chain = sox.EffectsChain(in_encoding=input_format.encoding, out_encoding=output_format.encoding)

# C: sox_effect_t *e = sox_create_effect(sox_find_effect("vol"));
# Python:
vol_effect = sox.Effect(sox.find_effect("vol"))
```

### Error Handling

The Python version uses exceptions instead of return codes:

```python
# C: assert(sox_init() == SOX_SUCCESS);
# Python:
sox.init()  # Raises exception on failure

# C: assert((in = sox_open_read(argv[1], NULL, NULL, NULL)));
# Python:
input_format = sox.Format(filename, mode='r')  # Raises exception on failure
```

### Resource Management

The Python version uses context managers and automatic cleanup:

```python
# C: sox_close(out); sox_close(in); sox_quit();
# Python: Handled automatically by destructors and tearDown
```

## Dependencies

- `cysox` Python package (built from `src/cysox/sox.pyx`)
- `unittest` (standard library)
- `pytest` (for running tests)
- Test audio file: `tests/data/s00.wav`

## Notes

- The test uses the existing `s00.wav` file from `tests/data/`
- Temporary output files are created in a temporary directory
- All resources are properly cleaned up in test teardown
- The example script provides the same command-line interface as the C version
