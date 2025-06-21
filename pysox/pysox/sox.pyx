#
# Python objects wrapping the c implementation
#
# $Id: sox.pyx 126 2011-04-10 08:58:27Z patrick $
#
# Copyright 2011 Patrick Atamaniuk
#
# This source code is freely redistributable and may be used for
# any purpose.  This copyright notice must be maintained.
# Patrick Atamaniuk and Contributors are not responsible for
# the consequences of using this software.
#
from libc cimport stdlib
from libc.stdint cimport uint32_t, int32_t, uint64_t
cimport cpython.buffer
from cython.operator cimport dereference as deref, preincrement as inc 
cimport pysox.csox as csox

#from sox cimport CEffect #needed??? think not FIXME
#from sys import version_info #FIXME from python_version cimport PY_MAJOR_VERSION
from cpython cimport PY_MAJOR_VERSION
import types

DEF SOX_SUCCESS = 0
DEF SOX_SEEK_SET = 0

PY3 = PY_MAJOR_VERSION >= 3
if PY3:
    def b(s):
        return s.encode("utf-8")
    def u(s):
        return s
else:
    def b(s):
        return s
    def u(s):
        return unicode(s, "unicode_escape")

cdef unicode char2u(char * s):
    if PY3:
        return u(s.decode('utf-8'))
    else:
        return u(s)

cdef char * toCharP(uobj):
    cdef char * result
    try:
        if PY3:
            bobj = <bytes>b(uobj)
        else:
            bobj = uobj
        return <char *>bobj
    except Exception, e:
        print('XXXXXXX',e)
        print('XXXXXXX',uobj)
        import traceback,sys
        traceback.print_exc()
        sys.stdout.flush()
################################################################################################
#
#
################################################################################################
class PysoxError(Exception):
    """Exception which is raised by the pysox system when some configuration is not acceptable
    """
    pass

################################################################################################
#
#
################################################################################################
cdef class CEncodingInfo:
    """Representation of struct sox_encodinginfo_t"""
#    cdef csox.sox_encodinginfo_t * encoding
#    cdef csox.sox_encodinginfo_t  s_encoding

    UNKNOWN = 0  #,
    SIGN2 = 1    #, /* signed linear 2's comp: Mac */
    UNSIGNED = 2 #, /* unsigned linear: Sound Blaster */
    FLOAT = 3    #, /* floating point (binary format) */
    FLOAT_TEXT = 4 #, /* floating point (text format) */
    FLAC = 5     #, /* FLAC compression */
    HCOM = 6     #, /*  */
    WAVPACK = 7  #, /*  */
    WAVPACKF = 8 #, /*  */
    ULAW = 9     #, /* u-law signed logs: US telephony, SPARC */
    ALAW = 10     #, /* A-law signed logs: non-US telephony, Psion */
    G721 = 11     #, /* G.721 4-bit ADPCM */
    G723 = 12     #, /* G.723 3 or 5 bit ADPCM */
    CL_ADPCM = 13 #, /* Creative Labs 8 --> 2,3,4 bit Compressed PCM */
    CL_ADPCM16 = 14#, /* Creative Labs 16 --> 4 bit Compressed PCM */
    MS_ADPCM = 15 #, /* Microsoft Compressed PCM */
    IMA_ADPCM = 16#, /* IMA Compressed PCM */
    OKI_ADPCM = 17#, /* Dialogic/OKI Compressed PCM */
    DPCM = 18     #, /*  */
    DWVW = 19     #, /*  */
    DWVWN = 20    #, /*  */
    GSM = 21      #, /* GSM 6.10 33byte frame lossy compression */
    MP3 = 22      #, /* MP3 compression */
    VORBIS = 23   #, /* Vorbis compression */
    AMR_WB = 24   #, /* AMR-WB compression */
    AMR_NB = 25   #, /* AMR-NB compression */
    CVSD = 26     #, /*  */
    LPC10 = 27    #, /*  */

    def __init__(self, *args, **kwargs):
        """Constructor to create an encodinginfo

        .. class:: pysox.CEncodingInfo(CSoxEncoding.SIGN2, 32)
        
        The optional positional arguments encoding, bits_per_sample can be given,
        in order to generate a static encodinginfo suitable to provide configuration data for streams.
        """
        self.encoding = NULL
        if len(args) > 0:
            self.encoding = &self.s_encoding
            self.encoding.encoding = args[0]
        if len(args) > 1:
            self.encoding.bits_per_sample = args[1]

    def __repr__(self):
        cdef csox.sox_encodings_info_t edesc
        edesc = csox.sox_encodings_info[<int>self.encoding.encoding]

        return u'CencodingInfo(%s,%s,"%s","%s",%s)' % (
            str(self.encoding.encoding),
            str(self.encoding.bits_per_sample),
            edesc.name,edesc.desc,
            str(self.encoding.compression))
    def get_encodinginfo(self):
        """.. method:: get_encodinginfo()
        
        Return a dictionary describing the encoding of the stream.
        """
        cdef csox.sox_encodings_info_t edesc
        edesc = csox.sox_encodings_info[<int>self.encoding.encoding]
        return {'encoding':self.encoding.encoding,
                'bits_per_sample':self.encoding.bits_per_sample,
                'compression':self.encoding.compression,
                'name':edesc.name,
                'description':edesc.desc
                }

    cdef cset_encoding(self, csox.sox_encodinginfo_t * encoding):
        self.encoding = encoding
    cdef csox.sox_encodinginfo_t * cget_encoding(self):
        return self.encoding

    def set_param(self, **param):
        """.. method:: set_param( [encoding=ecode] [, bits_per_sample=bps] )
        
        Alter the given parameters of this encodinginfo.
        
        *ecode* is the numeric encoding, see sox.h, enum sox_encoding_t for encodings.
        CEncodingInfo defines symbols for encoding as class attributes::
        
            CSoxEncoding.UNKNOWN = 0 #,
            CSoxEncoding.SIGN2 = 1   #, /* signed linear 2's comp: Mac */
            CSoxEncoding.UNSIGNED = 2 #, /* unsigned linear: Sound Blaster */
            CSoxEncoding.FLOAT = 3    #, /* floating point (binary format) */
            CSoxEncoding.FLOAT_TEXT = 4 #, /* floating point (text format) */
            CSoxEncoding.FLAC = 5     #, /* FLAC compression */
            CSoxEncoding.HCOM = 6     #, /*  */
            CSoxEncoding.WAVPACK = 7  #, /*  */
            CSoxEncoding.WAVPACKF = 8 #, /*  */
            CSoxEncoding.ULAW = 9     #, /* u-law signed logs: US telephony, SPARC */
            CSoxEncoding.ALAW = 10     #, /* A-law signed logs: non-US telephony, Psion */
            CSoxEncoding.G721 = 11     #, /* G.721 4-bit ADPCM */
            CSoxEncoding.G723 = 12     #, /* G.723 3 or 5 bit ADPCM */
            CSoxEncoding.CL_ADPCM = 13 #, /* Creative Labs 8 --> 2,3,4 bit Compressed PCM */
            CSoxEncoding.CL_ADPCM16 = 14#, /* Creative Labs 16 --> 4 bit Compressed PCM */
            CSoxEncoding.MS_ADPCM = 15 #, /* Microsoft Compressed PCM */
            CSoxEncoding.IMA_ADPCM = 16#, /* IMA Compressed PCM */
            CSoxEncoding.OKI_ADPCM = 17#, /* Dialogic/OKI Compressed PCM */
            CSoxEncoding.DPCM = 18     #, /*  */
            CSoxEncoding.DWVW = 19     #, /*  */
            CSoxEncoding.DWVWN = 20    #, /*  */
            CSoxEncoding.GSM = 21      #, /* GSM 6.10 33byte frame lossy compression */
            CSoxEncoding.MP3 = 22      #, /* MP3 compression */
            CSoxEncoding.VORBIS = 23   #, /* Vorbis compression */
            CSoxEncoding.AMR_WB = 24   #, /* AMR-WB compression */
            CSoxEncoding.AMR_NB = 25   #, /* AMR-NB compression */
            CSoxEncoding.CVSD = 26     #, /*  */
            CSoxEncoding.LPC10 = 27    #, /*  */
        
        *bps* is the sample rate in bits per sample
        
        """
        if 'encoding' in param:
            self.signal.encoding = param['encoding']
        if 'bits_per_sample' in param:
            self.signal.bits_per_sample = param['bits_per_sample']

