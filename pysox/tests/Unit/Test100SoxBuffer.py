#
# $Id: Test100SoxBuffer.py 92 2011-03-26 18:24:34Z patrick $
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

class SoxBufferTestCase(unittest.TestCase):
    def test_000_import(self):
        """test importing the class"""
        from pysox.sox import SoxSampleBuffer
        self.assert_( type(SoxSampleBuffer) == type(type),'SoxSampleByffer is a type')
            
    def test_001_instance(self):
        """Instantiate a soxbuffer()"""
        buf = pysox.sox.SoxSampleBuffer()
        self.assert_(buf is not None,'we have an object')
        self.assert_(isinstance(buf, pysox.sox.SoxSampleBuffer), 'buf is right class')
        self.assert_(len(buf)==0, 'we have 0 elements: %s'%len(buf))
        list = buf.tolist()
        self.assert_(not list, 'list tests against not')
        self.assert_(len(list)==0, 'list len is 0: %s'%len(list))
        def readindex(): return buf[0]
        self.assertRaises(IndexError, readindex)
        def writeindex(): buf[0]=22
        self.assertRaises(IndexError, writeindex)
        
    def test_002_from_list(self):
        """Instantiate a soxbuffer(list)"""
        buf = pysox.sox.SoxSampleBuffer([1,2,3,4,5,6,7,8,9])
        self.assert_(buf is not None,'we have an object')
        self.assert_(isinstance(buf, pysox.sox.SoxSampleBuffer), 'buf is right class')
        self.assert_(len(buf)==9, 'we have 9 elements: %s'%len(buf))
        list = buf.tolist()
        self.assert_(list == [1,2,3,4,5,6,7,8, 9])

    def test_003_from_bytes(self):
        """Instantiate a soxbuffer(bytes)"""
        data = b'\x01\x00\x00\x00\xff\xff\xff\xff'
        buf = pysox.sox.SoxSampleBuffer(data)
        self.assert_(buf is not None,'we have an object')
        self.assert_(isinstance(buf, pysox.sox.SoxSampleBuffer), 'buf is right class')
        self.assert_(len(buf)==2, 'we have 2 elements: %s'%len(buf))
        list = buf.tolist()
        self.assert_(list == [1, -1],"got list:"+repr(list))
        bs = buf.tobytearray()
        self.assert_(bs==data, 'tobytearray returned original')

    def test_004_from_bytearray(self):
        """Instantiate a soxbuffer(bytearray)"""
        data = bytearray(b'\x01\x00\x00\x00\xff\xff\xff\xff')
        buf = pysox.sox.SoxSampleBuffer(data)
        self.assert_(buf is not None,'we have an object')
        self.assert_(isinstance(buf, pysox.sox.SoxSampleBuffer), 'buf is right class')
        self.assert_(len(buf)==2, 'we have 2 elements: %s'%len(buf))
        list = buf.tolist()
        self.assert_(list == [1, -1],"got list:"+repr(list))
        bs = buf.tobytearray()
        self.assert_(bs==data, 'tobytearray returned original')

    def test_005_from_bytes(self):
        """Instantiate a soxbuffer() and call frombytes(bytes)"""
        data = b'\x01\x00\x00\x00\xff\xff\xff\xff'
        buf = pysox.sox.SoxSampleBuffer()
        buf.frombytes(data)
        self.assert_(buf is not None,'we have an object')
        self.assert_(isinstance(buf, pysox.sox.SoxSampleBuffer), 'buf is right class')
        self.assert_(len(buf)==2, 'we have 2 elements: %s'%len(buf))
        list = buf.tolist()
        self.assert_(list == [1, -1],"got list:"+repr(list))
        bs = buf.tobytearray()
        self.assert_(bs==data, 'tobytearray returned original')

    def test_006_from_bytearray(self):
        """Instantiate a soxbuffer() and call frombytes(bytearray)"""
        data = bytearray(b'\x01\x00\x00\x00\xff\xff\xff\xff')
        buf = pysox.sox.SoxSampleBuffer()
        buf.frombytes(data)
        self.assert_(buf is not None,'we have an object')
        self.assert_(isinstance(buf, pysox.sox.SoxSampleBuffer), 'buf is right class')
        self.assert_(len(buf)==2, 'we have 2 elements: %s'%len(buf))
        list = buf.tolist()
        self.assert_(list == [1, -1],"got list:"+repr(list))
        bs = buf.tobytearray()
        self.assert_(bs==data, 'tobytearray returned original')

    def test_007_from_list(self):
        """Instantiate a soxbuffer() and call fromlist(list)"""
        data = [1,2,3,4,5,6,7,8]
        buf = pysox.sox.SoxSampleBuffer()
        buf.fromlist(data)
        self.assert_(buf is not None,'we have an object')
        self.assert_(isinstance(buf, pysox.sox.SoxSampleBuffer), 'buf is right class')
        self.assert_(len(buf)==8, 'we have 8 elements: %s'%len(buf))
        list = buf.tolist()
        self.assert_(list == data,"got list:"+repr(list))
        bs = buf.tobytearray()
        bdata = bytearray(b'\x01\x00\x00\x00\x02\x00\x00\x00\x03\x00\x00\x00\x04\x00\x00\x00\x05\x00\x00\x00\x06\x00\x00\x00\x07\x00\x00\x00\x08\x00\x00\x00')
        self.assert_(bs==bdata, 'tobytearray returned feasible data')
        
    def test_010_change_list(self):
        """Instantiate a soxbuffer(list) and change the list by index access"""
        buf = pysox.sox.SoxSampleBuffer([1,2,3,4,5,6,7,8,9])
        self.assert_(buf is not None,'we have an object')
        self.assert_(isinstance(buf, pysox.sox.SoxSampleBuffer), 'buf is right class')
        self.assert_(len(buf)==9, 'we have 9 elements: %s'%len(buf))
        list = buf.tolist()
        self.assert_(list == [1,2,3,4,5,6,7,8, 9])
        
        buf[0]=10
        buf[1]=11
        self.assert_(len(buf)==9, 'we have 9 elements: %s'%len(buf))
        list = buf.tolist()
        self.assert_(list == [10,11,3,4,5,6,7,8, 9])

    def test_011_change_writelist(self):
        """Instantiate a soxbuffer from list and change the list using writelist()"""
        buf = pysox.sox.SoxSampleBuffer([1,2,3,4,5,6,7,8,9])
        self.assert_( buf.get_buffer_size() == 9*4 )
        self.assert_(buf is not None,'we have an object')
        self.assert_(isinstance(buf, pysox.sox.SoxSampleBuffer), 'buf is right class')
        self.assert_(len(buf)==9, 'we have 9 elements: %s'%len(buf))
        list = buf.tolist()
        self.assert_(list == [1,2,3,4,5,6,7,8, 9])
        
        buf.writelist([10,11])
        self.assert_(len(buf)==2, 'we have 2 elements: %s'%len(buf))
        list = buf.tolist()
        self.assert_(list == [10,11])

        buf.set_datalen(9*4)
        self.assert_(len(buf)==9, 'we have 9 elements: %s'%len(buf))
        list = buf.tolist()
        self.assert_(list == [10,11,3,4,5,6,7,8, 9])
        self.assert_( buf.get_buffer_size() == 9*4 )
        
        self.assertRaises(IndexError, buf.writelist, [1,2,3,4,5,6,7,8,9,10,11,12])
        self.assertRaises(TypeError, buf.writelist, b'notalist')

    def test_012_change_writebytes(self):
        """Instantiate a soxbuffer from list and change the list using writebytes(b'xx')"""
        buf = pysox.sox.SoxSampleBuffer([1,2,3,4,5,6,7,8,9])
        self.assert_( buf.get_buffer_size() == 9*4 )
        self.assert_(buf is not None,'we have an object')
        self.assert_(isinstance(buf, pysox.sox.SoxSampleBuffer), 'buf is right class')
        self.assert_(len(buf)==9, 'we have 9 elements: %s'%len(buf))
        list = buf.tolist()
        self.assert_(list == [1,2,3,4,5,6,7,8, 9])
        
        buf.writebytes(b'\x09\x00\x00\x00\x0a\x00\x00\x00')
        self.assert_(len(buf)==2, 'we have 2 elements: %s'%len(buf))
        list = buf.tolist()
        self.assert_(list == [9,10])

        buf.set_datalen(9*4)
        self.assert_(len(buf)==9, 'we have 9 elements: %s'%len(buf))
        list = buf.tolist()
        self.assert_(list == [9,10,3,4,5,6,7,8, 9])
        self.assert_( buf.get_buffer_size() == 9*4 )
        
        self.assertRaises(IndexError, buf.writebytes, b'10000000200000003000000040000000500000006000000070000000100000002000000030000000400000005000000060000000700000001000000020000000300000004000000050000000600000007000000010000000200000003000000040000000500000006000000070000000')

    def test_300_memoryview(self):
