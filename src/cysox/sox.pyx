"""sox.pyx - a thin wrapper around libsox"""

from types import SimpleNamespace
from cpython.buffer cimport PyObject_CheckBuffer, PyObject_GetBuffer, PyBuffer_Release, PyBUF_WRITABLE, PyBUF_C_CONTIGUOUS, Py_buffer
from cpython.ref cimport PyObject
from libc.stdint cimport uintptr_t

cimport cysox.sox


# Global storage for flow_effects callback
# We use a dictionary to support multiple concurrent chains (thread-safety handled by GIL)
_flow_callbacks = {}

# Storage for the last callback exception (since exceptions can't propagate through C code)
_last_callback_exception = None

# Track initialization state to make init()/quit() idempotent
# (libsox crashes on repeated init/quit cycles, so we only do it once)
_sox_initialized = False


ERROR_CODES = {
    'SOX_SUCCESS': SOX_SUCCESS,
    'SOX_EOF': SOX_EOF,
    'SOX_EHDR': SOX_EHDR,
    'SOX_EFMT': SOX_EFMT,
    'SOX_ENOMEM': SOX_ENOMEM,
    'SOX_EPERM': SOX_EPERM,
    'SOX_ENOTSUP': SOX_ENOTSUP,
    'SOX_EINVAL': SOX_EINVAL,
}

# Expose constants at module level - Python accessible
SUCCESS = SOX_SUCCESS
EOF = SOX_EOF
EHDR = SOX_EHDR
EFMT = SOX_EFMT
ENOMEM = SOX_ENOMEM
EPERM = SOX_EPERM
ENOTSUP = SOX_ENOTSUP
EINVAL = SOX_EINVAL


ENCODINGS = [
    ("UNKNOWN",     "encoding has not yet been determined"),
    ("SIGN2",       "signed linear 2's comp: Mac"),
    ("UNSIGNED",    "unsigned linear: Sound Blaster"),
    ("FLOAT",       "floating point (binary format)"),
    ("FLOAT_TEXT",  "floating point (text format)"),
    ("FLAC",        "FLAC compression"),
    ("HCOM",        "Mac FSSD files with Huffman compression"),
    ("WAVPACK",     "WavPack with integer samples"),
    ("WAVPACKF",    "WavPack with float samples"),
    ("ULAW",        "u-law signed logs: US telephony, SPARC"),
    ("ALAW",        "A-law signed logs: non-US telephony, Psion"),
    ("G721",        "G.721 4-bit ADPCM"),
    ("G723",        "G.723 3 or 5 bit ADPCM"),
    ("CL_ADPCM  ",  "Creative Labs 8 --> 2,3,4 bit Compressed PCM"),
    ("CL_ADPCM16",  "Creative Labs 16 --> 4 bit Compressed PCM"),
    ("MS_ADPCM  ",  "Microsoft Compressed PCM"),
    ("IMA_ADPCM ",  "IMA Compressed PCM"),
    ("OKI_ADPCM ",  "Dialogic/OKI Compressed PCM"),
    ("DPCM",        "Differential PCM: Fasttracker 2 (xi)"),
    ("DWVW ",       "Delta Width Variable Word"),
    ("DWVWN",       "Delta Width Variable Word N-bit"),
    ("GSM",         "GSM 6.10 33byte frame lossy compression"),
    ("MP3",         "MP3 compression"),
    ("VORBIS",      "Vorbis compression"),
    ("AMR_WB",      "AMR-WB compression"),
    ("AMR_NB",      "AMR-NB compression"),
    ("CVSD",        "Continuously Variable Slope Delta modulation"),
    ("LPC10",       "Linear Predictive Coding"),
    ("OPUS",        "Opus compression"),
]

constant = SimpleNamespace(**{
    'INT8_MAX': SOX_INT8_MAX,
    'INT16_MAX': SOX_INT16_MAX,
    'INT24_MAX': SOX_INT24_MAX,
    'SAMPLE_PRECISION': SOX_SAMPLE_PRECISION,
    'SAMPLE_MAX': SOX_SAMPLE_MAX,
    'SAMPLE_MIN': SOX_SAMPLE_MIN,
    'SAMPLE_NEG': SOX_SAMPLE_NEG,

    'SIZE_MAX': SOX_SIZE_MAX,
    'UNSPEC': SOX_UNSPEC,
    'UNKNOWN_LEN': SOX_UNKNOWN_LEN,
    'IGNORE_LENGTH': SOX_IGNORE_LENGTH,
    'DEFAULT_RATE': SOX_DEFAULT_RATE,
    'DEFAULT_PRECISION': SOX_DEFAULT_PRECISION,
    'DEFAULT_ENCODING': SOX_DEFAULT_ENCODING,
    'LOOP_NONE': SOX_LOOP_NONE,
    'LOOP_8': SOX_LOOP_8,
    'LOOP_SUSTAIN_DECAY': SOX_LOOP_SUSTAIN_DECAY,
    'MAX_NLOOPS': SOX_MAX_NLOOPS,

    'FILE_NOSTDIO': SOX_FILE_NOSTDIO,
    'FILE_DEVICE': SOX_FILE_DEVICE,

    'FILE_PHONY': SOX_FILE_PHONY,
    'FILE_REWIND': SOX_FILE_REWIND,
    'FILE_BIT_REV': SOX_FILE_BIT_REV,
    'FILE_NIB_REV': SOX_FILE_NIB_REV,
    'FILE_ENDIAN': SOX_FILE_ENDIAN,
    'FILE_ENDBIG': SOX_FILE_ENDBIG,
    'FILE_MONO': SOX_FILE_MONO,
    'FILE_STEREO': SOX_FILE_STEREO,
    'FILE_QUAD': SOX_FILE_QUAD,

    'FILE_CHANS': SOX_FILE_CHANS,
    'FILE_LIT_END': SOX_FILE_LIT_END,
    'FILE_BIG_END': SOX_FILE_BIG_END,

    'EFF_CHAN': SOX_EFF_CHAN,
    'EFF_RATE': SOX_EFF_RATE,
    'EFF_PREC': SOX_EFF_PREC,
    'EFF_LENGTH': SOX_EFF_LENGTH,
    'EFF_MCHAN': SOX_EFF_MCHAN,
    'EFF_NULL': SOX_EFF_NULL,
    'EFF_DEPRECATED': SOX_EFF_DEPRECATED,
    'EFF_GAIN': SOX_EFF_GAIN,
    'EFF_MODIFY': SOX_EFF_MODIFY,
    'EFF_ALPHA': SOX_EFF_ALPHA,
    'EFF_INTERNAL': SOX_EFF_INTERNAL,
    'SEEK_SET': SOX_SEEK_SET,
})


# Custom exception classes for better error handling
class SoxError(Exception):
    """Base exception for all SoX-related errors."""
    pass


class SoxInitError(SoxError):
    """Exception raised when SoX initialization fails."""
    pass


class SoxFormatError(SoxError):
    """Exception raised when format operations fail."""
    pass


class SoxEffectError(SoxError):
    """Exception raised when effect operations fail."""
    pass


class SoxIOError(SoxError):
    """Exception raised when I/O operations fail."""
    pass


class SoxMemoryError(SoxError):
    """Exception raised when memory allocation fails."""
    pass