################################################################################################
#
#
################################################################################################
cdef class CSignalInfo:
    """Representation of struct sox_signalinfo_t"""
#    cdef csox.sox_signalinfo_t * signal
#    cdef csox.sox_signalinfo_t s_signal
    
    def __init__(self, *args, **kwargs):
        """create a signalinfo descriptor
        
        .. class:: pysox.CSignalInfo([rate, channels, precision] [,length])
        
        If the parameters are given, the signalinfo is a static structure usable to provide signal data for streams.
        """
        self.signal = NULL
        if len(args) > 0:
            self.signal = &self.s_signal
            self.signal.rate = args[0]
        if len(args) > 1:
            self.signal.channels = args[1]
        if len(args) > 2:
            self.signal.precision = args[2]
        if len(args) > 3:
            self.signal.length = args[3]

    def __repr__(self):
        return u'CSignalInfo(%s,%s,%s,%s)' % (
            str(self.signal.rate),
            str(self.signal.channels),
            str(self.signal.precision),
            str(self.signal.length))

    def get_signalinfo(self):
        """Retrieve the details of the signal
        
        Returns:
        
            dict containing rate, channels, precision and length
        """
        return {'rate':self.signal.rate,
                'channels':self.signal.channels,
                'precision':self.signal.precision,
                'length':self.signal.length
                }

    cdef cset_signal(self, csox.sox_signalinfo_t * signal):
        self.signal = signal
    cdef csox.sox_signalinfo_t * cget_signal(self):
        return self.signal
    
    def set_param(self, **param):
        """alter the parameters of this signalinfo.
        Either of the kwargs can be given to set appropriate aspect.
        
        Kwargs:
        rate: int
        
        channels: int
        
        precision: int
        
        length: int
        """
        if 'rate' in param:
            self.signal.rate = param['rate']
        if 'channels' in param:
            self.signal.channels = param['channels']
        if 'precision' in param:
            self.signal.precision = param['precision']
        if 'length' in param:
            self.signal.length = param['length']
            
