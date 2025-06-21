#!/usr/bin/env python
#
# test the SoxSampleBuffer object which exposes the sox sample buffer for
# effect callbacks
#
# $Id: mtest.py 89 2011-03-26 11:43:42Z patrick $
#
# Copyright 2011 Patrick Atamaniuk
#
# This source code is freely redistributable and may be used for
# any purpose.  This copyright notice must be maintained.
# Patrick Atamaniuk and Contributors are not responsible for
# the consequences of using this software.
#
from pysox.sox import SoxSampleBuffer
from pysox.sox import u
def main():
    print('test frombytes bytearray', '-'*20)
    ssb = SoxSampleBuffer()
    ssb.frombytes(bytearray(b'123457890'))
    print(ssb,len(ssb))
    print(bytearray(ssb))
    print(ssb.tobytearray())
    print('test frombytes bytearray overwrite', '-'*20)
    ssb.frombytes(bytearray(b'abcdefght'))
    print(ssb,len(ssb))
    print(bytearray(ssb))

    print('test constructor list', '-'*20)
    ssb = SoxSampleBuffer([60,61,62,63,64,65,66,67,68,69])
    print(ssb,len(ssb))
    print(bytearray(ssb))

    print('test constructor bytes', '-'*20)
    ssb = SoxSampleBuffer(b'ASDFGHJKSDFGH')
    print(ssb,len(ssb))
    print(bytearray(ssb))

    print('test constructor bytearray', '-'*20)
    ssb = SoxSampleBuffer(bytearray(b'ASDFGHJKSDFGH'))
    print(ssb,len(ssb))
    print(bytearray(ssb))

    print('test constructor unicode', '-'*20)
    ssb = SoxSampleBuffer(u('ASDFGHJKSDFGH').encode('utf-8'))
    print(ssb,len(ssb))
    print(bytearray(ssb))

main()