cdef class SignalInfo:
    """Signal parameters describing audio properties.

    This class encapsulates the signal characteristics of an audio stream,
    including sample rate, number of channels, precision, and length.

    All members can be set to SOX_UNSPEC (= 0) if unknown.

    Attributes:
        rate: Sample rate in samples per second (Hz), 0 if unknown
        channels: Number of audio channels, 0 if unknown
        precision: Bits per sample, 0 if unknown
        length: Total samples * channels in file, 0 if unknown, -1 if unspecified
        mult: Effects headroom multiplier, may be None

    Example:
        >>> signal = sox.SignalInfo(rate=44100, channels=2, precision=16)
        >>> f = sox.Format('output.wav', signal=signal, mode='w')
    """
    cdef sox_signalinfo_t* ptr
    cdef bint owner

    def __cinit__(self):
        self.ptr = NULL
        self.owner = False

    def __dealloc__(self):
        if self.ptr is not NULL and self.owner is True:
            if self.ptr.mult is not NULL:
                free(self.ptr.mult)
            free(self.ptr)
            self.ptr = NULL

    def __init__(self, rate: float = 0.0, channels: int = 0,
                precision: int = 0, length: int = 0, mult: float = 0.0):
        self.ptr = <sox_signalinfo_t*>malloc(sizeof(sox_signalinfo_t))
        if self.ptr is NULL:
            raise SoxMemoryError("Failed to allocate SignalInfo")
        self.rate = rate
        self.channels = channels
        self.precision = precision
        self.length = length
        self.mult = mult
        self.owner = True

    @staticmethod
    cdef SignalInfo from_ptr(sox_signalinfo_t* ptr, bint owner=False):
        cdef SignalInfo wrapper = SignalInfo.__new__(SignalInfo)
        wrapper.ptr = ptr
        wrapper.owner = owner
        return wrapper

    @property
    def rate(self) -> sox_rate_t:
        """samples per second, 0 if unknown"""
        if self.ptr is NULL:
            raise RuntimeError("SignalInfo pointer is NULL")
        return self.ptr.rate

    @rate.setter
    def rate(self, sox_rate_t value):
        if self.ptr is NULL:
            raise RuntimeError("SignalInfo pointer is NULL")
        self.ptr.rate = value

    @property
    def channels(self) -> int:
        """number of sound channels, 0 if unknown"""
        if self.ptr is NULL:
            raise RuntimeError("SignalInfo pointer is NULL")
        return self.ptr.channels

    @channels.setter
    def channels(self, int value):
        if self.ptr is NULL:
            raise RuntimeError("SignalInfo pointer is NULL")
        self.ptr.channels = value

    @property
    def precision(self) -> int:
        """bits per sample, 0 if unknown"""
        if self.ptr is NULL:
            raise RuntimeError("SignalInfo pointer is NULL")
        return self.ptr.precision

    @precision.setter
    def precision(self, int value):
        if self.ptr is NULL:
            raise RuntimeError("SignalInfo pointer is NULL")
        self.ptr.precision = value

    @property
    def length(self) -> sox_uint64_t:
        """samples * chans in file, 0 if unknown, -1 if unspecified"""
        if self.ptr is NULL:
            raise RuntimeError("SignalInfo pointer is NULL")
        return self.ptr.length

    @length.setter
    def length(self, sox_uint64_t value):
        if self.ptr is NULL:
            raise RuntimeError("SignalInfo pointer is NULL")
        self.ptr.length = value

    @property
    def mult(self) -> float:
        """Effects headroom multiplier may be null"""
        if self.ptr is NULL:
            raise RuntimeError("SignalInfo pointer is NULL")
        if not self.ptr.mult:
            return 0.0
        return self.ptr.mult[0]

    @mult.setter
    def mult(self, float value):
        if self.ptr is NULL:
            raise RuntimeError("SignalInfo pointer is NULL")
        if value == 0.0:
            # Free existing allocation before setting to NULL
            if self.ptr.mult is not NULL:
                free(self.ptr.mult)
            self.ptr.mult = NULL
        elif self.ptr.mult is NULL:
            self.ptr.mult = <double*>malloc(sizeof(double))
            if self.ptr.mult is NULL:
                raise SoxMemoryError("Failed to allocate memory for mult")
            self.ptr.mult[0] = value
        else:
            self.ptr.mult[0] = value


class EncodingsInfo:
    """Basic information about an encoding."""

    def __init__(self, sox_encodings_flags_t flags, str name, str desc):
        self.flags = flags
        self.name = name
        self.desc = desc

    def __repr__(self):
        return f"<EncodingsInfo '{self.name}' '{self.desc}' '{self.type}'>"

    @property
    def type(self):
        """Encoding type as human-readable string (lossless, lossy1, or lossy2)."""
        return {
            0: 'lossless',
            1: 'lossy1',
            2: 'lossy2',
        }[self.flags]


cdef class EncodingInfo:
    cdef sox_encodinginfo_t* ptr
    cdef bint owner

    def __cinit__(self):
        self.ptr = NULL
        self.owner = False

    def __dealloc__(self):
        if self.ptr is not NULL and self.owner is True:
            free(self.ptr)
            self.ptr = NULL

    def __init__(self, encoding: int = 0, bits_per_sample: int = 0,
                compression: float = 0.0, reverse_bytes: int = 0,
                reverse_nibbles: int = 0, reverse_bits: int = 0,
                opposite_endian: bool = False):
        self.ptr = <sox_encodinginfo_t*>malloc(sizeof(sox_encodinginfo_t))
        if self.ptr is NULL:
            raise SoxMemoryError("Failed to allocate EncodingInfo")
        self.encoding = encoding
        self.bits_per_sample = bits_per_sample
        self.compression = compression
        self.reverse_bytes = reverse_bytes
        self.reverse_nibbles = reverse_nibbles
        self.reverse_bits = reverse_bits
        self.opposite_endian = opposite_endian
        self.owner = True

    # def __init__(self):
    #     """Fills in an encodinginfo with default values."""
    #     self.ptr = <sox_encodinginfo_t*>malloc(sizeof(sox_encodinginfo_t))
    #     self.owner = True
    #     sox_init_encodinginfo(self.ptr)

    @staticmethod
    cdef EncodingInfo from_ptr(const sox_encodinginfo_t* ptr, bint owner=False):
        cdef EncodingInfo wrapper = EncodingInfo.__new__(EncodingInfo)
        wrapper.ptr = <sox_encodinginfo_t*>ptr
        wrapper.owner = owner
        return wrapper

    @property
    def encoding(self) -> sox_encoding_t:
        """format of sample numbers"""
        if self.ptr is NULL:
            raise RuntimeError("EncodingInfo pointer is NULL")
        return self.ptr.encoding

    @encoding.setter
    def encoding(self, sox_encoding_t value):
        if self.ptr is NULL:
            raise RuntimeError("EncodingInfo pointer is NULL")
        self.ptr.encoding = value

    @property
    def bits_per_sample(self) -> int:
        """0 if unknown or variable uncompressed value if lossless compressed value if lossy"""
        if self.ptr is NULL:
            raise RuntimeError("EncodingInfo pointer is NULL")
        return self.ptr.bits_per_sample

    @bits_per_sample.setter
    def bits_per_sample(self, unsigned value):
        if self.ptr is NULL:
            raise RuntimeError("EncodingInfo pointer is NULL")
        self.ptr.bits_per_sample = value

    @property
    def compression(self) -> float:
        """compression factor (where applicable)"""
        if self.ptr is NULL:
            raise RuntimeError("EncodingInfo pointer is NULL")
        return self.ptr.compression

    @compression.setter
    def compression(self, double value):
        if self.ptr is NULL:
            raise RuntimeError("EncodingInfo pointer is NULL")
        self.ptr.compression = value

    @property
    def reverse_bytes(self) -> sox_option_t:
        """Should bytes be reversed?"""
        if self.ptr is NULL:
            raise RuntimeError("EncodingInfo pointer is NULL")
        return self.ptr.reverse_bytes

    @reverse_bytes.setter
    def reverse_bytes(self, sox_option_t value):
        if self.ptr is NULL:
            raise RuntimeError("EncodingInfo pointer is NULL")
        self.ptr.reverse_bytes = value

    @property
    def reverse_nibbles(self) -> sox_option_t:
        """Should nibbles be reversed?"""
        if self.ptr is NULL:
            raise RuntimeError("EncodingInfo pointer is NULL")
        return self.ptr.reverse_nibbles

    @reverse_nibbles.setter
    def reverse_nibbles(self, sox_option_t value):
        if self.ptr is NULL:
            raise RuntimeError("EncodingInfo pointer is NULL")
        self.ptr.reverse_nibbles = value

    @property
    def reverse_bits(self) -> sox_option_t:
        """Should bits be reversed?"""
        if self.ptr is NULL:
            raise RuntimeError("EncodingInfo pointer is NULL")
        return self.ptr.reverse_bits

    @reverse_bits.setter
    def reverse_bits(self, sox_option_t value):
        if self.ptr is NULL:
            raise RuntimeError("EncodingInfo pointer is NULL")
        self.ptr.reverse_bits = value

    @property
    def opposite_endian(self) -> bool:
        """If set to true, the format should reverse its default endianness."""
        if self.ptr is NULL:
            raise RuntimeError("EncodingInfo pointer is NULL")
        return self.ptr.opposite_endian

    @opposite_endian.setter
    def opposite_endian(self, sox_bool value):
        if self.ptr is NULL:
            raise RuntimeError("EncodingInfo pointer is NULL")
        self.ptr.opposite_endian = value


cdef class LoopInfo:
    cdef sox_loopinfo_t* ptr
    cdef bint owner

    def __cinit__(self):
        self.ptr = NULL
        self.owner = False

    def __dealloc__(self):
        if self.ptr is not NULL and self.owner is True:
            free(self.ptr)
            self.ptr = NULL

    def __init__(self, start: int = 0, length: int = 0, count: int = 0,
                 type: int = 0):
        self.ptr = <sox_loopinfo_t*>malloc(sizeof(sox_loopinfo_t))
        self.start = start
        self.length = length
        self.count = count
        self.type = type
        self.owner = True

    @staticmethod
    cdef LoopInfo from_ptr(sox_loopinfo_t* ptr, bint owner=False):
        cdef LoopInfo wrapper = LoopInfo.__new__(LoopInfo)
        wrapper.ptr = ptr
        wrapper.owner = owner
        return wrapper

    @property
    def start(self) -> sox_uint64_t:
        """first sample"""
        if self.ptr is NULL:
            raise RuntimeError("LoopInfo pointer is NULL")
        return self.ptr.start

    @start.setter
    def start(self, sox_uint64_t value):
        if self.ptr is NULL:
            raise RuntimeError("LoopInfo pointer is NULL")
        self.ptr.start = value

    @property
    def length(self) -> sox_uint64_t:
        """length"""
        if self.ptr is NULL:
            raise RuntimeError("LoopInfo pointer is NULL")
        return self.ptr.length

    @length.setter
    def length(self, sox_uint64_t value):
        if self.ptr is NULL:
            raise RuntimeError("LoopInfo pointer is NULL")
        self.ptr.length = value

    @property
    def count(self) -> int:
        """number of repeats, 0=forever"""
        if self.ptr is NULL:
            raise RuntimeError("LoopInfo pointer is NULL")
        return self.ptr.count

    @count.setter
    def count(self, unsigned value):
        if self.ptr is NULL:
            raise RuntimeError("LoopInfo pointer is NULL")
        self.ptr.count = value

    @property
    def type(self) -> int:
        """0=no, 1=forward, 2=forward/back (see sox_loop_* for valid values)"""
        if self.ptr is NULL:
            raise RuntimeError("LoopInfo pointer is NULL")
        return self.ptr.type

    @type.setter
    def type(self, unsigned char value):
        if self.ptr is NULL:
            raise RuntimeError("LoopInfo pointer is NULL")
        self.ptr.type = value


