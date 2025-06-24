# Version utility functions

def lib_version(major: int, minor: int, patch: int) -> int:
    """Compute a 32-bit integer API version from three 8-bit parts."""
    return (((major) << 16) + ((minor) << 8) + (patch))

def lib_version_code() -> int:
    """Get the current libSoX version code."""
    return lib_version(14, 4, 2)


def int_min(bits: int) -> int:
    """Returns the smallest (negative) value storable in a twos-complement signed
    integer with the specified number of bits, cast to an unsigned integer.

    for example, SOX_INT_MIN(8) = 0x80, SOX_INT_MIN(16) = 0x8000, etc.
    @param bits Size of value for which to calculate minimum.
    @returns the smallest (negative) value storable in a twos-complement signed
    integer with the specified number of bits, cast to an unsigned integer.
    """
    return (1 <<((bits)-1))

def int_max(bits: int) -> int:
    """Returns the largest (positive) value storable in a twos-complement signed
    integer with the specified number of bits, cast to an unsigned integer.

    for example, SOX_INT_MAX(8) = 0x7F, SOX_INT_MAX(16) = 0x7FFF, etc.
    @param bits Size of value for which to calculate maximum.
    @returns the largest (positive) value storable in a twos-complement signed
    integer with the specified number of bits, cast to an unsigned integer.
    """
    return ((-1 + 2**32)>>(33-(bits)))

def uint_max(bits: int) -> int:
    """Returns the largest value storable in an unsigned integer with the specified
    number of bits; 

    for example, SOX_UINT_MAX(8) = 0xFF, SOX_UINT_MAX(16) = 0xFFFF, etc.
    @param bits Size of value for which to calculate maximum.
    @returns the largest value storable in an unsigned integer with the specified
    number of bits.
    """
    return int_min(bits) | int_max(bits)



# Add error code constants
# ERROR_CODES = {
#     'SOX_SUCCESS': SOX_SUCCESS,
#     'SOX_EOF': SOX_EOF,
#     'SOX_EHDR': SOX_EHDR,
#     'SOX_EFMT': SOX_EFMT,
#     'SOX_ENOMEM': SOX_ENOMEM,
#     'SOX_EPERM': SOX_EPERM,
#     'SOX_ENOTSUP': SOX_ENOTSUP,
#     'SOX_EINVAL': SOX_EINVAL,
# }

# Sample conversion utility functions
# def sample_to_unsigned(bits: int, sample: int, clips: int) -> int:
#     """Converts sox_sample_t to an unsigned integer of width (bits).

#     bits    Width of resulting sample (1 through 32).
#     sample  Input sample to be converted.
#     clips   Variable that is incremented if the result is too big.
#     returns Unsigned integer of width (bits).
#     """
#     return SOX_SAMPLE_TO_UNSIGNED(bits, sample, clips)


# cdef int demo():
#     return SOX_SAMPLE_TO_UNSIGNED(8, 121330, 0)

# def sample_to_signed(bits: int, sample: int, clips: int) -> int:
#     """Converts sox_sample_t to a signed integer of width (bits).

#     bits    Width of resulting sample (1 through 32).
#     sample  Input sample to be converted.
#     clips   Variable that is incremented if the result is too big.
#     returns Signed integer of width (bits).        
#     """
#     return SOX_SAMPLE_TO_SIGNED(bits, sample, clips)

# def signed_to_sample(bits: int, value: int) -> int:
#     """Converts signed integer of width (bits) to sox_sample_t.
    
#     bits    Width of input sample (1 through 32).
#     sample  Input sample to be converted.
#     returns SoX native sample value.    
#     """
#     return SOX_SIGNED_TO_SAMPLE(bits, value)

# def unsigned_to_sample(bits: int, value: int) -> int:
#     """Converts unsigned integer of width (bits) to sox_sample_t.
    
#     bits    Width of input sample (1 through 32).
#     sample  Input sample to be converted.
#     returns SoX native sample value.
#     """
#     return SOX_UNSIGNED_TO_SAMPLE(bits, value)

# def unsigned_8bit_to_sample(value: int, clips: int) -> int:
#     """Convert 8-bit unsigned value to sample."""
#     return SOX_UNSIGNED_8BIT_TO_SAMPLE(value, clips)

# def signed_8bit_to_sample(value: int, clips: int) -> int:
#     """Convert 8-bit signed value to sample."""
#     return SOX_SIGNED_8BIT_TO_SAMPLE(value, clips)

# def unsigned_16bit_to_sample(value: int, clips: int) -> int:
#     """Convert 16-bit unsigned value to sample."""
#     return SOX_UNSIGNED_16BIT_TO_SAMPLE(value, clips)

# def signed_16bit_to_sample(value: int, clips: int) -> int:
#     """Convert 16-bit signed value to sample."""
#     return SOX_SIGNED_16BIT_TO_SAMPLE(value, clips)

