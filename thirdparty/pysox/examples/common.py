#
# common example helper
#
# $Id: common.py 48 2011-03-22 17:56:11Z patrick $
#
# Copyright 2011 Patrick Atamaniuk
#
# This source code is freely redistributable and may be used for
# any purpose.  This copyright notice must be maintained.
# Patrick Atamaniuk and Contributors are not responsible for
# the consequences of using this software.
#

import pysox

def mktestfile(path=None, args=None, vol=None):
    """Create a test audio file
    
    Kwargs:
        path: string filename (optional)
        args: array of bytes used as waveform parameters
    """
    if path is None:
        path = 'test.wav'
    if args is None:
        args = [b'3', b'sine', b'300-3000']
    print("Writing data", path, args)
    nullfile = pysox.CNullFile()
    signal = nullfile.get_signal()
    out = pysox.CSoxStream(path, 'w', signal)
    chain = pysox.CEffectsChain(nullfile, out)
    effect = pysox.CEffect("synth", args)
    chain.add_effect(effect)
    
    if vol:
        chain.add_effect(pysox.CEffect("vol",[vol]))
    chain.flow_effects()
    out.close()
    del out
    nullfile.close()
    del nullfile

if __name__ == '__main__':
    mktestfile()