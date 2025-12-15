Quick Start Guide
=================

This guide covers the basic usage of cysox for common audio processing tasks.

Initialization
--------------

Before using any cysox functions, you must initialize the library:

.. code-block:: python

   import cysox as sox

   sox.init()

   # ... use cysox ...

   sox.quit()

Reading Audio Files
-------------------

Basic Reading
~~~~~~~~~~~~~

.. code-block:: python

   import cysox as sox

   sox.init()

   # Open a file for reading
   with sox.Format('input.wav') as f:
       # Access file properties
       print(f"Filename: {f.filename}")
       print(f"Format: {f.filetype}")
       print(f"Sample rate: {f.signal.rate} Hz")
       print(f"Channels: {f.signal.channels}")
       print(f"Precision: {f.signal.precision} bits")
       print(f"Total samples: {f.signal.length}")

       # Read samples into a list
       samples = f.read(1024)
       print(f"Read {len(samples)} samples")

   sox.quit()

Zero-Copy Reading with Buffer Protocol
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For better performance with large files, use the buffer protocol:

.. code-block:: python

   import array
   import cysox as sox

   sox.init()

   with sox.Format('input.wav') as f:
       # Option 1: Get a memoryview
       buf = f.read_buffer(1024)

       # Option 2: Read into a pre-allocated buffer
       arr = array.array('i', [0] * 1024)
       n = f.read_into(arr)
       print(f"Read {n} samples into array")

   sox.quit()

Writing Audio Files
-------------------

.. code-block:: python

   import cysox as sox

   sox.init()

   # Define output signal properties
   signal = sox.SignalInfo(
       rate=44100,      # 44.1 kHz
       channels=2,      # Stereo
       precision=16     # 16-bit
   )

   # Create output file
   with sox.Format('output.wav', signal=signal, mode='w') as f:
       # Write samples (list of integers)
       samples = [100, -100, 200, -200] * 1000
       f.write(samples)

   sox.quit()

Applying Effects
----------------

cysox provides access to all libsox effects through an effects chain:

.. code-block:: python

   import cysox as sox

   sox.init()

   # Open input and output files
   input_fmt = sox.Format('input.wav')
   output_fmt = sox.Format(
       'output.wav',
       signal=input_fmt.signal,
       mode='w'
   )

   # Create effects chain
   chain = sox.EffectsChain(
       in_encoding=input_fmt.encoding,
       out_encoding=output_fmt.encoding
   )

   # Add input effect (required first)
   input_handler = sox.find_effect("input")
   input_effect = sox.Effect(input_handler)
   input_effect.set_options([input_fmt])
   chain.add_effect(input_effect, input_fmt.signal, input_fmt.signal)

   # Add volume effect (+3dB)
   vol_handler = sox.find_effect("vol")
   vol_effect = sox.Effect(vol_handler)
   vol_effect.set_options(["3dB"])
   chain.add_effect(vol_effect, input_fmt.signal, input_fmt.signal)

   # Add output effect (required last)
   output_handler = sox.find_effect("output")
   output_effect = sox.Effect(output_handler)
   output_effect.set_options([output_fmt])
   chain.add_effect(output_effect, input_fmt.signal, input_fmt.signal)

   # Process audio
   chain.flow_effects()

   # Cleanup
   input_fmt.close()
   output_fmt.close()
   sox.quit()

Progress Callbacks
------------------

Monitor processing progress with callbacks:

.. code-block:: python

   import cysox as sox

   def progress_callback(all_done, user_data):
       if all_done:
           print("Processing complete!")
       else:
           user_data['count'] += 1
           if user_data['count'] % 100 == 0:
               print(f"Processing... ({user_data['count']} buffers)")
       return True  # Continue processing

   sox.init()

   # ... set up chain ...

   chain.flow_effects(
       callback=progress_callback,
       client_data={'count': 0}
   )

   sox.quit()

Error Handling
--------------

cysox uses a custom exception hierarchy:

.. code-block:: python

   import cysox as sox

   sox.init()

   try:
       f = sox.Format('nonexistent.wav')
   except sox.SoxFormatError as e:
       print(f"Format error: {e}")
   except sox.SoxError as e:
       print(f"General error: {e}")

   sox.quit()

Available exceptions:

- ``SoxError`` - Base exception for all cysox errors
- ``SoxInitError`` - Initialization failures
- ``SoxFormatError`` - File format errors
- ``SoxEffectError`` - Effect processing errors
- ``SoxIOError`` - I/O operation errors
- ``SoxMemoryError`` - Memory allocation errors
