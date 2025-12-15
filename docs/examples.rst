Examples
========

This section contains complete examples demonstrating various cysox features.

Example 1: Basic Effects Chain
------------------------------

Apply volume boost and flanger effect to an audio file:

.. code-block:: python

   import cysox as sox

   def apply_effects(input_path, output_path):
       sox.init()

       try:
           # Open input file
           input_fmt = sox.Format(input_path)

           # Create output with same signal properties
           output_fmt = sox.Format(
               output_path,
               signal=input_fmt.signal,
               mode='w'
           )

           # Create effects chain
           chain = sox.EffectsChain(
               in_encoding=input_fmt.encoding,
               out_encoding=output_fmt.encoding
           )

           # Input effect
           e = sox.Effect(sox.find_effect("input"))
           e.set_options([input_fmt])
           chain.add_effect(e, input_fmt.signal, input_fmt.signal)

           # Volume boost (+3dB)
           e = sox.Effect(sox.find_effect("vol"))
           e.set_options(["3dB"])
           chain.add_effect(e, input_fmt.signal, input_fmt.signal)

           # Flanger effect
           e = sox.Effect(sox.find_effect("flanger"))
           e.set_options([])
           chain.add_effect(e, input_fmt.signal, input_fmt.signal)

           # Output effect
           e = sox.Effect(sox.find_effect("output"))
           e.set_options([output_fmt])
           chain.add_effect(e, input_fmt.signal, input_fmt.signal)

           # Process
           chain.flow_effects()

           input_fmt.close()
           output_fmt.close()

       finally:
           sox.quit()

   if __name__ == "__main__":
       apply_effects("input.wav", "output.wav")

Example 2: Format Conversion
----------------------------

Convert between audio formats (e.g., WAV to FLAC):

.. code-block:: python

   import cysox as sox

   def convert_format(input_path, output_path):
       sox.init()

       try:
           input_fmt = sox.Format(input_path)

           # Output format is determined by file extension
           output_fmt = sox.Format(
               output_path,
               signal=input_fmt.signal,
               mode='w'
           )

           chain = sox.EffectsChain(
               in_encoding=input_fmt.encoding,
               out_encoding=output_fmt.encoding
           )

           # Minimal chain: input -> output
           e = sox.Effect(sox.find_effect("input"))
           e.set_options([input_fmt])
           chain.add_effect(e, input_fmt.signal, input_fmt.signal)

           e = sox.Effect(sox.find_effect("output"))
           e.set_options([output_fmt])
           chain.add_effect(e, input_fmt.signal, input_fmt.signal)

           chain.flow_effects()

           input_fmt.close()
           output_fmt.close()

       finally:
           sox.quit()

   if __name__ == "__main__":
       convert_format("audio.wav", "audio.flac")

Example 3: Trimming Audio
-------------------------

Extract a portion of an audio file:

.. code-block:: python

   import cysox as sox

   def trim_audio(input_path, output_path, start_seconds, duration_seconds):
       sox.init()

       try:
           input_fmt = sox.Format(input_path)

           output_fmt = sox.Format(
               output_path,
               signal=input_fmt.signal,
               mode='w'
           )

           chain = sox.EffectsChain(
               in_encoding=input_fmt.encoding,
               out_encoding=output_fmt.encoding
           )

           # Input
           e = sox.Effect(sox.find_effect("input"))
           e.set_options([input_fmt])
           chain.add_effect(e, input_fmt.signal, input_fmt.signal)

           # Trim effect: start=Xs, duration=Ys
           e = sox.Effect(sox.find_effect("trim"))
           e.set_options([str(start_seconds), str(duration_seconds)])
           chain.add_effect(e, input_fmt.signal, input_fmt.signal)

           # Output
           e = sox.Effect(sox.find_effect("output"))
           e.set_options([output_fmt])
           chain.add_effect(e, input_fmt.signal, input_fmt.signal)

           chain.flow_effects()

           input_fmt.close()
           output_fmt.close()

       finally:
           sox.quit()

   if __name__ == "__main__":
       # Extract 10 seconds starting at 5 seconds
       trim_audio("input.wav", "trimmed.wav", 5, 10)

Example 4: Sample Rate Conversion
---------------------------------

Change the sample rate of an audio file:

.. code-block:: python

   import cysox as sox

   def resample(input_path, output_path, target_rate):
       sox.init()

       try:
           input_fmt = sox.Format(input_path)

           # Create output signal with new sample rate
           out_signal = sox.SignalInfo(
               rate=target_rate,
               channels=input_fmt.signal.channels,
               precision=input_fmt.signal.precision
           )

           output_fmt = sox.Format(
               output_path,
               signal=out_signal,
               mode='w'
           )

           chain = sox.EffectsChain(
               in_encoding=input_fmt.encoding,
               out_encoding=output_fmt.encoding
           )

           # Input
           e = sox.Effect(sox.find_effect("input"))
           e.set_options([input_fmt])
           chain.add_effect(e, input_fmt.signal, input_fmt.signal)

           # Rate conversion
           e = sox.Effect(sox.find_effect("rate"))
           e.set_options(["-v", str(target_rate)])  # -v for very high quality
           chain.add_effect(e, input_fmt.signal, out_signal)

           # Output
           e = sox.Effect(sox.find_effect("output"))
           e.set_options([output_fmt])
           chain.add_effect(e, out_signal, out_signal)

           chain.flow_effects()

           input_fmt.close()
           output_fmt.close()

       finally:
           sox.quit()

   if __name__ == "__main__":
       resample("input.wav", "resampled.wav", 48000)

Example 5: Reading with NumPy
-----------------------------

Use the buffer protocol for efficient NumPy integration:

.. code-block:: python

   import numpy as np
   import cysox as sox

   def read_as_numpy(input_path):
       sox.init()

       try:
           with sox.Format(input_path) as f:
               # Calculate total samples
               total_samples = f.signal.length

               # Read all samples using buffer protocol
               buf = f.read_buffer(total_samples)

               # Convert to NumPy array (zero-copy view)
               samples = np.frombuffer(buf, dtype=np.int32)

               # Reshape for multi-channel audio
               if f.signal.channels > 1:
                   samples = samples.reshape(-1, f.signal.channels)

               return samples, f.signal.rate

       finally:
           sox.quit()

   if __name__ == "__main__":
       samples, rate = read_as_numpy("input.wav")
       print(f"Shape: {samples.shape}, Rate: {rate} Hz")

Example 6: Available Effects
----------------------------

List all available effects:

.. code-block:: python

   import cysox as sox

   def list_effects():
       sox.init()

       # Common effects to check
       effects = [
           "vol", "gain", "bass", "treble", "equalizer",
           "reverb", "echo", "chorus", "flanger", "phaser",
           "speed", "tempo", "pitch", "stretch",
           "trim", "pad", "fade", "silence",
           "highpass", "lowpass", "bandpass",
           "compand", "contrast", "loudness",
           "rate", "channels", "remix",
       ]

       print("Available effects:")
       for name in effects:
           handler = sox.find_effect(name)
           if handler:
               usage = handler.usage or "(no parameters)"
               print(f"  {name}: {usage}")

       sox.quit()

   if __name__ == "__main__":
       list_effects()
