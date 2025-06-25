from libc.stdlib cimport malloc, calloc, realloc, free

cdef extern from "<stdarg.h>":
    ctypedef struct va_list: pass

cdef extern from "sox.h":

    # ---------------------------------------------------------------------------
    # basic typedefs

    ctypedef signed char sox_int8_t
    ctypedef unsigned char sox_uint8_t
    ctypedef short sox_int16_t
    ctypedef unsigned short sox_uint16_t
    ctypedef int sox_int32_t
    ctypedef unsigned int sox_uint32_t
    ctypedef long sox_int64_t
    ctypedef unsigned long sox_uint64_t
    ctypedef sox_int32_t sox_int24_t
    ctypedef sox_uint32_t sox_uint24_t
    ctypedef sox_int32_t sox_sample_t
    ctypedef double sox_rate_t
    ctypedef char ** sox_comments_t


    # ---------------------------------------------------------------------------
    # enumerations

    # Boolean type, assignment (but not necessarily binary) compatible with C++ bool.
    cpdef enum sox_bool:
        sox_bool_dummy = -1
        sox_false = 0
        sox_true = 1

    # no, yes, or default (default usually implies some kind of auto-detect logic).
    cpdef enum sox_option_t:
        sox_option_no
        sox_option_yes
        sox_option_default

    # The libSoX-specific error codes.
    # libSoX functions may return these codes or others that map from errno codes.
    cpdef enum sox_error_t:
        SOX_SUCCESS = 0     # Function succeeded = 0
        SOX_EOF     = -1    # End Of File or other error = -1
        SOX_EHDR    = 2000  # Invalid Audio Header = 2000
        SOX_EFMT    = 2001  # Unsupported data format = 2001
        SOX_ENOMEM  = 2002  # Can't alloc memory = 2002
        SOX_EPERM   = 2003  # Operation not permitted = 2003
        SOX_ENOTSUP = 2004  # Operation not supported = 2004
        SOX_EINVAL  = 2005  # Invalid argument = 2005

    # Flags indicating whether optional features are present in this build of libSoX.
    cpdef enum sox_version_flags_t:
        sox_version_none = 0          # No special features = 0.
        sox_version_have_popen = 1    # popen = 1.
        sox_version_have_magic = 2    # magic = 2.
        sox_version_have_threads = 4  # threads = 4.
        sox_version_have_memopen = 8  # memopen = 8.

    # Format of sample data.
    cpdef enum sox_encoding_t:
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

    # Flags for sox_encodings_info_t: lossless/lossy1/lossy2.
    cpdef enum sox_encodings_flags_t:
        sox_encodings_none   = 0    # no flags specified (implies lossless encoding) = 0.
        sox_encodings_lossy1 = 1    # encode, decode: lossy once = 1.
        sox_encodings_lossy2 = 2    # encode, decode, encode, decode: lossy twice = 2.

    # Type of plot.
    cpdef enum sox_plot_t:
        sox_plot_off
        sox_plot_octave
        sox_plot_gnuplot
        sox_plot_data

    # Loop modes: upper 4 bits mask the loop blass, lower 4 bits describe
    # the loop behaviour, for example single shot, bidirectional etc.
    cpdef enum sox_loop_flags_t:
        sox_loop_none = 0           # single-shot = 0
        sox_loop_forward = 1        # forward loop = 1
        sox_loop_forward_back = 2   # forward/back loop = 2
        sox_loop_8 = 32             # 8 loops (??) = 32
        sox_loop_sustain_decay = 64 # AIFF style, one sustain & one decay loop = 64

    # Plugins API:
    # Is file a real file, a pipe, or a url?
    cdef enum lsx_io_type:
        lsx_io_file  # File is a real file = 0.
        lsx_io_pipe  # File is a pipe (no seeking) = 1.
        lsx_io_url   # File is a URL (no seeking) = 2.

    # ---------------------------------------------------------------------------
    # macros

    # Compute a 32-bit integer API version from three 8-bit parts.
    cdef int SOX_INT_MIN(int bits)
    cdef int SOX_INT_MAX(int bits)
    cdef int SOX_UINT_MAX(int bits)

    cdef int SOX_INT8_MAX
    cdef int SOX_INT16_MAX
    cdef int SOX_INT24_MAX
    cdef int SOX_SAMPLE_PRECISION
    cdef int SOX_SAMPLE_MAX
    cdef int SOX_SAMPLE_MIN
    cdef int SOX_SAMPLE_NEG

    # cdef int SOX_SAMPLE_TO_UNSIGNED(int bits, int d, int clips)
    # cdef int SOX_SAMPLE_TO_SIGNED(int bits, int d, int clips)
    # cdef int SOX_SIGNED_TO_SAMPLE(int bits, int d)
    # cdef int SOX_UNSIGNED_TO_SAMPLE(int bits, int d)
    # cdef int SOX_UNSIGNED_8BIT_TO_SAMPLE(int d, int clips)
    # cdef int SOX_SIGNED_8BIT_TO_SAMPLE(int d, int clips)
    # cdef int SOX_UNSIGNED_16BIT_TO_SAMPLE(int d, int clips)
    # cdef int SOX_SIGNED_16BIT_TO_SAMPLE(int d, int clips)
    # cdef int SOX_UNSIGNED_24BIT_TO_SAMPLE(int d, int clips)
    # cdef int SOX_SIGNED_24BIT_TO_SAMPLE(int d, int clips)
    # cdef int SOX_UNSIGNED_32BIT_TO_SAMPLE(int d, int clips)
    # cdef int SOX_SIGNED_32BIT_TO_SAMPLE(int d, int clips)
    # cdef int SOX_FLOAT_32BIT_TO_SAMPLE(float d, int clips)
    # cdef int SOX_FLOAT_64BIT_TO_SAMPLE(double d, int clips)

    # cdef int SOX_SAMPLE_TO_UNSIGNED_8BIT(int d, int clips)
    # cdef int SOX_SAMPLE_TO_SIGNED_8BIT(int d, int clips)
    # cdef int SOX_SAMPLE_TO_UNSIGNED_16BIT(int d, int clips)
    # cdef int SOX_SAMPLE_TO_SIGNED_16BIT(int d, int clips)
    # cdef int SOX_SAMPLE_TO_UNSIGNED_24BIT(int d, int clips)
    # cdef int SOX_SAMPLE_TO_SIGNED_24BIT(int d, int clips)
    # cdef int SOX_SAMPLE_TO_UNSIGNED_32BIT(int d, int clips)
    # cdef int SOX_SAMPLE_TO_SIGNED_32BIT(int d, int clips)
    # cdef int SOX_SAMPLE_TO_FLOAT_32BIT(int d, int clips)
    # cdef int SOX_SAMPLE_TO_FLOAT_64BIT(int d, int clips)

    # cdef int SOX_SAMPLE_CLIP_COUNT(int d, int clips)
    # cdef int SOX_ROUND_CLIP_COUNT(int d, int clips)
    # cdef int SOX_INTEGER_CLIP_COUNT(int d, int clips)
    # cdef int SOX_16BIT_CLIP_COUNT(int i, int clips)
    # cdef int SOX_24BIT_CLIP_COUNT(int i, int clips)

    # cdef int SOX_24BIT_CLIP_COUNT(int i, int clips)

    cdef size_t SOX_SIZE_MAX
    cdef int SOX_UNSPEC
    cdef sox_uint64_t SOX_UNKNOWN_LEN
    cdef sox_uint64_t SOX_IGNORE_LENGTH
    cdef int SOX_DEFAULT_RATE
    cdef int SOX_DEFAULT_PRECISION
    cdef int SOX_DEFAULT_ENCODING
    cdef int SOX_LOOP_NONE
    cdef int SOX_LOOP_8
    cdef int SOX_LOOP_SUSTAIN_DECAY
    cdef int SOX_MAX_NLOOPS

    cdef int SOX_FILE_NOSTDIO
    cdef int SOX_FILE_DEVICE
    cdef int SOX_FILE_PHONY
    cdef int SOX_FILE_REWIND
    cdef int SOX_FILE_BIT_REV
    cdef int SOX_FILE_NIB_REV
    cdef int SOX_FILE_ENDIAN
    cdef int SOX_FILE_ENDBIG
    cdef int SOX_FILE_MONO
    cdef int SOX_FILE_STEREO
    cdef int SOX_FILE_QUAD

    cdef int SOX_FILE_CHANS
    cdef int SOX_FILE_LIT_END
    cdef int SOX_FILE_BIG_END

    cdef int SOX_EFF_CHAN
    cdef int SOX_EFF_RATE
    cdef int SOX_EFF_PREC
    cdef int SOX_EFF_LENGTH
    cdef int SOX_EFF_MCHAN
    cdef int SOX_EFF_NULL
    cdef int SOX_EFF_DEPRECATED
    cdef int SOX_EFF_GAIN
    cdef int SOX_EFF_MODIFY
    cdef int SOX_EFF_ALPHA
    cdef int SOX_EFF_INTERNAL

    cdef int SOX_SEEK_SET

    # ---------------------------------------------------------------------------
    # forward declarations

    # ctypedef struct sox_format_t: pass
    # ctypedef struct sox_effect_t: pass
    # ctypedef struct sox_effect_handler_t: pass
    # ctypedef struct sox_format_handler_t: pass

    # ---------------------------------------------------------------------------
    # function pointers

    # Callback to write a message to an output device (console or log file),
    # used by sox_globals_t.output_message_handler.
    ctypedef void (* sox_output_message_handler_t)(
        unsigned level,     # 1 = FAIL, 2 = WARN, 3 = INFO, 4 = DEBUG, 5 = DEBUG_MORE, 6 = DEBUG_MOST.
        char * filename,    # Source code __FILENAME__ from which message originates.
        char * fmt,         # Message format string.
        va_list ap          # Message format parameters.
    )

    # Callback to retrieve information about a format handler,
    # used by sox_format_tab_t.fn.
    # @returns format handler information.
    ctypedef sox_format_handler_t * (* sox_format_fn_t)()

    # Callback to get information about an effect handler,
    # used by the table returned from sox_get_effect_fns(void).
    # @returns Pointer to information about an effect handler.
    ctypedef sox_effect_handler_t * (*sox_effect_fn_t)()

    # Callback to initialize reader (decoder), used by
    # sox_format_handler.startread.
    # @returns SOX_SUCCESS if successful.
    ctypedef int (* sox_format_handler_startread)(sox_format_t * ft)

    # Callback to read (decode) a block of samples,
    # used by sox_format_handler.read.
    # @returns number of samples read, or 0 if unsuccessful.
    ctypedef size_t (* sox_format_handler_read)(sox_format_t * ft, sox_sample_t *buf, size_t len)

    # Callback to close reader (decoder),
    # used by sox_format_handler.stopread.
    # @returns SOX_SUCCESS if successful.
    ctypedef int (* sox_format_handler_stopread)(sox_format_t * ft)

    # Callback to initialize writer (encoder),
    # used by sox_format_handler.startwrite.
    # @returns SOX_SUCCESS if successful.
    ctypedef int (* sox_format_handler_startwrite)(sox_format_t * ft)

    # Callback to write (encode) a block of samples,
    # used by sox_format_handler.write.
    # @returns number of samples written, or 0 if unsuccessful.
    ctypedef size_t (* sox_format_handler_write)(
        sox_format_t * ft,
        sox_sample_t * buf, # Buffer to which samples are written.
        size_t len # Capacity of buf, measured in samples.
    )

    # Callback to close writer (decoder),
    # used by sox_format_handler.stopwrite.
    # @returns SOX_SUCCESS if successful.
    ctypedef int (* sox_format_handler_stopwrite)(sox_format_t * ft)

    # Callback to reposition reader,
    # used by sox_format_handler.seek.
    # @returns SOX_SUCCESS if successful.
    ctypedef int (* sox_format_handler_seek)(
        sox_format_t * ft,
        sox_uint64_t offset # Sample offset to which reader should be positioned.
    )

    # Callback to parse command-line arguments (called once per effect),
    # used by sox_effect_handler.getopts.
    # @returns SOX_SUCCESS if successful.
    ctypedef int (* sox_effect_handler_getopts)(
        sox_effect_t * effp,
        int argc, # Number of arguments in argv.
        char *argv[] # Array of command-line arguments.
    )

    # Callback to initialize effect (called once per flow),
    # used by sox_effect_handler.start.
    # @returns SOX_SUCCESS if successful.
    ctypedef int (* sox_effect_handler_start)(sox_effect_t * effp)

    # Callback to process samples,
    # used by sox_effect_handler.flow.
    # @returns SOX_SUCCESS if successful.
    ctypedef int (* sox_effect_handler_flow)(
        sox_effect_t * effp,
        sox_sample_t * ibuf, # Buffer from which to read samples.
        sox_sample_t * obuf, # Buffer to which samples are written.
        size_t *isamp, # On entry, contains capacity of ibuf on exit, contains number of samples consumed.
        size_t *osamp # On entry, contains capacity of obuf on exit, contains number of samples written.
    )

    # Callback to finish getting output after input is complete,
    # used by sox_effect_handler.drain.
    # @returns SOX_SUCCESS if successful.
    ctypedef int (* sox_effect_handler_drain)(
        sox_effect_t * effp,
        sox_sample_t *obuf, # Buffer to which samples are written.
        size_t *osamp # On entry, contains capacity of obuf on exit, contains number of samples written.
    )

    # Callback to shut down effect (called once per flow),
    # used by sox_effect_handler.stop.
    # @returns SOX_SUCCESS if successful.
    ctypedef int (* sox_effect_handler_stop)(sox_effect_t * effp)

    # Callback to shut down effect (called once per effect),
    # used by sox_effect_handler.kill.
    # @returns SOX_SUCCESS if successful.
    ctypedef int (* sox_effect_handler_kill)(sox_effect_t * effp)

    # Callback called while flow is running (called once per buffer),
    # used by sox_flow_effects.callback.
    # @returns SOX_SUCCESS to continue, other value to abort flow.
    ctypedef int (* sox_flow_effects_callback)(sox_bool all_done, void * client_data)

    # Callback for enumerating the contents of a playlist,
    # used by the sox_parse_playlist function.
    # @returns SOX_SUCCESS if successful, any other value to abort playlist enumeration.
    ctypedef int (* sox_playlist_callback_t)(void * callback_data, char * filename)

    # ---------------------------------------------------------------------------
    # structs

    # Information about a build of libSoX, returned from the sox_version_info function.
    ctypedef struct sox_version_info_t:
        size_t size                 # structure size = sizeof(sox_version_info_t)
        sox_version_flags_t flags   # feature flags = popen | magic | threads | memopen
        sox_uint32_t version_code   # version number = 0x140400
        const char * version        # version string = sox_version(), for example, "14.4.0"
        const char * version_extra  # version extra info or null = "PACKAGE_EXTRA", for example, "beta"
        const char * time           # build time = "__DATE__ __TIME__", for example, "Jan  7 2010 03:31:50"
        const char * distro         # distro or null = "DISTRO", for example, "Debian"
        const char * compiler       # compiler info or null, for example, "msvc 160040219"
        const char * arch           # arch, for example, "1248 48 44 L OMP"
        # new info should be added at the end for version backwards-compatibility.

    # Global parameters (for effects & formats), returned from the sox_get_globals function.
    ctypedef struct sox_globals_t:
        # public
        unsigned     verbosity # messages are only written if globals.verbosity >= message.level
        sox_output_message_handler_t output_message_handler # client-specified message output callback
        sox_bool     repeatable # true to use pre-determined timestamps and PRNG seed

        # Default size (in bytes) used by libSoX for blocks of sample data.
        # Plugins should use similarly-sized buffers to get best performance.
        size_t       bufsiz

        # Default size (in bytes) used by libSoX for blocks of input sample data.
        # Plugins should use similarly-sized buffers to get best performance.
        size_t       input_bufsiz

        sox_int32_t  ranqd1  # Can be used to re-seed libSoX's PRNG

        const char * stdin_in_use_by      # Private: tracks the name of the handler currently using stdin
        const char * stdout_in_use_by     # Private: tracks the name of the handler currently using stdout
        const char * subsystem            # Private: tracks the name of the handler currently writing an output message
        char * tmp_path             # Private: client-configured path to use for temporary files
        sox_bool     use_magic      # Private: true if client has requested use of 'magic' file-type detection
        sox_bool     use_threads    # Private: true if client has requested parallel effects processing
        
        # Log to base 2 of minimum size (in bytes) used by libSoX for DFT (filtering).
        # Plugins should use similarly-sized DFTs to get best performance.
        size_t       log2_dft_min_size 

    # Signal parameters members should be set to SOX_UNSPEC (= 0) if unknown.
    ctypedef struct sox_signalinfo_t:
        sox_rate_t       rate         # samples per second, 0 if unknown
        unsigned         channels     # number of sound channels, 0 if unknown
        unsigned         precision    # bits per sample, 0 if unknown
        sox_uint64_t     length       # samples * chans in file, 0 if unknown, -1 if unspecified
        double           * mult       # Effects headroom multiplier may be null

    # Basic information about an encoding.
    ctypedef struct sox_encodings_info_t:
        sox_encodings_flags_t flags  # lossy once (lossy1), lossy twice (lossy2), or lossless (none).
        const char * name            # encoding name.
        const char * desc            # encoding description.

    # Encoding parameters.
    ctypedef struct sox_encodinginfo_t:
        sox_encoding_t encoding        # format of sample numbers
        unsigned bits_per_sample       # 0 if unknown or variable uncompressed value if lossless compressed value if lossy
        double compression             # compression factor (where applicable)
        sox_option_t reverse_bytes     # Should bytes be reversed?
        sox_option_t reverse_nibbles   # Should nibbles be reversed?
        sox_option_t reverse_bits      # Should bits be reversed?
        sox_bool opposite_endian       # If set to true, the format should reverse its default endianness.

    # Looping parameters (out-of-band data).
    ctypedef struct sox_loopinfo_t:
        sox_uint64_t  start  # first sample
        sox_uint64_t  length # length
        unsigned      count  # number of repeats, 0=forever
        unsigned char type   # 0=no, 1=forward, 2=forward/back (see sox_loop_* for valid values).

    # Instrument information.
    ctypedef struct sox_instrinfo_t:
        signed char MIDInote   # for unity pitch playback
        signed char MIDIlow    # MIDI pitch-bend low range
        signed char MIDIhi     # MIDI pitch-bend high range
        unsigned char loopmode # 0=no, 1=forward, 2=forward/back (see sox_loop_* values)
        unsigned nloops        # number of active loops (max SOX_MAX_NLOOPS).

    # File buffer info.  Holds info so that data can be read in blocks.
    ctypedef struct sox_fileinfo_t:
        char   *buf             # Pointer to data buffer
        size_t size             # Size of buffer in bytes
        size_t count            # Count read into buffer
        size_t pos              # Position in buffer

    # Handler structure defined by each format.
    ctypedef struct sox_format_handler_t:
        unsigned     sox_lib_version_code   # Checked on load must be 1st in struct*/
        const char   * description          # short description of format
        const char   ** names               # null-terminated array of filename extensions that are handled by this format
        unsigned int flags                  # File flags (SOX_FILE_* values).
        sox_format_handler_startread startread # called to initialize reader (decoder)
        sox_format_handler_read read        # called to read (decode) a block of samples
        sox_format_handler_stopread stopread # called to close reader (decoder) may be null if no closing necessary
        sox_format_handler_startwrite startwrite # called to initialize writer (encoder)
        sox_format_handler_write write      # called to write (encode) a block of samples
        sox_format_handler_stopwrite stopwrite # called to close writer (decoder) may be null if no closing necessary
        sox_format_handler_seek seek        # called to reposition reader may be null if not supported

        # Array of values indicating the encodings and precisions supported for
        # writing (encoding). Precisions specified with default precision first.
        # Encoding, precision, precision, ..., 0, repeat. End with one more 0.
        # Example:
        # unsigned const * formats = {
        #   SOX_ENCODING_SIGN2, 16, 24, 0, // Support SIGN2 at 16 and 24 bits, default to 16 bits.
        #   SOX_ENCODING_UNSIGNED, 8, 0,   // Support UNSIGNED at 8 bits, default to 8 bits.
        #   0 // No more supported encodings.
        #   };
        const unsigned * write_formats

        # Array of sample rates (samples per second) supported for writing (encoding).
        # NULL if all (or almost all) rates are supported. End with 0.
        const sox_rate_t * write_rates

        # SoX will automatically allocate a buffer in which the handler can store data.
        # Specify the size of the buffer needed here. Usually this will be sizeof(your_struct).
        # The buffer will be allocated and zeroed before the call to startread/startwrite.
        # The buffer will be freed after the call to stopread/stopwrite.
        # The buffer will be provided via format.priv in each call to the handler.
        size_t priv_size

    # Comments, instrument info, loop info (out-of-band data).
    ctypedef struct sox_oob_t:
        sox_comments_t   comments        # Comment strings in id=value format.
        sox_instrinfo_t  instr           # Instrument specification
        sox_loopinfo_t   loops[8]        # Looping specification

    # Data passed to/from the format handler
    ctypedef struct sox_format_t:
        char * filename

        # Signal specifications for reader (decoder) or writer (encoder):
        # sample rate, number of channels, precision, length, headroom multiplier.
        # Any info specified by the user is here on entry to startread or
        # startwrite. Info will be SOX_UNSPEC if the user provided no info.
        # At exit from startread, should be completely filled in, using
        # either data from the file's headers (if available) or whatever
        # the format is guessing/assuming (if header data is not available).
        # At exit from startwrite, should be completely filled in, using
        # either the data that was specified, or values chosen by the format
        # based on the format's defaults or capabilities.
        sox_signalinfo_t signal

        # Encoding specifications for reader (decoder) or writer (encoder):
        # encoding (sample format), bits per sample, compression rate, endianness.
        # Should be filled in by startread. Values specified should be used
        # by startwrite when it is configuring the encoding parameters.
        sox_encodinginfo_t encoding

        char             * filetype      # Type of file, as determined by header inspection or libmagic.
        sox_oob_t        oob             # comments, instrument info, loop info (out-of-band data)
        sox_bool         seekable        # Can seek on this file
        char             mode            # Read or write mode ('r' or 'w')
        sox_uint64_t     olength         # Samples * chans written to file
        sox_uint64_t     clips           # Incremented if clipping occurs
        int              sox_errno       # Failure error code
        char             sox_errstr[256] # Failure error text
        void             * fp            # File stream pointer
        lsx_io_type      io_type         # Stores whether this is a file, pipe or URL
        sox_uint64_t     tell_off        # Current offset within file
        sox_uint64_t     data_start      # Offset at which headers end and sound data begins (set by lsx_check_read_params)
        sox_format_handler_t handler     # Format handler for this file
        void             * priv          # Format handler's private data area

    # Information about a loaded format handler, including the format name and a
    # function pointer that can be invoked to get additional information about the
    # format.
    ctypedef struct sox_format_tab_t:
        char *name         # Name of format handler
        sox_format_fn_t fn # Function to call to get format handler's information

    # Global parameters for effects.
    ctypedef struct sox_effects_globals_t:
        sox_plot_t plot                # To help the user choose effect & options
        sox_globals_t * global_info    # Pointer to associated SoX globals

    # Effect handler information.
    ctypedef struct sox_effect_handler_t:
        const char * name;  # Effect name
        const char * usage; # Short explanation of parameters accepted by effect
        unsigned int flags; # Combination of SOX_EFF_* flags
        sox_effect_handler_getopts getopts; # Called to parse command-line arguments (called once per effect).
        sox_effect_handler_start start;     # Called to initialize effect (called once per flow).
        sox_effect_handler_flow flow;       # Called to process samples.
        sox_effect_handler_drain drain;     # Called to finish getting output after input is complete.
        sox_effect_handler_stop stop;       # Called to shut down effect (called once per flow).
        sox_effect_handler_kill kill;       # Called to shut down effect (called once per effect).
        size_t priv_size;                   # Size of private data SoX should pre-allocate for effect

    ctypedef struct sox_effect_t:
        sox_effects_globals_t    * global_info  # global effect parameters
        sox_signalinfo_t         in_signal      # Information about the incoming data stream
        sox_signalinfo_t         out_signal     # Information about the outgoing data stream
        const sox_encodinginfo_t * in_encoding  # Information about the incoming data encoding
        const sox_encodinginfo_t * out_encoding # Information about the outgoing data encoding
        sox_effect_handler_t     handler        # The handler for this effect
        sox_uint64_t         clips              # increment if clipping occurs
        size_t               flows              # 1 if MCHAN, number of chans otherwise
        size_t               flow               # flow number
        void                 * priv             # Effect's private data area (each flow has a separate copy)
        # The following items are private to the libSoX effects chain functions.
        sox_sample_t         * obuf             # output buffer
        size_t                obeg              # output buffer: start of valid data section
        size_t                oend              # output buffer: one past valid data section (oend-obeg is length of current content)
        size_t                imin              # minimum input buffer content required for calling this effect's flow function set via lsx_effect_set_imin()

    ctypedef struct sox_effects_chain_t:
        sox_effect_t **effects                  # Table of effects to be applied to a stream
        size_t length                           # Number of effects to be applied
        sox_effects_globals_t global_info       # Copy of global effects settings
        const sox_encodinginfo_t * in_enc       # Input encoding
        const sox_encodinginfo_t * out_enc      # Output encoding
        # The following items are private to the libSoX effects chain functions.
        size_t table_size                       # Size of effects table (including unused entries)
        sox_sample_t *il_buf                    # Channel interleave buffer

    # ---------------------------------------------------------------------------
    # functions

    # Returns version number string of libSoX, for example, "14.4.0".
    cdef const char * sox_version()

    # Returns information about this build of libsox.
    cdef const sox_version_info_t * sox_version_info()

    # Returns a pointer to the structure with libSoX's global settings.
    cdef sox_globals_t * sox_get_globals()

    # Returns a pointer to the list of available encodings.
    # End of list indicated by name == NULL.
    cdef const sox_encodings_info_t * sox_get_encodings_info()

    # Fills in an encodinginfo with default values.
    # e: Pointer to uninitialized encoding info structure to be initialized.
    cdef void sox_init_encodinginfo(sox_encodinginfo_t * e)

    # Given an encoding (for example, SIGN2) and the encoded bits_per_sample (for
    # example, 16), returns the number of useful bits per sample in the decoded data
    # (for example, 16), or returns 0 to indicate that the value returned by the
    # format handler should be used instead of a pre-determined precision.
    # @returns the number of useful bits per sample in the decoded data (for example
    # 16), or returns 0 to indicate that the value returned by the format handler
    # should be used instead of a pre-determined precision.
    cdef unsigned sox_precision(sox_encoding_t encoding, unsigned bits_per_sample)

    # Returns the number of items in the metadata block.
    cdef size_t sox_num_comments(sox_comments_t comments)

    # Adds an "id=value" item to the metadata block.
    cdef void sox_append_comment(sox_comments_t * comments, const char * item)

    # Adds a newline-delimited list of "id=value" items to the metadata block.
    cdef void sox_append_comments(sox_comments_t * comments, const char * items)

    # Duplicates the metadata block.
    # @returns the copied metadata block.
    cdef sox_comments_t sox_copy_comments(sox_comments_t comments)

    # Frees the metadata block.
    cdef void sox_delete_comments(sox_comments_t * comments)

    # If "id=value" is found, return value, else return null.
    # @returns value, or null if value not found.
    cdef char * sox_find_comment(sox_comments_t comments, const char * id)

    # Find and load format handler plugins.
    # @returns SOX_SUCCESS if successful.
    cdef int sox_format_init()

    # Unload format handler plugins.
    cdef void sox_format_quit()

    # Initialize effects library.
    # @returns SOX_SUCCESS if successful.
    cdef int sox_init()

    # Close effects library and unload format handler plugins.
    # @returns SOX_SUCCESS if successful.
    cdef int sox_quit()

    # Returns the table of format handler names and functions.
    # @returns the table of format handler names and functions.
    cdef const sox_format_tab_t * sox_get_format_fns()

    # Opens a decoding session for a file. Returned handle must be closed with sox_close().
    # @returns The handle for the new session, or null on failure.
    cdef sox_format_t * sox_open_read(
        const char               * path,
        const sox_signalinfo_t   * signal,
        const sox_encodinginfo_t * encoding,
        const char               * filetype
    )


    # Opens a decoding session for a memory buffer. Returned handle must be closed with sox_close().
    # @returns The handle for the new session, or null on failure.
    sox_format_t * sox_open_mem_read(
        void * buffer,                       # Pointer to audio data buffer (required).
        size_t buffer_size,                  # Number of bytes to read from audio data buffer.
        const sox_signalinfo_t * signal,     # Information already known about audio stream, or NULL if none.     
        const sox_encodinginfo_t * encoding, # Information already known about sample encoding, or NULL if none.   
        const char * filetype                # Previously-determined file type, or NULL to auto-detect.
    )

    # Opens an encoding session for a file. Returned handle must be closed with sox_close().
    # @returns The new session handle, or null on failure.
    cdef sox_format_t * sox_open_write(
        const char * path,                   # Path to file to be written (required). 
        const sox_signalinfo_t   * signal,   # Information about desired audio stream (required). 
        const sox_encodinginfo_t * encoding, # Information about desired sample encoding, or NULL to use defaults. 
        const char * filetype,               # Previously-determined file type, or NULL to auto-detect. 
        const sox_oob_t * oob,               # Out-of-band data to add to file, or NULL if none. 
        sox_bool (* overwrite_permitted)(char * filename) # Called if file exists to determine whether overwrite is ok. 
    )

    # Returns true if the format handler for the specified file type supports the specified encoding.
    # @returns true if the format handler for the specified file type supports the specified encoding.
    cdef sox_bool sox_format_supports_encoding(
        const char * path,       # Path to file to be examined (required if filetype is NULL). */
        const char * filetype,   # Previously-determined file type, or NULL to use extension from path. */
        const sox_encodinginfo_t * encoding    # Encoding for which format handler should be queried. */
    )

    # Gets the format handler for a specified file type.
    # @returns The found format handler, or null if not found.
    cdef sox_format_handler_t * sox_write_handler(
        const char * path,         # Path to file (required if filetype is NULL). 
        const char * filetype,     # Filetype for which handler is needed, or NULL to use extension from path. 
        const char ** filetype1    # Receives the filetype that was detected. Pass NULL if not needed. 
    )

    # Opens an encoding session for a memory buffer. Returned handle must be closed with sox_close().
    # @returns The new session handle, or null on failure.
    cdef sox_format_t * sox_open_mem_write(
        void * buffer,      # Pointer to audio data buffer that receives data (required). 
        size_t buffer_size, # Maximum number of bytes to write to audio data buffer. 
        const sox_signalinfo_t   * signal,      # Information about desired audio stream (required). 
        const sox_encodinginfo_t * encoding,    # Information about desired sample encoding, or NULL to use defaults. 
        const char               * filetype,    # Previously-determined file type, or NULL to auto-detect. 
        const sox_oob_t          * oob          # Out-of-band data to add to file, or NULL if none. 
    )

    # Opens an encoding session for a memstream buffer. Returned handle must be closed with sox_close().
    # @returns The new session handle, or null on failure.
    cdef sox_format_t * sox_open_memstream_write(
        char ** buffer_ptr,    # Receives pointer to audio data buffer that receives data (required). 
        size_t * buffer_size_ptr, # Receives size of data written to audio data buffer (required). 
        const sox_signalinfo_t   * signal,          # Information about desired audio stream (required). 
        const sox_encodinginfo_t * encoding,        # Information about desired sample encoding, or NULL to use defaults. 
        const char * filetype,        # Previously-determined file type, or NULL to auto-detect. 
        const sox_oob_t * oob         # Out-of-band data to add to file, or NULL if none. 
    )

    # Reads samples from a decoding session into a sample buffer.
    # @returns Number of samples decoded, or 0 for EOF.
    cdef size_t sox_read(
        sox_format_t * ft, # Format pointer. 
        sox_sample_t *buf, # Buffer from which to read samples. 
        size_t len # Number of samples available in buf. 
    )

    # Writes samples to an encoding session from a sample buffer.
    # @returns Number of samples encoded.
    cdef size_t sox_write(
        sox_format_t * ft,        # Format pointer. 
        const sox_sample_t * buf, # Buffer from which to read samples. 
        size_t len # Number of samples available in buf. 
    )

    # Closes an encoding or decoding session.
    # @returns SOX_SUCCESS if successful.
    cdef int sox_close(sox_format_t * ft)

    # Sets the location at which next samples will be decoded. Returns SOX_SUCCESS if successful.
    # @returns SOX_SUCCESS if successful.
    cdef int sox_seek(
        sox_format_t * ft, # Format pointer. 
        sox_uint64_t offset, # Sample offset at which to position reader. 
        int whence # Set to SOX_SEEK_SET. 
    )

    # Finds a format handler by name.
    # @returns Format handler data, or null if not found.
    cdef const sox_format_handler_t * sox_find_format(
        const char * name, # Name of format handler to find. 
        sox_bool ignore_devices # Set to true to ignore device names. 
    )

    # Returns global parameters for effects
    # @returns global parameters for effects.
    cdef sox_effects_globals_t * sox_get_effects_globals()

    # Finds the effect handler with the given name.
    # @returns Effect pointer, or null if not found.
    cdef sox_effect_handler_t * sox_find_effect(const char * name)

    # Creates an effect using the given handler.
    # @returns The new effect, or null if not found.
    cdef sox_effect_t * sox_create_effect(const sox_effect_handler_t * eh)

    # Applies the command-line options to the effect.
    # @returns the number of arguments consumed.
    cdef int sox_effect_options(
        sox_effect_t *effp, # Effect pointer on which to set options. 
        int argc, # Number of arguments in argv. 
        const char * argv[] # Array of command-line options. 
    )

    # Returns an array containing the known effect handlers.
    # @returns An array containing the known effect handlers.
    cdef const sox_effect_fn_t * sox_get_effect_fns()

    # Initializes an effects chain. Returned handle must be closed with sox_delete_effects_chain().
    # @returns Handle, or null on failure.
    cdef sox_effects_chain_t * sox_create_effects_chain(
        const sox_encodinginfo_t * in_enc, # Input encoding. 
        const sox_encodinginfo_t * out_enc # Output encoding. 
    )

    # Closes an effects chain.
    cdef void sox_delete_effects_chain(sox_effects_chain_t *ecp)

    # Adds an effect to the effects chain, returns SOX_SUCCESS if successful.
    # @returns SOX_SUCCESS if successful.
    cdef int sox_add_effect(
        sox_effects_chain_t * chain, # Effects chain to which effect should be added . 
        sox_effect_t * effp,         # Effect to be added. 
        sox_signalinfo_t * in_,      # Input format. 
        const sox_signalinfo_t * out # Output format. 
    )

    # Runs the effects chain, returns SOX_SUCCESS if successful.
    # @returns SOX_SUCCESS if successful.
    cdef int sox_flow_effects(
        sox_effects_chain_t * chain, # Effects chain to run. 
        sox_flow_effects_callback callback, # Callback for monitoring flow progress. 
        void * client_data # Data to pass into callback. 
    )

    # Gets the number of clips that occurred while running an effects chain.
    # @returns the number of clips that occurred while running an effects chain.
    cdef sox_uint64_t sox_effects_clips(
        sox_effects_chain_t * chain # Effects chain from which to read clip information. 
    )

    # Shuts down an effect (calls stop on each of its flows).
    # @returns the number of clips from all flows.
    cdef sox_uint64_t sox_stop_effect(sox_effect_t * effp)

    # Adds an already-initialized effect to the end of the chain.
    cdef void sox_push_effect_last(
        sox_effects_chain_t * chain, # Effects chain to which effect should be added. 
        sox_effect_t * effp # Effect to be added. 
    )

    # Removes and returns an effect from the end of the chain.
    # @returns the removed effect, or null if no effects.
    sox_effect_t * sox_pop_effect_last(
        sox_effects_chain_t *chain # Effects chain from which to remove an effect. 
    )

    # Shut down and delete an effect.
    cdef void sox_delete_effect(sox_effect_t *effp)

    # Shut down and delete the last effect in the chain.
    cdef void sox_delete_effect_last(sox_effects_chain_t *chain)

    # Shut down and delete all effects in the chain.
    cdef void sox_delete_effects(sox_effects_chain_t *chain)

    # Gets the sample offset of the start of the trim, useful for efficiently
    # skipping the part that will be trimmed anyway (get trim start, seek, then
    # clear trim start).
    # @returns the sample offset of the start of the trim.
    cdef sox_uint64_t sox_trim_get_start(sox_effect_t * effp)

    # Clears the start of the trim to 0.
    cdef void sox_trim_clear_start(sox_effect_t * effp)

    # Returns true if the specified file is a known playlist file type.
    # @returns true if the specified file is a known playlist file type.
    cdef sox_bool sox_is_playlist(const char * filename)

    # Parses the specified playlist file.
    # @returns SOX_SUCCESS if successful.
    cdef int sox_parse_playlist(
        sox_playlist_callback_t callback, # Callback to call for each item in the playlist. 
        void * p, # Data to pass to callback. 
        const char * listname # Filename of playlist file. 
    )

    # Converts a SoX error code into an error string.
    # @returns error string corresponding to the specified error code,
    # or a generic message if the error code is not recognized.
    cdef const char * sox_strerror(int sox_errno )

    # Gets the basename of the specified file for example, the basename of
    # "/a/b/c.d" would be "c".
    # @returns the number of characters written to base_buffer, excluding the null,
    # or 0 on failure.
    cdef size_t sox_basename(
        char * base_buffer, # Buffer into which basename should be written. 
        size_t base_buffer_len, # Size of base_buffer, in bytes. 
        const char * filename # Filename from which to extract basename. 
    )
