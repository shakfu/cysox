# Makefile for cysox - scikit-build-core + uv project
#
# This Makefile provides convenient targets for development, testing,
# and distribution of the cysox package.

# Configuration
LIBSOX := lib/libsox.a
LIBRARIES := $(wildcard lib/*.a)
DEBUG := 0

EXAMPLES := tests/examples
TEST_WAV := tests/data/s00.wav

# Debug mode uses custom Python build with sanitizers
ifeq ($(DEBUG),1)
DEBUGPY_BIN := $(PWD)/build/install/python-shared/bin
DEBUGPY_EXE := $(DEBUGPY_BIN)/python3
CYGDB := $(DEBUGPY_BIN)/cygdb
endif

# Build C examples macro (macOS only)
define build-example
gcc -std=c11 -o build/$1 \
	-I ./include -L ./lib \
	$(LIBRARIES) \
	-lz \
	-framework CoreAudio \
	tests/examples/$1.c
endef

.PHONY: all sync build rebuild test testpy lint typecheck format qa \
        wheel sdist delocate strip check publish publish-test \
        examples-p examples-c benchmark benchmark-save benchmark-compare \
        docs docs-clean docs-serve clean reset distclean help

# Default target
all: build

# Setup libsox and dependencies (run once)
$(LIBSOX):
	@scripts/setup.sh

# Sync environment (initial setup, installs dependencies + package)
sync:
	@uv sync

# Build/rebuild the extension after code changes
build: $(LIBSOX)
	@uv sync --reinstall-package cysox

# Alias for build
rebuild: build

# ============================================================================
# Testing
# ============================================================================

# Run all tests
test:
	@uv run pytest tests/ -v

# Quick test of a single example
testpy:
	@uv run python tests/examples/example0.py tests/data/s00.wav build/out.wav

# Run Python examples
examples-p:
	@mkdir -p build
	@echo "example 0 ------------------------------------------------------"
	@uv run python $(EXAMPLES)/example0.py $(TEST_WAV) build/out0-p.wav
	@echo "example 1 ------------------------------------------------------"
	@uv run python $(EXAMPLES)/example1.py $(TEST_WAV) build/out1-p.wav
	@echo "example 2 ------------------------------------------------------"
	@uv run python $(EXAMPLES)/example2.py $(TEST_WAV) 2 1
	@echo "example 3 ------------------------------------------------------"
	@uv run python $(EXAMPLES)/example3.py $(TEST_WAV)
	@echo "example 4 ------------------------------------------------------"
	@uv run python $(EXAMPLES)/example4.py $(TEST_WAV) $(TEST_WAV) build/out4-p.wav
	@echo "example 5 ------------------------------------------------------"
	@uv run python $(EXAMPLES)/example5.py $(TEST_WAV) build/out5-p.wav
	@echo "example 6 ------------------------------------------------------"
	@uv run python $(EXAMPLES)/example6.py $(TEST_WAV) build/out6-p.wav

# Build and run C examples (macOS only)
examples-c:
	@mkdir -p build
	@for i in $$(seq 0 6); do \
		$(call build-example,example$$i); \
	done
	@cp tests/data/s00.wav ./build
	@echo "example 0 ------------------------------------------------------"
	./build/example0 $(TEST_WAV) build/out0-c.wav
	@echo "example 1 ------------------------------------------------------"
	./build/example1 $(TEST_WAV) build/out1-c.wav
	@echo "example 2 ------------------------------------------------------"
	./build/example2 $(TEST_WAV) 2 1
	@echo "example 3 ------------------------------------------------------"
	./build/example3 $(TEST_WAV)
	@echo "example 4 ------------------------------------------------------"
	./build/example4 $(TEST_WAV) $(TEST_WAV) build/out4-c.wav
	@echo "example 5 ------------------------------------------------------"
	./build/example5 $(TEST_WAV) build/out5-c.wav
	@echo "example 6 ------------------------------------------------------"
	./build/example6 $(TEST_WAV) build/out6-c.wav

# ============================================================================
# Benchmarks
# ============================================================================

benchmark:
	@uv run pytest tests/test_benchmarks.py -v --benchmark-only --benchmark-group-by=group

benchmark-save:
	@uv run pytest tests/test_benchmarks.py -v --benchmark-only --benchmark-save=baseline --benchmark-group-by=group

benchmark-compare:
	@uv run pytest tests/test_benchmarks.py -v --benchmark-only --benchmark-compare=baseline --benchmark-group-by=group

# ============================================================================
# Code Quality
# ============================================================================

lint:
	@uv run ruff check --fix src/

typecheck:
	@uv run mypy src/

format:
	@uv run ruff format src/

# Run all QA checks (test, lint, typecheck, format)
qa: test lint
	@echo "All checks passed!"
	@uv run mypy src/
	@uv run ruff format src/

# ============================================================================
# Distribution
# ============================================================================

# Build wheel
wheel:
	@uv build --wheel
	@uv run twine check dist/*

# Build source distribution
sdist:
	@uv build --sdist

# Strip debug symbols from extension (reduces size)
strip:
	@strip -x src/cysox/sox.*.so 2>/dev/null || true

# Delocate wheel (bundle dylibs for macOS distribution)
delocate: wheel
	@uv run delocate-wheel dist/cysox-*.whl

# Check distribution files
check:
	@uv run twine check dist/*

# Publish to PyPI
publish:
	@uv run twine upload dist/*

# Publish to TestPyPI
publish-test:
	@uv run twine upload --repository testpypi dist/*

# ============================================================================
# Documentation
# ============================================================================

docs:
	@uv run sphinx-build -b html docs docs/_build/html

docs-clean:
	@rm -rf docs/_build

docs-serve: docs
	@uv run python -m http.server 8000 --directory docs/_build/html

# ============================================================================
# Cleanup
# ============================================================================

# Clean build artifacts
clean:
	@rm -rf build/lib.* build/temp.* dist src/*.egg-info htmlcov
	@rm -rf src/cysox/sox.*.so
	@rm -rf *.egg-info/
	@rm -rf .pytest_cache/
	@rm -rf .ruff_cache/
	@rm -rf .mypy_cache/
	@find . -name "*.so" -path "./src/*" -delete
	@find . -name "*.pyd" -delete
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

# Clean everything including CMake cache
distclean: clean
	@rm -rf dist build/

# Full reset (removes lib, include, venv - requires re-running setup.sh)
reset: distclean
	@rm -rf include lib .venv

# ============================================================================
# Debug Mode (requires custom Python build with sanitizers)
# ============================================================================

ifeq ($(DEBUG),1)
$(DEBUGPY_EXE):
	@./scripts/buildpy.py -d -c shared_max \
		-a with_assertions \
		   with_address_sanitizer \
		-p setuptools cython pytest pip

pydebug: $(DEBUGPY_EXE)

debug: $(LIBSOX) $(DEBUGPY_EXE)
	@DEBUG=1 $(DEBUGPY_EXE) -m pip install -e .
	@$(CYGDB) . -- --args $(DEBUGPY_EXE) tests/examples/example0.py tests/data/s00.wav build/out.wav
endif

# ============================================================================
# Help
# ============================================================================

help:
	@echo "cysox Makefile - available targets:"
	@echo ""
	@echo "Build:"
	@echo "  all           - Build the extension (default)"
	@echo "  sync          - Sync environment (initial setup)"
	@echo "  build         - Build/rebuild extension after code changes"
	@echo "  rebuild       - Alias for build"
	@echo ""
	@echo "Testing:"
	@echo "  test          - Run all tests"
	@echo "  testpy        - Quick test with example0.py"
	@echo "  examples-p    - Run all Python examples"
	@echo "  examples-c    - Build and run C examples (macOS)"
	@echo ""
	@echo "Benchmarks:"
	@echo "  benchmark         - Run benchmarks"
	@echo "  benchmark-save    - Run and save benchmark baseline"
	@echo "  benchmark-compare - Compare against saved baseline"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint          - Run ruff linter with auto-fix"
	@echo "  typecheck     - Run mypy type checker"
	@echo "  format        - Format code with ruff"
	@echo "  qa            - Run all QA checks (test, lint, typecheck, format)"
	@echo ""
	@echo "Distribution:"
	@echo "  wheel         - Build wheel distribution"
	@echo "  sdist         - Build source distribution"
	@echo "  strip         - Strip debug symbols from extension"
	@echo "  delocate      - Bundle dylibs into wheel (macOS)"
	@echo "  check         - Check distribution files with twine"
	@echo "  publish       - Upload to PyPI"
	@echo "  publish-test  - Upload to TestPyPI"
	@echo ""
	@echo "Documentation:"
	@echo "  docs          - Build HTML documentation"
	@echo "  docs-clean    - Remove built documentation"
	@echo "  docs-serve    - Build and serve docs locally"
	@echo ""
	@echo "Cleanup:"
	@echo "  clean         - Remove build artifacts"
	@echo "  distclean     - Clean everything including CMake cache"
	@echo "  reset         - Full reset (removes lib, include, venv)"
	@echo ""
	@echo "Debug (DEBUG=1):"
	@echo "  pydebug       - Build debug Python with sanitizers"
	@echo "  debug         - Run with cygdb debugger"
