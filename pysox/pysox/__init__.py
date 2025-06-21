#
# $Id: __init__.py 126 2011-04-10 08:58:27Z patrick $
#
# Copyright 2011 Patrick Atamaniuk
#
# This source code is freely redistributable and may be used for
# any purpose.  This copyright notice must be maintained.
# Patrick Atamaniuk and Contributors are not responsible for
# the consequences of using this software.
#
"""
Python bindings for libsox
--------------------------

This are the python bindings for the library
libsox, which is an audio manipulation library used by sox.

Quickstart
----------
The most important classes are CSoxStream, CEffectsChain and CEffect. Using
these classes all internal effects provided by libsox can be applied to
audio files.

Using CNullFile, the effects requiring dummy input (such as synth) can also be used.

Please check out the examples provided with the source, they will set you up fast and easy.

Example
-------
::

	import pysox

	def mktestfile():
            #open the nullfile to provide signal parameters: 48000kHz, 32bit on 2 channels
            #the nullfile produces an infinite amount of silence. So only to be used with
            # trim effect or synth, which has a length parameter
	    nullfile = pysox.CNullFile()
	    signal = nullfile.get_signal()
            #open an output file using the nullfiles signal parameters
	    out = pysox.CSoxStream('test.wav', 'w', signal)

            #create the effect chain with input and output streams
	    chain = pysox.CEffectsChain(nullfile, out)
            #add the synth effect to the chain, we use 3 seconds of sine sweep
	    effect = pysox.CEffect("synth",[b'3', b'sine', b'300-3000'])
	    chain.add_effect(effect)

            #process the effects chain, this applies all effecte on the input, producing the output
	    chain.flow_effects()

            #cleanup
	    out.close()
            #libsox internal cleanup takes place if we delete our chain or the script exits. So we are lazy here.

	mktestfile()
	
"""

from pysox.sox import CSoxStream, CEffect, CEffectsChain, CPysoxPipeStream
from pysox.sox import CSignalInfo, CEncodingInfo, SoxSampleBuffer

from pysox.sox import CNullFile
from pysox.customeffects import CCustomEffect
from pysox.combiner import ConcatenateFiles, MixFiles, PowerMixFiles, SocketOutput
from pysox.SoxApp import CSoxApp

__all__ = [ k for k in locals().keys() if not k.startswith('_') ]
