
.PHONY: all build clean test

all: build


build: clean
	@python3 setup.py build_ext --inplace

clean:
	@rm -rf build sox.*.so

test:
	@pytest
