#!/usr/bin/env python
#
# test and example usage
#
# $Id: example8-combine_mix.py 110 2011-03-30 15:01:21Z patrick $
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

mktestfile("test1.wav",[b'1', b'sine', b'300-3000'], vol=b'0.7')
mktestfile("test1b.wav",[b'0.5', b'sine', b'3000-4000'], vol=b'0.7')
mktestfile("test2.wav",[b'2', b'sine', b'3000-300'], vol=b'0.7')

dummy = pysox.CNullFile()
out = pysox.CSoxStream('out1.wav', 'w', dummy.get_signal())
chain = pysox.CEffectsChain(dummy, out)
id = pysox.MixFiles("input", ["test1.wav", "test2.wav"])
chain.add_effect(id)
chain.flow_effects()

out = pysox.CSoxStream('out2.wav', 'w', dummy.get_signal())
chain = pysox.CEffectsChain(dummy, out)
id = pysox.MixFiles("input", ["test2.wav", "test1.wav"])
chain.add_effect(id)
chain.flow_effects()

out = pysox.CSoxStream('out3.wav', 'w', dummy.get_signal())
chain = pysox.CEffectsChain(dummy, out)
id = pysox.PowerMixFiles("input", ["test1.wav", "test2.wav"])
chain.add_effect(id)
chain.flow_effects()

out = pysox.CSoxStream('out4.wav', 'w', dummy.get_signal())
chain = pysox.CEffectsChain(dummy, out)
id = pysox.PowerMixFiles("input", ["test2.wav", "test1.wav"])
chain.add_effect(id)
chain.flow_effects()

out = pysox.CSoxStream('test3.wav', 'w', dummy.get_signal())
chain = pysox.CEffectsChain(dummy, out)
id = pysox.ConcatenateFiles("input", ["test1.wav", "test1b.wav", "test1.wav"])
chain.add_effect(id)
chain.flow_effects()

out = pysox.CSoxStream('test4.wav', 'w', dummy.get_signal())
chain = pysox.CEffectsChain(dummy, out)
id = pysox.ConcatenateFiles("input", ["test1b.wav", "test2.wav"])
chain.add_effect(id)
chain.flow_effects()

out = pysox.CSoxStream('out5.wav', 'w', dummy.get_signal())
chain = pysox.CEffectsChain(dummy, out)
id = pysox.MixFiles("input", ["test4.wav", "test3.wav"])
chain.add_effect(id)
chain.flow_effects()

# chain with no input file, but input effect

#setup an input effect which will mix 2 files
id = pysox.MixFiles("input", ["test4.wav", "test3.wav"])
#setup an output file using the signal parameters of our input effect
out = pysox.CSoxStream('out6.wav', 'w', id.get_out_signal())
#setup a chain using output parameters from output file
chain = pysox.CEffectsChain(ostream=out)
#add input effect, this will setup our chain's input parameters
chain.add_effect(id)
#process the effects -> mix the files
chain.flow_effects()

