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
import sys
from cython.operator cimport dereference as deref
from cpython cimport PY_MAJOR_VERSION
cimport pysox.csox as csox
from sox cimport CEffect, CSoxStream, toCharP, SoxSampleBuffer, pysoxtransportheader_t, CPysoxPipeStream

DEF SOX_SUCCESS = 0
DEF SOX_EOF = -1

cdef class MixerBase(CEffect):
    """Virtual object to replace the internal input effect of sox
    
    Kwargs:
        defer_file_open <Boolean> use for pipes as input to avoid early opening of subprocesses
    """
    cdef object inputnames
    cdef object inputs
    cdef csox.sox_effect_handler_t *handler
    cdef int currentInput
    cdef size_t out_length
    
    cdef object defer_file_open # do not open input streams in constructor
    
    def __init__(self, *args, **kwargs):
        self.inputs = [] #these need to contain sox_format_t thingies
        self.inputnames = []
        self.currentInput = 0
        self.out_length = 0
        self.defer_file_open = False
        if 'defer_file_open' in kwargs:
            self.defer_file_open = True
            
        CEffect.__init__(self, *args, **kwargs)
        
        
    def __dealloc__(self):
        if self.handler:
            csox.free(self.handler)
            
    cdef create(self, name, arguments):
        """create the effects internal structures
        called from constructor
        """
        self.name = name
        self.inputnames = arguments
        self.effect = csox.sox_create_effect(self._setup_handler());
        self.effect.priv = <void *>self

        #if at least one input is a pipe, defer opening of inputs
        for name in self.inputnames:
            if isinstance(name, CPysoxPipeStream):
                self.defer_file_open = True
                break

        if not self.defer_file_open:
            self.setup_signals()
#        else:
#            print('deferring signal open()')
        
    cdef setup_signals(self):
        self.inputs = [] #these need to contain sox_format_t thingies
        sys.stdout.flush()
        for name in self.inputnames:
            if isinstance(name, CPysoxPipeStream): #name is already a pipe object
                inf = name
                inf.start_read() #get the header
            elif isinstance(name, CSoxStream): #name is already a soxstream, assume it is opened
                inf = name
            else: # name is a string
                inf = CSoxStream(name, 'r') #will do start reading and get the header
            self.inputs.append(inf)

        sys.stdout.flush()
        cdef csox.sox_signalinfo_t * insignal = (<CSoxStream>self.inputs[self.currentInput]).cget_signal()
        cdef csox.sox_encodinginfo_t * inencoding = (<CSoxStream>self.inputs[self.currentInput]).cget_encoding()
      
        self.effect.in_signal = deref(insignal) 
        self.effect.out_signal = deref(insignal) 
        self.effect.in_encoding = inencoding
        self.effect.out_encoding = inencoding
        self.precalculate_output_length()
        
    cdef csox.sox_effect_handler_t * _setup_handler(self):
        self.handler = <csox.sox_effect_handler_t *>csox.malloc(sizeof(csox.sox_effect_handler_t))
        self.handler.name = toCharP(self.name)
        self.handler.flags = csox.SOX_EFF_MCHAN + csox.SOX_EFF_LENGTH
        self.handler.drain = __combiner_mixerbase_cb_drain
        self.handler.start = __combiner_mixerbase_cb_start
        self.handler.stop = __combiner_mixerbase_cb_stop
        self.handler.kill = __combiner_mixerbase_cb_kill
        self.handler.priv_size = 0
        return self.handler;
        
    cdef size_t precalculate_output_length(self):
        """overload to initialize self.effect.out_signal.length with a proper value.
        Defaults to in_signal.length from setup_signals()"""
        pass

    cdef int sox_read_wide(self, CSoxStream input, csox.sox_sample_t * buf, size_t max):
        """
        read max wide samples into buf returning the number of read wide samples.
        A wide sample contains one sample from each channel.
        """
        return input.sox_read_wide(buf, max / self.effect.in_signal.channels)

    cdef int start(self):
        """start is called within chain.sox_add_effect, and at that point,
        our effect in_signal and out_signal are set,
        our effect in_encoding is chain->in_enc, out_encoding is chain->out_enc,
        
        Returns:
            SOX_SUCCESS to indicate readiness
            otherwise, to indicate a failure in setup
        """
        if self.defer_file_open:
            self.setup_signals()
        return SOX_SUCCESS
    
    cdef int stop(self):
        return 0 #return number of clippings

    cdef int kill(self):
        return 0 #return value ignored

    cdef int drain(self, csox.sox_sample_t * obuf, size_t * osamp):
        """same as flow but without input"""
        return SOX_EOF

    cdef int flow(self, csox.sox_sample_t *ibuf, csox.sox_sample_t *obuf, size_t *isamp, size_t *osamp):
        """Run effect on all channels at once, or
        flow multiple times, once per channel
        Returns:
            SOX_SUCCESS: can continue
            SOX_EOF: request stop for end of data
        """
        return SOX_EOF

cdef int __combiner_mixerbase_cb_start(csox.sox_effect_t * effp):
    obj = <MixerBase>effp.priv # class ConcatenateFiles
    return obj.start()

