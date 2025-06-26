#
# $Id: Test000Import.py 110 2011-03-30 15:01:21Z patrick $
#
# Copyright 2011 Patrick Atamaniuk
#
# This source code is freely redistributable and may be used for
# any purpose.  This copyright notice must be maintained.
# Patrick Atamaniuk and Contributors are not responsible for
# the consequences of using this software.
#
import unittest
import sys
print sys.path
class ImportingTestCase(unittest.TestCase):
    def setUp(self):
        pass
    def tearDown(self):
        pass
    
    def test_001_import(self):
        """try to import pysox"""
        import pysox
