#
# run all examples
#
# $Id: Makefile 72 2011-03-24 18:07:12Z patrick $
#
# Copyright 2011 Patrick Atamaniuk
#
# This source code is freely redistributable and may be used for
# any purpose.  This copyright notice must be maintained.
# Patrick Atamaniuk and Contributors are not responsible for
# the consequences of using this software.
#
PYTHON?=python
PYTHON3?=python3

all: test

TESTS := $(patsubst %.py,%.test,$(wildcard *.py))
TESTS3 := $(patsubst %.py,%.test3,$(wildcard *.py))

test: $(TESTS)
test3: $(TESTS3)

%.test: %.py
	@echo "----------------" $< $@ "---------------"
	@env PYTHONPATH=.. $(PYTHON) $<
	@echo "-------------------------------------"

%.test3: %.py
	@echo "----------------" $< $@ "---------------"
	@env PYTHONPATH=.. $(PYTHON3) $<
	@echo "-------------------------------------"

clean:
	-rm *.wav *.pyo *.pyc

debug:
	@env PYTHONPATH=.. ddd $(PYTHON)
