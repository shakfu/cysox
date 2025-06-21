#!/usr/bin/env python
#
# test and example usage
#
# $Id: example5-customeffect.py 110 2011-03-30 15:01:21Z patrick $
#
# Copyright 2011 Patrick Atamaniuk
#
# This source code is freely redistributable and may be used for
# any purpose.  This copyright notice must be maintained.
# Patrick Atamaniuk and Contributors are not responsible for
# the consequences of using this software.
#
import pysox

class IEff(pysox.CCustomEffect):
    count = 300
    def drain(self, buffer_object):
        """create 1.68 seconds of sawtooth on both channels
        
        using the container interface of the buffer"""
        #print("Extern callback", self.count, len(buffer_object))
        self.count -= 1
        if not self.count:
            return 0
        
        l = 512 # MUST be less than len(buffer_object)
        for i in xrange(l):
            buffer_object[i]=i*4194304
        return l

#create a custom effect which serves as input provider.
#it generates some audio data, which then will be processed by the rest of the chain (output to out.wav)
input = IEff("input", [])
print(input.get_in_signal())
input.get_in_signal().set_param(rate=44100, channels=2, precision=32)
input.get_out_signal().set_param(rate=44100, channels=2, precision=32)

#setup out file with signal parameters of our input stream
out = pysox.CSoxStream('out1.wav', 'w', input.get_out_signal())
#provide dummy input for encoding parameters, we replace the nullfile with our own input effect
#since IEff is an effect, we set up our stuff like we would be using the internal "synth" effect.
nullfile=pysox.CNullFile(signalInfo=input.get_in_signal())
chain = pysox.CEffectsChain(nullfile, out)
chain.add_effect(input)
print(input.get_in_signal())


print('flowing')
chain.flow_effects()
print(input.get_in_signal())
print('flowing done')
out.close()