cdef class InstrInfo:
    cdef sox_instrinfo_t* ptr
    cdef bint owner

    def __cinit__(self):
        self.ptr = NULL
        self.owner = False

    def __dealloc__(self):
        if self.ptr is not NULL and self.owner is True:
            free(self.ptr)
            self.ptr = NULL

    def __init__(self, note: int = 0, low: int = 0, high: int = 0,
                 loopmode: int = 0, nloops: int = 0):
        self.ptr = <sox_instrinfo_t*>malloc(sizeof(sox_instrinfo_t))
        self.note = note
        self.low = low
        self.high = high
        self.loopmode = loopmode
        self.nloops = nloops
        self.owner = True

    @staticmethod
    cdef InstrInfo from_ptr(sox_instrinfo_t* ptr, bint owner=False):
        cdef InstrInfo wrapper = InstrInfo.__new__(InstrInfo)
        wrapper.ptr = ptr
        wrapper.owner = owner
        return wrapper

    @property
    def note(self) -> int:
        """for unity pitch playback"""
        return self.ptr.MIDInote

    @note.setter
    def note(self, signed char value):
        self.ptr.MIDInote = value

    @property
    def low(self) -> int:
        """MIDI pitch-bend low range"""
        return self.ptr.MIDIlow

    @low.setter
    def low(self, signed char value):
        self.ptr.MIDIlow = value

    @property
    def high(self) -> int:
        """MIDI pitch-bend high range"""
        return self.ptr.MIDIhi

    @high.setter
    def high(self, signed char value):
        self.ptr.MIDIhi = value

    @property
    def loopmode(self) -> int:
        """0=no, 1=forward, 2=forward/back (see sox_loop_* values)"""
        return self.ptr.loopmode

    @loopmode.setter
    def loopmode(self, unsigned char value):
        self.ptr.loopmode = value

    @property
    def nloops(self) -> int:
        """number of active loops (max SOX_MAX_NLOOPS)"""
        return self.ptr.nloops

    @nloops.setter
    def nloops(self, unsigned value):
        self.ptr.nloops = value


cdef class FileInfo:
    cdef sox_fileinfo_t* ptr
    cdef bint owner

    def __cinit__(self):
        self.ptr = NULL
        self.owner = False

    def __dealloc__(self):
        if self.ptr is not NULL and self.owner is True:
            free(self.ptr)
            self.ptr = NULL

    def __init__(self, buf: bytes = None, size: int = 0, count: int = 0,
                 pos: int = 0):
        self.ptr = <sox_fileinfo_t*>malloc(sizeof(sox_fileinfo_t))
        if self.ptr is NULL:
            raise SoxMemoryError("Failed to allocate FileInfo")

        # Initialize struct members directly (buf property is read-only)
        # Note: buf parameter is ignored since setting it would be unsafe
        self.ptr.buf = NULL
        self.ptr.size = size
        self.ptr.count = count
        self.ptr.pos = pos
        self.owner = True

    @staticmethod
    cdef FileInfo from_ptr(sox_fileinfo_t* ptr, bint owner=False):
        cdef FileInfo wrapper = FileInfo.__new__(FileInfo)
        wrapper.ptr = ptr
        wrapper.owner = owner
        return wrapper

    @property
    def buf(self) -> bytes:
        """Pointer to data buffer (read-only).

        Note: This property is read-only because the buffer is managed internally
        by the sox_fileinfo_t structure. Setting it would create a dangling pointer
        to a temporary Python bytes object.
        """
        if self.ptr.buf == NULL:
            return None
        return self.ptr.buf[:self.ptr.size]

    @property
    def size(self) -> int:
        """Size of buffer in bytes"""
        return self.ptr.size

    @size.setter
    def size(self, size_t value):
        self.ptr.size = value

    @property
    def count(self) -> int:
        """Count read into buffer"""
        return self.ptr.count

    @count.setter
    def count(self, size_t value):
        self.ptr.count = value

    @property
    def pos(self) -> int:
        """Position in buffer"""
        return self.ptr.pos

    @pos.setter
    def pos(self, size_t value):
        self.ptr.pos = value


cdef class OutOfBand:
    cdef sox_oob_t* ptr
    cdef bint owner

    def __cinit__(self):
        self.ptr = NULL
        self.owner = False

    def __dealloc__(self):
        if self.ptr is not NULL and self.owner is True:
            # Clean up comments before freeing the struct
            if self.ptr.comments:
                sox_delete_comments(&self.ptr.comments)
            free(self.ptr)
            self.ptr = NULL

    def __init__(self):
        self.ptr = <sox_oob_t*>malloc(sizeof(sox_oob_t))
        self.owner = True

    @staticmethod
    cdef OutOfBand from_ptr(sox_oob_t* ptr, bint owner=False):
        cdef OutOfBand wrapper = OutOfBand.__new__(OutOfBand)
        wrapper.ptr = ptr
        wrapper.owner = owner
        return wrapper

    def num_comments(self) -> int:
        """Returns the number of items in the metadata block."""
        return <int>sox_num_comments(self.ptr.comments)

    def append_comment(self, item: str):
        """Adds an 'id=value' item to the metadata block."""
        sox_append_comment(&self.ptr.comments, item.encode())

    def append_comments(self, items: str):
        """Adds a newline-delimited list of "id=value" items to the metadata block."""
        sox_append_comments(&self.ptr.comments, items.encode())

    cdef sox_comments_t copy_comments(self):
        """Duplicates the metadata block."""
        return sox_copy_comments(self.ptr.comments)

    def find_comment(self, id: str) -> str:
        """If "id=value" is found, return value, else return null."""
        cdef char * value = <char*>sox_find_comment(self.ptr.comments, id.encode())
        if value is not NULL:
            return value.decode()

    @property
    def comments(self) -> list[str]:
        """Comment strings in id=value format."""
        cdef size_t n = sox_num_comments(self.ptr.comments)
        _comments = []
        for i in range(n):
            _comments.append(self.ptr.comments[i].decode())
        return _comments

    # FIXME: use list[str]
    # @comments.setter
    # def comments(self, sox_comments_t value):
    #     self.ptr.comments = value

    # cdef char** create_char_array(list python_strings):
    #     cdef int num_strings = len(python_strings)
    #     cdef char** c_array = <char**> malloc(num_strings * sizeof(char*))
    #     if not c_array:
    #         # Handle allocation error
    #         pass

    #     for i in range(num_strings):
    #         # Convert Python string to C string and store pointer
    #         c_array[i] = python_strings[i].encode('utf-8')  # Or other encoding
    #     return c_array

    # cdef void free_char_array(char** c_array, int num_strings):
    #     for i in range(num_strings):
    #         free(c_array[i]) # Free individual strings if they were allocated
    #     free(c_array)

    @property
    def instr(self) -> InstrInfo:
        """Instrument specification"""
        return InstrInfo.from_ptr(&self.ptr.instr, False)

    @property
    def loops(self) -> list:
        """Looping specification"""
        result = []
        for i in range(8):
            result.append(LoopInfo.from_ptr(&self.ptr.loops[i], False))
        return result


cdef class VersionInfo:
    cdef sox_version_info_t* ptr
    cdef bint owner

    def __cinit__(self):
        self.ptr = NULL
        self.owner = False

    def __dealloc__(self):
        if self.ptr is not NULL and self.owner is True:
            free(self.ptr)
            self.ptr = NULL

    @staticmethod
    cdef VersionInfo from_ptr(sox_version_info_t* ptr, bint owner=False):
        cdef VersionInfo wrapper = VersionInfo.__new__(VersionInfo)
        wrapper.ptr = ptr
        wrapper.owner = owner
        return wrapper

    @property
    def size(self) -> int:
        """structure size = sizeof(sox_version_info_t)"""
        return self.ptr.size

    @property
    def flags(self) -> sox_version_flags_t:
        """feature flags = popen | magic | threads | memopen"""
        return self.ptr.flags

    @property
    def version_code(self) -> sox_uint32_t:
        """version number = 0x140400"""
        return self.ptr.version_code

    @property
    def version(self) -> str:
        """version string = sox_version(), for example, 14.4.0"""
        if self.ptr.version == NULL:
            return None
        return self.ptr.version.decode()

    @property
    def version_extra(self) -> str:
        """version extra info or null = PACKAGE_EXTRA, for example, beta"""
        if self.ptr.version_extra == NULL:
            return None
        return self.ptr.version_extra.decode()

    @property
    def time(self) -> str:
        """build time = __DATE__ __TIME__, for example, Jan  7 2010 03:31:50"""
        if self.ptr.time == NULL:
            return None
        return self.ptr.time.decode()

    @property
    def distro(self) -> str:
        """distro or null = DISTRO, for example, Debian"""
        if self.ptr.distro == NULL:
            return None
        return self.ptr.distro.decode()

    @property
    def compiler(self) -> str:
        """compiler info or null, for example, msvc 160040219"""
        if self.ptr.compiler == NULL:
            return None
        return self.ptr.compiler.decode()

    @property
    def arch(self) -> str:
        """arch, for example, 1248 48 44 L OMP"""
        if self.ptr.arch == NULL:
            return None
        return self.ptr.arch.decode()


