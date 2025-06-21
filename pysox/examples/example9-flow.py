#!/usr/bin/env python
#
# test and example usage
#
# $Id: example9-flow.py 83 2011-03-25 21:53:45Z patrick $
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
mktestfile(args = [b'0.002', b'sine', b'300-3000']) #make about 100 samples

class OEff(pysox.CCustomEffect):
    def flow(self, ibuf, obuf, isamp):
        """read from ibuf and end the chain by providing 0 output"""
        print("Extern callback", isamp, len(ibuf))
        lr='L'
        for n in ibuf:
            print(lr,n)
            if lr=='L':
                lr='R'
            else:
                lr='L'
        return 0 #0 samples put in obuf, we are end of chain

#create a custom effect which serves as input provider.
#it generates some audio data, which then will be processed by the rest of the chain (output to out.wav)
testwav = pysox.CSoxStream("test.wav")
output = OEff("output", [])
#provide no output to chain, we add it later
chain = pysox.CEffectsChain(testwav)
#add the output
chain.add_effect(output)
#process
chain.flow_effects()
#cleanup
testwav.close()