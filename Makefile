LIBSOX := lib/libsox.a
LIBRARIES := $(wildcard lib/*.a)
DEBUGPY_BIN := $(PWD)/build/install/python-shared/bin
DEBUGPY_EXE := $(DEBUGPY_BIN)/python3
DEBUG=0

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

.PHONY: all build wheel clean reset test testpy examples strip delocate

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

examples:
	@for i in $(shell seq 0 6); \
		do $(call build-example,example$$i); \
	done
	@cp tests/data/s00.wav ./build

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