# def unsigned_24bit_to_sample(value: int, clips: int) -> int:
#     """Convert 24-bit unsigned value to sample."""
#     return SOX_UNSIGNED_24BIT_TO_SAMPLE(value, clips)

# def signed_24bit_to_sample(value: int, clips: int) -> int:
#     """Convert 24-bit signed value to sample."""
#     return SOX_SIGNED_24BIT_TO_SAMPLE(value, clips)

# def unsigned_32bit_to_sample(value: int, clips: int) -> int:
#     """Convert 32-bit unsigned value to sample."""
#     return SOX_UNSIGNED_32BIT_TO_SAMPLE(value, clips)

# def signed_32bit_to_sample(value: int, clips: int) -> int:
#     """Convert 32-bit signed value to sample."""
#     return SOX_SIGNED_32BIT_TO_SAMPLE(value, clips)

# def float_32bit_to_sample(value: float, clips: int) -> int:
#     """Convert 32-bit float value to sample."""
#     return SOX_FLOAT_32BIT_TO_SAMPLE(value, clips)

# def float_64bit_to_sample(value: float, clips: int) -> int:
#     """Convert 64-bit float value to sample."""
#     return SOX_FLOAT_64BIT_TO_SAMPLE(value, clips)

# def sample_to_unsigned_8bit(sample: int, clips: int) -> int:
#     """Convert sample to 8-bit unsigned value."""
#     return SOX_SAMPLE_TO_UNSIGNED_8BIT(sample, clips)

# def sample_to_signed_8bit(sample: int, clips: int) -> int:
#     """Convert sample to 8-bit signed value."""
#     return SOX_SAMPLE_TO_SIGNED_8BIT(sample, clips)

# def sample_to_unsigned_16bit(sample: int, clips: int) -> int:
#     """Convert sample to 16-bit unsigned value."""
#     return SOX_SAMPLE_TO_UNSIGNED_16BIT(sample, clips)

# def sample_to_signed_16bit(sample: int, clips: int) -> int:
#     """Convert sample to 16-bit signed value."""
#     return SOX_SAMPLE_TO_SIGNED_16BIT(sample, clips)

# def sample_to_unsigned_24bit(sample: int, clips: int) -> int:
#     """Convert sample to 24-bit unsigned value."""
#     return SOX_SAMPLE_TO_UNSIGNED_24BIT(sample, clips)

# def sample_to_signed_24bit(sample: int, clips: int) -> int:
#     """Convert sample to 24-bit signed value."""
#     return SOX_SAMPLE_TO_SIGNED_24BIT(sample, clips)

# def sample_to_unsigned_32bit(sample: int, clips: int) -> int:
#     """Convert sample to 32-bit unsigned value."""
#     return SOX_SAMPLE_TO_UNSIGNED_32BIT(sample, clips)

# def sample_to_signed_32bit(sample: int, clips: int) -> int:
#     """Convert sample to 32-bit signed value."""
#     return SOX_SAMPLE_TO_SIGNED_32BIT(sample, clips)

# def sample_to_float_32bit(sample: int, clips: int) -> float:
#     """Convert sample to 32-bit float value."""
#     return SOX_SAMPLE_TO_FLOAT_32BIT(sample, clips)

# def sample_to_float_64bit(sample: int, clips: int) -> float:
#     """Convert sample to 64-bit float value."""
#     return SOX_SAMPLE_TO_FLOAT_64BIT(sample, clips)

# # Clip counting utility functions
# def sample_clip_count(sample: int, clips: int) -> int:
#     """Get clip count for sample."""
#     return SOX_SAMPLE_CLIP_COUNT(sample, clips)

# # def round_clip_count(value: float, clips: int) -> int:
# #     """Get clip count for rounded value."""
# #     return SOX_ROUND_CLIP_COUNT(value, clips)

# def integer_clip_count(value: int, clips: int) -> int:
#     """Get clip count for integer value."""
#     return SOX_INTEGER_CLIP_COUNT(value, clips)

# def clip_count_16bit(value: int, clips: int) -> int:
#     """Get clip count for 16-bit value."""
#     return SOX_16BIT_CLIP_COUNT(value, clips)

# def clip_count_24bit(value: int, clips: int) -> int:
#     """Get clip count for 24-bit value."""
#     return SOX_24BIT_CLIP_COUNT(value, clips)

# Utility functions for integer limits
# def int_min(bits: int) -> int:
#     """Get minimum value for given bit depth."""
#     return SOX_INT_MIN(bits)

# def int_max(bits: int) -> int:
#     """Get maximum value for given bit depth."""
#     return SOX_INT_MAX(bits)

# def uint_max(bits: int) -> int:
#     """Get maximum unsigned value for given bit depth."""
#     return SOX_UINT_MAX(bits)

