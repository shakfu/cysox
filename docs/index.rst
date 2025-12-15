cysox Documentation
===================

**cysox** is a Cython wrapper for `libsox <https://github.com/chirlu/sox>`_, providing
high-performance Python bindings to the SoX (Sound eXchange) audio processing library.

.. note::
   cysox requires libsox to be installed on your system. See :doc:`installation` for details.

Quick Start
-----------

.. code-block:: python

   import cysox as sox

   # Initialize the library
   sox.init()

   try:
       # Open an audio file
       with sox.Format('input.wav') as f:
           print(f"Sample rate: {f.signal.rate}")
           print(f"Channels: {f.signal.channels}")
           print(f"Duration: {f.signal.length / f.signal.rate / f.signal.channels:.2f}s")

           # Read samples
           samples = f.read(1024)
   finally:
       sox.quit()

Features
--------

- **Audio Processing**: Convert between different audio formats (WAV, MP3, FLAC, OGG, etc.)
- **Signal Manipulation**: Apply various audio effects and filters
- **High Performance**: Direct C bindings through Cython for optimal performance
- **Buffer Protocol**: Zero-copy integration with NumPy, PyTorch, and array.array
- **Context Managers**: Automatic resource cleanup with ``with`` statements
- **Type Hints**: Full IDE autocomplete support via type stubs

Contents
--------

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   installation
   quickstart
   examples
   benchmarks

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/modules
   api/exceptions

.. toctree::
   :maxdepth: 1
   :caption: Development

   changelog
   contributing

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
