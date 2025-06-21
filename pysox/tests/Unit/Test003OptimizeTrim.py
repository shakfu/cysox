#
# $Id: Test003OptimizeTrim.py 113 2011-03-31 08:03:46Z patrick $
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
        self.iname = "test1.wav"
        self.oname = "out.wav"
    def tearDown(self):
        try:
            os.unlink(self.iname)
        except Exception:
            pass
        try:
            os.unlink(self.oname)
        except Exception:
            pass

    def test_003_trim(self):
        """test seeking with trim effect"""
        common.mktestfile(self.iname, [b'600', b'sine', b'300-3000'])
        print("testfile created")
        input = pysox.CSoxStream(self.iname)
        output = pysox.CSoxStream(self.oname, 'w', input.get_signal())        

        chain = pysox.CEffectsChain(input, output)

        chain.add_effect( pysox.CEffect("trim",[b'550', b'10']) )
        chain.flow_effects()
        output.close()
        input.close()
        info = common.soxi(self.oname)
        print(info)
