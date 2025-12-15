Performance Benchmarks
======================

This page documents cysox performance characteristics and provides
guidance for optimizing audio processing workflows.

Running Benchmarks
------------------

Install benchmark dependencies:

.. code-block:: bash

   pip install pytest-benchmark memory-profiler

Run all benchmarks:

.. code-block:: bash

   make benchmark

Run specific benchmark groups:

.. code-block:: bash

   # Read throughput only
   pytest tests/test_benchmarks.py -v --benchmark-only -k "TestReadThroughput"

   # Effects chain only
   pytest tests/test_benchmarks.py -v --benchmark-only -k "TestEffectsChain"

Compare benchmark runs:

.. code-block:: bash

   # Save baseline
   pytest tests/test_benchmarks.py --benchmark-save=baseline

   # Compare after changes
   pytest tests/test_benchmarks.py --benchmark-compare=baseline

Benchmark Groups
----------------

Read Throughput
~~~~~~~~~~~~~~~

Compares different methods for reading audio samples:

+---------------------------+-------------+----------------------------------+
| Method                    | Best For    | Notes                            |
+===========================+=============+==================================+
| ``read(n)``               | Small data  | Returns Python list, copies data |
+---------------------------+-------------+----------------------------------+
| ``read_buffer(n)``        | Large data  | Returns memoryview, minimal copy |
+---------------------------+-------------+----------------------------------+
| ``read_into(buffer)``     | Streaming   | Zero-copy into pre-allocated buf |
+---------------------------+-------------+----------------------------------+

**Recommendation**: Use ``read_buffer()`` or ``read_into()`` for files larger
than 1MB to reduce memory allocations and copying.

.. code-block:: python

   # Slow: Creates new list each call
   samples = f.read(65536)

   # Fast: Returns memoryview, minimal allocation
   buf = f.read_buffer(65536)

   # Fastest: Zero-copy into existing buffer
   buffer = array.array('i', [0] * 65536)
   n = f.read_into(buffer)

Write Throughput
~~~~~~~~~~~~~~~~

Compares different input types for writing:

+---------------------------+-------------+----------------------------------+
| Input Type                | Performance | Notes                            |
+===========================+=============+==================================+
| Python list               | Slowest     | Requires conversion to C array   |
+---------------------------+-------------+----------------------------------+
| ``array.array``           | Fast        | Direct buffer access             |
+---------------------------+-------------+----------------------------------+
| ``memoryview``            | Fast        | Direct buffer access             |
+---------------------------+-------------+----------------------------------+
| NumPy array               | Fast        | Direct buffer access             |
+---------------------------+-------------+----------------------------------+

**Recommendation**: Use ``array.array``, ``memoryview``, or NumPy arrays
for write operations, especially when writing large amounts of data.

.. code-block:: python

   import array

   # Slow: List requires conversion
   f.write([100, 200, 300, 400])

   # Fast: array.array uses buffer protocol
   arr = array.array('i', [100, 200, 300, 400])
   f.write(arr)

Effects Chain Performance
~~~~~~~~~~~~~~~~~~~~~~~~~

Effect processing time varies significantly by effect type:

+---------------------------+-------------+----------------------------------+
| Effect                    | Complexity  | Notes                            |
+===========================+=============+==================================+
| ``vol``, ``gain``         | O(n)        | Simple sample multiplication     |
+---------------------------+-------------+----------------------------------+
| ``bass``, ``treble``      | O(n)        | IIR filter, constant overhead    |
+---------------------------+-------------+----------------------------------+
| ``rate``                  | O(n*r)      | Resampling, depends on ratio     |
+---------------------------+-------------+----------------------------------+
| ``reverb``                | O(n*k)      | Convolution, memory intensive    |
+---------------------------+-------------+----------------------------------+
| ``tempo``                 | O(n*log n)  | FFT-based time stretching        |
+---------------------------+-------------+----------------------------------+

**Recommendation**: Order effects from least to most expensive when possible.
Apply volume/gain changes before reverb to reduce processing load.

Memory Usage
~~~~~~~~~~~~

Memory allocation patterns affect performance:

+---------------------------+----------------------------------+
| Operation                 | Memory Pattern                   |
+===========================+==================================+
| ``Format()`` open         | ~1KB per file handle             |
+---------------------------+----------------------------------+
| ``SignalInfo()``          | ~64 bytes per instance           |
+---------------------------+----------------------------------+
| ``Effect()``              | ~256 bytes + private data        |
+---------------------------+----------------------------------+
| ``EffectsChain()``        | ~1KB + effect storage            |
+---------------------------+----------------------------------+
| ``read(n)``               | n * 4 bytes (32-bit samples)     |
+---------------------------+----------------------------------+
| ``read_buffer(n)``        | n * 4 bytes (shared)             |
+---------------------------+----------------------------------+

**Recommendation**: Reuse ``SignalInfo`` and ``Effect`` objects when
processing multiple files with the same parameters.

Optimization Tips
-----------------

1. Use Buffer Protocol
~~~~~~~~~~~~~~~~~~~~~~

For large files, always prefer buffer-based I/O:

.. code-block:: python

   # Before: ~100 MB/s
   samples = f.read(1000000)

   # After: ~400 MB/s
   buf = f.read_buffer(1000000)

2. Pre-allocate Buffers
~~~~~~~~~~~~~~~~~~~~~~~

When processing in a loop, allocate once:

.. code-block:: python

   # Allocate once outside loop
   buffer = array.array('i', [0] * 65536)

   while True:
       n = f.read_into(buffer)
       if n == 0:
           break
       # Process buffer[:n]

3. Batch Operations
~~~~~~~~~~~~~~~~~~~

Process larger chunks to reduce call overhead:

.. code-block:: python

   # Slow: Many small reads
   for _ in range(1000):
       chunk = f.read(1024)

   # Fast: Fewer large reads
   for _ in range(10):
       chunk = f.read(102400)

4. Reuse Effect Chains
~~~~~~~~~~~~~~~~~~~~~~

For batch processing, create chain once:

.. code-block:: python

   # Create handlers once
   vol_handler = sox.find_effect("vol")

   for input_file in files:
       # Reuse handler, create new effect instance
       effect = sox.Effect(vol_handler)
       effect.set_options(["3dB"])

5. Close Files Promptly
~~~~~~~~~~~~~~~~~~~~~~~

Use context managers to ensure cleanup:

.. code-block:: python

   # Good: Automatic cleanup
   with sox.Format('input.wav') as f:
       samples = f.read(1024)

   # Bad: May leak if exception occurs
   f = sox.Format('input.wav')
   samples = f.read(1024)
   f.close()

Sample Benchmark Results
------------------------

Results from a typical development machine (Apple M1, 16GB RAM):

**Read Throughput** (64KB chunks, ~1MB file):

.. code-block:: text

   test_read_list_large         12.3 ms (81 MB/s)
   test_read_buffer_large        3.1 ms (323 MB/s)
   test_read_into_preallocated   2.8 ms (357 MB/s)

**Effects Chain** (~1MB stereo WAV):

.. code-block:: text

   test_passthrough_chain       15.2 ms
   test_volume_effect           16.8 ms (+10%)
   test_multiple_effects        21.3 ms (+40%)
   test_reverb_effect           89.4 ms (+488%)
   test_rate_conversion         34.7 ms (+128%)

**Memory Operations**:

.. code-block:: text

   test_repeated_open_close      8.2 ms (100 cycles)
   test_signal_info_creation     1.4 ms (1000 objects)
   test_effect_creation          2.1 ms (100 objects)

.. note::

   These numbers are illustrative. Run ``make benchmark`` on your
   system for accurate measurements.
