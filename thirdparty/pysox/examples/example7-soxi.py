#!/usr/bin/env python
#
# test and example usage
#
# $Id: example7-soxi.py 110 2011-03-30 15:01:21Z patrick $
#
# Copyright 2011 Patrick Atamaniuk
#
# This source code is freely redistributable and may be used for
# any purpose.  This copyright notice must be maintained.
# Patrick Atamaniuk and Contributors are not responsible for
# the consequences of using this software.
#
"""Open test.wav, apply the vol effect and write to out.wav"""

import pysox
from common import mktestfile

mktestfile()


#open an audio file
testwav = pysox.CSoxStream("test.wav")
signal = testwav.get_signal()
info = signal.get_signalinfo()
encoding = testwav.get_encoding()
encodinginfo = encoding.get_encodinginfo()

length = info['length']
samples = length / info['channels']
duration = samples / info['rate']
size = length * info['precision'] / 8 / 1024 / 1024.0
print("""Input File   : %s
Channels     : %s
Bit rate     : %s
Precision    : %s-bit
Samples      : %s
Duration     : %s seconds
Encoding     : %s (see sox.h)
Bits/channel : %s
audio size   : %.2fM (not including headers and metadata)
""" % (str(testwav),
       info['channels'], info['rate'], info['precision'],
       samples,
       duration,
       encodinginfo['encoding'], encodinginfo['bits_per_sample'],
       size
       ))

del testwav
