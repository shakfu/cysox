API Reference
=============

This section documents the cysox public API.

Module Functions
----------------

Initialization
~~~~~~~~~~~~~~

.. function:: init()

   Initialize the SoX library. Must be called before using any other cysox functions.

   :raises SoxInitError: If initialization fails.

   .. code-block:: python

      import cysox as sox
      sox.init()

.. function:: quit()

   Clean up the SoX library. Should be called when done using cysox.

   :raises SoxInitError: If cleanup fails.

.. function:: format_init()

   Initialize format handlers. Called automatically by :func:`init`.

.. function:: format_quit()

   Clean up format handlers. Called automatically by :func:`quit`.

Version Information
~~~~~~~~~~~~~~~~~~~

.. function:: version() -> str

   Returns the libsox version string (e.g., "14.4.2").

.. function:: version_info() -> dict

   Returns detailed version information as a dictionary with keys:

   - ``version``: Version string
   - ``version_code``: Numeric version code
   - ``flags``: Feature flags
   - ``time``: Build time
   - ``compiler``: Compiler info
   - ``arch``: Architecture info

Lookup Functions
~~~~~~~~~~~~~~~~

.. function:: find_effect(name: str) -> Optional[EffectHandler]

   Find an effect handler by name.

   :param name: Effect name (e.g., "vol", "trim", "reverb")
   :returns: EffectHandler if found, None otherwise

   .. code-block:: python

      handler = sox.find_effect("vol")
      if handler:
          print(f"Usage: {handler.usage}")

.. function:: find_format(name: str, ignore_devices: bool = False) -> Optional[FormatHandler]

   Find a format handler by name.

   :param name: Format name (e.g., "wav", "mp3", "flac")
   :param ignore_devices: If True, skip device handlers
   :returns: FormatHandler if found, None otherwise

Utility Functions
~~~~~~~~~~~~~~~~~

.. function:: strerror(sox_errno: int) -> str

   Convert a SoX error code to an error message string.

.. function:: is_playlist(filename: str) -> bool

   Check if a file is a known playlist format.

.. function:: basename(filename: str) -> str

   Extract the basename from a file path.

.. function:: precision(encoding: int, bits_per_sample: int) -> int

   Calculate the precision (useful bits) for an encoding.

.. function:: format_supports_encoding(path: str, encoding: EncodingInfo) -> bool

   Check if a format supports a specific encoding.

.. function:: get_encodings() -> List[EncodingsInfo]

   Get a list of all available encodings.

.. function:: get_effects_globals() -> dict

   Get global effects settings.

.. function:: get_format_fns() -> List[dict]

   Get a list of available format handlers.

.. function:: get_last_callback_exception() -> Optional[Tuple]

   Retrieve the last exception that occurred in a flow_effects callback.

   Since exceptions cannot propagate through C code, they are stored for
   later retrieval. Returns ``(type, value, traceback)`` or ``None``.

   .. code-block:: python

      chain.flow_effects(callback=my_callback)
      exc_info = sox.get_last_callback_exception()
      if exc_info:
          raise exc_info[1].with_traceback(exc_info[2])

Core Classes
------------

Format
~~~~~~

.. class:: Format(filename, signal=None, encoding=None, mode='r')

   Audio format handle for reading and writing audio files.

   :param filename: Path to the audio file
   :param signal: SignalInfo for output files (required for write mode)
   :param encoding: EncodingInfo (optional)
   :param mode: 'r' for reading, 'w' for writing

   **Properties:**

   - ``filename`` (str): Path to the audio file
   - ``signal`` (SignalInfo): Signal information
   - ``encoding`` (EncodingInfo): Encoding information
   - ``filetype`` (str): Format identifier (e.g., "wav")
   - ``seekable`` (bool): Whether seeking is supported
   - ``mode`` (str): 'r' or 'w'
   - ``clips`` (int): Clipping counter
   - ``sox_errno`` (int): Last error code
   - ``sox_errstr`` (str): Last error message

   **Methods:**

   .. method:: read(length: int) -> List[int]

      Read samples into a Python list.

   .. method:: read_buffer(length: int) -> memoryview

      Read samples into a memoryview (buffer protocol).

   .. method:: read_into(buffer) -> int

      Read samples into a pre-allocated buffer. Returns samples read.

   .. method:: write(samples) -> int

      Write samples from a list or buffer. Returns samples written.

   .. method:: seek(offset: int, whence: int = SOX_SEEK_SET) -> int

      Seek to a sample position.

   .. method:: close() -> int

      Close the file handle.

   **Context Manager:**

   .. code-block:: python

      with sox.Format('input.wav') as f:
          samples = f.read(1024)

