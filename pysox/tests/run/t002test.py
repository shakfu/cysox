#
# $Id: t002test.py 82 2011-03-25 20:06:33Z patrick $
#
# Copyright 2011 Patrick Atamaniuk
#
# This source code is freely redistributable and may be used for
# any purpose.  This copyright notice must be maintained.
# Patrick Atamaniuk and Contributors are not responsible for
# the consequences of using this software.
#

"""use nullfile, generate synth sounds, chain effects, write to out.wav

>>> import pysox
>>> makeTestFile('test.wav')
>>> input = pysox.CNullFile()
>>> output = pysox.CSoxStream('out.wav', 'w', input.get_signal())
>>> chain = pysox.CEffectsChain(input, output)
>>> effect = pysox.CEffect("synth",[b'10', b'sine', b'300-3000'])
>>> chain.add_effect(effect)
>>> chain.add_effect(pysox.CEffect("synth",[b'10', b'sine', b'mix', b'2000-200']))
>>> chain.add_effect(pysox.CEffect("synth",[b'10', b'sine', b'fmod', b'100-200']))
>>> chain.add_effect(pysox.CEffect("trim",[b'2', b'4']))
>>> chain.flow_effects()
0
>>> output.close()
>>> print("%d"%os.stat('out.wav').st_size)
1536080
"""
from tests import makeTestFile
import os