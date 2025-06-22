cdef extern from "<stdlib.h>":
    cdef free(void * ptr)

cdef extern from "sox.h":

    ctypedef unsigned long sox_uint64_t
    ctypedef int sox_int32_t
    # ctypedef sox_int32_t sox_int24_t
    # ctypedef sox_uint32_t sox_uint24_t
    ctypedef sox_int32_t sox_sample_t
    ctypedef double sox_rate_t
    ctypedef char ** sox_comments_t


    ctypedef enum sox_bool:
        sox_bool_dummy = -1
        sox_false = 0
        sox_true = 1

    ctypedef enum sox_option_t:
        sox_option_no
        sox_option_yes
        sox_option_default

    ctypedef enum sox_encoding_t:
        SOX_ENCODING_UNKNOWN    # encoding has not yet been determined
        SOX_ENCODING_SIGN2      # signed linear 2's comp: Mac
        SOX_ENCODING_UNSIGNED   # unsigned linear: Sound Blaster
        SOX_ENCODING_FLOAT      # floating point (binary format)
        SOX_ENCODING_FLOAT_TEXT # floating point (text format)
        SOX_ENCODING_FLAC       # FLAC compression
        SOX_ENCODING_HCOM       # Mac FSSD files with Huffman compression
        SOX_ENCODING_WAVPACK    # WavPack with integer samples
        SOX_ENCODING_WAVPACKF   # WavPack with float samples
        SOX_ENCODING_ULAW       # u-law signed logs: US telephony, SPARC
        SOX_ENCODING_ALAW       # A-law signed logs: non-US telephony, Psion
        SOX_ENCODING_G721       # G.721 4-bit ADPCM
        SOX_ENCODING_G723       # G.723 3 or 5 bit ADPCM
        SOX_ENCODING_CL_ADPCM   # Creative Labs 8 --> 2,3,4 bit Compressed PCM
        SOX_ENCODING_CL_ADPCM16 # Creative Labs 16 --> 4 bit Compressed PCM
        SOX_ENCODING_MS_ADPCM   # Microsoft Compressed PCM
        SOX_ENCODING_IMA_ADPCM  # IMA Compressed PCM
        SOX_ENCODING_OKI_ADPCM  # Dialogic/OKI Compressed PCM
        SOX_ENCODING_DPCM       # Differential PCM: Fasttracker 2 (xi)
        SOX_ENCODING_DWVW       # Delta Width Variable Word
        SOX_ENCODING_DWVWN      # Delta Width Variable Word N-bit
        SOX_ENCODING_GSM        # GSM 6.10 33byte frame lossy compression
        SOX_ENCODING_MP3        # MP3 compression
        SOX_ENCODING_VORBIS     # Vorbis compression
        SOX_ENCODING_AMR_WB     # AMR-WB compression
        SOX_ENCODING_AMR_NB     # AMR-NB compression
        SOX_ENCODING_CVSD       # Continuously Variable Slope Delta modulation
        SOX_ENCODING_LPC10      # Linear Predictive Coding
        SOX_ENCODING_OPUS       # Opus compression

        SOX_ENCODINGS           # End of list marker


    ctypedef enum sox_error_t:
        SOX_SUCCESS = 0
        SOX_EOF = -1
        SOX_EHDR = 2000
        SOX_EFMT = 2001
        SOX_ENOMEM = 2002
        SOX_EPERM = 2003
        SOX_ENOTSUP = 2004
        SOX_EINVAL = 2005


    ctypedef struct sox_signalinfo_t:
        sox_rate_t       rate         # samples per second, 0 if unknown
        unsigned         channels     # number of sound channels, 0 if unknown
        unsigned         precision    # bits per sample, 0 if unknown
        sox_uint64_t     length       # samples * chans in file, 0 if unknown, -1 if unspecified
        double           * mult       # Effects headroom multiplier; may be null

    ctypedef struct sox_encodinginfo_t:
        sox_encoding_t encoding        # format of sample numbers
        unsigned bits_per_sample       # 0 if unknown or variable uncompressed value if lossless compressed value if lossy
        double compression             # compression factor (where applicable)
        sox_option_t reverse_bytes
        sox_option_t reverse_nibbles
        sox_option_t reverse_bits
        sox_bool opposite_endian


    ctypedef struct sox_oob_t:
        sox_comments_t   comments               # Comment strings in id=value format.
        #sox_instrinfo_t  instr                 # Instrument specification
        #sox_loopinfo_t   loops[SOX_MAX_NLOOPS] # Looping specification



    ctypedef struct sox_format_t:
        char * filename

        sox_signalinfo_t signal
        sox_encodinginfo_t encoding;

        char             * filetype      # Type of file, as determined by header inspection or libmagic.
        sox_oob_t        oob             # comments, instrument info, loop info (out-of-band data)
        sox_bool         seekable        # Can seek on this file
        char             mode            # Read or write mode ('r' or 'w')
        sox_uint64_t     olength         # Samples * chans written to file
        sox_uint64_t     clips           # Incremented if clipping occurs
        int              sox_errno       # Failure error code
        char             sox_errstr[256] # Failure error text
        void             * fp            # File stream pointer
        # lsx_io_type      io_type       # Stores whether this is a file, pipe or URL
        sox_uint64_t     tell_off        # Current offset within file
        sox_uint64_t     data_start      # Offset at which headers end and sound data begins (set by lsx_check_read_params)
        # sox_format_handler_t handler   # Format handler for this file
        void             * priv


    ctypedef enum sox_plot_t:
        sox_plot_off
        sox_plot_octave
        sox_plot_gnuplot
        sox_plot_data


    ctypedef struct sox_globals_t:
        unsigned     verbosity
        # sox_output_message_handler_t output_message_handler
        sox_bool     repeatable
        size_t       bufsiz;
        size_t       input_bufsiz;
        sox_int32_t  ranqd1
        # private #
        char * stdin_in_use_by
        char * stdout_in_use_by
        char * subsystem
        char       * tmp_path
        sox_bool     use_magi
        sox_bool     use_threads
        size_t       log2_dft_min_size;


    ctypedef struct sox_effects_globals_t:
        sox_plot_t plot                # To help the user choose effect & options */
        sox_globals_t * global_info    # Pointer to associated SoX globals */


    # ctypedef sox_effect_handler_t * (*sox_effect_fn_t)(void)

    ctypedef struct sox_effect_handler_t:
        char * name
        char * usage
        unsigned int flags
        # sox_effect_handler_getopts getopts
        # sox_effect_handler_start start
        # sox_effect_handler_flow flow
        # sox_effect_handler_drain drain
        # sox_effect_handler_stop stop
        # sox_effect_handler_kill kill
        size_t       priv_size



    ctypedef struct sox_effect_t:
        #sox_effects_globals_t    * global_info; # global effect parameters
        sox_signalinfo_t         in_signal;     # Information about the incoming data stream
        sox_signalinfo_t         out_signal;    # Information about the outgoing data stream
        sox_encodinginfo_t       * in_encoding;  # Information about the incoming data encoding
        sox_encodinginfo_t       * out_encoding; # Information about the outgoing data encoding
        sox_effect_handler_t     handler;   # The handler for this effect
        sox_uint64_t         clips;         # increment if clipping occurs
        size_t               flows;         # 1 if MCHAN, number of chans otherwise
        size_t               flow;          # flow number
        void                 * priv;        # Effect's private data area (each flow has a separate copy)
        # The following items are private to the libSoX effects chain functions.
        sox_sample_t         * obuf;    # output buffer
        size_t                obeg;      # output buffer: start of valid data section
        size_t                oend;      # output buffer: one past valid data section (oend-obeg is length of current content)
        size_t                imin;          # minimum input buffer content required for calling this effect's flow function; set via lsx_effect_set_imin()





    # ctypedef struct sox_effect_handler_t
    ctypedef struct sox_format_handler_t

    ctypedef struct sox_effects_chain_t:
        sox_effect_t **effects           # Table of effects to be applied to a stream
        size_t length                      # Number of effects to be applied
        sox_effects_globals_t global_info       # Copy of global effects settings
        sox_encodinginfo_t * in_enc       # Input encoding
        sox_encodinginfo_t * out_enc      # Output encoding
        # The following items are private to the libSoX effects chain functions.
        size_t table_size                       # Size of effects table (including unused entries)
        sox_sample_t *il_buf                    # Channel interleave buffer

    ctypedef int (* sox_flow_effects_callback)(
        sox_bool all_done,
        void * client_data)

    ### -------------------------------------------------------------------------------------
    ### FUNCTIONS

    cdef int sox_init()

    cdef sox_format_t * sox_open_read(
        char               * path,
        sox_signalinfo_t   * signal,
        sox_encodinginfo_t * encoding,
        char               * filetype)

    cdef sox_format_t * sox_open_write(
        char               * path,
        sox_signalinfo_t   * signal,
        sox_encodinginfo_t * encoding,
        char               * filetype,
        sox_oob_t          * oob,
        sox_bool          (* overwrite_permitted)(char * filename))

    cdef sox_effects_chain_t * sox_create_effects_chain(sox_encodinginfo_t * in_enc, sox_encodinginfo_t * out_enc)
    cdef sox_effect_t * sox_create_effect(sox_effect_handler_t * eh)
    cdef sox_effect_handler_t * sox_find_effect(char * name)
    cdef int sox_effect_options(sox_effect_t *effp, int argc, char * argv[])
    cdef int sox_add_effect(sox_effects_chain_t * chain, sox_effect_t * effp, sox_signalinfo_t * in_, sox_signalinfo_t * out)
    cdef int sox_flow_effects(sox_effects_chain_t * chain, sox_flow_effects_callback callback, void * client_data)

    cdef void sox_delete_effects_chain(sox_effects_chain_t *ecp)
    cdef int sox_close(sox_format_t * ft)
    cdef int sox_quit()




