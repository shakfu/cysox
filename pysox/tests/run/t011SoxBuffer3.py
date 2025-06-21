#
# $Id: t011SoxBuffer3.py 89 2011-03-26 11:43:42Z patrick $
#
# Copyright 2011 Patrick Atamaniuk
#
# This source code is freely redistributable and may be used for
# any purpose.  This copyright notice must be maintained.
# Patrick Atamaniuk and Contributors are not responsible for
# the consequences of using this software.
#
__doc__="""
>>> pass
"""

from pysox.sox import PY3
if PY3:
    __doc__="""Open an audio file and decrease the volume using the builtin vol effect, write to out.wav
    >>> from pysox.sox import SoxSampleBuffer
    >>> from pysox.sox import u
    >>> ssb = SoxSampleBuffer(u('ASDFGHJKSDFGH').encode('utf-8'))
    >>> print(len(ssb))
    3
    >>> print("%s"%bytearray(ssb).decode('utf-8'))
    ASDFGHJKSDFG
    >>> memoryview(ssb.tobytearray()).tobytes()
    b'ASDFGHJKSDFG'
    """
pass
