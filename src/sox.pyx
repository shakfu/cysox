cimport sox


def version() -> str:
    """Returns version number string of libSoX, for example, 14.4.0."""
    return (<const char*>sox_version()).decode()


def version_info():
    """Returns information about this build of libsox."""
    cdef sox_version_info_t* info = sox_version_info()
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


def get_encodings_info():
    """Returns a pointer to the list of available encodings."""
    cdef sox_encodings_info_t* encodings = sox_get_encodings_info()
    if encodings == NULL:
        return []
    
    result = []
    cdef int i = 0
    while encodings[i].name != NULL:
        result.append({
            'flags': encodings[i].flags,
            'name': encodings[i].name.decode(),
            'desc': encodings[i].desc.decode() if encodings[i].desc else None
        })
        i += 1
    
    return result


def format_init() -> int:
    """Find and load format handler plugins."""
    return sox_format_init()


def format_quit():
    """Unload format handler plugins."""
    sox_format_quit()


def init() -> int:
    """Initialize effects library."""
    return sox_init()


def quit() -> int:
    """Close effects library and unload format handler plugins."""
    return sox_quit()


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


def num_comments(comments) -> int:
    """Returns the number of items in the metadata block."""
    # This would need proper handling of sox_comments_t
    # For now, returning a placeholder
    return 0


def append_comment(comments, item: str):
    """Adds an 'id=value' item to the metadata block."""
    cdef bytes item_bytes = item.encode('utf-8')
    # This would need proper handling of sox_comments_t
    # sox_append_comment(comments, item_bytes)


# def find_comment(comments, id_str: str) -> str:
#     """If 'id=value' is found, return value, else return null."""
#     cdef bytes id_bytes = id_str.encode('utf-8')
#     cdef char* result = sox_find_comment(comments, id_bytes)
#     if result == NULL:
#         return None
#     return result.decode('utf-8')


def find_format(name: str, ignore_devices: bool = False):
    """Finds a format handler by name."""
    cdef bytes name_bytes = name.encode('utf-8')
    cdef sox_format_handler_t* handler = sox_find_format(name_bytes, ignore_devices)
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
    cdef sox_effect_handler_t* handler = sox_find_effect(name_bytes)
    if handler == NULL:
        return None
    
    return {
        'name': handler.name.decode() if handler.name else None,
        'usage': handler.usage.decode() if handler.usage else None,
        'flags': handler.flags,
        'priv_size': handler.priv_size
    }


