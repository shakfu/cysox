#!/usr/bin/env python
#
# test and example usage
#
# $Id: example6-combine_concatenate.py 110 2011-03-30 15:01:21Z patrick $
#
# Copyright 2011 Patrick Atamaniuk
#
# This source code is freely redistributable and may be used for
# any purpose.  This copyright notice must be maintained.
# Patrick Atamaniuk and Contributors are not responsible for
# the consequences of using this software.
#
import pysox
from common import mktestfile

mktestfile("test1.wav",[b'1', b'sine', b'300-3000'])
mktestfile("test2.wav",[b'1', b'sine', b'3000-300'])
    
dummy = pysox.CNullFile()
out = pysox.CSoxStream('out1.wav', 'w', dummy.get_signal())

chain = pysox.CEffectsChain(dummy, out)
id = pysox.ConcatenateFiles("input", ["test1.wav", "test2.wav"])
print(id)
chain.add_effect(id)
print('flowing')
chain.flow_effects()
print('flowing done')
