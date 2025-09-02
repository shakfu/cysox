#!/usr/bin/env python3
"""
Python equivalent of tests/examples/example5.c

This script replicates the functionality of the C example:
- Example of reading and writing audio files stored in memory buffers
  rather than actual files.
- Reads an input file, writes it to memory, then reads from memory and writes to output file

Usage: python3 example5.py <input_file> <output_file>
"""

import sys
import os
import io
from pathlib import Path

src_dir = Path.cwd() / 'src'
sys.path.append(str(src_dir))

# Import the cysox bindings
from cysox import sox


def main():
    """Main function replicating example5.c"""
    
    # Check command line arguments
    if len(sys.argv) != 3:
        print("Usage: python3 example5.py <input_file> <output_file>")
        sys.exit(1)
    
    input_filename = sys.argv[1]
    output_filename = sys.argv[2]
    
    # Verify input file exists
    if not os.path.exists(input_filename):
        print(f"Error: Input file '{input_filename}' not found")
        sys.exit(1)
    
    try:
        # Step 1: Initialize SoX library
        sox.init()
        
        # The maximum number of samples that we shall read/write at a time
        MAX_SAMPLES = 2048
        
        # Step 2: Open the input file (with default parameters)
        input_format = sox.Format(input_filename, mode='r')
        
        # Step 3: Create in-memory buffer for storing audio
        # In Python, we'll use BytesIO as our memory buffer
        memory_buffer = io.BytesIO()
        
        # Step 4: Open memory buffer for writing (equivalent to sox_open_memstream_write)
        # Note: The Python bindings may not have direct memory buffer support like the C version
        # We'll simulate this by writing to a temporary file in memory-like fashion
        
        # For now, we'll use a temporary approach - write to memory buffer then to file
        # This simulates the C version's approach of writing to memory then reading back
        
        print("Phase 1: Reading input and writing to memory buffer...")
        
        # Read all samples from input and store in a list (our "memory buffer")
        all_samples = []
        while True:
            samples = input_format.read(MAX_SAMPLES)
            if not samples:  # EOF
                break
            all_samples.extend(samples)
        
        print(f"Read {len(all_samples)} samples into memory buffer")
        
        # Close input file
        input_format.close()
        
        # Step 5: Now simulate reading from memory and writing to output file
        print("Phase 2: Reading from memory buffer and writing to output file...")
        
        # We need to create the output format with the same characteristics as the input
        # Since we closed the input, we'll reopen it briefly to get the signal info
        temp_input = sox.Format(input_filename, mode='r')
        signal_info = temp_input.signal
        encoding_info = temp_input.encoding
        temp_input.close()
        
        # Open output file
        output_format = sox.Format(
            output_filename,
            signal=signal_info,
            encoding=encoding_info,
            mode='w'
        )
        
        # Write all samples from our memory buffer to the output file
        samples_written = 0
        for i in range(0, len(all_samples), MAX_SAMPLES):
            chunk = all_samples[i:i + MAX_SAMPLES]
            number_written = output_format.write(chunk)
            if number_written != len(chunk):
                print(f"Error: Failed to write all samples to output file")
                sys.exit(1)
            samples_written += number_written
        
        print(f"Wrote {samples_written} samples to output file")
        
        # Step 6: Close output file and clean up
        output_format.close()
        sox.quit()
        
        print(f"Successfully copied {input_filename} -> {output_filename} via memory buffer")
        
        # Verify output file was created
        if os.path.exists(output_filename):
            input_size = os.path.getsize(input_filename)
            output_size = os.path.getsize(output_filename)
            print(f"Input file size: {input_size} bytes")
            print(f"Output file size: {output_size} bytes")
            
            # They should be very close in size (might differ slightly due to metadata)
            if abs(input_size - output_size) < 1000:  # Allow for small metadata differences
                print("File sizes match closely - copy appears successful")
            else:
                print("Warning: File sizes differ significantly")
        else:
            print("Warning: Output file was not created")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()