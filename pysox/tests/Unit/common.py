#
# common example helper
#
# $Id: common.py 101 2011-03-30 10:43:02Z patrick $
#
# Copyright 2011 Patrick Atamaniuk
#
# This source code is freely redistributable and may be used for
# any purpose.  This copyright notice must be maintained.
# Patrick Atamaniuk and Contributors are not responsible for
# the consequences of using this software.
#
import os
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
    #print("Writing data", path, args)
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

def soxi(path):    
    #open an audio file
    st = os.stat(path)
    if not st:
        return None
    filesize = st.st_size
    testwav = pysox.CSoxStream(path)
    info = testwav.get_signal().get_signalinfo()
    encoding = testwav.get_encoding()
    encodinginfo = encoding.get_encodinginfo()

    length = info['length']
    samples = length / info['channels']
    duration = samples / info['rate']
    size = length * info['precision'] / 8
    try:
        return {'filename':str(testwav),
               'length':info['length'], 
               'channels':info['channels'], 
               'rate': info['rate'], 
               'precision': info['precision'],
               'samples':samples,
               'duration':duration,
               'encoding':[encodinginfo['encoding'],encodinginfo['name']], 
               'bits_per_sample':encodinginfo['bits_per_sample'],
               'audiosize':size, 
               'filesize':filesize}
    finally:
        testwav.close()

if __name__ == '__main__':
    mktestfile()