cdef class Globals:
    cdef sox_globals_t* ptr
    cdef bint owner

    def __cinit__(self):
        self.ptr = NULL
        self.owner = False

    def __dealloc__(self):
        if self.ptr is not NULL and self.owner is True:
            free(self.ptr)
            self.ptr = NULL

    def __init__(self):
        self.ptr = sox_get_globals()
        self.owner = False # not owned
        if self.ptr is NULL:
            raise MemoryError

    @staticmethod
    cdef Globals from_ptr(sox_globals_t* ptr, bint owner=False):
        cdef Globals wrapper = Globals.__new__(Globals)
        wrapper.ptr = ptr
        wrapper.owner = owner
        return wrapper

    def as_dict(self):
        """Returns a dict of libSoX's global settings."""
        return {
            'verbosity': self.verbosity,
            'repeatable': self.repeatable,
            'bufsiz': self.bufsiz,
            'input_bufsiz': self.input_bufsiz,
            'ranqd1': self.ranqd1,
            'stdin_in_use_by': self.stdin_in_use_by.decode() if self.stdin_in_use_by else None,
            'stdout_in_use_by': self.stdout_in_use_by.decode() if self.stdout_in_use_by else None,
            'subsystem': self.subsystem.decode() if self.subsystem else None,
            'tmp_path': self.tmp_path.decode() if self.tmp_path else None,
            'use_magic': self.use_magic,
            'use_threads': self.use_threads,
            'log2_dft_min_size': self.log2_dft_min_size
        }


    @property
    def verbosity(self) -> int:
        """messages are only written if globals.verbosity >= message.level"""
        return self.ptr.verbosity

    @verbosity.setter
    def verbosity(self, unsigned value):
        self.ptr.verbosity = value

    @property
    def repeatable(self) -> bool:
        """true to use pre-determined timestamps and PRNG seed"""
        return self.ptr.repeatable

    @repeatable.setter
    def repeatable(self, sox_bool value):
        self.ptr.repeatable = value

    @property
    def bufsiz(self) -> int:
        """Default size (in bytes) used by libSoX for blocks of sample data."""
        return self.ptr.bufsiz

    @bufsiz.setter
    def bufsiz(self, size_t value):
        self.ptr.bufsiz = value

    @property
    def input_bufsiz(self) -> int:
        """Default size (in bytes) used by libSoX for blocks of input sample data."""
        return self.ptr.input_bufsiz

    @input_bufsiz.setter
    def input_bufsiz(self, size_t value):
        self.ptr.input_bufsiz = value

    @property
    def ranqd1(self) -> int:
        """Can be used to re-seed libSoX's PRNG"""
        return self.ptr.ranqd1

    @ranqd1.setter
    def ranqd1(self, sox_int32_t value):
        self.ptr.ranqd1 = value

    @property
    def stdin_in_use_by(self) -> str:
        """Private: tracks the name of the handler currently using stdin"""
        if self.ptr.stdin_in_use_by == NULL:
            return None
        return self.ptr.stdin_in_use_by.decode()

    @property
    def stdout_in_use_by(self) -> str:
        """Private: tracks the name of the handler currently using stdout"""
        if self.ptr.stdout_in_use_by == NULL:
            return None
        return self.ptr.stdout_in_use_by.decode()

    @property
    def subsystem(self) -> str:
        """Private: tracks the name of the handler currently writing an output message"""
        if self.ptr.subsystem == NULL:
            return None
        return self.ptr.subsystem.decode()

    @property
    def tmp_path(self) -> str:
        """Private: client-configured path to use for temporary files"""
        if self.ptr.tmp_path == NULL:
            return None
        return self.ptr.tmp_path.decode()

    @property
    def use_magic(self) -> bool:
        """Private: true if client has requested use of 'magic' file-type detection"""
        return self.ptr.use_magic

    @property
    def use_threads(self) -> bool:
        """Private: true if client has requested parallel effects processing"""
        return self.ptr.use_threads

    @property
    def log2_dft_min_size(self) -> int:
        """Log to base 2 of minimum size (in bytes) used by libSoX for DFT (filtering)."""
        return self.ptr.log2_dft_min_size


cdef class EffectsGlobals:
    cdef sox_effects_globals_t* ptr
    cdef bint owner

    def __cinit__(self):
        self.ptr = NULL
        self.owner = False

    def __dealloc__(self):
        if self.ptr is not NULL and self.owner is True:
            free(self.ptr)
            self.ptr = NULL

    def __init__(self):
        self.ptr = sox_get_effects_globals()
        self.owner = False # never owned

    @staticmethod
    cdef EffectsGlobals from_ptr(sox_effects_globals_t* ptr, bint owner=False):
        cdef EffectsGlobals wrapper = EffectsGlobals.__new__(EffectsGlobals)
        wrapper.ptr = ptr
        wrapper.owner = owner
        return wrapper

    @property
    def plot(self) -> sox_plot_t:
        """To help the user choose effect & options"""
        return self.ptr.plot

    @plot.setter
    def plot(self, sox_plot_t value):
        self.ptr.plot = value

    @property
    def global_info(self) -> Globals:
        """Pointer to associated SoX globals"""
        if self.ptr.global_info == NULL:
            return None
        return Globals.from_ptr(self.ptr.global_info, False)


