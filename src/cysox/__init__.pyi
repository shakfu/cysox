# Type stubs for cysox
# This file provides type hints for IDEs and type checkers

from typing import Optional, List, Union, Tuple
import array

# Exception classes
class SoxError(Exception): ...
class SoxInitError(SoxError): ...
class SoxFormatError(SoxError): ...
class SoxEffectError(SoxError): ...
class SoxIOError(SoxError): ...
class SoxMemoryError(SoxError): ...

# Core classes
class SignalInfo:
    rate: float
    channels: int
    precision: int
    length: int
    mult: Optional[float]

    def __init__(
        self,
        rate: float = 0.0,
        channels: int = 0,
        precision: int = 0,
        length: int = 0,
        mult: float = 0.0
    ) -> None: ...

class EncodingInfo:
    encoding: int
    bits_per_sample: int
    compression: float
    reverse_bytes: int
    reverse_nibbles: int
    reverse_bits: int
    opposite_endian: bool

    def __init__(
        self,
        encoding: int = 0,
        bits_per_sample: int = 0,
        compression: float = 0.0,
        reverse_bytes: int = 0,
        reverse_nibbles: int = 0,
        reverse_bits: int = 0,
        opposite_endian: bool = False
    ) -> None: ...

class Format:
    filename: str
    signal: SignalInfo
    encoding: EncodingInfo
    filetype: str
    seekable: bool
    mode: str
    olength: int
    clips: int
    sox_errno: int
    sox_errstr: str

    def __init__(
        self,
        filename: str,
        signal: Optional[SignalInfo] = None,
        encoding: Optional[EncodingInfo] = None,
        filetype: Optional[str] = None,
        mode: str = 'r'
    ) -> None: ...

    def __enter__(self) -> Format: ...
    def __exit__(self, exc_type, exc_val, exc_tb) -> bool: ...

    def read(self, length: int) -> List[int]: ...
    def read_buffer(self, length: int) -> memoryview: ...
    def read_into(self, buffer) -> int: ...
    def write(self, samples: Union[List[int], array.array, memoryview]) -> int: ...
    def seek(self, offset: int, whence: int = 0) -> int: ...
    def close(self) -> int: ...

class EffectHandler:
    name: str
    usage: str
    flags: int
    priv_size: int

    @staticmethod
    def find(name: str, ignore_devices: bool = False) -> Optional[EffectHandler]: ...

class Effect:
    handler: EffectHandler
    in_signal: SignalInfo
    out_signal: SignalInfo
    in_encoding: Optional[EncodingInfo]
    out_encoding: Optional[EncodingInfo]
    clips: int
    flows: int
    flow: int

    def __init__(self, handler: EffectHandler) -> None: ...
    def set_options(self, options: List[str]) -> int: ...
    def stop(self) -> int: ...
    def trim_get_start(self) -> int: ...
    def trim_clear_start(self) -> None: ...

class EffectsChain:
    effects: List[Effect]
    length: int
    table_size: int

    def __init__(
        self,
        in_encoding: Optional[EncodingInfo] = None,
        out_encoding: Optional[EncodingInfo] = None
    ) -> None: ...

    def add_effect(
        self,
        effect: Effect,
        in_signal: SignalInfo,
        out_signal: SignalInfo
    ) -> int: ...

    def flow_effects(self, callback=None, client_data=None) -> int: ...
    def get_clips(self) -> int: ...
    def push_effect_last(self, effect: Effect) -> None: ...
    def pop_effect_last(self) -> Optional[Effect]: ...
    def delete_effect_last(self) -> None: ...
    def delete_effects(self) -> None: ...

class FormatHandler:
    sox_lib_version_code: int
    description: str
    names: List[str]
    flags: int
    priv_size: int

    def __init__(self, path: str) -> None: ...

    @staticmethod
    def find(name: str, ignore_devices: bool = False) -> Optional[FormatHandler]: ...

class Globals:
    verbosity: int
    repeatable: bool
    bufsiz: int
    input_bufsiz: int
    ranqd1: int
    stdin_in_use_by: Optional[str]
    stdout_in_use_by: Optional[str]
    subsystem: Optional[str]
    tmp_path: Optional[str]
    use_magic: bool
    use_threads: bool
    log2_dft_min_size: int

    def as_dict(self) -> dict: ...

# Functions
def init() -> None: ...
def quit() -> None: ...
def format_init() -> None: ...
def format_quit() -> None: ...
def version() -> str: ...
def version_info() -> dict: ...
def strerror(sox_errno: int) -> str: ...
def find_effect(name: str) -> Optional[EffectHandler]: ...
def find_format(name: str, ignore_devices: bool = False) -> Optional[FormatHandler]: ...
def is_playlist(filename: str) -> bool: ...
def basename(filename: str) -> str: ...
def precision(encoding: int, bits_per_sample: int) -> int: ...
def format_supports_encoding(path: str, encoding: EncodingInfo) -> bool: ...
def get_encodings() -> List: ...
def get_effects_globals() -> dict: ...
def get_format_fns() -> List[dict]: ...
def get_effect_fns() -> List[int]: ...

# Memory I/O
def open_mem_read(
    buffer: bytes,
    signal: Optional[SignalInfo] = None,
    encoding: Optional[EncodingInfo] = None,
    filetype: Optional[str] = None
) -> Format: ...

def open_mem_write(
    buffer: bytearray,
    signal: SignalInfo,
    encoding: EncodingInfo,
    filetype: Optional[str] = None,
    oob = None
) -> Format: ...

def open_memstream_write(
    signal: SignalInfo,
    encoding: EncodingInfo,
    filetype: Optional[str] = None,
    oob = None
) -> Tuple[Format, int, int]: ...

# Sample I/O
def read_samples(format: Format, buffer: List, length: int) -> int: ...
def write_samples(format: Format, samples: List) -> int: ...
def seek_samples(format: Format, offset: int, whence: int = 0) -> int: ...

# Callback exception handling
def get_last_callback_exception() -> Optional[Tuple[type, BaseException, object]]: ...

# Constants
SUCCESS: int
EOF: int
EHDR: int
EFMT: int
ENOMEM: int
EPERM: int
ENOTSUP: int
EINVAL: int

SOX_SEEK_SET: int

ENCODINGS: List[Tuple[str, str]]
