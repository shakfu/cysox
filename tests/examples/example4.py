#!/usr/bin/env python3
"""
Python equivalent of tests/examples/example4.c

This script replicates the functionality of the C example:
- Concatenates audio files. Note that the files must have the same number
  of channels and the same sample rate.

Usage: python3 example4.py input-1 input-2 [... input-n] output
"""

import sys
import os
from pathlib import Path

src_dir = Path.cwd() / 'src'
sys.path.append(str(src_dir))

# Import the cysox bindings
from cysox import sox


def main():
    """Main function replicating example4.c"""
    
    # Check command line arguments - need at least 2 input files + 1 output file
    if len(sys.argv) < 4:
        print("Usage: python3 example4.py input-1 input-2 [... input-n] output")
        print("Need at least 2 input files + 1 output file.")
        sys.exit(1)
    
    input_filenames = sys.argv[1:-1]  # All arguments except the last one
    output_filename = sys.argv[-1]    # Last argument is output file
    
    # Verify all input files exist
    for filename in input_filenames:
        if not os.path.exists(filename):
            print(f"Error: Input file '{filename}' not found")
            sys.exit(1)
    
    output_format = None
    
    try:
        # Step 1: Initialize SoX library
        sox.init()
        
        # Defer opening the output file as we want to set its characteristics
        # based on those of the input files.
        first_input_channels = None  # Will store characteristics from first file
        first_input_rate = None
        
        # Step 2: Process each input file
        for i, input_filename in enumerate(input_filenames):
            print(f"Processing input file {i+1}/{len(input_filenames)}: {input_filename}")
            
            # Open this input file
            try:
                input_format = sox.Format(input_filename, mode='r')
            except Exception as e:
                print(f"Failed to open input file '{input_filename}': {e}")
                sys.exit(1)
            
            if i == 0:  # If this is the first input file
                # Store the signal characteristics for comparison with other files
                first_input_channels = input_format.signal.channels
                first_input_rate = input_format.signal.rate
                
                # Open the output file using the same signal and encoding characteristics
                # as the first input file
                try:
                    output_format = sox.Format(
                        output_filename,
                        signal=input_format.signal,
                        encoding=input_format.encoding,
                        mode='w'
                    )
                except Exception as e:
                    print(f"Failed to open output file '{output_filename}': {e}")
                    input_format.close()
                    sys.exit(1)
            else:  # Second or subsequent input file
                # Check that this input file's signal matches that of the first file
                if input_format.signal.channels != first_input_channels:
                    print(f"Error: Channel mismatch - first file has {first_input_channels} channels, "
                          f"but '{input_filename}' has {input_format.signal.channels} channels")
                    input_format.close()
                    sys.exit(1)
                
                if input_format.signal.rate != first_input_rate:
                    print(f"Error: Sample rate mismatch - first file has {first_input_rate} Hz, "
                          f"but '{input_filename}' has {input_format.signal.rate} Hz")
                    input_format.close()
                    sys.exit(1)
            
            # Step 3: Copy all of the audio from this input file to the output file
            # The maximum number of samples that we shall read/write at a time
            MAX_SAMPLES = 2048
            
            while True:
                samples = input_format.read(MAX_SAMPLES)
                if not samples:  # EOF or error
                    break
                
                number_written = output_format.write(samples)
                if number_written != len(samples):
                    print(f"Error: Failed to write all samples to output file. "
                          f"Wrote {number_written} out of {len(samples)} samples")
                    input_format.close()
                    sys.exit(1)
            
            # Close this input file
            input_format.close()
            print(f"  Completed processing {input_filename}")
        
        # Step 4: Close output file and clean up
        if output_format:
            output_format.close()
        
        result = sox.quit()
        if result != sox.SUCCESS:
            print("Warning: SoX cleanup returned error")
        
        print(f"Successfully concatenated {len(input_filenames)} files into '{output_filename}'")
        
        # Verify output file was created and has reasonable size
        if os.path.exists(output_filename):
            file_size = os.path.getsize(output_filename)
            print(f"Output file size: {file_size} bytes")
        else:
            print("Warning: Output file was not created")
        
    except Exception as e:
        print(f"Error: {e}")
        # Clean up on error - truncate output file
        if output_format:
            try:
                output_format.close()
            except:
                pass
        
        # Truncate output file on error (equivalent to C version)
        try:
            with open(output_filename, 'w'):
                pass  # This truncates the file
        except:
            pass
        
        sys.exit(1)


if __name__ == "__main__":
    main()