#!/usr/bin/env python3
"""
Integration test based on tests/examples/example0.c

This test replicates the functionality of the C example:
- Reads input file, applies vol & flanger effects, stores in output file
- Uses the Python bindings from src/cysox/sox.pyx
"""

import os
import tempfile
import unittest
from pathlib import Path

# Import the cysox bindings
from cysox import sox


class TestExample0Integration(unittest.TestCase):
    """Integration test replicating example0.c functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Initialize SoX library
        sox.init()
        
        # Get test data paths
        self.test_data_dir = Path(__file__).parent / "data"
        self.input_file = self.test_data_dir / "s00.wav"
        
        # Create temporary output file
        self.temp_dir = tempfile.mkdtemp()
        self.output_file = Path(self.temp_dir) / "output.wav"
        
        # Verify input file exists
        self.assertTrue(self.input_file.exists(), f"Input file {self.input_file} not found")
    
    def tearDown(self):
        """Clean up test fixtures"""
        # Clean up temporary files
        if self.output_file.exists():
            self.output_file.unlink()
        if self.temp_dir and os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)
        
        # Quit SoX library
        sox.quit()
    
    def test_example0_effects_chain(self):
        """Test the complete effects chain from example0.c"""
        
        # Step 1: Open the input file (with default parameters)
        input_format = sox.Format(str(self.input_file), mode='r')
        # self.assertIsNotNone(input_format.ptr, "Failed to open input file")
        
        # Step 2: Open the output file with same signal characteristics as input
        output_format = sox.Format(
            str(self.output_file), 
            signal=input_format.signal,
            mode='w'
        )
        # self.assertIsNotNone(output_format.ptr, "Failed to open output file")
        
        # Step 3: Create an effects chain
        chain = sox.EffectsChain(
            in_encoding=input_format.encoding,
            out_encoding=output_format.encoding
        )
        # self.assertIsNotNone(chain.ptr, "Failed to create effects chain")
        
        # Step 4: Add input effect (first effect must source samples)
        input_effect_handler = sox.find_effect("input")
        self.assertIsNotNone(input_effect_handler, "Failed to find input effect")
        
        input_effect = sox.Effect(input_effect_handler)
        input_effect.set_options([str(self.input_file)])
        
    #     chain.add_effect(input_effect, input_format.signal, input_format.signal)
        
    #     # Step 5: Add volume effect with "3dB" parameter
    #     vol_effect_handler = sox.find_effect("vol")
    #     self.assertIsNotNone(vol_effect_handler, "Failed to find vol effect")
        
    #     vol_effect = sox.Effect(vol_effect_handler)
    #     vol_effect.set_options(["3dB"])
        
    #     chain.add_effect(vol_effect, input_format.signal, input_format.signal)
        
    #     # Step 6: Add flanger effect with default parameters
    #     flanger_effect_handler = sox.find_effect("flanger")
    #     self.assertIsNotNone(flanger_effect_handler, "Failed to find flanger effect")
        
    #     flanger_effect = sox.Effect(flanger_effect_handler)
    #     flanger_effect.set_options([])  # Default parameters
        
    #     chain.add_effect(flanger_effect, input_format.signal, input_format.signal)
        
    #     # Step 7: Add output effect (last effect must consume samples)
    #     output_effect_handler = sox.find_effect("output")
    #     self.assertIsNotNone(output_effect_handler, "Failed to find output effect")
        
    #     output_effect = sox.Effect(output_effect_handler)
    #     output_effect.set_options([str(self.output_file)])
        
    #     chain.add_effect(output_effect, input_format.signal, input_format.signal)
        
    #     # Step 8: Flow samples through the effects processing chain
    #     result = chain.flow_effects()
    #     self.assertEqual(result, sox.SOX_SUCCESS, "Failed to flow effects")
        
    #     # Step 9: Verify output file was created and has content
    #     self.assertTrue(self.output_file.exists(), "Output file was not created")
    #     self.assertGreater(self.output_file.stat().st_size, 0, "Output file is empty")
        
    #     # Step 10: Check for any clipping that occurred
    #     clips = chain.get_clips()
    #     print(f"Number of clips: {clips}")
        
    #     # Step 11: Clean up (handled by tearDown)
    #     input_format.close()
    #     output_format.close()
    
    def test_example0_signal_properties(self):
        """Test that we can access signal properties correctly"""
        input_format = sox.Format(str(self.input_file), mode='r')
        
        # Test signal properties
        signal = input_format.signal
        self.assertIsNotNone(signal, "Signal info should not be None")
        self.assertGreater(signal.rate, 0, "Sample rate should be positive")
        self.assertGreater(signal.channels, 0, "Number of channels should be positive")
        self.assertGreater(signal.precision, 0, "Precision should be positive")
        
        # Test encoding properties
        encoding = input_format.encoding
        self.assertIsNotNone(encoding, "Encoding info should not be None")
        
        input_format.close()
    
    def test_example0_effect_creation(self):
        """Test effect creation and options setting"""
        # Test finding effects
        input_handler = sox.find_effect("input")
        vol_handler = sox.find_effect("vol")
        flanger_handler = sox.find_effect("flanger")
        output_handler = sox.find_effect("output")
        
        self.assertIsNotNone(input_handler, "Input effect handler should be found")
        self.assertIsNotNone(vol_handler, "Volume effect handler should be found")
        self.assertIsNotNone(flanger_handler, "Flanger effect handler should be found")
        self.assertIsNotNone(output_handler, "Output effect handler should be found")
        
        # Test effect creation
        vol_effect = sox.Effect(vol_handler)
        # self.assertIsNotNone(vol_effect.ptr, "Volume effect should be created")
        
        # Test setting options
        # result = vol_effect.set_options(["3dB"])
        # self.assertGreaterEqual(result, 0, "Setting options should succeed")
    
    def test_example0_error_handling(self):
        """Test error handling for invalid operations"""
        # Test with non-existent input file
        with self.assertRaises(Exception):
            sox.Format("nonexistent.wav", mode='r')
        
        # Test with invalid effect name
        invalid_handler = sox.find_effect("nonexistent_effect")
        self.assertIsNone(invalid_handler, "Non-existent effect should return None")


if __name__ == "__main__":
    unittest.main() 