cdef class Format:
    """Audio format handle for reading and writing audio files.

    This class provides the main interface for opening, reading, and writing
    audio files in various formats supported by libsox.

    The Format class implements the context manager protocol, allowing automatic
    resource cleanup:

        with sox.Format('input.wav') as f:
            samples = f.read(1024)

    Attributes:
        filename: Path to the audio file
        signal: SignalInfo object describing audio properties
        encoding: EncodingInfo object describing encoding
        filetype: String identifier for the file format
        seekable: Whether seeking is supported
        mode: 'r' for reading, 'w' for writing
        olength: Samples * channels written to file
        clips: Counter incremented if clipping occurs
        sox_errno: Failure error code
        sox_errstr: Failure error text

    Example - Reading:
        >>> with sox.Format('input.wav') as f:
        ...     print(f"Rate: {f.signal.rate}, Channels: {f.signal.channels}")
        ...     samples = f.read(1024)

    Example - Writing:
        >>> signal = sox.SignalInfo(rate=44100, channels=2, precision=16)
        >>> with sox.Format('output.wav', signal=signal, mode='w') as f:
        ...     f.write([100, 200, 300, 400])
    """
    cdef sox_format_t* ptr
    cdef bint owner

    def __cinit__(self):
        self.ptr = NULL
        self.owner = False

    def __dealloc__(self):
        if self.ptr is not NULL and self.owner is True:
            sox_close(self.ptr)
            self.ptr = NULL

    def __init__(self, str filename, SignalInfo signal = None,
                 EncodingInfo encoding = None, str filetype = None, mode: str = 'r'):
        """Opens a file for reading or writing.

        Args:
            filename: Path to the audio file
            signal: Signal information (required for writing)
            encoding: Encoding information (optional)
            filetype: File format type (e.g., 'wav', 'coreaudio', 'alsa').
                      If None, format is inferred from filename extension.
            mode: 'r' for reading, 'w' for writing

        Raises:
            SoxFormatError: If file cannot be opened
            ValueError: If mode is invalid or signal missing for write mode
        """
        cdef char* filetype_c = NULL
        cdef bytes filetype_bytes
        if filetype is not None:
            filetype_bytes = filetype.encode('utf-8')
            filetype_c = filetype_bytes

        if mode == 'r':
            self.ptr = sox_open_read(
                filename.encode(),
                signal.ptr if signal else NULL,
                encoding.ptr if encoding else NULL,
                filetype_c
            )
        elif mode == 'w':
            if signal is None:
                raise ValueError("Signal information is required for writing")
            self.ptr = sox_open_write(
                filename.encode(),
                signal.ptr,
                encoding.ptr if encoding else NULL,
                filetype_c,
                NULL,
                NULL  # No overwrite callback for now
            )
        else:
            raise ValueError("Mode must be 'r' or 'w'")

        if self.ptr is NULL:
            raise SoxFormatError(f"Failed to open file {filename} in mode {mode}")

        self.owner = True

    @staticmethod
    cdef Format from_ptr(sox_format_t* ptr, bint owner=False):
        cdef Format wrapper = Format.__new__(Format)
        wrapper.ptr = ptr
        wrapper.owner = owner
        return wrapper

    def read(self, length: int) -> list:
        """Read samples from the file into a Python list.

        Args:
            length: Number of samples to read

        Returns:
            List of sample values (sox_sample_t integers)

        Note:
            For better performance with large data, use read_buffer() to get
            a memory view, or read_into() to read into a pre-allocated buffer.
        """
        cdef size_t samples_read = 0
        cdef sox_sample_t* buffer = <sox_sample_t*>malloc(length * sizeof(sox_sample_t))
        if buffer == NULL:
            raise SoxMemoryError("Failed to allocate read buffer")

        try:
            samples_read = sox_read(self.ptr, buffer, length)
            result = []
            for i in range(samples_read):
                result.append(buffer[i])
            return result
        finally:
            free(buffer)

    def read_buffer(self, length: int):
        """Read samples from the file into a buffer that supports the buffer protocol.

        Args:
            length: Number of samples to read

        Returns:
            A memory view of sox_sample_t values. Compatible with NumPy, PyTorch,
            array.array, and other buffer protocol objects.

        Example:
            >>> import numpy as np
            >>> with sox.Format('input.wav') as f:
            ...     buf = f.read_buffer(1024)
            ...     arr = np.asarray(buf, dtype=np.int32)
        """
        cdef size_t samples_read = 0
        cdef sox_sample_t* buffer = <sox_sample_t*>malloc(length * sizeof(sox_sample_t))
        if buffer == NULL:
            raise SoxMemoryError("Failed to allocate read buffer")

        samples_read = sox_read(self.ptr, buffer, length)

        # Create a memory view from the C buffer
        # We need to copy the data because we're freeing the buffer
        cdef sox_sample_t[::1] view = <sox_sample_t[:samples_read]>buffer
        result = bytearray(samples_read * sizeof(sox_sample_t))
        cdef unsigned char[::1] result_view = result
        cdef size_t i
        for i in range(samples_read * sizeof(sox_sample_t)):
            result_view[i] = (<unsigned char*>buffer)[i]

        free(buffer)
        return memoryview(result).cast('i', shape=[samples_read])

    def read_into(self, buffer) -> int:
        """Read samples from the file into a pre-allocated buffer.

        Args:
            buffer: Any object supporting the buffer protocol (numpy array,
                   array.array, bytearray, memoryview, etc.). Must be writable
                   and have enough space for sox_sample_t values.

        Returns:
            Number of samples actually read

        Example:
            >>> import numpy as np
            >>> arr = np.zeros(1024, dtype=np.int32)
            >>> with sox.Format('input.wav') as f:
            ...     n = f.read_into(arr)
            ...     print(f"Read {n} samples")
        """
        cdef Py_buffer pybuf
        cdef int flags = PyBUF_WRITABLE | PyBUF_C_CONTIGUOUS
        cdef size_t max_samples
        cdef size_t samples_read

        if PyObject_GetBuffer(buffer, &pybuf, flags) != 0:
            raise TypeError("Buffer must be writable and contiguous")

        try:
            # Calculate how many samples fit in the buffer
            max_samples = pybuf.len // sizeof(sox_sample_t)
            samples_read = sox_read(self.ptr, <sox_sample_t*>pybuf.buf, max_samples)
            return samples_read
        finally:
            PyBuffer_Release(&pybuf)

    def write(self, samples) -> int:
        """Write samples to the file.

        Args:
            samples: Can be a list, or any buffer protocol object (numpy array,
                    array.array, memoryview, etc.) containing sox_sample_t values

        Returns:
            Number of samples written

        Example:
            >>> import numpy as np
            >>> arr = np.array([100, 200, 300], dtype=np.int32)
            >>> with sox.Format('output.wav', signal=..., mode='w') as f:
            ...     f.write(arr)
        """
        cdef size_t length
        cdef sox_sample_t* buffer
        cdef size_t samples_written
        cdef Py_buffer pybuf
        cdef size_t i

        # Try buffer protocol first (more efficient)
        if PyObject_CheckBuffer(samples):
            if PyObject_GetBuffer(samples, &pybuf, PyBUF_C_CONTIGUOUS) != 0:
                raise TypeError("Buffer must be contiguous")

            try:
                length = pybuf.len // sizeof(sox_sample_t)
                samples_written = sox_write(self.ptr, <sox_sample_t*>pybuf.buf, length)
                return samples_written
            finally:
                PyBuffer_Release(&pybuf)

        # Fall back to list/sequence
        else:
            length = len(samples)
            buffer = <sox_sample_t*>malloc(length * sizeof(sox_sample_t))
            if buffer == NULL:
                raise SoxMemoryError("Failed to allocate write buffer")

            try:
                for i in range(length):
                    buffer[i] = samples[i]
                return <int>sox_write(self.ptr, buffer, length)
            finally:
                free(buffer)

    def seek(self, offset: int, whence: int = SOX_SEEK_SET) -> int:
        """Seek to a specific sample position."""
        cdef int result = sox_seek(self.ptr, offset, whence)
        if result != SOX_SUCCESS:
            raise SoxIOError(f"Failed to seek: {strerror(result)}")
        return result

    def close(self) -> int:
        """Closes an encoding or decoding session."""
        if self.ptr is NULL:
            # Already closed, return success
            return <int>SOX_SUCCESS

        cdef int result = sox_close(self.ptr)
        self.ptr = NULL  # Set to NULL regardless of result to prevent double-free
        if result != SOX_SUCCESS:
            raise SoxIOError(f"Failed to close: {strerror(result)}")
        return result

    def __enter__(self):
        """Context manager entry point.

        Returns:
            self: The Format object for use in with statement.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit point.

        Automatically closes the format when exiting the with block.

        Args:
            exc_type: Exception type if an exception occurred.
            exc_val: Exception value if an exception occurred.
            exc_tb: Exception traceback if an exception occurred.

        Returns:
            False: Allow exceptions to propagate.
        """
        if self.ptr is not NULL:
            try:
                self.close()
            except SoxIOError as e:
                # If close fails during exception handling, log but don't raise
                if exc_type is None:
                    raise
                else:
                    # Log the close error but don't mask the original exception
                    import sys
                    import warnings
                    warnings.warn(
                        f"Error closing format during exception handling: {e}",
                        ResourceWarning,
                        stacklevel=2
                    )
        return False

    @property
    def filename(self) -> str:
        """Path to the audio file."""
        return self.ptr.filename.decode()

    @property
    def signal(self) -> SignalInfo:
        """Signal information (sample rate, channels, precision, length)."""
        return SignalInfo.from_ptr(&self.ptr.signal)

    @property
    def encoding(self) -> EncodingInfo:
        """Encoding information (format, bits per sample, compression)."""
        return EncodingInfo.from_ptr(&self.ptr.encoding)

    @property
    def filetype(self) -> str:
        """File type identifier (e.g., 'wav', 'mp3', 'flac')."""
        if self.ptr.filetype == NULL:
            return None
        return self.ptr.filetype.decode()

    @property
    def seekable(self) -> bool:
        """Can seek on this file"""
        return self.ptr.seekable

    @property
    def mode(self) -> str:
        """Read or write mode ('r' or 'w')"""
        return chr(self.ptr.mode)

    @property
    def olength(self) -> int:
        """Samples * chans written to file"""
        return self.ptr.olength

    @property
    def clips(self) -> int:
        """Incremented if clipping occurs"""
        return self.ptr.clips

    @property
    def sox_errno(self) -> int:
        """Failure error code"""
        return self.ptr.sox_errno

    @property
    def sox_errstr(self) -> str:
        """Failure error text"""
        return self.ptr.sox_errstr.decode()

    @property
    def io_type(self) -> int:
        """Stores whether this is a file, pipe or URL"""
        return self.ptr.io_type

    @property
    def tell_off(self) -> int:
        """Current offset within file"""
        return self.ptr.tell_off

    @property
    def data_start(self) -> int:
        """Offset at which headers end and sound data begins"""
        return self.ptr.data_start


cdef class FormatHandler:
    """Handler structure defined by each format."""
    cdef sox_format_handler_t* ptr
    cdef bint owner

    def __cinit__(self):
        self.ptr = NULL
        self.owner = False

    def __dealloc__(self):
        if self.ptr is not NULL and self.owner is True:
            free(self.ptr)
            self.ptr = NULL

    def __init__(self, str path):
        self.ptr = <sox_format_handler_t*>sox_write_handler(
            path.encode(), NULL, NULL)
        self.owner = False  # sox_write_handler returns a static pointer, don't free it
        if self.ptr is NULL:
            raise SoxFormatError(f"Failed to find format handler for path: {path}")

    @staticmethod
    cdef FormatHandler from_ptr(sox_format_handler_t* ptr, bint owner=False):
        cdef FormatHandler wrapper = FormatHandler.__new__(FormatHandler)
        wrapper.ptr = ptr
        wrapper.owner = owner
        return wrapper

    @staticmethod
    def find(name: str, ignore_devices: bool = False) -> FormatHandler:
        """Finds a format handler by name.

        Note: Prefer using the module-level function `sox.find_format(name)`
        for better API consistency.
        """
        cdef bytes name_bytes = name.encode('utf-8')
        cdef const sox_format_handler_t* handler = sox_find_format(
            name_bytes, <sox_bool>ignore_devices)
        if handler == NULL:
            return None
        return FormatHandler.from_ptr(<sox_format_handler_t*>handler)

    @property
    def sox_lib_version_code(self) -> int:
        """Checked on load must be 1st in struct"""
        return self.ptr.sox_lib_version_code

    @property
    def description(self) -> str:
        """short description of format"""
        if self.ptr.description == NULL:
            return None
        return self.ptr.description.decode()

    @property
    def names(self) -> list:
        """null-terminated array of filename extensions that are handled by this format"""
        if self.ptr.names == NULL:
            return []

        result = []
        cdef int i = 0
        while self.ptr.names[i] != NULL:
            result.append(self.ptr.names[i].decode())
            i += 1
        return result

    @property
    def flags(self) -> int:
        """File flags (SOX_FILE_* values)."""
        return self.ptr.flags

    @property
    def priv_size(self) -> int:
        """Size of private data SoX should pre-allocate for format"""
        return self.ptr.priv_size