cdef int __combiner_mixerbase_cb_stop(csox.sox_effect_t * effp):
    obj = <MixerBase>effp.priv # class ConcatenateFiles
    return obj.stop()

cdef int __combiner_mixerbase_cb_kill(csox.sox_effect_t * effp):
    obj = <MixerBase>effp.priv # class ConcatenateFiles
    obj.kill()
    effp.priv=NULL #need to void the pointer to the python object since sox_delete_effect would otherwise free it
    return 0

cdef int __combiner_mixerbase_cb_drain(csox.sox_effect_t * effp, csox.sox_sample_t * obuf, size_t * osamp):
    obj = <MixerBase>effp.priv # class ConcatenateFiles
    return obj.drain(obuf, osamp)

cdef int __combiner_mixerbase_cb_flow(csox.sox_effect_t * effp, csox.sox_sample_t *ibuf, csox.sox_sample_t *obuf, size_t *isamp, size_t *osamp):
    obj = <MixerBase>effp.priv # class ConcatenateFiles
    return obj.flow(ibuf, obuf, isamp, osamp)

cdef class ConcatenateFiles(MixerBase):
    """ConcatenateFiles("input", ["test1.wav", "test2.wav"])
    
    Input effect provider for CEffectChain in order to concatenate multiple input files.
    This effect replaces the sox internal input effect.

    All audio data must be the same format (bitrate, channels, precision)
    The output's length is the total length of all combined signals.
    """
    cdef size_t precalculate_output_length(self):
        """initialize self.effect.out_signal.length with a proper value"""
        cdef size_t length = 0
        for iobj in self.inputs:
            length += (<CSoxStream>iobj).cget_signal().length
        #print("precalc output l",length)
        self.effect.out_signal.length = length

    cdef int drain(self, csox.sox_sample_t * obuf, size_t * osamp):
        cdef size_t nread
        if self.currentInput >= len(self.inputs):
            return SOX_EOF #last one reached
        nread = 1024
        nread = (<CSoxStream>self.inputs[self.currentInput]).sox_read_wide(obuf, nread)

        osamp[0] = nread * self.effect.in_signal.channels #nread is wide
        self.out_length += osamp[0]
        self.effect.out_signal.length = self.out_length
        if nread > 0:
            return SOX_SUCCESS

        #advance
        (<CSoxStream>self.inputs[self.currentInput]).close()
        self.currentInput +=1
        if self.currentInput >= len(self.inputs):
            return SOX_EOF #last one reached
        #print 'advanced to',self.currentInput
        return self.drain(obuf, osamp)

#
#
#
DEF MIXFILES_BUFSIZE = 1024 #FIXME use sox_globals.bufsiz

cdef class MixFiles(MixerBase):
    """MixFiles("input", ["test1.wav", "test2.wav"])
    
    Input effect provider for CEffectChain in order to mix multiple input files.
    This effect replaces the sox internal input effect.
    
    Volumes are mixed down by 1/n where n is the number of inputs.
    
    Clipping probably will not occur with this method, but the signal appears to be
    less loud than the originals.
    
    The input files signals must be equal, meaning bitrate and channels must be equal.
    The signal's length can be different, the output will get the length of the longest signal.
    """
    cdef csox.sox_sample_t * mixbuffer
    cdef csox.sox_sample_t * readbuffer
    cdef float volume
    cdef size_t bufsize

    cdef float __calc_volume(self):
        self.volume = 1.0/len(self.inputs)

    cdef setup_signals(self):
        MixerBase.setup_signals(self)
        self.bufsize = MIXFILES_BUFSIZE * sizeof(csox.sox_sample_t) * self.effect.in_signal.channels #wide
        self.mixbuffer = <csox.sox_sample_t *>csox.malloc(self.bufsize) #free in kill
        self.readbuffer = <csox.sox_sample_t *>csox.malloc(self.bufsize) #free in kill
        csox.bzero(self.mixbuffer, self.bufsize)
        csox.bzero(self.readbuffer, self.bufsize)
        self.__calc_volume()
        
    cdef int kill(self):
        if not self.mixbuffer is NULL:
            csox.free(self.mixbuffer)
            self.mixbuffer = NULL
        if not self.readbuffer is NULL:
            csox.free(self.readbuffer)
            self.readbuffer = NULL
        return 0 #return value ignored

    #mixer function, this will create quite optimal c code.
    #FIXME use one buffer per input and mix using (double) cast
    cdef size_t do_mix(self, csox.sox_sample_t *inb, csox.sox_sample_t *outb, size_t wlen, float factor):
        """
        Args:
            wlen: number of wide samples
        """
        cdef csox.sox_sample_t i=0
        cdef size_t len = wlen * self.effect.in_signal.channels
        while i < len:
            outb[i] = outb[i] + <csox.sox_sample_t>(inb[i]*factor)
            i +=1
        return len

    cdef int drain(self, csox.sox_sample_t * obuf, size_t * osamp):
        cdef csox.sox_format_t * ft
        cdef size_t nread
        cdef size_t max_nread
        cdef int ninputs

        ninputs = len(self.inputs)   
        self.currentInput = 0
        max_nread = 0
        csox.bzero(self.mixbuffer, self.bufsize)
        while self.currentInput < ninputs:
            
            nread = MIXFILES_BUFSIZE
            csox.bzero(self.readbuffer, self.bufsize)
            nread = (<CSoxStream>self.inputs[self.currentInput]).sox_read_wide(self.readbuffer, nread) #wide
            
            if nread:
                self.do_mix(self.readbuffer, self.mixbuffer, nread, self.volume) #wide
                max_nread = max(nread, max_nread)
            self.currentInput +=1
            
        osamp[0] = max_nread * self.effect.in_signal.channels
        self.out_length += osamp[0]
        self.effect.out_signal.length = self.out_length
        if max_nread > 0: # can read again in next iteration
            csox.bcopy(self.mixbuffer, obuf, max_nread * sizeof(csox.sox_sample_t) * self.effect.in_signal.channels);
            return SOX_SUCCESS
        return SOX_EOF #last one reached

