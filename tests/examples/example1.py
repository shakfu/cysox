#!/usr/bin/env python3
"""
Python equivalent of tests/examples/example1.c

This script replicates the functionality of the C example:
- Reads input file, applies vol & flanger effects, stores in output file
- Uses custom input and output effect handlers like the C version
- Demonstrates vol effect with "3dB" parameter and flanger with default parameters

Usage: python3 example1.py <input_file> <output_file>
"""

import sys
import os
from pathlib import Path

src_dir = Path.cwd() / 'src'
sys.path.append(str(src_dir))

# Import the cysox bindings
from cysox import sox


def main():
    """Main function replicating example1.c"""
    
    # Check command line arguments
    if len(sys.argv) != 3:
        print("Usage: python3 example1.py <input_file> <output_file>")
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
        
        # Step 2: Open the input file (with default parameters)
        input_format = sox.Format(input_filename, mode='r')
        
        # Step 3: Open the output file with same signal characteristics as input
        output_format = sox.Format(
            output_filename, 
            signal=input_format.signal,
            mode='w'
        )
        
        # Step 4: Create an effects chain
        chain = sox.EffectsChain(
            in_encoding=input_format.encoding,
            out_encoding=output_format.encoding
        )
        
        # Step 5: Add input effect (first effect must source samples)
        # This is equivalent to the custom input_handler() in the C version
        input_effect_handler = sox.find_effect("input")
        input_effect = sox.Effect(input_effect_handler)
        input_effect.set_options([input_format])
        result = chain.add_effect(input_effect, input_format.signal, input_format.signal)
        if result != sox.SUCCESS:
            print("Failed to add input effect")
            sys.exit(1)
        
        # Step 6: Add volume effect with "3dB" parameter
        vol_effect_handler = sox.find_effect("vol")
        vol_effect = sox.Effect(vol_effect_handler)
        vol_effect.set_options(["3dB"])
        result = chain.add_effect(vol_effect, input_format.signal, input_format.signal)
        if result != sox.SUCCESS:
            print("Failed to add volume effect")
            sys.exit(1)
        
        # Step 7: Add flanger effect with default parameters (empty options)
        flanger_effect_handler = sox.find_effect("flanger")
        flanger_effect = sox.Effect(flanger_effect_handler)
        flanger_effect.set_options([])  # Default parameters (equivalent to NULL in C)
        result = chain.add_effect(flanger_effect, input_format.signal, input_format.signal)
        if result != sox.SUCCESS:
            print("Failed to add flanger effect")
            sys.exit(1)
        
        # Step 8: Add output effect (last effect must consume samples)
        # This is equivalent to the custom output_handler() in the C version
        output_effect_handler = sox.find_effect("output")
        output_effect = sox.Effect(output_effect_handler)
        output_effect.set_options([output_format])
        result = chain.add_effect(output_effect, input_format.signal, input_format.signal)
        if result != sox.SUCCESS:
            print("Failed to add output effect")
            sys.exit(1)
        
        # Step 9: Flow samples through the effects processing chain until EOF
        result = chain.flow_effects()
        
        if result == sox.SUCCESS:
            print("Effects processing completed successfully!")
        else:
            print(f"Error: Effects processing failed with result {result}")
            sys.exit(1)
        
        # Step 10: Clean up (equivalent to C version cleanup)
        # Note: Python's garbage collection will handle cleanup, but we'll be explicit
        input_format.close()
        output_format.close()
        sox.quit()
        
        print(f"Successfully processed {input_filename} -> {output_filename}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()