cdef class FormatTab:
    """Information about a loaded format handler, including the format name and a
    function pointer that can be invoked to get additional information about the
    format."""
    cdef sox_format_tab_t* ptr
    cdef bint owner

    def __cinit__(self):
        self.ptr = NULL
        self.owner = False

    def __dealloc__(self):
        if self.ptr is not NULL and self.owner is True:
            free(self.ptr)
            self.ptr = NULL

    def __init__(self, name: str = None):
        self.ptr = <sox_format_tab_t*>malloc(sizeof(sox_format_tab_t))
        if self.ptr is NULL:
            raise SoxMemoryError("Failed to allocate FormatTab")

        # Initialize struct members directly (name property is read-only)
        # Note: name parameter is ignored since setting it would be unsafe
        self.ptr.name = NULL
        self.ptr.fn = NULL
        self.owner = True

    @staticmethod
    cdef FormatTab from_ptr(sox_format_tab_t* ptr, bint owner=False):
        cdef FormatTab wrapper = FormatTab.__new__(FormatTab)
        wrapper.ptr = ptr
        wrapper.owner = owner
        return wrapper

    @property
    def name(self) -> str:
        """Name of format handler (read-only).

        Note: This property is read-only because the name pointer is managed
        by libsox and should not be modified externally.
        """
        if self.ptr.name == NULL:
            return None
        return self.ptr.name.decode()

    @property
    def fn(self):
        """Function to call to get format handler's information"""
        # Return None for function pointers as they can't be easily exposed to Python
        return None


cdef class EffectHandler:
    """Effect handler information."""
    cdef sox_effect_handler_t* ptr
    cdef bint owner

    def __cinit__(self):
        self.ptr = NULL
        self.owner = False

    def __dealloc__(self):
        if self.ptr is not NULL and self.owner is True:
            free(self.ptr)
            self.ptr = NULL

    @staticmethod
    cdef EffectHandler from_ptr(sox_effect_handler_t* ptr, bint owner=False):
        cdef EffectHandler wrapper = EffectHandler.__new__(EffectHandler)
        wrapper.ptr = ptr
        wrapper.owner = owner
        return wrapper

    @staticmethod
    def find(name: str) -> Effect:
        """Finds the effect handler with the given name.

        Note: Prefer using the module-level function `sox.find_effect(name)`
        for better API consistency.
        """
        cdef bytes name_bytes = name.encode('utf-8')
        cdef const sox_effect_handler_t* handler = sox_find_effect(name_bytes)
        if handler == NULL:
            return None
        return EffectHandler.from_ptr(<sox_effect_handler_t*>handler)

    @property
    def name(self) -> str:
        """Effect name"""
        if self.ptr.name == NULL:
            return None
        return self.ptr.name.decode()

    @property
    def usage(self) -> str:
        """Short explanation of parameters accepted by effect"""
        if self.ptr.usage == NULL:
            return None
        return self.ptr.usage.decode()

    @property
    def flags(self) -> int:
        """Combination of SOX_EFF_* flags"""
        return self.ptr.flags

    @property
    def priv_size(self) -> int:
        """Size of private data SoX should pre-allocate for effect"""
        return self.ptr.priv_size


cdef class Effect:
    """Effect structure."""
    cdef sox_effect_t* ptr
    cdef bint owner

    def __cinit__(self):
        self.ptr = NULL
        self.owner = False

    def __dealloc__(self):
        if self.ptr is not NULL and self.owner is True:
            free(self.ptr)
            self.ptr = NULL

    def __init__(self, handler: EffectHandler):
        """Initialize an effect with an optional handler."""
        self.ptr = sox_create_effect(handler.ptr)
        if self.ptr == NULL:
            raise SoxEffectError("Failed to create effect")
        self.owner = True

    @staticmethod
    cdef Effect from_ptr(sox_effect_t* ptr, bint owner=False):
        cdef Effect wrapper = Effect.__new__(Effect)
        wrapper.ptr = ptr
        wrapper.owner = owner
        return wrapper

    def delete(self):
        """Shut down and delete an effect."""
        sox_delete_effect(self.ptr)

    def set_options(self, options):
        """Applies the command-line options to the effect.

        Returns the number of arguments consumed."""
        cdef int argc = len(options) if options else 0
        cdef char** argv = <char**>malloc(argc * sizeof(char*)) if argc > 0 else NULL
        if argc > 0 and argv == NULL:
            raise SoxMemoryError("Failed to allocate argument array")

        cdef list byte_strings = []
        try:
            for i in range(argc):
                option = options[i]
                if isinstance(option, Format):
                    # For input/output effects, pass Format pointer cast to char*
                    argv[i] = <char*>(<Format>option).ptr
                elif isinstance(option, str):
                    # Encode string to bytes and keep reference
                    byte_str = option.encode('utf-8')
                    byte_strings.append(byte_str)
                    argv[i] = <char*>byte_str
                else:
                    raise TypeError(f"Unsupported option type: {type(option)}")
            return sox_effect_options(self.ptr, argc, argv)
        finally:
            if argv != NULL:
                free(argv)

    def stop(self) -> int:
        """Shuts down an effect (calls stop on each of its flows).

        Returns the number of clips from all flows."""
        if self.ptr == NULL:
            return 0
        return <int>sox_stop_effect(self.ptr)

    def trim_get_start(self) -> int:
        """Gets the sample offset of the start of the trim."""
        if self.ptr == NULL:
            return 0
        return <int>sox_trim_get_start(self.ptr)

    def trim_clear_start(self):
        """Clears the start of the trim to 0."""
        if self.ptr != NULL:
            sox_trim_clear_start(self.ptr)

    @property
    def global_info(self):
        """global effect parameters"""
        if self.ptr.global_info == NULL:
            return None
        return EffectsGlobals.from_ptr(self.ptr.global_info, False)

    @property
    def in_signal(self) -> SignalInfo:
        """Information about the incoming data stream"""
        return SignalInfo.from_ptr(&self.ptr.in_signal, False)

    @property
    def out_signal(self) -> SignalInfo:
        """Information about the outgoing data stream"""
        return SignalInfo.from_ptr(&self.ptr.out_signal, False)

    @property
    def in_encoding(self) -> EncodingInfo:
        """Information about the incoming data encoding"""
        if self.ptr.in_encoding == NULL:
            return None
        return EncodingInfo.from_ptr(self.ptr.in_encoding, False)

    @property
    def out_encoding(self) -> EncodingInfo:
        """Information about the outgoing data encoding"""
        if self.ptr.out_encoding == NULL:
            return None
        return EncodingInfo.from_ptr(self.ptr.out_encoding, False)

    @property
    def handler(self) -> EffectHandler:
        """The handler for this effect"""
        return EffectHandler.from_ptr(&self.ptr.handler, False)

    @property
    def clips(self) -> sox_uint64_t:
        """increment if clipping occurs"""
        return self.ptr.clips

    @property
    def flows(self) -> int:
        """1 if MCHAN, number of chans otherwise"""
        return self.ptr.flows

    @property
    def flow(self) -> int:
        """flow number"""
        return self.ptr.flow

    @property
    def priv(self):
        """Effect's private data area (each flow has a separate copy)"""
        # Return None for void* pointers as they can't be easily exposed to Python
        return None


# C callback function for flow_effects
# This is called by libsox and needs to invoke the Python callback
cdef int _flow_effects_callback_wrapper(sox_bool all_done, void* client_data) noexcept nogil:
    """C callback that wraps Python callback for flow_effects.

    This function is called from C code without the GIL, so we need to
    acquire it before calling Python code.
    """
    global _last_callback_exception
    with gil:
        try:
            # client_data is a pointer to the chain's address (as an integer)
            chain_id = <uintptr_t>client_data

            # Look up the callback in our global dictionary
            if chain_id not in _flow_callbacks:
                return SOX_SUCCESS  # No callback registered, continue

            callback, user_data = _flow_callbacks[chain_id]

            # Call the Python callback
            # all_done is a sox_bool (enum), convert to Python bool
            result = callback(bool(all_done), user_data)

            # If callback returns None or True, continue; False or int error code aborts
            if result is None or result is True:
                return SOX_SUCCESS
            elif result is False:
                return -1  # Generic error
            else:
                return int(result)  # Assume it's an error code

        except Exception as e:
            # Store the exception for later retrieval since we can't propagate through C code
            import sys
            _last_callback_exception = sys.exc_info()
            sys.stderr.write(f"Error in flow_effects callback: {e}\n")
            return -1