SignalInfo
~~~~~~~~~~

.. class:: SignalInfo(rate=0.0, channels=0, precision=0, length=0, mult=0.0)

   Audio signal parameters.

   :param rate: Sample rate in Hz
   :param channels: Number of channels
   :param precision: Bits per sample
   :param length: Total samples * channels
   :param mult: Effects headroom multiplier

   **Properties:**

   - ``rate`` (float): Sample rate (0 if unknown)
   - ``channels`` (int): Channel count (0 if unknown)
   - ``precision`` (int): Bits per sample (0 if unknown)
   - ``length`` (int): Total samples * channels
   - ``mult`` (float): Headroom multiplier

EncodingInfo
~~~~~~~~~~~~

.. class:: EncodingInfo(encoding=0, bits_per_sample=0, compression=0.0, ...)

   Audio encoding parameters.

   **Properties:**

   - ``encoding`` (int): Encoding type
   - ``bits_per_sample`` (int): Bits per sample
   - ``compression`` (float): Compression factor
   - ``reverse_bytes`` (int): Byte reversal setting
   - ``reverse_nibbles`` (int): Nibble reversal setting
   - ``reverse_bits`` (int): Bit reversal setting
   - ``opposite_endian`` (bool): Endianness reversal

Effect Classes
--------------

EffectHandler
~~~~~~~~~~~~~

.. class:: EffectHandler

   Describes an effect type. Obtained via :func:`find_effect`.

   **Properties:**

   - ``name`` (str): Effect name
   - ``usage`` (str): Parameter usage description
   - ``flags`` (int): Effect flags
   - ``priv_size`` (int): Private data size

Effect
~~~~~~

.. class:: Effect(handler: EffectHandler)

   An effect instance.

   :param handler: The EffectHandler for this effect type

   **Methods:**

   .. method:: set_options(options: List) -> int

      Set effect options. Options can be strings or Format objects.

      .. code-block:: python

         effect.set_options(["3dB"])  # Volume boost
         effect.set_options([input_format])  # Input effect

   .. method:: stop() -> int

      Stop the effect and return clip count.

   **Properties:**

   - ``handler`` (EffectHandler): The effect's handler
   - ``in_signal`` (SignalInfo): Input signal info
   - ``out_signal`` (SignalInfo): Output signal info
   - ``clips`` (int): Clipping count

EffectsChain
~~~~~~~~~~~~

.. class:: EffectsChain(in_encoding=None, out_encoding=None)

   A chain of effects to process audio.

   :param in_encoding: Input encoding info
   :param out_encoding: Output encoding info

   **Methods:**

   .. method:: add_effect(effect, in_signal, out_signal) -> int

      Add an effect to the chain.

   .. method:: flow_effects(callback=None, client_data=None) -> int

      Process audio through the chain.

      :param callback: Optional progress callback ``(all_done, user_data) -> bool``
      :param client_data: User data passed to callback

   .. method:: get_clips() -> int

      Get total clipping count.

   **Properties:**

   - ``effects`` (List[Effect]): Effects in the chain
   - ``length`` (int): Number of effects

Constants
---------

Error Codes
~~~~~~~~~~~

- ``SUCCESS`` - Operation succeeded
- ``EOF`` - End of file
- ``EHDR`` - Invalid header
- ``EFMT`` - Invalid format
- ``ENOMEM`` - Out of memory
- ``EPERM`` - Permission denied
- ``ENOTSUP`` - Not supported
- ``EINVAL`` - Invalid argument

Encodings
~~~~~~~~~

``ENCODINGS`` is a list of ``(name, description)`` tuples for all supported encodings:

.. code-block:: python

   for name, desc in sox.ENCODINGS:
       print(f"{name}: {desc}")
