#
# $Id: Test002EncodingInfo.py 108 2011-03-30 12:14:29Z patrick $
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

class ImportingTestCase(unittest.TestCase):
    def setUp(self):
        pass
    def tearDown(self):
        pass
    
    def test_001_constr(self):
        """encodinginfo constructor"""
        e = pysox.CEncodingInfo(0,32)
        self.assert_(isinstance(e, pysox.CEncodingInfo), 'have a CEncodingInfo')
        info = pysox.CEncodingInfo(0,32).get_encodinginfo()
        expect = {'name': 'n/a', 'description': 'Unknown or not applicable', 'compression': 0.0, 'bits_per_sample': 32L, 'encoding': 0}
        self.assert_(info == expect, "encodinginfo match\n%s\n%s"%(info,expect))

        info = pysox.CEncodingInfo(1,32).get_encodinginfo()
        expect = 'Signed PCM'
        self.assert_(info['name'] == expect, "encodinginfo name match\n%s\n%s"%(info,expect))
        info = pysox.CEncodingInfo(12,32).get_encodinginfo()
        expect = 'G.723 ADPCM'
        self.assert_(info['name'] == expect, "encodinginfo match\n%s\n%s"%(info,expect))

        e = pysox.CNullFile().get_encoding()
        self.assert_(isinstance(e, pysox.CEncodingInfo), 'have a CEncodingInfo')
        info = e.get_encodinginfo()
        print info
        self.assert_(info['encoding']==1,'encoding of nullfile is 1: %s'%repr(info))
        self.assert_(info['bits_per_sample']==32,'bps of nullfile is 32: %s'%repr(info))
        

        