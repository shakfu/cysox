LIBSOX := lib/libsox.a
LIBRARIES := $(wildcard lib/*.a)

define build-example
gcc -std=c11 -o build/$1 \
	-I ./include -L ./lib \
	$(LIBRARIES) \
	-lz \
	-framework CoreAudio \
	tests/examples/$1.c
endef

.PHONY: all build wheel clean reset test eg0 examples strip delocate

all: build

$(LIBSOX):
	@scripts/setup.sh

build: $(LIBSOX)
	@python3 setup.py build_ext --inplace

wheel:
	@rm -rf dist
	@python3 setup.py bdist_wheel

clean:
	@rm -rf build/lib.* build/temp.* dist sox.*.so src/*.egg-info htmlcov
	@find . -type d -name __pycache__ -exec rm -rf {} \; -prune
	@find . -type d -path ".*_cache"  -exec rm -rf {} \; -prune

reset: clean
	@rm -rf build include lib

test:
	@pytest -v

eg0:
	@python3 tests/examples/example0.py tests/data/s00.wav build/out.wav

examples:
	@for i in $(shell seq 0 6); \
		do $(call build-example,example$$i); \
	done

strip:
	@strip -x src/cysox/sox.*.so

delocate: wheel
	@cd dist && delocate-wheel cysox-*.whl


# debug: $(LIBSOX)
# 	@build/debug_python/bin/python3 setup.py build_ext --inplace
# 	@build/debug_python/bin/cygdb . -- --args build/debug_python/bin/python3 example0.py