import math
cdef class PowerMixFiles(MixFiles):
    """PowerMixFiles("input", ["test1.wav", "test2.wav"])
    
    Input effect provider for CEffectChain in order to mix multiple input files.
    This effect replaces the sox internal input effect.
    
    Volumes are mixed down by 1/sqrt(n) where n is the number of inputs.
    
    Clipping might occur here, but in most cases distortions are not susceptible.
    """
    cdef float __calc_volume(self):
        self.volume = 1.0/math.sqrt(len(self.inputs))

cdef class SocketOutput(MixerBase):
    """SocketOutput("output",[connection])
    
    Output the chain data to a multiprocess socket. Used as output effect at the end of a chain.
    
    Args:
        connection: multiprocessing Pipe of a process child
        
    Example::
    
        parent_conn, child_conn = Pipe()
        output = SocketOutput("output", [child_conn])
        chain = pysox.CEffectsChain()
        chain.add_effect(output)
        ...
    
    """
    cdef object conn
    cdef create(self, name, arguments):
        self.name = name
        # not calling MixerBase.create(self, name, arguments)
        self.effect = csox.sox_create_effect(self._setup_handler());
        self.effect.priv = <void *>self
        self.conn = arguments[0]

    cdef csox.sox_effect_handler_t * _setup_handler(self):
        self.handler = <csox.sox_effect_handler_t *>csox.malloc(sizeof(csox.sox_effect_handler_t))
        #print 'creating handler'
        self.handler.name = toCharP(self.name)
        self.handler.flags = csox.SOX_EFF_MCHAN + csox.SOX_EFF_LENGTH
        self.handler.flow = __combiner_mixerbase_cb_flow
        self.handler.drain = NULL
        self.handler.start = __combiner_mixerbase_cb_start
        self.handler.stop = __combiner_mixerbase_cb_stop
        self.handler.kill = __combiner_mixerbase_cb_kill
        self.handler.priv_size = 0
        return self.handler;

    cdef int flow(self, csox.sox_sample_t *ibuf, csox.sox_sample_t *obuf, size_t *isamp, size_t *osamp):
#        print("SocketOutput flow ", deref(isamp))
        cdef char *s
        cdef bytes b
        cdef size_t length
        osamp[0] = 0
        try:
            if self.conn:
                if not deref(isamp): #nothing to send
                    return SOX_SUCCESS
                if PY_MAJOR_VERSION >= 3:
                    inbuf = SoxSampleBuffer()
                    inbuf.set_buffer(ibuf, deref(isamp))
                    self.conn.send_bytes(inbuf)
                else:
                    length = deref(isamp)*4 #FIXME use self.effect.in_signal.precision
                    s = <char *>ibuf
                    b=s[:length] #will make a copy to a python bytes() object
                    self.conn.send_bytes(b, 0, length)
                return SOX_SUCCESS
        except Exception as e:
#            print("Exception",e)
            import traceback
            traceback.print_exc()
            return SOX_EOF
        return SOX_SUCCESS #0 samples put in obuf, we are end of chain

    cdef int send_header(self):
        cdef csox.sox_signalinfo_t * isig
        cdef pysoxtransportheader_t header
        cdef char * chead
        cdef bytes bhead
        if not self.conn:
            return 0
        cdef length = sizeof(pysoxtransportheader_t)
        csox.bcopy(b'.PYS', header.magic, 4)
        csox.bcopy(&self.effect.in_signal, &header.signalinfo, sizeof(self.effect.out_signal))
        
        chead = <char *>&header
        bhead = chead[:length]
        self.conn.send_bytes(bytes(bhead), 0, length)
        return 0
    
    cdef int start(self):
        """send signal info header"""
#        print 'sending',self.get_out_signal()
        #MixerBase.start(self)
        self.send_header()
        return 0
    
    cdef int stop(self):
        if self.conn:
            self.conn.send_bytes(b'')
            self.conn.close()
            self.conn = None
        return 0