def get_last_callback_exception():
    """Retrieve the last exception that occurred in a flow_effects callback.

    Since exceptions cannot propagate through C code, they are stored for
    later retrieval. This function returns the exception info tuple
    (type, value, traceback) or None if no exception occurred.

    After calling this function, the stored exception is cleared.

    Returns:
        Tuple of (exception_type, exception_value, traceback) or None

    Example:
        >>> chain.flow_effects(callback=my_callback)
        >>> exc_info = sox.get_last_callback_exception()
        >>> if exc_info:
        ...     raise exc_info[1].with_traceback(exc_info[2])
    """
    global _last_callback_exception
    exc_info = _last_callback_exception
    _last_callback_exception = None
    return exc_info


cdef class EffectsChain:
    """Effects chain structure."""
    cdef sox_effects_chain_t* ptr
    cdef bint owner

    def __cinit__(self):
        self.ptr = NULL
        self.owner = False

    def __dealloc__(self):
        if self.ptr is not NULL and self.owner is True:
            sox_delete_effects_chain(self.ptr)
            self.ptr = NULL

    def __init__(self, in_encoding: EncodingInfo = None,
                       out_encoding: EncodingInfo = None):
        """Initialize an effects chain with optional input and output encodings."""
        self.ptr = sox_create_effects_chain(
            in_encoding.ptr if in_encoding else NULL,
            out_encoding.ptr if out_encoding else NULL)
        if self.ptr == NULL:
            raise SoxEffectError("Failed to create effects chain")
        self.owner = True

    @staticmethod
    cdef EffectsChain from_ptr(sox_effects_chain_t* ptr, bint owner=False):
        cdef EffectsChain wrapper = EffectsChain.__new__(EffectsChain)
        wrapper.ptr = ptr
        wrapper.owner = owner
        return wrapper

    def add_effect(self, effect: Effect, in_signal: SignalInfo,
                   out_signal: SignalInfo):
        """Adds an effect to the effects chain."""

        assert effect.ptr is not NULL, "effect is NULL"
        assert in_signal.ptr is not NULL, "in_signal is NULL"
        assert out_signal.ptr is not NULL, "out_signal is NULL"

        cdef int result = sox_add_effect(
            self.ptr, effect.ptr, in_signal.ptr, out_signal.ptr)
        if result != SOX_SUCCESS:
            raise SoxEffectError(f"Failed to add effect to chain: {strerror(result)}")
        return result

    def flow_effects(self, callback=None, client_data=None):
        """Runs the effects chain, optionally calling a callback for progress monitoring.

        Args:
            callback: Optional callable that receives (all_done: bool, user_data) and
                     returns None/True to continue, False to abort, or an integer error code.
                     Called periodically during processing (once per buffer).
            client_data: Optional user data passed to the callback

        Returns:
            SOX_SUCCESS if successful

        Raises:
            SoxEffectError: If the effects chain fails to run

        Example:
            >>> def progress_callback(all_done, user_data):
            ...     if all_done:
            ...         print("Processing complete!")
            ...     else:
            ...         print("Processing...")
            ...     return True  # Continue processing
            >>>
            >>> chain = sox.EffectsChain()
            >>> # ... add effects ...
            >>> chain.flow_effects(callback=progress_callback, client_data={'count': 0})
        """
        cdef int result
        cdef uintptr_t chain_id

        if callback is not None:
            # Store the callback in our global dictionary using chain pointer as key
            chain_id = <uintptr_t>self.ptr
            _flow_callbacks[chain_id] = (callback, client_data)

            try:
                # Call sox_flow_effects with our wrapper callback
                result = sox_flow_effects(
                    self.ptr,
                    _flow_effects_callback_wrapper,
                    <void*>chain_id
                )
            finally:
                # Clean up callback storage
                if chain_id in _flow_callbacks:
                    del _flow_callbacks[chain_id]
        else:
            # No callback, call with NULL
            result = sox_flow_effects(self.ptr, NULL, NULL)

        if result != SOX_SUCCESS:
            raise SoxEffectError(f"Failed to flow effects: {strerror(result)}")
        return result

    def get_clips(self) -> int:
        """Gets the number of clips that occurred while running the effects chain."""
        return <int>sox_effects_clips(self.ptr)

    def push_effect_last(self, effect: Effect):
        """Adds an already-initialized effect to the end of the chain."""
        if self.ptr != NULL and effect.ptr != NULL:
            sox_push_effect_last(self.ptr, effect.ptr)

    def pop_effect_last(self):
        """Removes and returns an effect from the end of the chain.

        Returns None if no effects."""
        cdef sox_effect_t* effect
        if self.ptr == NULL:
            return None
        effect = sox_pop_effect_last(self.ptr)
        if effect == NULL:
            return None
        return Effect.from_ptr(effect, True)

    def delete_effect_last(self):
        """Shut down and delete the last effect in the chain."""
        if self.ptr != NULL:
            sox_delete_effect_last(self.ptr)

    def delete_effects(self):
        """Shut down and delete all effects in the chain."""
        if self.ptr != NULL:
            sox_delete_effects(self.ptr)

    @property
    def effects(self) -> list:
        """Table of effects to be applied to a stream"""
        if self.ptr.effects == NULL:
            return []

        result = []
        for i in range(self.ptr.length):
            if self.ptr.effects[i] != NULL:
                result.append(Effect.from_ptr(self.ptr.effects[i], False))
        return result

    @property
    def length(self) -> int:
        """Number of effects to be applied"""
        return self.ptr.length

    @property
    def global_info(self) -> EffectsGlobals:
        """Copy of global effects settings"""
        return EffectsGlobals.from_ptr(&self.ptr.global_info, False)

    @property
    def in_enc(self) -> EncodingInfo:
        """Input encoding"""
        if self.ptr.in_enc == NULL:
            return None
        return EncodingInfo.from_ptr(self.ptr.in_enc, False)

    @property
    def out_enc(self) -> EncodingInfo:
        """Output encoding"""
        if self.ptr.out_enc == NULL:
            return None
        return EncodingInfo.from_ptr(self.ptr.out_enc, False)

    @property
    def table_size(self) -> int:
        """Size of effects table (including unused entries)"""
        return self.ptr.table_size

    @property
    def il_buf(self):
        """Channel interleave buffer"""
        # Return None for sox_sample_t* pointers as they can't be easily exposed to Python
        return None


# -------------------------------------------------------------------
# functions


def version() -> str:
    """Returns version number string of libSoX, for example, 14.4.0."""
    return (<const char*>sox_version()).decode()


def version_info():
    """Returns information about this build of libsox."""
    cdef const sox_version_info_t* info = sox_version_info()
    if info == NULL:
        return None

    return {
        'size': info.size,
        'flags': info.flags,
        'version_code': info.version_code,
        'version': info.version.decode() if info.version else None,
        'version_extra': info.version_extra.decode() if info.version_extra else None,
        'time': info.time.decode() if info.time else None,
        'distro': info.distro.decode() if info.distro else None,
        'compiler': info.compiler.decode() if info.compiler else None,
        'arch': info.arch.decode() if info.arch else None
    }





def get_encodings() -> list[EncodingsInfo]:
    """Returns the list of available encodings."""
    cdef const sox_encodings_info_t* encodings = sox_get_encodings_info()
    if encodings == NULL:
        return []

    result = []
    cdef int i = 0
    while encodings[i].name != NULL and encodings[i].flags < 3:
        result.append(
            EncodingsInfo(
                flags=encodings[i].flags,
                name=encodings[i].name.decode(),
                desc=encodings[i].desc.decode() if encodings[i].desc else None
            )
        )
        i += 1
    return result


def format_init():
    """Find and load format handler plugins.

    Raises:
        RuntimeError: If format initialization fails.
    """
    cdef int result = sox_format_init()
    if result != SOX_SUCCESS:
        raise SoxInitError(f"Failed to initialize format handlers: {strerror(result)}")


def format_quit():
    """Unload format handler plugins."""
    sox_format_quit()


def init():
    """Initialize the SoX effects library.

    Must be called before using any SoX functionality. This initializes
    the effects system and format handlers.

    This function is idempotent - calling it multiple times is safe.
    Subsequent calls after the first are no-ops.

    Raises:
        SoxInitError: If initialization fails.

    Example:
        >>> import cysox as sox
        >>> sox.init()
        >>> # Use sox functions...
        >>> sox.quit()
    """
    global _sox_initialized
    if _sox_initialized:
        return  # Already initialized, no-op
    cdef int result = sox_init()
    if result != SOX_SUCCESS:
        raise SoxInitError(f"Failed to initialize SoX library: {strerror(result)}")
    _sox_initialized = True


def quit():
    """Close the SoX effects library and unload format handlers.

    Note:
        Due to libsox limitations (crashes on re-initialization after quit),
        this function is a no-op during normal execution. Actual cleanup
        happens automatically at process exit via atexit. This ensures the
        library remains usable throughout the process lifetime.

        This function is retained for API compatibility but does not
        actually call sox_quit(). Use _force_quit() for testing if needed.

    Example:
        >>> import cysox as sox
        >>> sox.init()
        >>> # Use sox functions...
        >>> sox.quit()  # No-op; cleanup happens at process exit
    """
    # No-op: actual cleanup happens via atexit to prevent crashes from
    # repeated init/quit cycles. See KNOWN_LIMITATIONS.md
    pass


