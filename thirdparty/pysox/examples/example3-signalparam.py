#!/usr/bin/env python
#
# test and example usage
#
# $Id: example3-signalparam.py 110 2011-03-30 15:01:21Z patrick $
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
inputwav = pysox.CNullFile()

#create an audio file with OTHER parameters. rate 9600, 1 channel, 8 bits
out = pysox.CSoxStream('out.wav', 'w', pysox.CSignalInfo(9600,1,8))
#NOTE: the sine effect thinks, we have the rate of the nullfile, which is 48000.

#create an effects chain using the signal and encoding parameters of our files
#thereby defining input and output effect
chain = pysox.CEffectsChain(inputwav, out)

#create the sine effect, producing 3 seconds of sine sweep
effect = pysox.CEffect("synth",[b'10', b'sine', b'300-18000'])
chain.add_effect(effect)
#trim from second 2 to 4 seconds length
chain.add_effect(pysox.CEffect("trim",[b'2', b'0.3']))

chain.flow_effects()
out.close()
#implicit cleanup when python shuts down
