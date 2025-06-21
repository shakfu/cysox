#
# cython declaration of the c implementation
#
# $Id: csox.pxd 113 2011-03-31 08:03:46Z patrick $
#
# Copyright 2011 Patrick Atamaniuk
#
# This source code is freely redistributable and may be used for
# any purpose.  This copyright notice must be maintained.
# Patrick Atamaniuk and Contributors are not responsible for
# the consequences of using this software.
#
from libc.stdint cimport uint32_t, int32_t, uint64_t

ctypedef double sox_rate_t
ctypedef int32_t sox_sample_t

cdef extern from "stdio.h":
    ctypedef struct FILE:
        pass

cdef extern from "stdlib.h":
    void free(void* ptr)
    void* malloc(size_t size)

cdef extern from "strings.h":
    void bzero(void *s, size_t n)
    void bcopy(void *src, void *dest, size_t n)

cdef extern from "sox.h":
    
    ctypedef enum sox_bool:
        sox_false
        sox_true
    
    ctypedef struct sox_signalinfo_t:
        sox_rate_t       rate #;         /* sampling rate */
        unsigned         channels #;     /* number of sound channels */
        unsigned         precision #;    /* in bits */
        size_t           length #;       /* samples * chans in file */
        double           * mult #;       /* Effects headroom multiplier; may be null */

    ctypedef enum sox_encoding_t:
        SOX_ENCODING_UNKNOWN   #,
        SOX_ENCODING_SIGN2     #, /* signed linear 2's comp: Mac */
        SOX_ENCODING_UNSIGNED  #, /* unsigned linear: Sound Blaster */
        SOX_ENCODING_FLOAT     #, /* floating point (binary format) */
        SOX_ENCODING_FLOAT_TEXT#, /* floating point (text format) */
        SOX_ENCODING_FLAC      #, /* FLAC compression */
        SOX_ENCODING_HCOM      #, /*  */
        SOX_ENCODING_WAVPACK   #, /*  */
        SOX_ENCODING_WAVPACKF  #, /*  */
        SOX_ENCODING_ULAW      #, /* u-law signed logs: US telephony, SPARC */
        SOX_ENCODING_ALAW      #, /* A-law signed logs: non-US telephony, Psion */
        SOX_ENCODING_G721      #, /* G.721 4-bit ADPCM */
        SOX_ENCODING_G723      #, /* G.723 3 or 5 bit ADPCM */
        SOX_ENCODING_CL_ADPCM  #, /* Creative Labs 8 --> 2,3,4 bit Compressed PCM */
        SOX_ENCODING_CL_ADPCM16#, /* Creative Labs 16 --> 4 bit Compressed PCM */
        SOX_ENCODING_MS_ADPCM  #, /* Microsoft Compressed PCM */
        SOX_ENCODING_IMA_ADPCM #, /* IMA Compressed PCM */
        SOX_ENCODING_OKI_ADPCM #, /* Dialogic/OKI Compressed PCM */
        SOX_ENCODING_DPCM      #, /*  */
        SOX_ENCODING_DWVW      #, /*  */
        SOX_ENCODING_DWVWN     #, /*  */
        SOX_ENCODING_GSM       #, /* GSM 6.10 33byte frame lossy compression */
        SOX_ENCODING_MP3       #, /* MP3 compression */
        SOX_ENCODING_VORBIS    #, /* Vorbis compression */
        SOX_ENCODING_AMR_WB    #, /* AMR-WB compression */
        SOX_ENCODING_AMR_NB    #, /* AMR-NB compression */
        SOX_ENCODING_CVSD      #, /*  */
        SOX_ENCODING_LPC10     #, /*  */
        SOX_ENCODINGS          #  /* End of list marker */
    
    ctypedef enum sox_option_t:
        SOX_OPTION_NO, SOX_OPTION_YES, SOX_OPTION_DEFAULT

    ctypedef struct sox_encodinginfo_t:
        sox_encoding_t encoding #; /* format of sample numbers */
        unsigned bits_per_sample #;  /* 0 if unknown or variable; uncompressed value if lossless; compressed value if lossy */
        double compression #;      /* compression factor (where applicable) */
        
        #/* If these 3 variables are set to DEFAULT, then, during
        # * sox_open_read or sox_open_write, libSoX will set them to either
        # * NO or YES according to the machine or format default. */
        sox_option_t reverse_bytes #;    /* endiannesses... */
        sox_option_t reverse_nibbles #;
        sox_option_t reverse_bits #;
        sox_bool opposite_endian #;

    ctypedef struct sox_encodings_info_t:
        unsigned flags
        char * name
        char * desc

    cdef sox_encodings_info_t sox_encodings_info[]
    
    ctypedef enum lsx_io_type:
        lsx_io_file
        lsx_io_pipe
        lsx_io_url
    
    ctypedef struct sox_oob_t: # /* Out Of Band data */
        pass
        #sox_comments_t   comments;              /* Comment strings */
        #sox_instrinfo_t  instr;                 /* Instrument specification */
        #sox_loopinfo_t   loops[SOX_MAX_NLOOPS]; /* Looping specification */


    ctypedef struct sox_format_t #forward declaration
        
    ctypedef struct sox_format_handler_t:
        unsigned     sox_lib_version_code #; /* Checked on load; must be 1st in struct*/
        char          * description #;
        char          * * names #;
        unsigned int flags #;
        int          (*startread)(sox_format_t * ft) #;
        size_t   (*read)(sox_format_t * ft, sox_sample_t *buf, size_t len) #;
        int          (*stopread)(sox_format_t * ft) #;
        int          (*startwrite)(sox_format_t * ft) #;
        size_t   (*write)(sox_format_t * ft, sox_sample_t *buf, size_t len) #;
        int          (*stopwrite)(sox_format_t * ft) #;
        int          (*seek)(sox_format_t * ft, uint64_t offset) #;
        unsigned      * write_formats #;
        sox_rate_t    * write_rates #;
        size_t       priv_size #;

    ctypedef struct sox_format_t:
        char             * filename #;      /* File name */
        sox_signalinfo_t signal #;          /* Signal specifications */
        sox_encodinginfo_t encoding #;      /* Encoding specifications */
        char             * filetype #;      /* Type of file */
        sox_oob_t        oob #;             /* Out Of Band data */
        sox_bool         seekable #;        /* Can seek on this file */
        char             mode #;            /* Read or write mode ('r' or 'w') */
        size_t       olength #;         /* Samples * chans written to file */
        size_t       clips #;           /* Incremented if clipping occurs */
        int              sox_errno #;       /* Failure error code */
        char             sox_errstr[256] #; /* Failure error text */
        FILE             * fp #;            /* File stream pointer */
        lsx_io_type      io_type #;
        long             tell_off #;
        long             data_start #;
        sox_format_handler_t handler #;     /* Format handler for this file */
        void             * priv #;          /* Format handler's private data area */

    
    int sox_format_init()
    void sox_format_quit()

    int sox_init()
    int sox_quit()

    sox_format_t * sox_open_read(
        char                * path,
        sox_signalinfo_t    * signal,
        sox_encodinginfo_t  * encoding,
        char                * filetype)
    sox_bool sox_format_supports_encoding(
        char                * path,
        char                * filetype,
        sox_encodinginfo_t  * encoding)
    sox_format_handler_t  * sox_write_handler(
        char                * path,
        char                * filetype,
        char                * * filetype1)
    sox_format_t * sox_open_write(
        char                * path,
        sox_signalinfo_t    * signal,
        sox_encodinginfo_t  * encoding,
        char                * filetype,
        sox_oob_t           * oob,
        sox_bool           (*overwrite_permitted)( char *filename))
    size_t sox_read(sox_format_t * ft, sox_sample_t *buf, size_t len)
    size_t sox_write(sox_format_t * ft,  sox_sample_t *buf, size_t len)
    int sox_close(sox_format_t * ft)
    
    #define SOX_SEEK_SET 0
    int sox_seek(sox_format_t * ft, uint64_t offset, int whence)
    
    sox_format_handler_t  * sox_find_format(char  * name, sox_bool no_dev)
    
