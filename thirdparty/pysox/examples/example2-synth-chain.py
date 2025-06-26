#!/usr/bin/env python
#
# test and example usage
#
# $Id: example2-synth-chain.py 110 2011-03-30 15:01:21Z patrick $
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

#create an audio file with the same parameters as the input file
out = pysox.CSoxStream('out.wav', 'w', inputwav.get_signal())

#create an effects chain using the signal and encoding parameters of our files
#thereby defining input and output effect
chain = pysox.CEffectsChain(inputwav, out)

#create the sine effect, producing 3 seconds of sine
effect = pysox.CEffect("synth",[b'10', b'sine', b'300-3000'])
chain.add_effect(effect)
#mix with another waveform
chain.add_effect(pysox.CEffect("synth",[b'10', b'sine', b'mix', b'2000-200']))
#and apply frequency modulation
chain.add_effect(pysox.CEffect("synth",[b'10', b'sine', b'fmod', b'100-200']))
#trim from second 2 to 4 seconds length
chain.add_effect(pysox.CEffect("trim",[b'2', b'4']))

chain.flow_effects()

#cleanup
out.close()
del out
inputwav.close()
del inputwav