################################################################################################
#
#
################################################################################################
cdef class CSoxStream:
    """
    Representation of struct sox_format_t
    
    This class also has the capability of opening audio files for reading and writing
    and to retrieve their stream parameters such as encodinginfo and signalinfo.
    
    """
    #cdef csox.sox_format_t * ft
    def __init__(self, path=None, mode=None, CSignalInfo signalInfo=None, CEncodingInfo encodingInfo=None, fileType=None):
        """Create a sox stream (sox_format_t)

        .. py:class:: pysox.CSoxStream(path)
        .. py:class:: pysox.CSoxStream(path, 'w', CSignalInfo signalInfo)
        .. py:class:: pysox.CSoxStream(path, 'w', CSignalInfo signalInfo [, CEncodingInfo encodingInfo] [, fileType])
        
        Constructor
    
        Kwargs:
            :param String path: The filename to read or write
            :param String mode: optional file mode 'r' or 'w', defaults to 'r'
            :param CSignalInfo signalInfo: required only for write mode to define the signal characteristics using the :py:class:`CSignalInfo` class.
            :param CEncodingInfo encodingInfo: optional output encoding for write mode using the :py:class:`CEncodingInfo` class.
            :param String fileType: optional, e.g. "wav"
            :raises IOError: if the file cannot be opened
            :raises TypeError: if write mode is requested and the signalInfo is not given        
        """
        self.ft = NULL
        if not mode:
            mode = 'r'
        if path:
            if mode == 'r':
                self.open_read(path, signalInfo, encodingInfo, fileType)
            elif mode == 'w':
                self.open_write(path, signalInfo, encodingInfo, fileType)
        
    def __dealloc__(self):
        self.close()

    def __str__(self):
        if not self.ft:
            return u''
        return char2u(self.ft.filename)
    def __repr__(self):
        if not self.ft:
            return u'CSoxStream()'
        return u'CSoxStream(%s, %s)' %(char2u(self.ft.filename), char2u(self.ft.filetype))
    
    cdef csox.sox_format_t * get_ft(self):
        return self.ft
    
    cdef char * asCharP(self):
        return <char *>self.ft
    
    cdef int sox_read(self, csox.sox_sample_t * obuf, size_t max):
        """public size_t sox_read(csox.sox_sample_t * obuf, size_t max)
        
        read max samples into obuf returning the number of read samples.
        max must be divisable by the number of channels.
        """
        cdef size_t nread
        nread = csox.sox_read(self.ft, obuf, max);
        return nread

    cdef int sox_read_wide(self, csox.sox_sample_t * obuf, size_t max):
        """public size_t sox_read_wide(csox.sox_sample_t * obuf, size_t max)
        
        read max wide samples into obuf returning the number of read wide samples.
        A wide sample contains one sample from each channel.
        """
        cdef size_t nread
        nread = self.sox_read(obuf, max * self.ft.signal.channels) // self.ft.signal.channels;
        return nread

    cpdef int open_read(self, path, CSignalInfo signalInfo=None, CEncodingInfo encodingInfo=None, fileType=None) except ?0:
        """
        .. method:: open_read(path [, CSignalInfo signalInfo=None] [, CEncodingInfo encodingInfo=None] [, fileType=None])
        
        open an audio file for reading
        
        Raises:
            IOError if file not existent
        """
        cdef char * cpath = NULL
        cdef csox.sox_encodinginfo_t * encoding = NULL
        cdef csox.sox_signalinfo_t * signal = NULL
        cdef char * cfiletype = NULL
        
        cpath = toCharP(path)
        
        if signalInfo:
            signal = signalInfo.cget_signal() #exctract the c struct
        if encodingInfo:
            encoding = encodingInfo.cget_encoding()
        if fileType:
            cfiletype = toCharP(fileType)

        self.ft = csox.sox_open_read(cpath, signal , encoding,  cfiletype)
        if not self.ft:
            raise IOError("No such file")
        return 1

    cpdef open_write(self, path, CSignalInfo signalInfo, CEncodingInfo encodingInfo=None, fileType=None):
        """
        .. method:: open_write(path, CSignalInfo signalInfo [, CEncodingInfo encodingInfo=None] [, fileType=None])

        Open this stream for writing
        
        Args:
            path
            
            signalInfo
        
        Kwargs:
            encodingInfo
            
            fileType
            
        Raises:
            TypeError if signalInfo is missing
            
            IOError if the file cannot be opened

        """
        cdef char * cpath = NULL
        cdef csox.sox_signalinfo_t * signal = NULL
        cdef csox.sox_encodinginfo_t  * encoding = NULL
        cdef char * cfiletype = NULL

        if not signalInfo:
            raise TypeError("signalInfo must be a CSignalInfo instance")
        
        cpath = toCharP(path)
        signal = signalInfo.cget_signal() #exctract the c struct
        
        if encodingInfo:
            encoding = encodingInfo.cget_encoding()

        if fileType:
            cfiletype = toCharP(fileType)
        
        self.ft = csox.sox_open_write(cpath, signal, encoding, cfiletype, NULL, NULL)
        if not self.ft:
            raise IOError("No such file")

    def close(self):
        """Close the stream"""
        if self.ft:
            csox.sox_close(self.ft)
            self.ft = NULL

    def get_signal(self):
        """retrieve the CSignalInfo object representation of this streams signal
        
        Changes to the signal's parameter will change the stream's parameters, too"""
        if not self.ft:
            return None
        si = CSignalInfo()
        si.cset_signal(&self.ft.signal)
        return si
    cdef csox.sox_signalinfo_t * cget_signal(self):
        return &self.ft.signal
    
    def get_encoding(self):
        """retrieve the CEncodingInfo object representation of this streams encoding
        
        Changes to the encoding's parameters will change the stream's encoding, too"""
        if not self.ft:
            return None
        si = CEncodingInfo()
        si.cset_encoding(&self.ft.encoding)
        return si
    cdef csox.sox_encodinginfo_t * cget_encoding(self):
        return &self.ft.encoding

################################################################################################
#
#
################################################################################################
cdef class CPysoxPipeStream(CSoxStream):
    """Input stream analog to CSoxStream, but reading from a python:processes Pipe
    
    Kwargs:
        path: multiprocessing.Pipe socket endpoint
    """
