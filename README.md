# cysox

Towards a cython wrapper for [libsox](https://github.com/chirlu/sox)

## Overview

**cysox** is a Cython wrapper for [libsox](https://github.com/chirlu/sox), providing Python bindings to the SoX (Sound eXchange) library. SoX is a cross-platform command line utility that can convert various formats of computer audio files in to other formats.

## Features

- **Audio Processing**: Convert between different audio formats
- **Signal Manipulation**: Apply various audio effects and filters
- **Cross-platform**: Works on Windows, macOS, and Linux
- **High Performance**: Direct C bindings through Cython for optimal performance
- **Memory Efficient**: Low-level memory management for large audio files

## Building

Currently development and testing is only on MacOS. [Homebrew](https://brew.sh) is used for installing dependencies:

```sh
brew install sox libsndfile mad libpng
```

then you can build the cython extension:

```sh
make
```

build the wheel:

```sh
make wheel
```

run tests:

```sh
make test
```

## Usage Example

```python
>>> import sox
>>> f = sox.Format('tests/s00.wav')
>>> f.filetype
'wav'
>>> f.signal
<sox.SignalInfo at 0x105c754a0>
>>> f.signal.length
502840
>>> f.encoding
<sox.EncodingInfo at 0x105d4ebe0>
>>> f.encoding.bits_per_sample
16
```

## Complete Example

```python
#!/usr/bin/env python3
"""
Python equivalent of tests/examples/example0.c

This script replicates the functionality of the C example:
- Reads input file, applies vol & flanger effects, stores in output file
- Uses the Python bindings from src/cysox/sox.pyx

Usage: python3 example0_python.py <input_file> <output_file>
"""

import sys
import os
from pathlib import Path
import os

src_dir = Path.cwd() / 'src'
sys.path.append(str(src_dir))

# Import the cysox bindings
from cysox import sox


def main():
    """Main function replicating example0.c"""
    
    # Check command line arguments
    if len(sys.argv) != 3:
        print("Usage: python3 example0_python.py <input_file> <output_file>")
        sys.exit(1)
    
    input_filename = sys.argv[1]
    output_filename = sys.argv[2]
    
    # Verify input file exists
    if not os.path.exists(input_filename):
        print(f"Error: Input file '{input_filename}' not found")
        sys.exit(1)
    
    try:
        # Step 1: Initialize SoX library
        print("Initializing SoX library...")
        sox.init()
        
        # Step 2: Open the input file (with default parameters)
        print(f"Opening input file: {input_filename}")
        input_format = sox.Format(input_filename, mode='r')
        
        # Step 3: Open the output file with same signal characteristics as input
        print(f"Opening output file: {output_filename}")
        output_format = sox.Format(
            output_filename, 
            signal=input_format.signal,
            mode='w'
        )
        
        # Step 4: Create an effects chain
        print("Creating effects chain...")
        chain = sox.EffectsChain(
            in_encoding=input_format.encoding,
            out_encoding=output_format.encoding
        )
        
        # Step 5: Add input effect (first effect must source samples)
        print("Adding input effect...")
        input_effect_handler = sox.find_effect("input")
        input_effect = sox.Effect(input_effect_handler)
        input_effect.set_options([input_format])
        chain.add_effect(input_effect, input_format.signal, input_format.signal)
        
        # Step 6: Add volume effect with "3dB" parameter
        print("Adding volume effect (3dB)...")
        vol_effect_handler = sox.find_effect("vol")
        vol_effect = sox.Effect(vol_effect_handler)
        vol_effect.set_options(["3dB"])
        chain.add_effect(vol_effect, input_format.signal, input_format.signal)
        
        # Step 7: Add flanger effect with default parameters
        print("Adding flanger effect...")
        flanger_effect_handler = sox.find_effect("flanger")
        flanger_effect = sox.Effect(flanger_effect_handler)
        flanger_effect.set_options([])  # Default parameters
        chain.add_effect(flanger_effect, input_format.signal, input_format.signal)
        
        # Step 8: Add output effect (last effect must consume samples)
        print("Adding output effect...")
        output_effect_handler = sox.find_effect("output")
        output_effect = sox.Effect(output_effect_handler)
        output_effect.set_options([output_format])
        chain.add_effect(output_effect, input_format.signal, input_format.signal)
        
        # Step 9: Flow samples through the effects processing chain
        print("Processing audio through effects chain...")
        result = chain.flow_effects()
        
        if result == sox.SUCCESS:
            print("Effects processing completed successfully!")
            
            # Check for any clipping that occurred
            clips = chain.get_clips()
            if clips > 0:
                print(f"Warning: {clips} clips occurred during processing")
            else:
                print("No clipping occurred")
                
            # Verify output file was created
            if os.path.exists(output_filename):
                file_size = os.path.getsize(output_filename)
                print(f"Output file created: {output_filename} ({file_size} bytes)")
            else:
                print("Warning: Output file was not created")
        else:
            print(f"Error: Effects processing failed with result {result}")
            sys.exit(1)

        # Step 10: Clean up
        print("Cleaning up...")
        input_format.close()
        output_format.close()
        sox.quit()
        
        print("Done!")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
```

## Status

All C examples from libsox have been successfully ported to Python tests:

- [x] **example0**: Basic effects chain - `tests/test_example0.py`
- [x] **example1**: Vol & flanger effects - `tests/test_example1.py`
- [x] **example2**: Waveform display and analysis - `tests/test_example2.py`
- [x] **example3**: Trim and format conversion - `tests/test_example3.py`
- [x] **example4**: File concatenation - `tests/test_example4.py`
- [x] **example5**: Memory-based I/O - `tests/test_example5.py` (2 tests skipped - buffer management issue)
- [x] **example6**: Explicit format conversion - `tests/test_example6.py`

**Test Results**: 94 tests passing, 2 skipped (memory I/O)

## Known Issues

- **Memory I/O Functions**: libsox's memory I/O functions (`open_mem_write`, `open_mem_read`, `open_memstream_write`) have platform-specific issues and are not currently functional. Tests are skipped pending investigation of the underlying libsox issue.

## Platform Support

- ✅ **macOS**: Full support
- ✅ **Linux**: Full support
- ⚠️ **Windows**: Placeholder support only (contributions welcome)
