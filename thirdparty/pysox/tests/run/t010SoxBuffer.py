#
# $Id: t010SoxBuffer.py 89 2011-03-26 11:43:42Z patrick $
#
# Copyright 2011 Patrick Atamaniuk
#
# This source code is freely redistributable and may be used for
# any purpose.  This copyright notice must be maintained.
# Patrick Atamaniuk and Contributors are not responsible for
# the consequences of using this software.
#

"""Open an audio file and decrease the volume using the builtin vol effect, write to out.wav
>>> from pysox.sox import SoxSampleBuffer
>>> from pysox.sox import u
>>> ssb = SoxSampleBuffer()
>>> ssb.frombytes(bytearray(b'123457890'))
>>> print(len(ssb))
2
>>> print("%s"%bytearray(ssb).decode('utf-8'))
12345789
>>> print("%s"%ssb.tobytearray().decode('utf-8'))
12345789
>>> ssb.frombytes(bytearray(b'abcdefght'))
>>> print(len(ssb))
2
>>> print("%s"%bytearray(ssb).decode('utf-8'))
abcdefgh
>>> ssb = SoxSampleBuffer([65,66,67,68,69,70,71,72,73,74])
>>> print(len(ssb))
10
>>> print(len(ssb.tobytearray()))
40
>>> ssb = SoxSampleBuffer(b'ASDFGHJKSDFGH')
>>> print(len(ssb))
3
>>> print("%s"%bytearray(ssb).decode('utf-8'))
ASDFGHJKSDFG
>>> ssb = SoxSampleBuffer(bytearray(b'ASDFGHJKSDFGH'))
>>> print(len(ssb))
3
>>> print("%s"%bytearray(ssb).decode('utf-8'))
ASDFGHJKSDFG
>>> ssb = SoxSampleBuffer(u('ASDFGHJKSDFGH').encode('utf-8'))
>>> print(len(ssb))
3
>>> print("%s"%bytearray(ssb).decode('utf-8'))
ASDFGHJKSDFG
"""
pass
