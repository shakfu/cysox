
.PHONY: all build wheel clean test

all: build


build: clean
	@python3 setup.py build_ext --inplace

wheel:
	@rm -rf dist
	@python3 setup.py bdist_wheel

clean:
	@rm -rf build sox.*.so dist src/*.egg-info src/cysox/__pycache__

test:
	@pytest
