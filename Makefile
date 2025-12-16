LIBSOX := lib/libsox.a
LIBRARIES := $(wildcard lib/*.a)
DEBUG=0

EXAMPLES := tests/examples
TEST_WAV := tests/data/s00.wav

# Debug mode uses custom Python build with sanitizers
ifeq ($(DEBUG),1)
DEBUGPY_BIN := $(PWD)/build/install/python-shared/bin
DEBUGPY_EXE := $(DEBUGPY_BIN)/python3
CYGDB := $(DEBUGPY_BIN)/cygdb
endif

define build-example
gcc -std=c11 -o build/$1 \
	-I ./include -L ./lib \
	$(LIBRARIES) \
	-lz \
	-framework CoreAudio \
	tests/examples/$1.c
endef

.PHONY: all build wheel clean reset test testpy examples-p examples-c strip delocate check publish publish-test docs docs-clean docs-serve benchmark benchmark-save benchmark-compare pydebug debug

all: build

$(LIBSOX):
	@scripts/setup.sh

build: $(LIBSOX)
	@uv sync --reinstall-package cysox

wheel: build
	@uv run python -m build --wheel

clean:
	@rm -rf build/lib.* build/temp.* dist src/*.egg-info htmlcov
	@rm -rf src/cysox/sox.*.so
	@find . -type d -name __pycache__ -exec rm -rf {} \; -prune
	@find . -type d -path ".*_cache"  -exec rm -rf {} \; -prune

reset: clean
	@rm -rf build include lib .venv

test:
	@uv run pytest -s -vv

testpy:
	@uv run python tests/examples/example0.py tests/data/s00.wav build/out.wav

examples-p:
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

examples-c:
	@for i in $(shell seq 0 6); \
		do $(call build-example,example$$i); \
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

strip:
	@strip -x src/cysox/sox.*.so

delocate: wheel
	@uv run delocate-wheel dist/cysox-*.whl

check:
	@uv run twine check dist/*

publish:
	@uv run twine upload dist/*

publish-test:
	@uv run twine upload --repository testpypi dist/*

# Documentation
docs:
	@uv run sphinx-build -b html docs docs/_build/html

docs-clean:
	@rm -rf docs/_build

docs-serve: docs
	@uv run python -m http.server 8000 --directory docs/_build/html

# Benchmarks
benchmark:
	@uv run pytest tests/test_benchmarks.py -v --benchmark-only --benchmark-group-by=group

benchmark-save:
	@uv run pytest tests/test_benchmarks.py -v --benchmark-only --benchmark-save=baseline --benchmark-group-by=group

benchmark-compare:
	@uv run pytest tests/test_benchmarks.py -v --benchmark-only --benchmark-compare=baseline --benchmark-group-by=group

# Debug mode (requires custom Python build with sanitizers)
ifeq ($(DEBUG),1)
$(DEBUGPY_EXE):
	@./scripts/buildpy.py -d -c shared_max \
		-a with_assertions \
		   with_address_sanitizer \
		-p setuptools cython pytest pip

pydebug: $(DEBUGPY_EXE)

debug: $(LIBSOX) $(DEBUGPY_EXE)
	@DEBUG=1 $(DEBUGPY_EXE) setup.py build_ext --inplace
	@$(CYGDB) . -- --args $(DEBUGPY_EXE) tests/examples/example0.py tests/data/s00.wav build/out.wav
	# set arch aarch64
endif
