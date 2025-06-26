#
# $Id: Test011CombineMix.py 100 2011-03-30 09:55:44Z patrick $
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

class MixTestCase(unittest.TestCase):
    def setUp(self):
        mktestfile("test1.wav",[b'1', b'sine', b'300-3000'])
        mktestfile("test2.wav",[b'1', b'sine', b'3000-300'])

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
    
    def test_001_mix(self):
        """mix 2 wavefiles into out.wav"""
        rate = 48000
        precision = 32
        channels = 2
        outlength = channels * rate
        inlength = channels * rate
        
        dummy = sox.CNullFile()
        out = sox.CSoxStream('outcombine.wav', 'w', dummy.get_signal())
        
        chain = sox.CEffectsChain(dummy, out)
        id = sox.MixFiles("input", ["test1.wav", "test2.wav"])
        self.assert_(id)
        iinfo = id.get_in_signal().get_signalinfo()
        self.assert_(iinfo['length']==inlength )
        self.assert_(iinfo['channels']==channels )
        self.assert_(iinfo['precision']==precision )
        self.assert_(iinfo['rate']==rate )

        chain.add_effect(id)
        chain.flow_effects()

        oinfo = out.get_signal().get_signalinfo()
        out.close()
        
        self.assert_(oinfo['length']==outlength )
        self.assert_(oinfo['channels']==channels )
        self.assert_(oinfo['precision']==precision )
        self.assert_(oinfo['rate']==rate )
        
        so = os.stat('outcombine.wav')
        self.assert_(so, 'have output file %s'%repr(so))
        #print(soxi('test1.wav'))

        oinfo = soxi('outcombine.wav')
        #print(oinfo)
        self.assert_(oinfo['length']==outlength , oinfo)
        self.assert_(oinfo['channels']==channels , oinfo)
        self.assert_(oinfo['precision']==precision , oinfo)
        self.assert_(oinfo['rate']==rate )
        #print(int(oinfo['samples']), int(rate)*channels)
        self.assert_(int(oinfo['samples'])==int(rate), oinfo) #1 seconds of signal
        size = rate*channels*precision/8
        #print(oinfo['audiosize'], size)
        self.assert_(oinfo['audiosize'] == size, oinfo)

    def test_002_powermix(self):
        """powermix 2 wavefiles into out.wav"""
        rate = 48000
        precision = 32
        channels = 2
        outlength = channels * rate
        inlength = channels * rate
        
        dummy = sox.CNullFile()
        out = sox.CSoxStream('outcombine.wav', 'w', dummy.get_signal())
        
        chain = sox.CEffectsChain(dummy, out)
        id = sox.PowerMixFiles("input", ["test1.wav", "test2.wav"])
        self.assert_(id)
        iinfo = id.get_in_signal().get_signalinfo()
        self.assert_(iinfo['length']==inlength )
        self.assert_(iinfo['channels']==channels )
        self.assert_(iinfo['precision']==precision )
        self.assert_(iinfo['rate']==rate )

        chain.add_effect(id)
        chain.flow_effects()

        oinfo = out.get_signal().get_signalinfo()
        out.close()
        
        self.assert_(oinfo['length']==outlength )
        self.assert_(oinfo['channels']==channels )
        self.assert_(oinfo['precision']==precision )
        self.assert_(oinfo['rate']==rate )
        
        so = os.stat('outcombine.wav')
        self.assert_(so, 'have output file %s'%repr(so))
        #print(soxi('test1.wav'))

        oinfo = soxi('outcombine.wav')
        #print(oinfo)
        self.assert_(oinfo['length']==outlength , oinfo)
        self.assert_(oinfo['channels']==channels , oinfo)
        self.assert_(oinfo['precision']==precision , oinfo)
        self.assert_(oinfo['rate']==rate )
        #print(int(oinfo['samples']), int(rate)*channels)
        self.assert_(int(oinfo['samples'])==int(rate), oinfo) #1 seconds of signal
        size = rate*channels*precision/8
        #print(oinfo['audiosize'], size)
        self.assert_(oinfo['audiosize'] == size, oinfo)
        