#    cdef object channel
#    cdef object initialdata

    def __init__(self, path=None, mode=None, CSignalInfo signalInfo=None, CEncodingInfo encodingInfo=None, fileType=None):
        #NOT calling __parent__.__init__(self)
        self.channel = path
        self.initialdata = None

    def __str__(self):
        if not self.channel:
            return u''
        return str(self.channel)
    def __repr__(self):
        if not self.channel:
            return u'CPysoxPipeStream()'
        return u'CPysoxPipeStream(%s)' %(str(self.channel))

    cdef int sox_read(self, csox.sox_sample_t * obuf, size_t max):
        raise RuntimeError('CPysoxPipeStream::sox_read not implemented')
        return 0

    cdef int sox_read_wide(self, csox.sox_sample_t * obuf, size_t max):
        """public size_t sox_read_wide(csox.sox_sample_t * obuf, size_t max)

        read max wide samples into obuf returning the number of read wide samples.
        A wide sample contains one sample from each channel.
        """
        cdef bytes data
        cdef char * cdata
        cdef size_t length=0
        print('ZZZZZZZZZZ',self,'sox_read_wide',max)
        try:
            data = self.channel.recv_bytes()
        except EOFError:
            print('CPySoxPipeStream EOF')
            return 0
        length = len(data)
##            print("MixSockets::drain td",type(data), length, data)
        if not data or not length:
            print("IEffr data is None, channel is finished", self)
        else:
            cdata = data #cast to char
            csox.bcopy(cdata, obuf, length); #FIXME: return max samples at most!
            return length // sizeof(csox.sox_sample_t) // self.ft.signal.channels #wide
        return 0

    cpdef int open_read(self, path, CSignalInfo signalInfo=None, CEncodingInfo encodingInfo=None, fileType=None) except ?0:
        print(self,'open_read')
        return 0

    cpdef open_write(self, path, CSignalInfo signalInfo, CEncodingInfo encodingInfo=None, fileType=None):
        return 0
    
    def close(self):
        """Close the stream"""
        if self.ft:
            stdlib.free(self.ft)
            self.ft = NULL

    def start_read(self):
        print("CPysoxPipeStream::start_read")
        self.ft = <csox.sox_format_t *>stdlib.malloc(sizeof(csox.sox_format_t)) #will free in close
        self.receive_header()

    cdef int receive_header(self):
        cdef pysoxtransportheader_t header
        cdef size_t length 
        length = sizeof(pysoxtransportheader_t)        
        self.initialdata = b''
        
        data = self.channel.recv_bytes()
        csox.bcopy(<char *>data, <char *>&header, length)
        print(self,"got header")
        csox.bcopy((<char *>&header)+4, &self.ft.signal, length-4) 
        
        if len(data) > length:
            self.initialdata = data[length:]
            print("Got excessive data while reading header",len(self.initialdata))
        return SOX_SUCCESS
################################################################################################
#
#
################################################################################################
cdef class CNullFile(CSoxStream):
    """nullstream = CNullFile()
    
    The null input file, which produces an infinite amount of silence
    
    Kwargs:
        path: string
        
        mode: string
        
        signalInfo: CSignalInfo
            if provided, these signal parameters are used.
            Otherwise the signal will be 48000 rate, 2 channels, 32 bits
        
        encodingInfo: CEncodingInfo
            if provided, use that encodingInfo,
            otherwise we'll have 32bit signed integer PCM
        
        fileType: string
    """
    def __init__(self, path=None, mode=None, CSignalInfo signalInfo=None, CEncodingInfo encodingInfo=None, fileType=None):
        """Create the null input file, which produces silence of infinite length."""
        mode= u'r'
        path= u'null'
        fileType = u'null'
        if not signalInfo:
            signalInfo = CSignalInfo(48000,2,32, 0)
        if not encodingInfo:
            encodingInfo = CEncodingInfo(1,32)
        CSoxStream.__init__(self, path, mode, signalInfo, encodingInfo, fileType)
    
################################################################################################
#
#
################################################################################################
cdef class CEffect:
    """CEffect("trim", [ b'2', b'4'])
    
    Basic sox effect wraps all builtin effects.
    It is also used to derive custom effects by inheriting and overloading the create method.
    
    Kwargs:
        name: string of the effects name
        
        arguments: array of effect arguments containing byte strings
    """
#    cdef csox.sox_effect_t *effect
#    cdef name
    
    SOX_EFF_CHAN = 1           #/* Can alter # of channels */
    SOX_EFF_RATE = 2           #/* Can alter sample rate */
    SOX_EFF_PREC = 4           #/* Can alter sample precision */
    SOX_EFF_LENGTH = 8           #/* Can alter audio length */
    SOX_EFF_MCHAN = 16          #/* Can handle multi-channel */
    SOX_EFF_NULL = 32          #/* Does nothing */
    SOX_EFF_DEPRECATED = 64        #/* Is living on borrowed time */
    SOX_EFF_GAIN = 128         #/* Does not support gain -r */
    SOX_EFF_MODIFY = 256         #/* Does not modify samples */
    SOX_EFF_ALPHA = 512         #/* Is experimental/incomplete */
    SOX_EFF_INTERNAL = 1024        #/* Is in libSoX but not sox */

    def __init__(self, *args, **kwargs):
        """Create a sox internal effect
        
        optional parameters to initialize the effect:
        @param <string> name of the effect
        @param <[]> array of effect arguments
        @see create 
        """
        self.name = None
        self.effect = NULL
        self.argv = NULL
        self.argc=0
        if len(args):
            self.create(args[0], args[1])

    def __dealloc__(self):
        cdef int c = 0
        if self.argc > 0:
            while c<self.argc:
                if self.argv[c]:
                    stdlib.free(self.argv[c])
                inc(c)
            stdlib.free(self.argv)
            self.argv = NULL
            self.argc = 0

    def __repr__(self):
        return u"CEffect(%s)"%self.name #name is pyobj
    
    cpdef get_name(self):
        """Retrieve the effect's name
        
        Returns:
            string
        """
        return self.name
    cdef csox.sox_effect_t * get_effect(self):
        return self.effect
    
    cdef create(self, name, arguments):
        """Create an effect
        
        Kwargs:
            name: string Name of the effect (e.g. 'vol')
            
            arguments: array of  [bytes, ...] array of bytes up to 10
                e.g. [ b'2', b'sine', b'1500' ]
        """ 
        cdef int argc = 0
        cdef int clen = 0
        cdef char *carg
        cdef csox.sox_format_t * ft
        cdef char *cname
        self.name = name
        cname = toCharP(name)
        self.effect = csox.sox_create_effect(csox.sox_find_effect(cname))
        
        self.argc = len(arguments)
        self.argv = <char **>stdlib.malloc((self.argc+1) * sizeof(char *))
        for a in arguments:
            if isinstance(a, CSoxStream):
                carg = (<CSoxStream>a).asCharP()
                clen = sizeof(csox.sox_format_t)
            else:
                carg = <char *>a
                clen = len(a)
            self.argv[argc] = <char *>stdlib.malloc(clen+1)
            csox.bcopy(carg, self.argv[argc],clen)
            self.argv[argc][clen]=<char>0
            argc +=1
        self.argv[argc]=NULL
        csox.sox_effect_options(self.effect, self.argc, self.argv)
    
    #
    # access to signal and encoding of effect_t
    #
    def get_in_signal(self):
        """retrieve the CSignalInfo object representation of this streams in_signal"""
        if not self.effect:
            return None
        si = CSignalInfo()
        si.cset_signal(&self.effect.in_signal)
        return si
