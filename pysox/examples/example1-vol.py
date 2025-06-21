#!/usr/bin/env python
#
# test and example usage
#
# $Id: example1-vol.py 47 2011-03-22 16:36:31Z patrick $
#
# Copyright 2011 Patrick Atamaniuk
#
# This source code is freely redistributable and may be used for
# any purpose.  This copyright notice must be maintained.
# Patrick Atamaniuk and Contributors are not responsible for
# the consequences of using this software.
#
"""Open test.wav, apply the vol effect and write to out.wav"""
from common import mktestfile
import pysox

mktestfile()


#open an audio file
testwav = pysox.CSoxStream("test.wav")

#create an audio file with the same parameters as the input file
out = pysox.CSoxStream('out.wav', 'w', testwav.get_signal())

#create an effects chain using the signal end encoding parameters of our files
#thereby defining input and output effect
chain = pysox.CEffectsChain(testwav, out)

chain.add_effect(pysox.CEffect("vol",[b'18db']))

chain.flow_effects()

#cleanup
out.close()
del out
testwav.close()
del testwav
