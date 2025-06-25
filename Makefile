
LIBRARIES=$(wildcard lib/*.a)

define build-example
gcc -std=c11 -o build/$1 \
	-I ./include -L ./lib \
	$(LIBRARIES) \
	-lz \
	-framework CoreAudio \
	tests/examples/$1.c
endef


.PHONY: all build examples wheel clean test strip

all: build

build: clean
	@python3 setup.py build_ext --inplace

wheel:
	@rm -rf dist
	@python3 setup.py bdist_wheel

clean:
	@rm -rf build dist sox.*.so src/*.egg-info htmlcov
	@find . -type d -name __pycache__ -exec rm -rf {} \; -prune
	@find . -type d -path ".*_cache"  -exec rm -rf {} \; -prune

test:
	@pytest -v

strip:
	@strip -x src/cysox/sox.*.so

examples:
	@for i in $(shell seq 0 6); \
		do $(call build-example,example$$i); \
	done

