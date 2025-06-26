#
# $Id: Test001IO.py 121 2011-04-03 09:37:33Z patrick $
#
# Copyright 2011 Patrick Atamaniuk
#
# This source code is freely redistributable and may be used for
# any purpose.  This copyright notice must be maintained.
# Patrick Atamaniuk and Contributors are not responsible for
# the consequences of using this software.
#
import unittest
import pysox
import common

class IOTestCase(unittest.TestCase):
    def setUp(self):
        pass
    def tearDown(self):
        try:
            os.unlink('test1.wav')
        except Exception:
            pass

    def test_001_nullfile(self):
        """try to write and read an audio file"""
        #print("Writing data", path, args)
        nullfile = pysox.CNullFile()
        signal = nullfile.get_signal()
        expect = {'channels': 2L, 'length': 0, 'rate': 48000.0, 'precision': 32L}
        info = signal.get_signalinfo()
        self.assert_(info == expect, 'signalinfo of nullfile ok \n%s\n%s'%(repr(expect), repr(info)))
        del nullfile
    
    def test_002_writefile(self):
        """try to write and read an audio file"""
        path = "test1.wav"
        args = [b'3', b'sine', b'300-3000']
        #print("Writing data", path, args)
        nullfile = pysox.CNullFile()
        signal = nullfile.get_signal()
        out = pysox.CSoxStream(path, 'w', signal)
        chain = pysox.CEffectsChain(nullfile, out)
        effect = pysox.CEffect("synth", args)
        chain.add_effect(effect)
        chain.flow_effects()
        out.close()
        nullfile.close()
        del out
        del nullfile
        soxi = common.soxi(path)
        expect = {'encoding': [1,'Signed PCM'], 'precision': 32L, 'channels': 2L, 'rate': 48000.0, 'bits_per_sample': 32L, 'duration': 3.0, 'audiosize': 1152000L, 'filename': 'test1.wav', 'length': 288000, 'filesize': 1152080L, 'samples': 144000L}
        self.assert_(soxi==expect,"Expected output file signal ok \n%s\n%s"%(repr(soxi),repr(expect)))

    def test_003_chain(self):
        """make an effect chain using stream constructor"""
        #create a nullfile for input parameter definition. synth effect needs this
        nullfile = pysox.CNullFile()
        #create an audio file with the same parameters as the input file
        out = pysox.CSoxStream('out.wav', 'w', nullfile.get_signal())        
        #create an effects chain using the signal and encoding parameters of our files
        #thereby defining input and output effect
        chain = pysox.CEffectsChain(nullfile, out)
        
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

        info = out.get_signal().get_signalinfo()
        length = 48000*2*4 #2 channels, 4 seconds
        expect = {'channels': 2L, 'length': length, 'rate': 48000.0, 'precision': 32L}
        self.assert_(info == expect, 'signalinfo of outfile ok \n%s\n%s'%(repr(expect), repr(info)))
        info = out.get_encoding().get_encodinginfo()
        del info['compression'] #inf is not testable??
        expect = {'name': 'Signed PCM', 'description': 'Signed Integer PCM', 'bits_per_sample': 32L, 'encoding': 1}
        self.assert_(info == expect, 'encodinginfo of outfile ok \n%s\n%s'%(repr(expect), repr(info)))
        out.close()
        del nullfile
        del out