#    def setInSignal(self):
#        pass
    def get_out_signal(self):
        """retrieve the CSignalInfo object representation of this streams out_signal"""
        if not self.effect:
            return None
        si = CSignalInfo()
        si.cset_signal(&self.effect.out_signal)
        return si
    def set_out_signal(self):
        pass
# CHECK: encoding is const in here???
    def get_in_encoding(self):
        """retrieve the CEncodingInfo object representation of this streams in_encoding"""
        if not self.effect:
            return None
        si = CEncodingInfo()
        si.cset_encoding(<csox.sox_encodinginfo_t *>self.effect.in_encoding) #discard const by casting
        return si
#    def set_in_encoding(self):
#        pass
    def get_out_encoding(self):
        """retrieve the CEncodingInfo object representation of this streams in_encoding"""
        if not self.effect:
            return None
        si = CEncodingInfo()
        si.cset_encoding(<csox.sox_encodinginfo_t *>self.effect.out_encoding) #discard const by casting
        return si
#    def set_out_encoding(self):
#        pass


################################################################################################
#
#
################################################################################################
cdef class CEffectsChain:
    """The effectschain is the primary instrument of processing audio data.
    CEffectsChain is basically a wrapper around sox_effects_chain_t and provides
    methods to add effects, to start the processing (flow) and to set parameters on
    input and output.
    
    """ 
    cdef csox.sox_effects_chain_t * chain
    cdef CSoxStream instream
    cdef CSoxStream outstream
    cdef CEncodingInfo inencoding
    cdef CEncodingInfo outencoding
    cdef CSignalInfo insignal
    cdef CSignalInfo outsignal
    cdef haveInputEffect    
    cdef haveOutputEffect
    cdef object effects #pre-store CEffect objects
    
    def __init__(self, CSoxStream istream=None, CSoxStream ostream=None):
        """Create an effect chain
        
        Kwargs:
            istream: :class:`CSoxStream` input stream object
            
            ostream: :class:`CSoxStream` output stream object
            
        """
        self.effects = []
        self.haveInputEffect = False
        self.haveOutputEffect = False
        self.inencoding = None
        self.outencoding = None
        self.insignal = None
        self.outsignal = None
        self.chain = NULL
        if istream:
            self.__setInput(istream)
        if ostream:
            self.__setOutput(ostream)

    def __dealloc__(self):
        self.__do_dealloc()

    cdef __do_dealloc(self):
        if not self.chain is NULL:
            csox.sox_delete_effects_chain(self.chain)
            self.chain = NULL
        
    def __repr__(self):
        return u'Ceffects_chain()'
    
    cdef set_chain(self, csox.sox_effects_chain_t * chain):
        self.chain = chain
        
    cdef csox.sox_effects_chain_t * get_chain(self):
        return self.chain

    cdef __create_effects_chain(self, CEncodingInfo inEncoding, CEncodingInfo outEncoding):
        cdef csox.sox_encodinginfo_t * in_encoding = NULL
        cdef csox.sox_encodinginfo_t * out_encoding = NULL
        in_encoding = inEncoding.cget_encoding()
        if outEncoding:
            out_encoding = outEncoding.cget_encoding()
        else:
            out_encoding = in_encoding
        self.chain = csox.sox_create_effects_chain(in_encoding, out_encoding)

    cdef __setInput(self, CSoxStream istream):
        self.instream = istream
        self.inencoding = istream.get_encoding()
        self.insignal = istream.get_signal() #get the object

    cdef __setOutput(self, CSoxStream ostream):
        self.outstream = ostream
        self.outencoding = ostream.get_encoding()
        self.outsignal = ostream.get_signal() #get the object
    
    cdef __calculate_signals(self):
        """calculate the inputsignal parameters(sox.c combiner_signal)
        and retrieve the outputsignal parameters
        
        input: take the input effects output signal?
          /* If user didn't specify # of channels then see if an effect
           * is specifying them.  This is of most use currently with the
           * synth effect were user can use null input handler and specify
           * channel counts directly in effect.  Forcing to use -c with
           * -n isn't as convenient.
           */
          /* For historical reasons, default to one channel if not specified. */
          /* Set the combiner output signal attributes to those of the 1st/next input
           * file.  If we are in sox_sequence mode then we don't need to check the
           * attributes of the other inputs, otherwise, it is mandatory that all input
           * files have the same sample rate, and for sox_concatenate, it is mandatory
           * that they have the same number of channels, otherwise, the number of
           * channels at the output of the combiner is calculated according to the
           * combiner mode. */

        
        output: take the last effect that sets signal, or from input 
        
        Our version:
         input stream must have a signal
         output stream must have a signal
        """
        cdef csox.sox_effect_t *effp
        cdef csox.sox_signalinfo_t * insignal
        cdef csox.sox_signalinfo_t * outsignal
        cdef int inlength = 0 #FIXME type?
        cdef int outlength = 0 #FIXME type?
        #fixme calc channels and rate
        cdef CEffect effect
        inlength = self.insignal.cget_signal().length
        outlength = self.outsignal.cget_signal().length
        
        for effect in self.effects:
            effp = effect.get_effect()
            insignal = &effp.in_signal
            outsignal = &effp.out_signal
            inlength = max(inlength, insignal.length)
            outlength = max(outlength, outsignal.length)
            if effect.get_name()=='input':
                inlength = max(inlength, outlength)

        if outlength==0:
            outlength=inlength
        # calculate ouput signal parameters
        outsignal = self.outsignal.cget_signal()
        outsignal.length = outlength

    cdef void fixup_out_signal_length(self):
        self.__calculate_signals()
        
    def add_effect(self, CEffect effect):
        """Add an effect to the chain
        
        Args:
            effect: CEffect object
        """
        self.effects.append(effect)
        if effect.get_name() == 'input':
            self.haveInputEffect = True
            self.inencoding = effect.get_in_encoding()
            self.insignal = effect.get_in_signal()
        if effect.get_name() == 'output':
            self.haveOutputEffect = True
            self.outencoding = effect.get_out_encoding()
            self.outsignal = effect.get_out_signal()

    cdef int __init_effects(self) except -1:
        """
static int process(void)
{         /* Input(s) -> Balancing -> Combiner -> Effects -> Output */

  create_user_effects();
  calculate_combiner_signal_parameters();
  set_combiner_and_output_encoding_parameters();
  calculate_output_signal_parameters();
  open_output_file();
  effects_chain = sox_create_effects_chain(&combiner_encoding,
                                             &ofile->ft->encoding);
  add_effects(effects_chain);
        """
        cdef CEffect eff
        if not self.haveInputEffect:
            if not self.instream:
                raise PysoxError("neither instream nor an inputeffect are configured")
            inputeffect = CEffect("input", [self.instream])
            self.effects.insert(0, inputeffect)
            self.haveInputEffect = True
        if not self.haveOutputEffect:
            if not self.outstream:
                raise PysoxError("neither outstream nor an outputeffect are configured")
            outputeffect = CEffect("output", [self.outstream])
            self.effects.append(outputeffect)
            self.haveOutputEffect = True

        self.__calculate_signals()
        
        self.__create_effects_chain(self.inencoding, self.outencoding)
        for eff in self.effects:
            self.__init_effect(eff)
        return 0
        
    cdef int __init_effect(self, CEffect effect) except -1:
        cdef csox.sox_effect_t *effp
        effp = effect.get_effect()
        cdef csox.sox_signalinfo_t * insignal
        cdef csox.sox_signalinfo_t * outsignal

        if not self.instream and not self.insignal:
            raise PysoxError("neither instream nor insignal are configured")
        insignal = self.insignal.cget_signal() #get struct
        if not self.outstream and not self.outsignal:
            raise PysoxError("neither outstream nor outsignal are configured")
        outsignal = self.outsignal.cget_signal() #get struct