#        from pysox.sox import PY3
#        if not PY3:
#            return
        import sys
        try:
            memoryview
        except NameError:
            print("\nnot checking memoryview for Python %s"%sys.version)
            return
        print("\n")
        data = bytearray(b'\x01\x00\x00\x00\xff\xff\xff\xff\x00\x01\x00\x00')
        buf = pysox.sox.SoxSampleBuffer(data)
        self.assert_(bytearray(buf) == data, 'bytearray(buf) gives us correct data')
        m = memoryview(buf)
        self.assert_(m.tobytes() == data, 'memoryview tobytes gives us correct data')
#        print(m[:2].tobytes())
#        print(bytes(data[:8]))
        self.assert_(m[:2].tobytes() == bytes(data[:8]), 'memoryview[:2] tobytes gives us correct data')
        self.assert_(len(m)==3, 'len(m) is 3')
        

        data2 = b'\xff\xff\xff\xff\xff\xff\xff\xff'
        buf2 = pysox.sox.SoxSampleBuffer(data2)
        m2 = memoryview(buf2)
        m[1:3]=m2[0:2]
        self.assert_(m.tobytes() == b'\x01\x00\x00\x00\xff\xff\xff\xff\xff\xff\xff\xff', 'Altered memoryview using index assign')
        self.assert_(buf.tobytearray() == b'\x01\x00\x00\x00\xff\xff\xff\xff\xff\xff\xff\xff', 'Altered buf through memoryview')
