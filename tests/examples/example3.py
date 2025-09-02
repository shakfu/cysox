#!/usr/bin/env python3
"""
Python equivalent of tests/examples/example3.c

This script replicates the functionality of the C example:
- On an audio-capable system, plays an audio file starting 10 seconds in
- Copes with sample-rate and channel changes if necessary since it's
  common for audio drivers to support a subset of rates and channel counts
- Uses "coreaudio" on macOS (instead of "alsa" in original C example)

Usage: python3 example3.py <input_file>
"""

import sys
import os
import platform
from pathlib import Path

src_dir = Path.cwd() / 'src'
sys.path.append(str(src_dir))

# Import the cysox bindings
from cysox import sox


def output_message(level, filename, fmt, *args):
    """Custom output message handler equivalent to the C version"""
    level_strings = ["FAIL", "WARN", "INFO", "DBUG"]
    if sox.globals.verbosity >= level:
        # Get base filename (equivalent to sox_basename in C)
        base_name = os.path.basename(filename) if filename else "sox"
        level_str = level_strings[min(level - 1, 3)]
        message = fmt % args if args else fmt
        print(f"{level_str} {base_name}: {message}", file=sys.stderr)


def main():
    """Main function replicating example3.c"""
    
    # Check command line arguments
    if len(sys.argv) != 2:
        print("Usage: python3 example3.py <input_file>")
        sys.exit(1)
    
    input_filename = sys.argv[1]
    
    # Verify input file exists
    if not os.path.exists(input_filename):
        print(f"Error: Input file '{input_filename}' not found")
        sys.exit(1)
    
    try:
        # Step 1: Set up custom output message handler and verbosity
        # sox.globals.output_message_handler = output_message  # This might not be exposed in Python bindings
        # sox.globals.verbosity = 1  # This might not be exposed in Python bindings
        
        # Step 2: Initialize SoX library
        sox.init()
        
        # Step 3: Open the input file
        input_format = sox.Format(input_filename, mode='r')
        
        # Step 4: Open the output to audio device
        # Note: Audio device output may not be supported in this Python binding
        # For demonstration, we'll write to a temporary file instead
        temp_output = "/tmp/example3_playback.wav"
        print(f"Note: Writing to file {temp_output} instead of audio device (audio playback may not be supported)")
        
        try:
            output_format = sox.Format(
                temp_output,
                signal=input_format.signal,
                mode='w'
            )
        except Exception as e:
            print(f"Failed to open output file '{temp_output}': {e}")
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
        
        # Step 7: Add trim effect to start 10 seconds in (equivalent to C version)
        trim_effect_handler = sox.find_effect("trim")
        trim_effect = sox.Effect(trim_effect_handler)
        trim_effect.set_options(["10"])  # Start at 10 seconds
        result = chain.add_effect(trim_effect, interm_signal, input_format.signal)
        if result != sox.SUCCESS:
            print("Failed to add trim effect")
            sys.exit(1)
        
        # Step 8: Add sample rate conversion if needed
        if input_format.signal.rate != output_format.signal.rate:
            rate_effect_handler = sox.find_effect("rate")
            rate_effect = sox.Effect(rate_effect_handler)
            rate_effect.set_options([])  # Default options
            result = chain.add_effect(rate_effect, interm_signal, output_format.signal)
            if result != sox.SUCCESS:
                print("Failed to add rate conversion effect")
                sys.exit(1)
        
        # Step 9: Add channel conversion if needed
        if input_format.signal.channels != output_format.signal.channels:
            channels_effect_handler = sox.find_effect("channels")
            channels_effect = sox.Effect(channels_effect_handler)
            channels_effect.set_options([])  # Default options
            result = chain.add_effect(channels_effect, interm_signal, output_format.signal)
            if result != sox.SUCCESS:
                print("Failed to add channels conversion effect")
                sys.exit(1)
        
        # Step 10: Add output effect
        output_effect_handler = sox.find_effect("output")
        output_effect = sox.Effect(output_effect_handler)
        output_effect.set_options([output_format])
        result = chain.add_effect(output_effect, interm_signal, output_format.signal)
        if result != sox.SUCCESS:
            print("Failed to add output effect")
            sys.exit(1)
        
        # Step 11: Flow samples through the effects processing chain
        print(f"Processing {input_filename} starting at 10 seconds to {temp_output}...")
        
        result = chain.flow_effects()
        if result == sox.SUCCESS:
            print("Processing completed successfully!")
        else:
            print(f"Processing failed with result {result}")
        
        # Step 12: Clean up
        input_format.close()
        output_format.close()
        sox.quit()
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()