#        print("adding effect with",effect.get_name() ,self.insignal, self.outsignal)
#        print outsignal.length
        csox.sox_add_effect(self.chain, effp, insignal, outsignal)
#        print effp.in_signal.length, effp.out_signal.length
        return 0
            
    cpdef int flow_effects(self, optimize_trim=True) except -1:
        """Flow samples through the effects processing chain until EOF is reached.
        
        Kwargs:
            optimize_trim: boolean, default True
        Raises:
            PysoxError if configuration of chain is inconsistent
                or chain is not valid anymore
        """
        self.__init_effects()
        if not self.chain:
            raise PysoxError('chain not valid')
        if optimize_trim:
            self.__optimize_trim()
        csox.sox_flow_effects(self.chain, NULL, NULL)
#        print("flow done")
        self.fixup_out_signal_length()
        self.__do_dealloc()
        return 0

    cdef int __optimize_trim(self):
        """  
if (input_count == 1 && effects_chain->length > 1 && strcmp(effects_chain->effects[1][0].handler.name, "trim") == 0) {
    if (files[0]->ft->handler.seek && files[0]->ft->seekable){
      uint64_t offset = sox_trim_get_start(&effects_chain->effects[1][0]);
      if (offset && sox_seek(files[0]->ft, offset, SOX_SEEK_SET) == SOX_SUCCESS) {
        read_wide_samples = offset / files[0]->ft->signal.channels;
        /* Assuming a failed seek stayed where it was.  If the seek worked then
         * reset the start location of trim so that it thinks user didn't
         * request a skip.  */
        sox_trim_clear_start(&effects_chain->effects[1][0]);
        lsx_debug("optimize_trim successful");
      }
    }
  }

        """
        cdef uint64_t offset
        cdef csox.sox_format_t * ft
        if not self.instream: #or not self.instream.is_seekable():
            return -1
	# if we have a combiner as input, we won't have an instream??? FIXME
	# check the number of input files on the instream FIXME

        ft = self.instream.get_ft()
        if self.chain.length > 1 and self.chain.effects[1][0].handler.name == b'trim' and \
            ft.handler.seek and ft.seekable:
            offset = csox.sox_trim_get_start(&self.chain.effects[1][0])
            #seek
            if offset and csox.sox_seek(ft, offset, SOX_SEEK_SET) == SOX_SUCCESS:
                csox.sox_trim_clear_start(&self.chain.effects[1][0]);
                #print("__optimize_trim successful")
                return 0
        return -1

