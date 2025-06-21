#
# $Id: t001test.py 80 2011-03-25 10:57:42Z patrick $
#
# Copyright 2011 Patrick Atamaniuk
#
# This source code is freely redistributable and may be used for
# any purpose.  This copyright notice must be maintained.
# Patrick Atamaniuk and Contributors are not responsible for
# the consequences of using this software.
#

"""Open an audio file and decrease the volume using the builtin vol effect, write to out.wav

>>> import pysox
>>> makeTestFile('test.wav')
>>> osize = os.stat('test.wav').st_size
>>> input = pysox.CSoxStream("test.wav")
>>> output = pysox.CSoxStream('out.wav', 'w', input.get_signal())
>>> chain = pysox.CEffectsChain(input, output)
>>> chain.add_effect(pysox.CEffect("vol",[b'-18db']))
>>> chain.flow_effects()
0
>>> output.close()    
>>> os.stat('out.wav').st_size == osize
True
"""
from tests import makeTestFile
import os