#
# effects
#
#
    #define SOX_EFF_CHAN     1           /* Can alter # of channels */
    #define SOX_EFF_RATE     2           /* Can alter sample rate */
    #define SOX_EFF_PREC     4           /* Can alter sample precision */
    #define SOX_EFF_LENGTH   8           /* Can alter audio length */
    cdef int SOX_EFF_LENGTH =     8  #         /* Can alter audio length */
    #define SOX_EFF_MCHAN    16          /* Can handle multi-channel */
    cdef int SOX_EFF_MCHAN =      16 #          /* Can handle multi-channel */
    #define SOX_EFF_NULL     32          /* Does nothing */
    #define SOX_EFF_DEPRECATED 64        /* Is living on borrowed time */
    #define SOX_EFF_GAIN     128         /* Does not support gain -r */
    #define SOX_EFF_MODIFY   256         /* Does not modify samples */
    #define SOX_EFF_ALPHA    512         /* Is experimental/incomplete */
    #define SOX_EFF_INTERNAL 1024        /* Is in libSoX but not sox */

    ctypedef struct sox_effects_globals_t:
        pass

    ctypedef struct sox_effect_t
    ctypedef struct sox_effect_handler_t:
        char * name
        char * usage
        int flags
        int (*getopts)(sox_effect_t * effp, int argc, char *argv[])
        int (*start)(sox_effect_t * effp)
        int (*flow)(sox_effect_t * effp, sox_sample_t *ibuf, sox_sample_t *obuf, size_t *isamp, size_t *osamp)
        int (*drain)(sox_effect_t * effp, sox_sample_t *obuf, size_t *osamp)
        int (*stop)(sox_effect_t * effp)
        int (*kill)(sox_effect_t * effp)
        size_t       priv_size

    ctypedef struct sox_effect_t:
        sox_effects_globals_t    * global_info #; /* global parameters */
        sox_signalinfo_t         in_signal
        sox_signalinfo_t         out_signal
        sox_encodinginfo_t       * in_encoding
        sox_encodinginfo_t       * out_encoding
        sox_effect_handler_t     handler
        sox_sample_t             * obuf #;        /* output buffer */
        size_t               obeg, oend #;    /* consumed, total length */
        size_t               imin #;          /* minimum input buffer size */
        size_t               clips #;         /* increment if clipping occurs */
        size_t               flows #;         /* 1 if MCHAN, # chans otherwise */
        size_t               flow #;          /* flow # */
        void                     * priv #;        /* Effect's private data area */
    
    sox_effect_handler_t  * sox_find_effect(char  * name)
    sox_effect_t * sox_create_effect(sox_effect_handler_t  * eh)
    int sox_effect_options(sox_effect_t *effp, int argc, char *  argv[])
    
    #/* Effects chain */
    ctypedef  sox_effect_handler_t *(*sox_effect_fn_t)()
    
    ctypedef struct sox_effects_chain_t:
        sox_effect_t ** effects #[SOX_MAX_EFFECTS];
        unsigned length
        sox_sample_t **ibufc, **obufc #; /* Channel interleave buffers */
        sox_effects_globals_t global_info
        sox_encodinginfo_t * in_enc
        sox_encodinginfo_t * out_enc
    
    sox_effects_chain_t * sox_create_effects_chain(
        sox_encodinginfo_t  * in_enc, sox_encodinginfo_t  * out_enc)
    void sox_delete_effects_chain(sox_effects_chain_t *ecp)
    int sox_add_effect( sox_effects_chain_t * chain, sox_effect_t * effp, sox_signalinfo_t * in_, sox_signalinfo_t  * out)
    int sox_flow_effects(sox_effects_chain_t *, int (* callback)(sox_bool all_done, void * client_data), void * client_data)
    size_t sox_effects_clips(sox_effects_chain_t *)
    size_t sox_stop_effect(sox_effect_t *effp)
    void sox_push_effect_last(sox_effects_chain_t *chain, sox_effect_t *effp)
    sox_effect_t *sox_pop_effect_last(sox_effects_chain_t *chain)
    void sox_delete_effect(sox_effect_t *effp)
    void sox_delete_effect_last(sox_effects_chain_t *chain)
    void sox_delete_effects(sox_effects_chain_t *chain)

#    /* The following routines are unique to the trim effect.
#     * sox_trim_get_start can be used to find what is the start
#     * of the trim operation as specified by the user.
#     * sox_trim_clear_start will reset what ever the user specified
#     * back to 0.
#     * These two can be used together to find out what the user
#     * wants to trim and use a sox_seek() operation instead.  After
#     * sox_seek()'ing, you should set the trim option to 0.
#     */
    size_t sox_trim_get_start(sox_effect_t * effp)
    void sox_trim_clear_start(sox_effect_t * effp)
    size_t sox_crop_get_start(sox_effect_t * effp)
    void sox_crop_clear_start(sox_effect_t * effp)