################################################################################################
#
#
################################################################################################


available_flags = (
    ('FORMAT', cpython.buffer.PyBUF_FORMAT),
    ('INDIRECT', cpython.buffer.PyBUF_INDIRECT),
    ('ND', cpython.buffer.PyBUF_ND),
    ('STRIDES', cpython.buffer.PyBUF_STRIDES),
    ('C_CONTIGUOUS', cpython.buffer.PyBUF_C_CONTIGUOUS),
    ('F_CONTIGUOUS', cpython.buffer.PyBUF_F_CONTIGUOUS),
    ('WRITABLE', cpython.buffer.PyBUF_WRITABLE)
)
cdef class SoxSampleBuffer:
    """Python representation of a sox buffer memory area
    
    Supports the PEP-3118 buffer interface and can be used within a
    memoryview object.
    
    Additionally, __getitem__ and __setitem__ and the iterator interface are
    supported in order to access the buffer data using index operations

    Kwargs:
        data: default None, initialize the buffer with a bytarray, bytes or an array of integers.
        The data is being copied.

    Raises:
        TypeError if data is not bytes or an array
    """
    def __init__(self, data=None):
        """
        Raises:
            TypeError if data is not bytes or an array
        """
        self.viewcount = 0
        # data must be factor of self.itemsize
        
        # It is important not to store references to data after the constructor
        # as refcounting is checked on object buffers.
        self.buffer = NULL
        self.strides = NULL
        self.shape = NULL
        self.release_ok = True
        self.read_only = 0
        self.offset = 0
        self.itemsize = sizeof(csox.sox_sample_t)
        self.format = self.get_default_format()
        self.ndim = 1
        
        if data:
            self.__create_buffer(data), len(data)
        else:
            self.set_buffer(NULL, 0)
            
        #self.buffer = self.create_buffer(data)
        self.suboffsets = NULL
        
    cdef void set_buffer(self, csox.sox_sample_t* buffer, size_t lsamp):
        """Set our buffer, len, ndim and shape.
        
        Used to setup our data from constructor (python) data, which we did copy and will free, or
        from sox buffers, which we did not copy and will not free.
        Args:
            csox.sox_sample_t* buffer: the buffer
            
            size_t lsamp: number of samples
        """
        self.__do_dealloc_if()
        self.buffer = buffer
        self.must_dealloc_buffer = 0
        self.len = lsamp * self.itemsize
        self.datalen = self.len
        shape = (lsamp, )
        self.shape = self.list_to_sizebuf(shape)
        self.strides = self.list_to_sizebuf([self.itemsize])
            
    cdef int __create_buffer(self, data) except -1:
        """create our buffer from data
        Args:
            data
            
        Raises:
            TypeError
        """
        if data is None:
            self.must_dealloc_buffer = 0
        elif type(data) == type(bytearray()):
            self.frombytes(bytes(data))
        elif not PY3 and type(data) == type(''):
            self.frombytes(bytes(data))
        elif type(data) == type(b''):
            self.frombytes(data)
# not 2.6
#        elif type(data) == type(memoryview(b'')):
#            self.frombytes(data.tobytes())
        elif type(data) == type([]):
            self.fromlist(data)
        else:
            raise TypeError("need bytes, bytearray, memoryview or list of integers")
        return 0

    def __dealloc__(self):
        self.__do_dealloc_if()
        
    cdef void __do_dealloc_if(self):
        if self.viewcount > 0:
            #somebody holds a reference, we must not change our state
            return
        if self.strides:
            stdlib.free(self.strides)
            self.strides = NULL
        if self.shape:
            stdlib.free(self.shape)
            self.shape = NULL
        if self.buffer and self.must_dealloc_buffer:
            stdlib.free(self.buffer)
            self.buffer = NULL
            self.must_dealloc_buffer = 0

    cdef int write(self, csox.sox_sample_t* buf, object value) except -1:
        (<csox.sox_sample_t*>buf)[0] = <csox.sox_sample_t>value
        return 0

    cdef get_default_format(self): return b"@i"

    cdef Py_ssize_t* list_to_sizebuf(self, l):
        cdef Py_ssize_t* buf = <Py_ssize_t*>stdlib.malloc(len(l) * sizeof(Py_ssize_t))
        for i, x in enumerate(l):
            buf[i] = x
        return buf

    #
    # Buffer interface
    #
    def __getbuffer__(SoxSampleBuffer self, Py_buffer* buffer, int flags):
#        print("getbuffer")
        cdef int value
        def testflag(flagname,flags):
            return flagname in received_flags
        received_flags = []
        for name, value in available_flags:
            if (value & flags) == value:
                received_flags.append(name)

        self.viewcount += 1
        buffer.buf = <void*>(<char*>self.buffer + (<int>self.offset * self.itemsize))
        buffer.obj = self
        buffer.len = self.datalen
        buffer.readonly = self.read_only
        if testflag('FORMAT',flags):
            buffer.format = <char*>self.format
        else:
            buffer.format = NULL
        buffer.ndim = self.ndim
        if testflag('ND',flags):
            buffer.shape = self.shape
        else:
            buffer.shape = NULL
            
        if testflag('STRIDES',flags):
            buffer.strides = self.strides
        else:
            buffer.strides = NULL
        buffer.suboffsets = self.suboffsets
        buffer.itemsize = self.itemsize
        buffer.internal = NULL
        
    def __releasebuffer__(SoxSampleBuffer self, Py_buffer* buffer):
