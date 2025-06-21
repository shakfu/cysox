#
# $Id: Test010CombineConcatenate.py 122 2011-04-03 13:26:54Z patrick $
#
# Copyright 2011 Patrick Atamaniuk
#
# This source code is freely redistributable and may be used for
# any purpose.  This copyright notice must be maintained.
# Patrick Atamaniuk and Contributors are not responsible for
# the consequences of using this software.
#
import unittest
import os
import pysox as sox
from .common import mktestfile, soxi

class ConcatenateTestCase(unittest.TestCase):
    def setUp(self):
        mktestfile("test1.wav",[b'1', b'sine', b'300-3000'])
        mktestfile("test2.wav",[b'1', b'sine', b'3000-300'])
        print('setup done.','-'*40)
    def tearDown(self):
        try:
            os.unlink('test1.wav')
        except Exception:
            pass
        try:
            os.unlink('test2.wav')
        except Exception:
            pass
        try:
            os.unlink('outcombine.wav')
        except Exception:
            pass
    
    def test_001_concatenate(self):
        """concatenate 2 wavefiles into out.wav"""
        rate = 48000
        precision = 32
        channels = 2
        outlength = channels * rate * 2
        inlength = channels * rate
        
        dummy = sox.CNullFile()
        out = sox.CSoxStream('outcombine.wav', 'w', dummy.get_signal())
        
        chain = sox.CEffectsChain(dummy, out)
        id = sox.ConcatenateFiles("input", ["test1.wav", "test2.wav"])
        self.assert_(id)
        iinfo = id.get_in_signal().get_signalinfo()
#        print('iinfo',iinfo, inlength)
        self.assert_(iinfo['length']==inlength )
        self.assert_(iinfo['channels']==channels )
        self.assert_(iinfo['precision']==precision )
        self.assert_(iinfo['rate']==rate )

        chain.add_effect(id)
        oinfo = out.get_signal().get_signalinfo()
#        print('oinfo',oinfo)
        chain.flow_effects()

        oinfo = out.get_signal().get_signalinfo()
        print 'output signal',oinfo

        self.assert_(oinfo['length']==outlength )
        self.assert_(oinfo['channels']==channels )
        self.assert_(oinfo['precision']==precision )
        self.assert_(oinfo['rate']==rate )
        out.close()
        
        so = os.stat('outcombine.wav')
        self.assert_(so, 'have output file %s'%repr(so))
        #print(soxi('test1.wav'))

        oinfo = soxi('outcombine.wav') 
        print(oinfo)
        self.assert_(oinfo['length']==outlength , oinfo)
        self.assert_(oinfo['channels']==channels , oinfo)
        self.assert_(oinfo['precision']==precision , oinfo)
        self.assert_(oinfo['rate']==rate )
        #print(int(oinfo['samples']), int(rate)*channels)
        self.assert_(int(oinfo['samples'])==int(rate)*2, oinfo) #2 seconds of signal
        size = rate*channels*precision/8 *2
        #print(oinfo['audiosize'], size)
        self.assert_(oinfo['audiosize'] == size, oinfo)
        