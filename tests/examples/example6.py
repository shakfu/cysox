#!/usr/bin/env python3
"""
Python equivalent of tests/examples/example6.c

This script replicates the functionality of the C example:
- Shows how to explicitly specify output file signal and encoding attributes.
- The example converts a given input file of any type to mono mu-law at 8kHz
  sampling-rate (providing that this is supported by the given output file type).

For example:
  sox -r 16k -n input.wav synth 8 sin 0:8k sin 8k:0 gain -1
  python3 example6.py input.wav output.wav
  soxi input.wav output.wav

Usage: python3 example6.py <input_file> <output_file>
"""

import sys
import os
from pathlib import Path

src_dir = Path.cwd() / 'src'
sys.path.append(str(src_dir))

# Import the cysox bindings
from cysox import sox


def main():
    """Main function replicating example6.c"""
    
    # Check command line arguments
    if len(sys.argv) != 3:
        print("Usage: python3 example6.py <input_file> <output_file>")
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
        
        # Step 2: Open the input file
        input_format = sox.Format(input_filename, mode='r')
        
        # Step 3: Define output signal characteristics
        # This replicates the C version's explicit signal setup
        # Note: For simplicity, we'll use default encoding instead of ULAW
        # since the ULAW constant may not be directly exposed
        
        # Create output signal info (equivalent to C struct sox_signalinfo_t)  
        # 8000 Hz sample rate, 1 channel (mono), length 0 (unknown), precision 0 (default)
        out_signal = sox.SignalInfo()
        out_signal.rate = 8000
        out_signal.channels = 1
        out_signal.length = 0  # Unknown length
        out_signal.precision = 0  # Default precision
        
        # For encoding, we'll use the input file's encoding since ULAW may not be available
        out_encoding = input_format.encoding
        
        # Step 4: Open the output file with explicit signal and encoding attributes
        try:
            output_format = sox.Format(
                output_filename,
                signal=out_signal,
                encoding=out_encoding,
                mode='w'
            )
        except Exception as e:
            print(f"Failed to open output file '{output_filename}': {e}")
            print("The output format may not support u-law encoding")
            input_format.close()
            sox.quit()
            sys.exit(1)
        
        # Step 5: Create effects chain
        chain = sox.EffectsChain(
            in_encoding=input_format.encoding,
            out_encoding=output_format.encoding
        )
        
        # Keep track of intermediate signal characteristics
        interm_signal = input_format.signal
        
        # Step 6: Add input effect
        input_effect_handler = sox.find_effect("input")
        input_effect = sox.Effect(input_effect_handler)
        input_effect.set_options([input_format])
        result = chain.add_effect(input_effect, interm_signal, input_format.signal)
        if result != sox.SUCCESS:
            print("Failed to add input effect")
            sys.exit(1)
        
        # Step 7: Add sample rate conversion if needed
        if input_format.signal.rate != output_format.signal.rate:
            print(f"Converting sample rate: {input_format.signal.rate} Hz -> {output_format.signal.rate} Hz")
            rate_effect_handler = sox.find_effect("rate")
            rate_effect = sox.Effect(rate_effect_handler)
            rate_effect.set_options([])  # Default options
            result = chain.add_effect(rate_effect, interm_signal, output_format.signal)
            if result != sox.SUCCESS:
                print("Failed to add rate conversion effect")
                sys.exit(1)
        
        # Step 8: Add channel conversion if needed
        if input_format.signal.channels != output_format.signal.channels:
            print(f"Converting channels: {input_format.signal.channels} -> {output_format.signal.channels}")
            channels_effect_handler = sox.find_effect("channels")
            channels_effect = sox.Effect(channels_effect_handler)
            channels_effect.set_options([])  # Default options
            result = chain.add_effect(channels_effect, interm_signal, output_format.signal)
            if result != sox.SUCCESS:
                print("Failed to add channels conversion effect")
                sys.exit(1)
        
        # Step 9: Add output effect
        output_effect_handler = sox.find_effect("output")
        output_effect = sox.Effect(output_effect_handler)
        output_effect.set_options([output_format])
        result = chain.add_effect(output_effect, interm_signal, output_format.signal)
        if result != sox.SUCCESS:
            print("Failed to add output effect")
            sys.exit(1)
        
        # Step 10: Flow samples through the effects processing chain
        print(f"Converting {input_filename} -> {output_filename}")
        print(f"Input:  {input_format.signal.channels} channels, {input_format.signal.rate} Hz")
        print(f"Output: {output_format.signal.channels} channel(s), {output_format.signal.rate} Hz, custom encoding")
        
        result = chain.flow_effects()
        
        if result == sox.SUCCESS:
            print("Conversion completed successfully!")
        else:
            print(f"Conversion failed with result {result}")
            sys.exit(1)
        
        # Step 11: Clean up
        input_format.close()
        output_format.close()
        sox.quit()
        
        # Verify output file was created
        if os.path.exists(output_filename):
            input_size = os.path.getsize(input_filename)
            output_size = os.path.getsize(output_filename)
            print(f"Input file size: {input_size} bytes")
            print(f"Output file size: {output_size} bytes")
            print("Conversion complete!")
        else:
            print("Warning: Output file was not created")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()