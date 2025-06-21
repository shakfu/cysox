#
# $Id: __init__.py 80 2011-03-25 10:57:42Z patrick $
#
# Copyright 2011 Patrick Atamaniuk
#
# This source code is freely redistributable and may be used for
# any purpose.  This copyright notice must be maintained.
# Patrick Atamaniuk and Contributors are not responsible for
# the consequences of using this software.
#
def makeTestFile(path=None, args=None):
    """Create a test audio file
    
    Kwargs:
        path: string filename (optional)
        args: set of effects 
    """
    import pysox
    if path is None:
        path = 'test.wav'
    if args is None:
        args = [ ('synth', [b'3', b'sine', b'300-3000']), ]
    nullfile = pysox.CNullFile()
    signal = nullfile.get_signal()
    out = pysox.CSoxStream(path, 'w', signal)
    chain = pysox.CEffectsChain(nullfile, out)
    for eff in args:
        effect = pysox.CEffect(eff[0], eff[1])
        chain.add_effect(effect)    
    chain.flow_effects()
    out.close()
    del out
    nullfile.close()
    del nullfile