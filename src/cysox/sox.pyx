"""sox.pyx - a thin wrapper around libsox

classes:

- [x] SignalInfo
- [x] EncodingsInfo
- [x] EncodingInfo
- [x] LoopInfo
- [x] InstrInfo
- [x] FileInfo
- [x] OutOfBand
- [x] VersionInfo
- [x] Globals
- [x] EffectsGlobals
- [x] Format
- [x] FormatHandler
- [x] FormatTab
- [x] EffectHandler
- [x] Effect
- [x] EffectsChain

"""

# from collections import namedtuple
from types import SimpleNamespace

cimport sox


constant = SimpleNamespace({
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


cdef class SignalInfo:
    """Signal parameters

    members should be set to SOX_UNSPEC (= 0) if unknown.
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

    def __init__(self, rate: float = 0.0, channels: int = 0, precision: int = 0, length: int = 0, mult: float = 0.0):
        self.ptr = <sox_signalinfo_t*>malloc(sizeof(sox_signalinfo_t))
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
        return self.ptr.rate

    @rate.setter
    def rate(self, sox_rate_t value):
        self.ptr.rate = value

    @property
    def channels(self) -> int:
        """number of sound channels, 0 if unknown"""
        return self.ptr.channels

    @channels.setter
    def channels(self, int value):
        self.ptr.channels = value

    @property
    def precision(self) -> int:
        """bits per sample, 0 if unknown"""
        return self.ptr.precision

    @precision.setter
    def precision(self, int value):
        self.ptr.precision = value

    @property
    def length(self) -> sox_uint64_t:
        """samples * chans in file, 0 if unknown, -1 if unspecified"""
        return self.ptr.length

    @length.setter
    def length(self, sox_uint64_t value):
        self.ptr.length = value

    @property
    def mult(self) -> float:
        """Effects headroom multiplier may be null"""
        if not self.ptr.mult:
            return 0.0
        return self.ptr.mult[0]

    @mult.setter
    def mult(self, float value):
        if value == 0.0:
            self.ptr.mult = NULL
        elif self.ptr.mult is NULL:
            self.ptr.mult = <double*>malloc(sizeof(double))
            self.ptr.mult[0] = value
        else:
            self.ptr.mult[0] = value


class EncodingsInfo:
    """Basic information about an encoding."""

    def __init__(self, int flags, str name, str desc):
        self.flags = flags
        self.name = name
        self.desc = desc

    def __repr__(self):
        return f"<EncodingsInfo '{self.name}' '{self.desc}' '{self.type}'>"

    @property
    def type(self):
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

    def __init__(self, encoding: int = 0, bits_per_sample: int = 0, compression: float = 0.0, 
                 reverse_bytes: int = 0, reverse_nibbles: int = 0, reverse_bits: int = 0, 
                 opposite_endian: bool = False):
        self.ptr = <sox_encodinginfo_t*>malloc(sizeof(sox_encodinginfo_t))
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
        return self.ptr.encoding

    @encoding.setter
    def encoding(self, sox_encoding_t value):
        self.ptr.encoding = value

    @property
    def bits_per_sample(self) -> int:
        """0 if unknown or variable uncompressed value if lossless compressed value if lossy"""
        return self.ptr.bits_per_sample

    @bits_per_sample.setter
    def bits_per_sample(self, unsigned value):
        self.ptr.bits_per_sample = value

    @property
    def compression(self) -> float:
        """compression factor (where applicable)"""
        return self.ptr.compression

    @compression.setter
    def compression(self, double value):
        self.ptr.compression = value

    @property
    def reverse_bytes(self) -> int:
        """Should bytes be reversed?"""
        return self.ptr.reverse_bytes

    @reverse_bytes.setter
    def reverse_bytes(self, sox_option_t value):
        self.ptr.reverse_bytes = value

    @property
    def reverse_nibbles(self) -> int:
        """Should nibbles be reversed?"""
        return self.ptr.reverse_nibbles

    @reverse_nibbles.setter
    def reverse_nibbles(self, sox_option_t value):
        self.ptr.reverse_nibbles = value

    @property
    def reverse_bits(self) -> int:
        """Should bits be reversed?"""
        return self.ptr.reverse_bits

    @reverse_bits.setter
    def reverse_bits(self, sox_option_t value):
        self.ptr.reverse_bits = value

    @property
    def opposite_endian(self) -> bool:
        """If set to true, the format should reverse its default endianness."""
        return self.ptr.opposite_endian

    @opposite_endian.setter
    def opposite_endian(self, sox_bool value):
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

    def __init__(self, start: int = 0, length: int = 0, count: int = 0, type: int = 0):
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
        return self.ptr.start

    @start.setter
    def start(self, sox_uint64_t value):
        self.ptr.start = value

    @property
    def length(self) -> sox_uint64_t:
        """length"""
        return self.ptr.length

    @length.setter
    def length(self, sox_uint64_t value):
        self.ptr.length = value

    @property
    def count(self) -> int:
        """number of repeats, 0=forever"""
        return self.ptr.count

    @count.setter
    def count(self, unsigned value):
        self.ptr.count = value

    @property
    def type(self) -> int:
        """0=no, 1=forward, 2=forward/back (see sox_loop_* for valid values)"""
        return self.ptr.type

    @type.setter
    def type(self, unsigned char value):
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

    def __init__(self, buf: bytes = None, size: int = 0, count: int = 0, pos: int = 0):
        self.ptr = <sox_fileinfo_t*>malloc(sizeof(sox_fileinfo_t))
        self.buf = buf
        self.size = size
        self.count = count
        self.pos = pos
        self.owner = True

    @staticmethod
    cdef FileInfo from_ptr(sox_fileinfo_t* ptr, bint owner=False):
        cdef FileInfo wrapper = FileInfo.__new__(FileInfo)
        wrapper.ptr = ptr
        wrapper.owner = owner
        return wrapper

    @property
    def buf(self) -> bytes:
        """Pointer to data buffer"""
        if self.ptr.buf == NULL:
            return None
        return self.ptr.buf[:self.ptr.size]

    @buf.setter
    def buf(self, bytes value):
        if value is None:
            self.ptr.buf = NULL
        else:
            self.ptr.buf = value

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
            free(self.ptr)
            if self.ptr.comments:
                sox_delete_comments(&self.ptr.comments)
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

    @staticmethod
    cdef Globals from_ptr(sox_globals_t* ptr, bint owner=False):
        cdef Globals wrapper = Globals.__new__(Globals)
        wrapper.ptr = ptr
        wrapper.owner = owner
        return wrapper

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
    cdef sox_format_t* ptr
    cdef bint owner

    def __cinit__(self):
        self.ptr = NULL
        self.owner = False

    def __dealloc__(self):
        if self.ptr is not NULL and self.owner is True:
            assert SOX_SUCCESS == sox_close(self.ptr)
            self.ptr = NULL

    def __init__(self, str filename, SignalInfo signal = None, EncodingInfo encoding = None):
        """Opens a decoding session for a file. Returned handle must be closed with sox_close().
        
        returns The handle for the new session, or null on failure.
        """
        self.ptr = sox_open_read(
            filename.encode(), 
            signal.ptr if signal else NULL,
            encoding.ptr if encoding else NULL,
            NULL
        )
        if self.ptr is NULL:
            raise MemoryError


    @staticmethod
    cdef Format from_ptr(sox_format_t* ptr, bint owner=False):
        cdef Format wrapper = Format.__new__(Format)
        wrapper.ptr = ptr
        wrapper.owner = owner
        return wrapper

    @property
    def filename(self) -> str:
        return self.ptr.filename.decode()

    @property
    def signal(self) -> SignalInfo:
        return SignalInfo.from_ptr(&self.ptr.signal)

    @property
    def encoding(self) -> EncodingInfo:
        return EncodingInfo.from_ptr(&self.ptr.encoding)

    @property
    def filetype(self) -> str:
        return self.ptr.filetype.decode()


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
        self.ptr = <sox_format_handler_t*>sox_write_handler(path.encode(), NULL, NULL)
        self.owner = True
        if self.ptr is NULL:
            raise MemoryError

    @staticmethod
    cdef FormatHandler from_ptr(sox_format_handler_t* ptr, bint owner=False):
        cdef FormatHandler wrapper = FormatHandler.__new__(FormatHandler)
        wrapper.ptr = ptr
        wrapper.owner = owner
        return wrapper

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
        self.name = name
        self.owner = True

    @staticmethod
    cdef FormatTab from_ptr(sox_format_tab_t* ptr, bint owner=False):
        cdef FormatTab wrapper = FormatTab.__new__(FormatTab)
        wrapper.ptr = ptr
        wrapper.owner = owner
        return wrapper

    @property
    def name(self) -> str:
        """Name of format handler"""
        if self.ptr.name == NULL:
            return None
        return self.ptr.name.decode()

    @name.setter
    def name(self, str value):
        if value is None:
            self.ptr.name = NULL
        else:
            # Note: This is a char* in the struct, but we need to be careful about memory management
            # This setter is provided for completeness but won't actually work safely
            pass

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

    def __init__(self):
        self.ptr = <sox_effect_t*>malloc(sizeof(sox_effect_t))
        self.owner = True

    @staticmethod
    cdef Effect from_ptr(sox_effect_t* ptr, bint owner=False):
        cdef Effect wrapper = Effect.__new__(Effect)
        wrapper.ptr = ptr
        wrapper.owner = owner
        return wrapper

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


cdef class EffectsChain:
    """Effects chain structure."""
    cdef sox_effects_chain_t* ptr
    cdef bint owner

    def __cinit__(self):
        self.ptr = NULL
        self.owner = False

    def __dealloc__(self):
        if self.ptr is not NULL and self.owner is True:
            free(self.ptr)
            self.ptr = NULL

    def __init__(self):
        self.ptr = <sox_effects_chain_t*>malloc(sizeof(sox_effects_chain_t))
        self.owner = True

    @staticmethod
    cdef EffectsChain from_ptr(sox_effects_chain_t* ptr, bint owner=False):
        cdef EffectsChain wrapper = EffectsChain.__new__(EffectsChain)
        wrapper.ptr = ptr
        wrapper.owner = owner
        return wrapper

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


def get_globals():
    """Returns a pointer to the structure with libSoX's global settings."""
    cdef sox_globals_t* globals = sox_get_globals()
    if globals == NULL:
        return None
    
    return {
        'verbosity': globals.verbosity,
        'repeatable': globals.repeatable,
        'bufsiz': globals.bufsiz,
        'input_bufsiz': globals.input_bufsiz,
        'ranqd1': globals.ranqd1,
        'stdin_in_use_by': globals.stdin_in_use_by.decode() if globals.stdin_in_use_by else None,
        'stdout_in_use_by': globals.stdout_in_use_by.decode() if globals.stdout_in_use_by else None,
        'subsystem': globals.subsystem.decode() if globals.subsystem else None,
        'tmp_path': globals.tmp_path.decode() if globals.tmp_path else None,
        'use_magic': globals.use_magic,
        'use_threads': globals.use_threads,
        'log2_dft_min_size': globals.log2_dft_min_size
    }


def get_encodings_info() -> list[dict]:
    """Returns the list of available encodings."""
    cdef const sox_encodings_info_t* encodings = sox_get_encodings_info()
    if encodings == NULL:
        return []
    
    result = []
    cdef int i = 0
    while encodings[i].name != NULL:
        result.append(
            dict(
                flags=encodings[i].flags,
                name=encodings[i].name.decode(),
                desc=encodings[i].desc.decode() if encodings[i].desc else None
            )
        )
        i += 1
    return result

def get_encodings() -> list[EncodingsInfo]:
    _encodings = get_encodings_info()
    return [EncodingsInfo(**e) for e in _encodings if e['flags'] < 3]

def format_init():
    """Find and load format handler plugins."""
    assert SOX_SUCCESS == sox_format_init()

def format_quit():
    """Unload format handler plugins."""
    sox_format_quit()

def init():
    """Initialize effects library."""
    assert SOX_SUCCESS == sox_init()

def quit():
    """Close effects library and unload format handler plugins."""
    assert SOX_SUCCESS == sox_quit()

def strerror(sox_errno: int) -> str:
    """Converts a SoX error code into an error string."""
    return (<const char*>sox_strerror(sox_errno)).decode()


def is_playlist(filename: str) -> bool:
    """Returns true if the specified file is a known playlist file type."""
    cdef bytes filename_bytes = filename.encode('utf-8')
    return sox_is_playlist(filename_bytes)


def basename(filename: str) -> str:
    """Gets the basename of the specified file."""
    cdef char base_buffer[256]
    cdef bytes filename_bytes = filename.encode('utf-8')
    cdef size_t result = sox_basename(base_buffer, 256, filename_bytes)
    
    if result == 0:
        return ""
    
    return base_buffer[:result].decode('utf-8')


def precision(encoding: int, bits_per_sample: int) -> int:
    """Given an encoding and bits_per_sample, returns the number of useful bits per sample."""
    return sox_precision(<sox_encoding_t>encoding, <unsigned>bits_per_sample)





def find_format(name: str, ignore_devices: bool = False):
    """Finds a format handler by name."""
    cdef bytes name_bytes = name.encode('utf-8')
    cdef const sox_format_handler_t* handler = sox_find_format(name_bytes, ignore_devices)
    if handler == NULL:
        return None
    
    return {
        'description': handler.description.decode() if handler.description else None,
        'names': [handler.names[i].decode() for i in range(10) if handler.names[i] != NULL]  # Assuming max 10 names
    }


def get_effects_globals():
    """Returns global parameters for effects."""
    cdef sox_effects_globals_t* globals = sox_get_effects_globals()
    if globals == NULL:
        return None
    
    return {
        'plot': globals.plot
    }


def find_effect(name: str):
    """Finds the effect handler with the given name."""
    cdef bytes name_bytes = name.encode('utf-8')
    cdef const sox_effect_handler_t* handler = sox_find_effect(name_bytes)
    if handler == NULL:
        return None
    
    return {
        'name': handler.name.decode() if handler.name else None,
        'usage': handler.usage.decode() if handler.usage else None,
        'flags': handler.flags,
        'priv_size': handler.priv_size
    }


def format_supports_encoding(str path, EncodingInfo encoding) -> bool:
    """Returns true if the format handler for the specified file type supports the specified encoding."""
    return <bint>sox_format_supports_encoding(path.encode(), NULL, encoding.ptr)







