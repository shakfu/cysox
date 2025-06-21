#
# Python objects wrapping the c implementation
#
# $Id: sox.pyx 9 2011-03-19 22:13:46Z patrick $
#
# Copyright 2011 Patrick Atamaniuk
#
# This source code is freely redistributable and may be used for
# any purpose.  This copyright notice must be maintained.
# Patrick Atamaniuk and Contributors are not responsible for
# the consequences of using this software.
#
from cython.operator cimport dereference as deref, preincrement as inc 
cimport pysox.csox as csox
from sox cimport CEffect, toCharP
from sox cimport SoxSampleBuffer

from pysox.sox import PY3

DEF SOX_SUCCESS = 0
DEF SOX_EOF = -1

#
#
#
cdef class CCustomEffect(CEffect):
    """Example custom effect usable as audio data input into a chain.
    CCustomEffect must be overloaded and the method callback is then used to
    provide audio input data. 
    """
    cdef csox.sox_effect_handler_t handler
    
    cdef create(self, name, arguments):
        self.name = name
        self.effect = csox.sox_create_effect(self._setup_handler());
        self.effect.priv = <void *>self
        
    cdef csox.sox_effect_handler_t * _setup_handler(self):
        self.handler.name = toCharP(self.name)
        self.handler.flags = csox.SOX_EFF_MCHAN
        self.handler.flow = __customeffects__CCustomEffect__flow
        self.handler.drain = __customeffects__CCustomEffect__drain
        self.handler.kill = __customeffects__CCustomEffect__kill
        self.handler.start = __customeffects__CCustomEffect__start
        self.handler.stop = __customeffects__CCustomEffect__stop
        self.handler.priv_size = 0
        return &self.handler;

    cpdef int start(self):
        """Called when chain starts flowing
        
        Used to do last setups
        """
        return SOX_SUCCESS
    
    cpdef int stop(self):
        """Called when chain shuts down
        
        Returns:
            number of clipped samples
        """
        return 0 #return number of clippings

    cpdef int kill(self):
        """Called when chain shuts down, after stop
        
        Used to do final cleanups
        """
        return 0 #return value ignored

    cpdef object drain(self, SoxSampleBuffer buffer_object):
        """virtual function, must be overloaded
        
        Args:
            SoxSampleBuffer buffer_object: accessor to raw sox buffer using Buffer interface or container interface
            
        Returns:
            number of samples processed or 0 if end of file
        """
        return 0

    cpdef int flow(self, SoxSampleBuffer ibuf, SoxSampleBuffer obuf, int isamp,):
        """virtual function, must be overloaded
        
        Args:
            SoxSampleBuffer buffer_object: accessor to raw sox buffer using Buffer interface or container interface
            
        Returns:
            number of samples in obuf for next effect or
            0 if this is the last effect (output)
        Raises:
            Exception if some error occured in order to stop processing
            
        """
        return 0

cdef int __customeffects__CCustomEffect__start(csox.sox_effect_t * effp):
    obj = <CCustomEffect>effp.priv # class ConcatenateFiles
    return obj.start()

cdef int __customeffects__CCustomEffect__stop(csox.sox_effect_t * effp):
    obj = <CCustomEffect>effp.priv # class ConcatenateFiles
    return obj.stop()

cdef int __customeffects__CCustomEffect__kill(csox.sox_effect_t * effp):
    obj = <CCustomEffect>effp.priv # class ConcatenateFiles
    obj.kill()
    effp.priv=NULL #need to void the pointer to the python object since sox_delete_effect would otherwise free it
    return 0

cdef int __customeffects__CCustomEffect__flow(csox.sox_effect_t * effp, csox.sox_sample_t *ibuf, csox.sox_sample_t *obuf, size_t *isamp, size_t *osamp):
    cdef int insamples, outsamples
    obj = <CCustomEffect>effp.priv # class ConcatenateFiles

    insamples = deref(isamp)
    outsamples = deref(osamp)
    inbuf = SoxSampleBuffer()
    inbuf.set_buffer(ibuf, insamples)
    outbuf = SoxSampleBuffer()
    outbuf.set_buffer(obuf, outsamples)
        
    try:
        osamp[0] = obj.flow(inbuf, outbuf, insamples)
    except Exception, e:
        print("Exception",e)
        osamp[0] = 0
        return SOX_EOF
    return SOX_SUCCESS

cdef int __customeffects__CCustomEffect__drain(csox.sox_effect_t * effp, csox.sox_sample_t * obuf, size_t * osamp):
    cdef int n=0
    cdef int nread
    cdef int length
    obj = <CCustomEffect>effp.priv
    try:
        length = deref(osamp)
        buf = SoxSampleBuffer()
        buf.set_buffer(obuf, length)
        
        nread = obj.drain(buf)
    except Exception, e:
        print("Exception", e)
        nread = 0

    if nread == 0:
        osamp[0] = 0
        return SOX_EOF
    osamp[0] = nread
    return SOX_SUCCESS

