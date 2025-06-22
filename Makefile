
.PHONY: all build clean

all: build


build: clean
	@python3 setup.py build_ext --inplace

clean:
	@rm -rf build sox.*.so
