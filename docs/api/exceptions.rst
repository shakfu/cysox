Exceptions
==========

cysox uses a custom exception hierarchy for error handling.

Exception Hierarchy
-------------------

.. code-block:: text

   SoxError (base)
       SoxInitError
       SoxFormatError
       SoxEffectError
       SoxIOError
       SoxMemoryError

Exception Classes
-----------------

.. exception:: SoxError

   Base exception for all cysox errors.

   All cysox exceptions inherit from this class, so you can catch
   all cysox-related errors with a single except clause:

   .. code-block:: python

      try:
          # cysox operations
      except sox.SoxError as e:
          print(f"cysox error: {e}")

.. exception:: SoxInitError

   Raised when library initialization or cleanup fails.

   Common causes:

   - libsox not properly installed
   - Calling ``init()`` when already initialized
   - Resource exhaustion

   .. code-block:: python

      try:
          sox.init()
      except sox.SoxInitError as e:
          print(f"Failed to initialize: {e}")

.. exception:: SoxFormatError

   Raised when format operations fail.

   Common causes:

   - File not found
   - Unsupported format
   - Corrupt audio file
   - Permission denied

   .. code-block:: python

      try:
          f = sox.Format('nonexistent.wav')
      except sox.SoxFormatError as e:
          print(f"Format error: {e}")

.. exception:: SoxEffectError

   Raised when effect operations fail.

   Common causes:

   - Invalid effect name
   - Invalid effect options
   - Effect chain misconfiguration

   .. code-block:: python

      try:
          chain.flow_effects()
      except sox.SoxEffectError as e:
          print(f"Effect error: {e}")

.. exception:: SoxIOError

   Raised when I/O operations fail.

   Common causes:

   - Seek failure on non-seekable stream
   - Write failure (disk full, permissions)
   - Read failure (corrupt data)

   .. code-block:: python

      try:
          f.seek(1000000)
      except sox.SoxIOError as e:
          print(f"I/O error: {e}")

.. exception:: SoxMemoryError

   Raised when memory allocation fails.

   Common causes:

   - Out of memory
   - Allocation too large

   .. code-block:: python

      try:
          signal = sox.SignalInfo()
      except sox.SoxMemoryError as e:
          print(f"Memory error: {e}")

Best Practices
--------------

Specific Exception Handling
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Handle specific exceptions when you need different behavior:

.. code-block:: python

   import cysox as sox

   sox.init()

   try:
       with sox.Format('input.wav') as f:
           samples = f.read(1024)
   except sox.SoxFormatError:
       print("Could not open file")
   except sox.SoxIOError:
       print("Could not read from file")
   except sox.SoxError:
       print("Unknown cysox error")
   finally:
       sox.quit()

Callback Exception Handling
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Exceptions in callbacks cannot propagate through C code. Use
``get_last_callback_exception()`` to retrieve them:

.. code-block:: python

   def my_callback(all_done, user_data):
       if some_condition:
           raise ValueError("Something went wrong")
       return True

   chain.flow_effects(callback=my_callback)

   exc_info = sox.get_last_callback_exception()
   if exc_info:
       # Re-raise the exception
       raise exc_info[1].with_traceback(exc_info[2])
