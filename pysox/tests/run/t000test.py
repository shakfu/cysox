#
# $Id: t000test.py 63 2011-03-24 15:52:13Z patrick $
#
# Copyright 2011 Patrick Atamaniuk
#
# This source code is freely redistributable and may be used for
# any purpose.  This copyright notice must be maintained.
# Patrick Atamaniuk and Contributors are not responsible for
# the consequences of using this software.
#

"""
>>> import pysox
>>> path="test.wav"
>>> nullfile = pysox.CNullFile()
>>> signal = nullfile.get_signal()
>>> out = pysox.CSoxStream(path, 'w', signal)
>>> chain = pysox.CEffectsChain(nullfile, out)
>>> effect = pysox.CEffect("synth", [b'3', b'sine', b'300-3000'])
>>> chain.add_effect(effect)
>>> chain.flow_effects()
0
>>> out.close()

"""
