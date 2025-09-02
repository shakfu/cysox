LIBSOX := lib/libsox.a
LIBRARIES := $(wildcard lib/*.a)
DEBUGPY_BIN := $(PWD)/build/install/python-shared/bin
DEBUGPY_EXE := $(DEBUGPY_BIN)/python3
DEBUG=0

EXAMPLES := tests/examples
TEST_WAV := tests/data/s00.wav

ifeq ($(DEBUG),1)
PYTHON := $(DEBUGPY_EXE)
CYGDB := $(DEBUGPY_BIN)/cygdb
PYTEST := $(DEBUGPY_BIN)/pytest
else
PYTHON := python3
PYTEST := pytest
endif

define build-example
gcc -std=c11 -o build/$1 \
	-I ./include -L ./lib \
	$(LIBRARIES) \
	-lz \
	-framework CoreAudio \
	tests/examples/$1.c
endef

.PHONY: all build wheel clean reset test testpy examples-p examples-c strip delocate

all: build

$(LIBSOX):
	@scripts/setup.sh

build: $(LIBSOX)
	@$(PYTHON) setup.py build_ext --inplace

wheel:
	@rm -rf dist
	@$(PYTHON) setup.py bdist_wheel

clean:
	@rm -rf build/lib.* build/temp.* dist src/*.egg-info htmlcov
	@rm -rf src/cysox/sox.*.so
	@find . -type d -name __pycache__ -exec rm -rf {} \; -prune
	@find . -type d -path ".*_cache"  -exec rm -rf {} \; -prune

reset: clean
	@rm -rf build include lib

test:
	@$(PYTEST) -s -vv

testpy:
	@$(PYTHON) tests/examples/example0.py tests/data/s00.wav build/out.wav

examples-p:
	@echo "example 0 ------------------------------------------------------"
	$(PYTHON) $(EXAMPLES)/example0.py $(TEST_WAV) build/out0-p.wav
	@echo "example 1 ------------------------------------------------------"
	$(PYTHON) $(EXAMPLES)/example1.py $(TEST_WAV) build/out1-p.wav
	@echo "example 2 ------------------------------------------------------"
	$(PYTHON) $(EXAMPLES)/example2.py $(TEST_WAV) 2 1
	@echo "example 3 ------------------------------------------------------"
	$(PYTHON) $(EXAMPLES)/example3.py $(TEST_WAV)
	@echo "example 4 ------------------------------------------------------"
	$(PYTHON) $(EXAMPLES)/example4.py $(TEST_WAV) $(TEST_WAV) build/out4-p.wav
	@echo "example 5 ------------------------------------------------------"
	$(PYTHON) $(EXAMPLES)/example5.py $(TEST_WAV) build/out5-p.wav
	@echo "example 6 ------------------------------------------------------"
	$(PYTHON) $(EXAMPLES)/example6.py $(TEST_WAV) build/out6-p.wav


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
	@cd dist && delocate-wheel cysox-*.whl

$(DEBUGPY_EXE):
	@./scripts/buildpy.py -d -c shared_max \
		-a with_assertions \
		   with_address_sanitizer \
		-p setuptools cython pytest pip

pydebug: $(DEBUGPY_EXE)

debug: $(LIBSOX)
	@$(PYTHON) setup.py build_ext --inplace
	@$(CYGDB) . -- --args $(PYTHON) tests/examples/example0.py tests/data/s00.wav build/out.wav
	# set arch aarch64
