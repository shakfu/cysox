#
# $Id: SoxApp.py 126 2011-04-10 08:58:27Z patrick $
#
# Copyright 2011 Patrick Atamaniuk
#
# This source code is freely redistributable and may be used for
# any purpose.  This copyright notice must be maintained.
# Patrick Atamaniuk and Contributors are not responsible for
# the consequences of using this software.
#
import pysox

class CSoxApp:
    """
    ::

        from pysox import CSoxApp
        sapp = CSoxApp(input1, input2, output, nullparams=(44100,2,32) )
        sapp.flow([ ('trim', [b'0',b'2']), ] )

    or::

        sapp = CSoxApp(input1, input2, input3, nullparams=(44100,2,32), effectparams=[('trim', [b'0',b'2']), ], output='output0' )
        sapp.flow()

    Args:
        inputfile [, ...] outputfile
    
    Kwargs:
        effectparams: list(effectparam)
            efectparam=( name, [arguments] )

        nullparams: set(rate,channels,precision)

        output: string
            if given, all positional arguments are inputs, and this kwarg is the output.
            If output is pysox-chain, the audio will be piped to it's input chain

    If any inputfile is the string 'null', then CNullFile is used to generate silence with the nullparams as signal parameters.
    """
    
    nullparams = None
    effectparams = None
    chain = None
    
    def __init__(self, *files, **kwargs):
        if 'nullparams' in kwargs:
            self.nullparams = kwargs['nullparams']
        else:
            self.nullparams = (48000,2,32)

        if 'effectparams' in kwargs:
            self.effectparams = kwargs['effectparams']
        else:
            self.effectparams = []

        if 'output' in kwargs:
            self.outfilename = kwargs['output']
            self.infilenames = files[:]
        else:
            self.infilenames = files[:-1]
            self.outfilename = files[-1]

        #if len(infilenames) > 1: use combiner
        #if an infilename is CSoxApp, chain it using subprocess
        #if kwargs['output'] then outfilename = %, infilenames=files[:]
        #if kwargs['output'] is pysox-chain: we are input to another pysox process, need chain-output
        
        
        
    def __setup(self, effectparams=None):
        """connect files and setup the chain with its effects"""
        if effectparams:
            self.effectparams = effectparams

        fn = self.infilenames[0]
        if fn == 'null':
            self.infile = self.__nullfile()
        else:
            self.infile = pysox.CSoxStream(self.infilenames[0])
        self.outfile = pysox.CSoxStream(self.outfilename,'w', self.infile.get_signal())
        
        self.chain = pysox.CEffectsChain(self.infile, self.outfile)
        
        for effect in self.effectparams:
            self.chain.add_effect(pysox.CEffect(effect[0],effect[1]))
        
    def flow(self, effectparams=None):
        """flow the chain created in setup
        
        Kwargs:
            effectparams=list(effectparam)
        """
        self.__setup(effectparams)
        self.chain.flow_effects()
        self.__teardown()
        
    def __teardown(self):
        self.infile.close()
        self.outfile.close()
        return True

    def __nullfile(self):
        nsignal = pysox.CSignalInfo(*self.nullparams)
        nencoding = pysox.CEncodingInfo(1,self.nullparams[1])
        return pysox.CNullFile(signalInfo=nsignal, encodingInfo=nencoding)

        