def _force_quit():
    """Internal: Actually quit sox (called by atexit handler).

    Warning: Do not call this directly - it will crash if sox is used again.
    This is only for use by the atexit cleanup handler.
    """
    global _sox_initialized
    if not _sox_initialized:
        return
    cdef int result = sox_quit()
    _sox_initialized = False
    if result != SOX_SUCCESS:
        raise SoxInitError(f"Failed to cleanup SoX library: {strerror(result)}")


def strerror(sox_errno: int) -> str:
    """Converts a SoX error code into an error string."""
    return (<const char*>sox_strerror(sox_errno)).decode()


def is_playlist(filename: str) -> bool:
    """Returns true if the specified file is a known playlist file type."""
    cdef bytes filename_bytes = filename.encode('utf-8')
    return sox_is_playlist(filename_bytes)


def basename(filename: str) -> str:
    """Gets the basename of the specified file.

    Args:
        filename: Path to extract basename from

    Returns:
        The basename portion of the filename
    """
    cdef bytes filename_bytes = filename.encode('utf-8')
    cdef size_t filename_len = len(filename_bytes)
    # Allocate buffer based on input length (basename can't be longer than full path)
    # Use at least 256 bytes for short paths, or filename length + 1 for longer paths
    cdef size_t buffer_size = filename_len + 1 if filename_len >= 256 else 256
    cdef char* base_buffer = <char*>malloc(buffer_size)

    if base_buffer is NULL:
        raise SoxMemoryError("Failed to allocate buffer for basename")

    try:
        result = sox_basename(base_buffer, buffer_size, filename_bytes)
        if result == 0:
            return ""
        return base_buffer[:result].decode('utf-8')
    finally:
        free(base_buffer)


def precision(sox_encoding_t encoding, unsigned bits_per_sample) -> int:
    """Given an encoding and bits_per_sample

    returns the number of useful bits per sample."""
    return sox_precision(encoding, bits_per_sample)


def get_effects_globals():
    """Returns global parameters for effects."""
    cdef sox_effects_globals_t* globals = sox_get_effects_globals()
    if globals == NULL:
        return None

    return {
        'plot': globals.plot
    }


def format_supports_encoding(str path, EncodingInfo encoding) -> bool:
    """Returns true if the format handler for the specified file type supports the specified encoding."""
    return bool(sox_format_supports_encoding(path.encode(), NULL, encoding.ptr))


def open_mem_read(buffer: bytes, signal: SignalInfo = None, encoding: EncodingInfo = None, filetype: str = None):
    """Opens a decoding session for a memory buffer. Returns a Format object or raises MemoryError."""
    cdef sox_format_t* fmt
    cdef char* filetype_c = NULL
    cdef bytes filetype_bytes
    if filetype is not None:
        filetype_bytes = filetype.encode('utf-8')
        filetype_c = filetype_bytes
    fmt = sox_open_mem_read(<void*>buffer, len(buffer),
                            signal.ptr if signal else NULL,
                            encoding.ptr if encoding else NULL,
                            filetype_c)
    if fmt == NULL:
        raise SoxFormatError("Failed to open memory buffer for reading")
    return Format.from_ptr(fmt, True)


def open_mem_write(buffer: bytearray, signal: SignalInfo,
        encoding: EncodingInfo, filetype: str = None, oob: OutOfBand = None):
    """Opens an encoding session for a memory buffer.

    Returns a Format object or raises MemoryError."""
    cdef sox_format_t* fmt
    cdef char* filetype_c = NULL
    cdef bytes filetype_bytes
    if filetype is not None:
        filetype_bytes = filetype.encode('utf-8')
        filetype_c = filetype_bytes
    fmt = sox_open_mem_write(<void*>buffer, len(buffer),
                             signal.ptr,
                             encoding.ptr,
                             filetype_c,
                             oob.ptr if oob else NULL)
    if fmt == NULL:
        raise SoxFormatError("Failed to open memory buffer for writing")
    return Format.from_ptr(fmt, True)


def open_memstream_write(signal: SignalInfo, encoding: EncodingInfo,
        filetype: str = None, oob: OutOfBand = None):
    """Opens an encoding session for a memstream buffer.

    Returns (Format, buffer_ptr, buffer_size_ptr) or raises MemoryError."""
    cdef sox_format_t* fmt
    cdef char* filetype_c = NULL
    cdef bytes filetype_bytes
    cdef char* buffer_ptr = NULL
    cdef size_t buffer_size = 0
    if filetype is not None:
        filetype_bytes = filetype.encode('utf-8')
        filetype_c = filetype_bytes
    fmt = sox_open_memstream_write(&buffer_ptr, &buffer_size,
                                   signal.ptr,
                                   encoding.ptr,
                                   filetype_c,
                                   oob.ptr if oob else NULL)
    if fmt == NULL:
        raise SoxFormatError("Failed to open memstream for writing")
    return Format.from_ptr(fmt, True), buffer_ptr, buffer_size


def get_format_fns():
    """Returns the table of format handler names and functions."""
    cdef const sox_format_tab_t* format_fns = sox_get_format_fns()
    if format_fns == NULL:
        return []

    result = []
    cdef int i = 0
    while format_fns[i].name != NULL:
        result.append({
            'name': format_fns[i].name.decode(),
            'fn': None  # Function pointers can't be easily exposed to Python
        })
        i += 1
    return result


def get_effect_fns():
    """Returns an array containing the known effect handlers."""
    cdef const sox_effect_fn_t* effect_fns = sox_get_effect_fns()
    if effect_fns == NULL:
        return []

    result = []
    cdef int i = 0
    while effect_fns[i] != NULL:
        # Note: We can't easily call the function pointer from Python
        # This is mainly for enumeration purposes
        result.append(i)
        i += 1
    return result


# cdef int playlist_callback(void * callback, char * filename) noexcept:
#     return SOX_SUCCESS


# def parse_playlist(callback, listname: str):
#     """Parses the specified playlist file."""
#     cdef int result
#     cdef bytes listname_bytes = listname.encode()

#     result = sox_parse_playlist(playlist_callback, NULL, listname_bytes)
#     if result != SOX_SUCCESS:
#         raise RuntimeError(f"Failed to parse playlist: {strerror(result)}")
#     return result


def read_samples(format: Format, buffer: list, length: int) -> int:
    """Reads samples from a decoding session into a sample buffer."""
    cdef size_t samples_read = 0
    cdef sox_sample_t* sample_buffer = <sox_sample_t*>malloc(length * sizeof(sox_sample_t))
    if sample_buffer == NULL:
        raise SoxMemoryError("Failed to allocate sample buffer")

    try:
        samples_read = sox_read(format.ptr, sample_buffer, length)
        # Convert C samples to Python list
        for i in range(samples_read):
            buffer.append(sample_buffer[i])
        return <int>samples_read
    finally:
        free(sample_buffer)


def write_samples(format: Format, samples: list) -> int:
    """Writes samples to an encoding session from a sample buffer."""
    cdef size_t length = len(samples)
    cdef sox_sample_t* sample_buffer = <sox_sample_t*>malloc(length * sizeof(sox_sample_t))
    if sample_buffer == NULL:
        raise SoxMemoryError("Failed to allocate sample buffer")

    try:
        # Convert Python list to C samples
        for i in range(length):
            sample_buffer[i] = samples[i]
        return <int>sox_write(format.ptr, sample_buffer, length)
    finally:
        free(sample_buffer)


def seek_samples(format: Format, offset: int, whence: int = SOX_SEEK_SET) -> int:
    """Sets the location at which next samples will be decoded."""
    cdef int result = sox_seek(format.ptr, offset, whence)
    if result != SOX_SUCCESS:
        raise SoxIOError(f"Failed to seek: {strerror(result)}")
    return result


def find_effect(name: str) -> EffectHandler:
    """Finds the effect handler with the given name.

    Args:
        name: Name of the effect (e.g., 'trim', 'rate', 'vol', 'reverb')

    Returns:
        EffectHandler object if found, None otherwise

    Example:
        >>> handler = sox.find_effect('trim')
        >>> if handler:
        ...     effect = sox.Effect(handler)
        ...     effect.set_options(['0', '10'])
    """
    cdef bytes name_bytes = name.encode('utf-8')
    cdef const sox_effect_handler_t* handler = sox_find_effect(name_bytes)
    if handler == NULL:
        return None
    return EffectHandler.from_ptr(<sox_effect_handler_t*>handler)


def find_format(name: str, ignore_devices: bool = False) -> FormatHandler:
    """Finds a format handler by name."""
    cdef bytes name_bytes = name.encode('utf-8')
    cdef const sox_format_handler_t* handler = sox_find_format(name_bytes, <sox_bool>ignore_devices)
    if handler == NULL:
        return None
    return FormatHandler.from_ptr(<sox_format_handler_t*>handler)

# def flow_effects(EffectsChain chain):
#     assert sox_flow_effects(chain.ptr, NULL, NULL) == SOX_SUCCESS

