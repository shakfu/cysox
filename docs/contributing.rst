Contributing
============

Thank you for your interest in contributing to cysox!

Development Setup
-----------------

1. Clone the repository:

   .. code-block:: bash

      git clone https://github.com/youruser/cysox.git
      cd cysox

2. Install development dependencies:

   .. code-block:: bash

      pip install -e ".[dev,docs]"

3. Install libsox (see :doc:`installation`).

4. Build the extension:

   .. code-block:: bash

      make build

5. Run tests:

   .. code-block:: bash

      make test

Code Style
----------

- Follow PEP 8 for Python code
- Use type hints where possible
- Add docstrings to public functions and classes
- Keep lines under 100 characters

Testing
-------

All changes must include tests:

.. code-block:: bash

   # Run all tests
   make test

   # Run specific test file
   pytest tests/test_sox_format.py

   # Run with coverage
   pytest --cov=cysox

Test requirements:

- All tests must pass
- New features need test coverage
- Bug fixes should include regression tests

Documentation
-------------

Build documentation locally:

.. code-block:: bash

   make docs

Documentation is built with Sphinx. Add docstrings following
Google style or NumPy style.

Pull Request Process
--------------------

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests (``make test``)
5. Update documentation if needed
6. Submit a pull request

Commit Messages
---------------

Use clear, descriptive commit messages:

.. code-block:: text

   Add null pointer checks to EncodingInfo properties

   - Added validation to compression, reverse_bytes, reverse_nibbles,
     reverse_bits, and opposite_endian properties
   - Raises RuntimeError if pointer is NULL

Reporting Issues
----------------

When reporting bugs, include:

- Python version
- Operating system
- libsox version (``sox.version()``)
- Minimal reproduction code
- Full error traceback

License
-------

By contributing, you agree that your contributions will be licensed
under the same license as the project (GPL v2).