#        print("releasebuffer")
        self.viewcount -= 1
        if self.viewcount < 0:
            self.viewcount = 0
        if buffer.suboffsets != self.suboffsets:
            self.release_ok = False

    def set_datalen(self, nbytes):
        if nbytes > self.len:
            raise IndexError('got more than i can chew')
        self.datalen = nbytes

    def set_readonly(self):
        self.read_only = 1
    #
    # Container type emulation
    #
    def __getitem__(self, i):
        if type(i) == type(slice(1,2)):
            raise IndexError("Slices are not supported")
        cdef int index = i
        if index*self.itemsize >= self.datalen:
            raise IndexError()
        return deref(<csox.sox_sample_t *>self.buffer + <int>index)

    def __setitem__(self, i, val):
        cdef int index = i
        if index*self.itemsize >= self.datalen:
            raise IndexError()
        self.write((<csox.sox_sample_t *>self.buffer + <int>index), val)
        #(<csox.sox_sample_t *>self.buffer + <int>index)[0] = <csox.sox_sample_t>val

    def get_buffer_size(self):
        """return the size of this buffer in bytes.
        len(obj) defaults to this unless set_datalen has been called.
        In that case, len(obj) returns the number of valid bytes, whereas this function still
        returns the size of our buffer"""
        return self.len

    def __len__(self):
        return self.datalen // self.itemsize

    def __iter__(self):
        return SoxBufferIterator(self)

    #
    # conversion helpers
    #
    def fromlist(self, data):
        """replace our buffer with the contents of the array of integers
        
        Args:
            ba: array of integers e.g. [1,2,3,4]
        
        Raises:
            BufferError if being held by a view
        """
        if self.viewcount > 0:
            raise BufferError('Cannot reallocate while being referenced')
        cdef char* buf = <char*>stdlib.malloc(len(data) * self.itemsize)

        cdef char* it = buf
        for value in data:
            self.write(<csox.sox_sample_t *>it, value)
            it += self.itemsize
        self.set_buffer(<csox.sox_sample_t *>buf, len(data))
        self.must_dealloc_buffer = 1

    def writelist(self, data):
        """fill our buffer with the contents of the array of integers
        
        Args:
            ba: array of integers e.g. [1,2,3,4]

        Raises:
            IndexError if too much data is given
        """
        if type(data) != type([]):
            raise TypeError("only accepting list type")
        cdef char* it = <char *>self.buffer
        cdef int lsamp
        lsamp = len(data)
        if lsamp * self.itemsize > self.len:
            raise IndexError("Too much data, check get_buffer_size()")
        for value in data:
            self.write(<csox.sox_sample_t *>it, value)
            it += self.itemsize
        self.must_dealloc_buffer = 0
        self.__do_dealloc_if()
        self.datalen = lsamp * self.itemsize
        shape = (lsamp, )
        self.ndim = len(shape)
        self.shape = self.list_to_sizebuf(shape)
        self.strides = self.list_to_sizebuf([self.itemsize])

    def frombytes(self, ba):
        """replace our buffer with the contents of the bytearray
        
        Args:
            ba: bytearray
        
        Raises:
            BufferError if being held by a view
        """
        cdef int c
        cdef int lsamp
        cdef char * buffer
        if self.viewcount > 0:
            raise BufferError('Cannot reallocate while being referenced')
        lsamp = len(ba) // self.itemsize
        buffer = <char *>stdlib.malloc(len(ba))
        
        if type(ba) == type(bytearray()):
            ba = bytes(ba)

        for c in range(len(ba)):
            (<char *>buffer)[c] = <char>(<char *>ba)[c]
        self.set_buffer(<csox.sox_sample_t *>buffer, lsamp)
        self.must_dealloc_buffer = 1

    def writebytes(self, ba):
        """fill our buffer with the contents of the bytearray
        
        Args:
            ba: bytearray
        """
        if len(ba) > self.len:
            raise IndexError("Too much data, check get_buffer_size()")
        cdef int c, lsamp
        cdef char * buffer = <char *>self.buffer
        for c in range(len(ba)):
            (<char *>buffer)[c] = (<char *>ba)[c]
        self.must_dealloc_buffer = 0
        self.__do_dealloc_if()
        lsamp = len(ba) // self.itemsize
        self.datalen = lsamp * self.itemsize
        shape = (lsamp, )
        self.ndim = len(shape)
        self.shape = self.list_to_sizebuf(shape)
        self.strides = self.list_to_sizebuf([self.itemsize])

    def tobytearray(self):
        """return a bytearray object of the buffer.
        
        The bytearray is a copy. Modifications will not reflect into the sox buffer"""
        return bytearray(self)
    
    def tolist(self):
        """Return a list of this buffers items.
        
        The list is a copy, changes will not reflect into the sox buffer"""
        return list(self)
        #return [x for x in self]

cdef class SoxBufferIterator:
    cdef SoxSampleBuffer b
    cdef int i
    cdef int len
    def __init__(self, SoxSampleBuffer b):
        self.b = b
        self.len = len(b)
    def __iter__(self):
        self.i=0
        return self
    def __next__(self):
        if self.i >= self.len:
            raise StopIteration
        inc(self.i)
        return self.b[self.i-1]


################################################################################################
#
#
################################################################################################
cdef class __CSox:
    def __cinit__(self):
        cdef int result
        result = csox.sox_init()
        if result != SOX_SUCCESS:
            raise ImportError("sox_init not successful")
        
    def __dealloc__(self):
        csox.sox_quit()

__sox_initializer = __CSox()
