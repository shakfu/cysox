#!/usr/bin/env python3
"""
Python equivalent of tests/examples/example2.c

This script replicates the functionality of the C example:
- Reads input file and displays a few seconds of wave-form, starting from
  a given time through the audio
- Displays stereo audio as left and right channel peaks over time
- Requires stereo (2 channel) input audio

Usage: python3 example2.py <input_file> [start_seconds] [display_period_seconds]
Example: python3 example2.py song2.au 30.75 1
"""

import sys
import os
import math
from pathlib import Path

src_dir = Path.cwd() / 'src'
sys.path.append(str(src_dir))

# Import the cysox bindings  
from cysox import sox
# Note: Using simple conversion instead of utils function


def main():
    """Main function replicating example2.c"""
    
    # Check command line arguments
    if len(sys.argv) < 2:
        print("Usage: python3 example2.py <input_file> [start_seconds] [display_period_seconds]")
        sys.exit(1)
    
    input_filename = sys.argv[1]
    start_secs = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
    period = float(sys.argv[3]) if len(sys.argv) > 3 else 2.0
    
    # Period of audio over which we will measure its volume in order to display the wave-form
    block_period = 0.025  # seconds
    
    # Verify input file exists
    if not os.path.exists(input_filename):
        print(f"Error: Input file '{input_filename}' not found")
        sys.exit(1)
    
    try:
        # Step 1: Initialize SoX library
        sox.init()
        
        # Step 2: Open the input file (with default parameters)
        input_format = sox.Format(input_filename, mode='r')
        
        # Step 3: This example program requires that the audio has precisely 2 channels
        if input_format.signal.channels != 2:
            print(f"Error: This example requires stereo (2 channel) audio, got {input_format.signal.channels} channels")
            input_format.close()
            sox.quit()
            sys.exit(1)
        
        # Step 4: Calculate the start position in number of samples
        seek = int(start_secs * input_format.signal.rate * input_format.signal.channels + 0.5)
        # Make sure that this is at a 'wide sample' boundary (multiple of channels)
        seek -= seek % input_format.signal.channels
        
        # Step 5: Move the file pointer to the desired starting position
        result = input_format.seek(seek)
        if result != sox.SUCCESS:
            print("Failed to seek to starting position")
            input_format.close()
            sox.quit()
            sys.exit(1)
        
        # Step 6: Convert block size (in seconds) to a number of samples
        block_size = int(block_period * input_format.signal.rate * input_format.signal.channels + 0.5)
        # Make sure that this is at a 'wide sample' boundary
        block_size -= block_size % input_format.signal.channels
        
        # Step 7: Read and process blocks of audio for the selected period or until EOF
        blocks = 0
        line = "==================================="  # 35 characters for scale
        
        while blocks * block_period < period:
            # Read a block of samples
            samples = input_format.read(block_size)
            if len(samples) != block_size:
                break  # EOF or error
            
            # Calculate peak volumes for left and right channels
            left_peak = 0.0
            right_peak = 0.0
            
            for i in range(0, len(samples), input_format.signal.channels):
                # Convert samples from SoX's internal format to float for processing
                # Simple conversion: SoX samples are typically 32-bit integers, normalize to [-1,1]
                left_sample = float(samples[i]) / (2**31 - 1)  # Assuming 32-bit samples
                right_sample = float(samples[i + 1]) / (2**31 - 1)
                
                # Find the peak volume in the block
                left_peak = max(left_peak, abs(left_sample))
                right_peak = max(right_peak, abs(right_sample))
            
            # Build up the wave form by displaying the left & right channel
            # volume as a line length (inverted so louder = longer line)
            l = int((1 - left_peak) * 35 + 0.5)
            r = int((1 - right_peak) * 35 + 0.5)
            
            current_time = start_secs + blocks * block_period
            print(f"{current_time:8.3f}{line[l:]}|{line[r:]}")
            
            blocks += 1
        
        # Step 8: Clean up
        input_format.close()
        sox.quit()
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()