#!/usr/bin/env python
#
# test and example usage
#
# $Id: example4-synth.py 110 2011-03-30 15:01:21Z patrick $
#
# Copyright 2011 Patrick Atamaniuk
#
# This source code is freely redistributable and may be used for
# any purpose.  This copyright notice must be maintained.
# Patrick Atamaniuk and Contributors are not responsible for
# the consequences of using this software.
#
"""Open test.wav, apply the vol effect and write to out.wav"""

import pysox

#create a nullfile for input parameter definition. synth effect needs this
nf = pysox.CNullFile()

#create an audio file with the same parameters as the input file
out = pysox.CSoxStream('out.wav', 'w', nf.get_signal())

#create an effects chain using the signal and encoding parameters of our files
#thereby defining input and output effect
chain = pysox.CEffectsChain(nf, out)

#create the sine effect, producing 3 seconds of sine
effect = pysox.CEffect("synth",[b'10', b'sine', b'300-3000'])
chain.add_effect(effect)
chain.flow_effects()

#cleanup
out.close()
